import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    apify_token: str
    apify_actor: str
    results_limit: int
    qualified_comment_min_words: int
    sentiment_model: str
    output_dir: Path
    data_dir: Path
    log_level: str
    log_format: str
    top_posts_limit: int
    chart_dpi: int
    xlsx_engine: str
    spacy_model: str
    bertopic_embedding_model: str
    nlp_top_terms_limit: int
    nlp_topic_count: int
    nlp_topic_terms_limit: int
    nlp_sentiment_terms_limit: int


def build_config(
    apify_token: str | None = None,
    apify_actor: str | None = None,
    results_limit: int | None = None,
    qualified_comment_min_words: int | None = None,
    sentiment_model: str | None = None,
    output_dir: str | Path | None = None,
    data_dir: str | Path | None = None,
    log_level: str | None = None,
    log_format: str | None = None,
    top_posts_limit: int | None = None,
    chart_dpi: int | None = None,
    xlsx_engine: str | None = None,
    spacy_model: str | None = None,
    bertopic_embedding_model: str | None = None,
    nlp_top_terms_limit: int | None = None,
    nlp_topic_count: int | None = None,
    nlp_topic_terms_limit: int | None = None,
    nlp_sentiment_terms_limit: int | None = None,
) -> Config:
    """Factory que constrói uma Config a partir de variáveis de ambiente e defaults."""
    token = apify_token if apify_token is not None else os.getenv("APIFY_API_KEY")
    if not token:
        raise ValueError("APIFY_API_KEY não configurada no ambiente.")

    def _resolve_path(value: str | Path | None, default: Path) -> Path:
        if value is None:
            return default.resolve()
        return Path(value).resolve()

    return Config(
        apify_token=token,
        apify_actor=apify_actor or os.getenv("APIFY_ACTOR", "apify/instagram-scraper"),
        results_limit=results_limit
        if results_limit is not None
        else int(os.getenv("RESULTS_LIMIT", "100")),
        qualified_comment_min_words=qualified_comment_min_words
        if qualified_comment_min_words is not None
        else int(os.getenv("QUALIFIED_COMMENT_MIN_WORDS", "5")),
        sentiment_model=sentiment_model
        or os.getenv(
            "SENTIMENT_MODEL", "nlptown/bert-base-multilingual-uncased-sentiment"
        ),
        output_dir=_resolve_path(output_dir, Path("output")),
        data_dir=_resolve_path(data_dir, Path("data")),
        log_level=log_level or os.getenv("LOG_LEVEL", "DEBUG"),
        log_format=log_format or os.getenv("LOG_FORMAT", "json"),
        top_posts_limit=top_posts_limit
        if top_posts_limit is not None
        else int(os.getenv("TOP_POSTS_LIMIT", "10")),
        chart_dpi=chart_dpi if chart_dpi is not None else int(os.getenv("CHART_DPI", "150")),
        xlsx_engine=xlsx_engine or os.getenv("XLSX_ENGINE", "openpyxl"),
        spacy_model=spacy_model or os.getenv("SPACY_MODEL", "pt_core_news_sm"),
        bertopic_embedding_model=bertopic_embedding_model
        or os.getenv(
            "BERTOPIC_EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2"
        ),
        nlp_top_terms_limit=nlp_top_terms_limit
        if nlp_top_terms_limit is not None
        else int(os.getenv("NLP_TOP_TERMS_LIMIT", "20")),
        nlp_topic_count=nlp_topic_count
        if nlp_topic_count is not None
        else int(os.getenv("NLP_TOPIC_COUNT", "10")),
        nlp_topic_terms_limit=nlp_topic_terms_limit
        if nlp_topic_terms_limit is not None
        else int(os.getenv("NLP_TOPIC_TERMS_LIMIT", "10")),
        nlp_sentiment_terms_limit=nlp_sentiment_terms_limit
        if nlp_sentiment_terms_limit is not None
        else int(os.getenv("NLP_SENTIMENT_TERMS_LIMIT", "10")),
    )
