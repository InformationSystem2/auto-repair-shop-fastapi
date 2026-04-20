import io
import json
import logging
import os
from dataclasses import dataclass
from urllib.parse import urlparse
from urllib.request import urlopen

from google.cloud import storage
from PIL import Image, ImageEnhance, ImageOps
import vertexai
from vertexai.generative_models import GenerationConfig, GenerativeModel, Part
from app.module_incidents.ai.services.storage_service import get_storage_client


logger = logging.getLogger(__name__)

VERTEX_PROJECT_ID = os.getenv("VERTEX_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
VERTEX_MODEL_NAME = os.getenv("VERTEX_MODEL_NAME", "gemini-1.5-flash")
HTTP_IMAGE_TIMEOUT = float(os.getenv("GOOGLE_VISION_HTTP_TIMEOUT", "20"))

_ALLOWED_CATEGORIES = {
    "battery",
    "tire",
    "engine",
    "ac",
    "transmission",
    "towing",
    "locksmith",
    "general",
    "collision",
    "uncertain",
}
_ALLOWED_PRIORITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


@dataclass
class PreparedImage:
    source_url: str
    content: bytes
    mime_type: str
    preprocessing: dict


def _download_image(file_url: str) -> bytes:
    parsed = urlparse(file_url)
    if parsed.scheme == "gs":
        client = get_storage_client()
        bucket = client.bucket(parsed.netloc)
        blob = bucket.blob(parsed.path.lstrip("/"))
        return blob.download_as_bytes()


    if parsed.scheme in {"http", "https"}:
        with urlopen(file_url, timeout=HTTP_IMAGE_TIMEOUT) as response:
            return response.read()

    raise ValueError("Only gs://, http://, and https:// URLs are supported for images")


def _enhance_image(image_bytes: bytes) -> tuple[bytes, dict]:
    with Image.open(io.BytesIO(image_bytes)) as img:
        img = ImageOps.exif_transpose(img).convert("RGB")
        original_size = img.size

        max_side = 1600
        img.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
        img = ImageEnhance.Contrast(img).enhance(1.12)
        img = ImageEnhance.Sharpness(img).enhance(1.08)

        out = io.BytesIO()
        img.save(out, format="JPEG", quality=88, optimize=True)
        enhanced_bytes = out.getvalue()

    preprocessing = {
        "original_size": {"width": original_size[0], "height": original_size[1]},
        "enhanced_size": {"width": img.size[0], "height": img.size[1]},
        "output_format": "image/jpeg",
    }
    return enhanced_bytes, preprocessing


def prepare_image_for_vertex(file_url: str) -> PreparedImage:
    original = _download_image(file_url)
    enhanced, preprocessing = _enhance_image(original)
    return PreparedImage(
        source_url=file_url,
        content=enhanced,
        mime_type="image/jpeg",
        preprocessing=preprocessing,
    )


def _build_prompt(description: str, audio_transcript: str | None) -> str:
    transcript = (audio_transcript or "").strip()
    return (
        "You are an automotive incident triage assistant. Analyze the provided accident images and text. "
        "Respond ONLY in valid JSON with this exact structure (do not use markdown blocks, just raw JSON):\n"
        "{\n"
        "  \"sistema\": {\n"
        "    \"categoria\": \"categoria_elegida\",\n"
        "    \"prioridad\": \"PRIORIDAD_ELEGIDA\",\n"
        "    \"requiere_grua\": false,\n"
        "    \"especialidad_requerida\": \"especialidad\",\n"
        "    \"confianza\": 0.9\n"
        "  },\n"
        "  \"tecnico\": {\n"
        "    \"diagnostico_tecnico\": \"string\",\n"
        "    \"herramientas_sugeridas\": [\"string\"],\n"
        "    \"procedimiento_recomendado\": \"string\"\n"
        "  },\n"
        "  \"cliente\": {\n"
        "    \"mensaje_tranquilizador\": \"string\",\n"
        "    \"posible_causa\": \"string\",\n"
        "    \"consejo_seguridad\": \"string\"\n"
        "  }\n"
        "}\n"
        "Rules: The category MUST be ONE OF [bateria, llanta, choque, motor, ac, transmision, grua, llave, general, incierto]. "
        "The priority MUST be ONE OF [LOW, MEDIUM, HIGH, CRITICAL]. "
        "The requiere_grua MUST be a boolean. The especialidad_requerida MUST be ONE OF [electricidad, mecanica_general, chapa_pintura, neumaticos, otro]. "
        "confianza must be a float between 0 and 1. If uncertain, use categoria=incierto and confidence <= 0.5. "
        f"Description from user: {description}\n"
        f"Audio transcript (Spanish): {transcript or 'N/A'}"
    )


def _extract_json(raw_text: str) -> dict | None:
    text = raw_text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None


def _normalize_vertex_result(payload: dict) -> dict:
    # Handle both old and new schema to prevent crashes
    sistema = payload.get("sistema", {})
    tecnico = payload.get("tecnico", {})
    cliente = payload.get("cliente", {})
    
    category = str(sistema.get("categoria", payload.get("category", "incierto"))).lower().strip()
    if category not in _ALLOWED_CATEGORIES and category != "incierto":
        category = "incierto"

    priority = str(sistema.get("prioridad", payload.get("priority", "MEDIUM"))).upper().strip()
    if priority not in _ALLOWED_PRIORITIES:
        priority = "MEDIUM"

    try:
        confidence = float(sistema.get("confianza", payload.get("confidence", 0.5)))
    except (TypeError, ValueError):
        confidence = 0.5
    confidence = max(0.0, min(1.0, confidence))

    return {
        "sistema": {
            "categoria": category,
            "prioridad": priority,
            "requiere_grua": bool(sistema.get("requiere_grua", False)),
            "especialidad_requerida": sistema.get("especialidad_requerida", "otro"),
            "confianza": confidence,
        },
        "tecnico": {
            "diagnostico_tecnico": tecnico.get("diagnostico_tecnico", "No evaluado"),
            "herramientas_sugeridas": tecnico.get("herramientas_sugeridas", []),
            "procedimiento_recomendado": tecnico.get("procedimiento_recomendado", ""),
        },
        "cliente": {
            "mensaje_tranquilizador": cliente.get("mensaje_tranquilizador", "Estamos analizando su problema."),
            "posible_causa": cliente.get("posible_causa", ""),
            "consejo_seguridad": cliente.get("consejo_seguridad", "Manténgase en un lugar seguro."),
        }
    }


def analyze_incident_with_vertex(
    description: str,
    audio_transcript: str | None,
    prepared_images: list[PreparedImage],
) -> dict | None:
    if not VERTEX_PROJECT_ID:
        logger.warning("VERTEX_PROJECT_ID/GOOGLE_CLOUD_PROJECT is not configured")
        return None

    if not prepared_images:
        logger.warning("No images provided for vertex multimodal analysis")
        return None

    try:
        vertexai.init(project=VERTEX_PROJECT_ID, location=VERTEX_LOCATION)
        model = GenerativeModel(VERTEX_MODEL_NAME)

        parts: list = [_build_prompt(description, audio_transcript)]
        for image in prepared_images:
            parts.append(Part.from_data(data=image.content, mime_type=image.mime_type))

        response = model.generate_content(
            parts,
            generation_config=GenerationConfig(
                temperature=0.1,
                top_p=0.8,
                max_output_tokens=8096,
                response_mime_type="application/json",
            ),
        )

        if not getattr(response, "text", None):
            logger.warning("Vertex returned empty response text")
            return None

        parsed = _extract_json(response.text)
        if not parsed:
            logger.warning(f"Vertex response was not valid JSON. Response text was:\n{response.text}")
            return None

        return _normalize_vertex_result(parsed)
    except Exception as exc:
        logger.exception("Vertex multimodal analysis failed: %s", exc)
        return None


def analyze_image(file_url: str) -> dict | None:
    """Backward-compatible wrapper used by older flows."""
    try:
        prepared = prepare_image_for_vertex(file_url)
        return {
            "source_url": prepared.source_url,
            "preprocessing": prepared.preprocessing,
        }
    except Exception as exc:
        logger.warning("Image preparation failed for '%s': %s", file_url, exc)
        return None
