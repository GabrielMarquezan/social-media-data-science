from dataclasses import dataclass


@dataclass(frozen=True)
class SentimentResult:
    label: str  # "positivo", "neutro" ou "negativo"
    score: float  # valor normalizado entre 0 e 1
