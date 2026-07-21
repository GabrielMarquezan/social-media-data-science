import pandas as pd
from unittest.mock import MagicMock

from social_media.src.config import build_config
from social_media.src.nlp.sentiment_terms import extract_sentiment_terms


def test_extract_sentiment_terms_empty():
    config = build_config(apify_token="test")
    nlp = MagicMock()
    result = extract_sentiment_terms(pd.DataFrame(), nlp, top_n=10)
    assert result.empty
