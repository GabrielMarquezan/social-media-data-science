from unittest.mock import MagicMock

from social_media.src.nlp.topics import fit_comment_topics


def test_fit_comment_topics_insufficient_texts():
    embedding_model = MagicMock()
    model, df = fit_comment_topics(["texto curto"], embedding_model, n_topics=10)
    assert model is None
    assert df.empty
