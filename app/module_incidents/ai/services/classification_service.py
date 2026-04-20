import logging
from typing import Optional

from app.module_incidents.ai.dtos.ai_dtos import ClassificationResult

logger = logging.getLogger(__name__)

_KEYWORD_MAP: dict[str, tuple[str, str]] = {
    "llanta": ("tire", "HIGH"),
    "pinch": ("tire", "MEDIUM"),
    "tire": ("tire", "HIGH"),
    "flat": ("tire", "MEDIUM"),
    "bateria": ("battery", "HIGH"),
    "battery": ("battery", "HIGH"),
    "motor": ("engine", "CRITICAL"),
    "engine": ("engine", "CRITICAL"),
    "freno": ("general", "HIGH"),
    "brake": ("general", "HIGH"),
    "aire": ("ac", "LOW"),
    " ac ": ("ac", "LOW"),
    "transmision": ("transmission", "HIGH"),
    "transmission": ("transmission", "HIGH"),
    "grua": ("towing", "MEDIUM"),
    "tow": ("towing", "MEDIUM"),
    "llave": ("locksmith", "MEDIUM"),
    "lock": ("locksmith", "MEDIUM"),
    "choque": ("general", "HIGH"),
    "collision": ("general", "HIGH"),
}


def classify_incident(
        description: str,
        audio_transcript: Optional[str] = None,
        image_analysis: Optional[dict] = None,
        text_analysis: Optional[dict] = None,
) -> ClassificationResult:
    if image_analysis:
        sistema = image_analysis.get("sistema", {})
        cliente = image_analysis.get("cliente", {})
        
        category = str(sistema.get("categoria", "incierto")).lower().strip()
        priority = str(sistema.get("prioridad", "MEDIUM")).upper().strip()

        try:
            confidence = float(sistema.get("confianza", 0.6))
        except (TypeError, ValueError):
            confidence = 0.6
        confidence = max(0.0, min(1.0, confidence))

        summary = str(cliente.get("mensaje_tranquilizador") or description[:200])

        logger.info(
            "Classification from vertex image_analysis: category=%s, priority=%s, confidence=%.2f",
            category,
            priority,
            confidence,
        )
        return ClassificationResult(
            category=category,
            priority=priority,
            confidence=confidence,
            summary=summary,
        )

    combined = " ".join(filter(None, [description, audio_transcript])).lower()

    category = "general"
    priority = "MEDIUM"
    confidence = 0.45
    summary = description[:200]

    for keyword, (cat, prio) in _KEYWORD_MAP.items():
        if keyword in combined:
            category = cat
            priority = prio
            confidence = 0.85
            summary = f"Detected {cat} issue — {description[:150]}"
            break

    logger.info(f"Classification: category={category}, priority={priority}, confidence={confidence}")
    return ClassificationResult(
        category=category,
        priority=priority,
        confidence=confidence,
        summary=summary,
    )
