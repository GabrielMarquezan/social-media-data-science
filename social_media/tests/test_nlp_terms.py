from unittest.mock import MagicMock

from social_media.src.config import build_config
from social_media.src.nlp.terms import extract_top_terms


def test_extract_top_terms_empty():
    config = build_config(apify_token="test")
    nlp = MagicMock()
    nlp.pipe.return_value = []
    embedding_model = MagicMock()

    result = extract_top_terms([], nlp, embedding_model, top_n=10)
    assert result.empty
