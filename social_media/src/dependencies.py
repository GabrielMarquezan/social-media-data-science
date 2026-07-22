from dataclasses import dataclass, field
from typing import Any, Callable

from social_media.src.config import Config
from social_media.src.domain.sentiment import SentimentResult

_DEFAULT_SENTIMENT_MODEL = "nlptown/bert-base-multilingual-uncased-sentiment"


@dataclass
class Dependencies:
    sentiment_analyzer: Callable[[str], SentimentResult] | None = field(
        default=None, repr=False
    )
    sentiment_model: str = field(default=_DEFAULT_SENTIMENT_MODEL, repr=False)
    spacy_model_name: str = field(default="pt_core_news_sm", repr=False)
    bertopic_embedding_model: str = field(
        default="paraphrase-multilingual-MiniLM-L12-v2", repr=False
    )
    _spacy_nlp: Any = field(default=None, repr=False)
    _embedding_model: Any = field(default=None, repr=False)

    def get_sentiment_analyzer(self) -> Callable[[str], SentimentResult]:
        if self.sentiment_analyzer is None:
            self.sentiment_analyzer = _build_transformers_sentiment_analyzer(
                self.sentiment_model
            )
        return self.sentiment_analyzer

    def get_spacy_nlp(self) -> Any:
        if self._spacy_nlp is None:
            import spacy

            self._spacy_nlp = spacy.load(self.spacy_model_name)
        return self._spacy_nlp

    def get_embedding_model(self) -> Any:
        if self._embedding_model is None:
            from sentence_transformers import SentenceTransformer

            self._embedding_model = SentenceTransformer(self.bertopic_embedding_model)
        return self._embedding_model


def _build_transformers_sentiment_analyzer(
    model_name: str,
) -> Callable[[str], SentimentResult]:
    from transformers import pipeline

    from social_media.src.nlp.sentiment import analyze_sentiment

    def analyzer(text: str) -> SentimentResult:
        if analyzer._pipeline_cache is None:  # type: ignore[attr-defined]
            analyzer._pipeline_cache = pipeline(  # type: ignore[attr-defined]
                "sentiment-analysis",
                model=model_name,
            )
        return analyze_sentiment(text, analyzer._pipeline_cache)  # type: ignore[attr-defined]

    analyzer._pipeline_cache = None  # type: ignore[attr-defined]
    return analyzer


def build_dependencies(config: Config) -> Dependencies:
    """Cria dependências injetáveis com lazy loading."""
    return Dependencies(
        sentiment_model=config.sentiment_model,
        spacy_model_name=config.spacy_model,
        bertopic_embedding_model=config.bertopic_embedding_model,
    )
