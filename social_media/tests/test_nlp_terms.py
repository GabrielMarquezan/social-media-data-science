from unittest.mock import MagicMock

import numpy as np

from social_media.src.config import build_config
from social_media.src.nlp.terms import extract_top_terms


def _make_mock_nlp() -> MagicMock:
    """Mock de spaCy nlp que tokeniza por espaços, mantendo tokens em minúsculas."""
    nlp = MagicMock()

    def mock_pipe(texts, batch_size=None):
        for text in texts:
            doc = MagicMock()
            token_mocks = []
            for token in text.split():
                tm = MagicMock()
                tm.lemma_ = token
                tm.is_stop = False
                tm.is_punct = False
                tm.is_space = False
                token_mocks.append(tm)
            doc.__iter__ = lambda self, _tokens=token_mocks: iter(_tokens)
            yield doc

    nlp.pipe = mock_pipe
    return nlp


def _make_mock_embedding_model() -> MagicMock:
    model = MagicMock()
    model.encode = MagicMock(
        side_effect=lambda texts, **kwargs: np.array([[0.1] * 384 for _ in texts])
    )
    return model


def test_extract_top_terms_empty():
    config = build_config(apify_token="test")
    nlp = MagicMock()
    nlp.pipe.return_value = []
    embedding_model = MagicMock()

    result = extract_top_terms([], nlp, embedding_model, top_n=10)
    assert result.empty


def test_extract_top_terms_returns_terms():
    """Regressão: stop_words="portuguese" fazia o KeyBERT retornar [] sempre."""
    nlp = _make_mock_nlp()
    embedding_model = _make_mock_embedding_model()
    texts = [
        "colecao nova de vestidos longos",
        "amei o vestido perfeito demais",
        "linda peca maravilhosa",
    ]

    result = extract_top_terms(texts, nlp, embedding_model, top_n=10)

    assert not result.empty
    assert list(result.columns) == ["term", "relevancia", "count"]
    assert len(result) <= 10
    assert result["term"].str.len().gt(0).all()
    assert result["relevancia"].notna().all()


def test_extract_top_terms_single_document():
    """Regressão: com 1 documento o KeyBERT retorna lista achatada de tuplas."""
    nlp = _make_mock_nlp()
    embedding_model = _make_mock_embedding_model()

    result = extract_top_terms(
        ["colecao nova de vestidos longos"], nlp, embedding_model, top_n=10
    )

    assert not result.empty
    assert list(result.columns) == ["term", "relevancia", "count"]
    assert result["term"].str.len().gt(0).all()
