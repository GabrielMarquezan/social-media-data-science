import re
from typing import Callable

from social_media.src.domain.sentiment import SentimentResult


def analyze_sentiment(
    text: str, analyzer: Callable[[str], list[dict]]
) -> SentimentResult:
    """Analisa o sentimento de um texto usando um pipeline/analisador injetado."""
    if not text or not text.strip():
        return SentimentResult(label="neutro", score=0.5)

    try:
        result = analyzer(text)
        if isinstance(result, list) and result:
            raw = result[0]
        else:
            raw = result
        raw_label = str(raw.get("label", ""))
        raw_score = float(raw.get("score", 0.0))
    except Exception:
        return SentimentResult(label="neutro", score=0.5)

    return SentimentResult(
        label=map_label(raw_label),
        score=map_score(raw_score, raw_label),
    )


def map_label(raw_label: str) -> str:
    """Mapeia rótulos do modelo nlptown (1-5 estrelas) para positivo/neutro/negativo."""
    stars = _extract_stars(raw_label)
    if stars <= 2:
        return "negativo"
    if stars == 3:
        return "neutro"
    return "positivo"


def map_score(raw_score: float, raw_label: str) -> float:
    """Mapeia o score bruto do modelo para uma escala 0..1."""
    stars = _extract_stars(raw_label)
    base = (stars - 1) / 4.0
    return float(base * raw_score)


def _extract_stars(raw_label: str) -> int:
    match = re.search(r"(\d+)", raw_label)
    if match:
        return max(1, min(5, int(match.group(1))))
    return 3
