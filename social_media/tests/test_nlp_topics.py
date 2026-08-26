from unittest.mock import MagicMock

import numpy as np
import pandas as pd

from social_media.src.nlp.topics import TOPIC_COLUMNS, extract_topic_keywords, fit_comment_topics


def _make_mock_embedding_model() -> MagicMock:
    """Mock de embedding que retorna um vetor por texto recebido (shape correto)."""
    model = MagicMock()
    model.encode = MagicMock(
        side_effect=lambda texts, **kwargs: np.array([[0.1] * 384 for _ in texts])
    )
    return model


def test_fit_comment_topics_insufficient_texts():
    embedding_model = MagicMock()
    model, df = fit_comment_topics(["texto curto"], embedding_model, n_topics=10)
    assert model is None
    assert df.empty
    assert list(df.columns) == TOPIC_COLUMNS


def test_fit_comment_topics_boundary_below_min_docs():
    embedding_model = MagicMock()
    model, df = fit_comment_topics(["a", "b", "c"], embedding_model, n_topics=10)
    assert model is None
    assert df.empty
    assert list(df.columns) == TOPIC_COLUMNS


def test_fit_comment_topics_small_dataset_produces_topics():
    """Regressão: datasets pequenos devem gerar tópicos (HDBSCAN esvaziava tudo)."""
    texts = [
        "amei o vestido perfeito",
        "linda peca maravilhosa",
        "entrega rapida demais",
        "chegou super rapido adorei",
        "tecido de otima qualidade",
        "material excelente recomendo",
    ]

    model, df = fit_comment_topics(texts, _make_mock_embedding_model(), n_topics=10)

    assert model is not None
    assert not df.empty
    assert list(df.columns) == TOPIC_COLUMNS
    assert (df["topic_id"] >= 0).all()  # sem outliers com KMeans
    assert df["topic_id"].nunique() <= 3  # limitado a len(texts) // 2


def test_extract_topic_keywords_only_outliers_returns_empty_with_columns():
    """BERTopic com apenas outliers (-1) deve retornar df vazio COM colunas.

    Sem as colunas, o CSV exportado fica sem cabeçalho e quebra o read_csv.
    """
    topic_model = MagicMock()
    topic_model.get_topic_info.return_value = pd.DataFrame(
        {"Topic": [-1], "Name": ["-1_outlier"]}
    )

    df = extract_topic_keywords(topic_model)

    assert df.empty
    assert list(df.columns) == TOPIC_COLUMNS
    topic_model.get_topic.assert_not_called()


def test_extract_topic_keywords_skips_bertopic_padding():
    """O BERTopic preenche tópicos com ("", 1e-05); essas linhas não entram."""
    topic_model = MagicMock()
    topic_model.get_topic_info.return_value = pd.DataFrame(
        {"Topic": [0], "Name": ["0_amo_linda"]}
    )
    topic_model.get_topic.return_value = [("amo", 0.5), ("", 1e-05), ("  ", 1e-05)]

    df = extract_topic_keywords(topic_model, top_n=10)

    assert list(df["keyword"]) == ["amo"]
