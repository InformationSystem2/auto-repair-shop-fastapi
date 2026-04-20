import json
import logging
import os

import vertexai
from vertexai.generative_models import GenerationConfig, GenerativeModel, Tool

logger = logging.getLogger(__name__)

VERTEX_PROJECT_ID = os.getenv("VERTEX_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
VERTEX_MODEL_NAME = os.getenv("VERTEX_MODEL_NAME", "gemini-2.5-flash")

def _build_estimation_prompt(diagnostic: str, category: str) -> str:
    return (
        f"You are an automotive cost estimation assistant. Using Google Search, find the current "
        f"market prices (labor and parts) in Bolivia (BOB) for the following incident.\n"
        f"Diagnostic: {diagnostic}\n"
        f"Category: {category}\n\n"
        f"Respond ONLY in valid JSON with this exact structure:\n"
        "{\n"
        "  \"costo_estimado\": {\n"
        "    \"moneda\": \"BOB\",\n"
        "    \"min\": 0.0,\n"
        "    \"max\": 0.0,\n"
        "    \"justificacion\": \"Resumen de la justificacion usando precios del mercado\"\n"
        "  }\n"
        "}\n"
    )

def estimate_cost(diagnostic: str, category: str) -> dict | None:
    if not VERTEX_PROJECT_ID:
        logger.warning("VERTEX_PROJECT_ID is not configured for estimation_service")
        return None

    try:
        vertexai.init(project=VERTEX_PROJECT_ID, location=VERTEX_LOCATION)
        
        # Tools: Using Grounding with Google Search
        try:
            tool = Tool.from_dict({"google_search": {}})
        except Exception:
            # Fallback for very old SDKs if needed
            tool = Tool.from_google_search_retrieval(google_search_retrieval=vertexai.generative_models.grounding.GoogleSearchRetrieval())
        
        model = GenerativeModel(VERTEX_MODEL_NAME, tools=[tool])

        prompt = _build_estimation_prompt(diagnostic, category)

        response = model.generate_content(
            prompt,
            generation_config=GenerationConfig(
                temperature=0.2,
                top_p=0.8,
            ),
        )

        text = response.text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Fallback inline parsing
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(text[start:end+1])
            return None
    except Exception as exc:
        logger.exception("Grounding estimation failed: %s", exc)
        return None
