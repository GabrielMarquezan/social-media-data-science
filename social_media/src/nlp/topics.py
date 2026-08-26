import logging
from typing import Any

import numpy as np
import pandas as pd
from bertopic import BERTopic
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import CountVectorizer
from spacy.lang.en.stop_words import STOP_WORDS as _EN_STOP_WORDS
from spacy.lang.pt.stop_words import STOP_WORDS as _PT_STOP_WORDS

logger = logging.getLogger(__name__)

TOPIC_COLUMNS = ["topic_id", "topic_label", "keyword", "importancia_no_topico"]

# Abaixo deste número de textos não há agrupamento significativo.
_MIN_DOCS_FOR_TOPICS = 4

# Nome do tópico: até 3 palavras, ignorando as de score < 25% da principal.
_MAX_LABEL_WORDS = 3
_LABEL_MIN_SCORE_RATIO = 0.25

_LABEL_STOP_WORDS = set(_PT_STOP_WORDS) | set(_EN_STOP_WORDS)


class _NoOpReducer:
    """Redutor de dimensionalidade no-op: mantém os embeddings originais.

    Necessário porque o BERTopic instancia `UMAP(n_neighbors=15)` quando
    `umap_model=None` — com poucos documentos, a decomposição espectral do
    UMAP quebra (exige mais amostras do que vizinhos).
    """

    def fit(self, embeddings: Any, y: Any = None) -> "_NoOpReducer":
        return self

    def transform(self, embeddings: Any) -> np.ndarray:
        return np.asarray(embeddings)

    def fit_transform(self, embeddings: Any, y: Any = None) -> np.ndarray:
        return np.asarray(embeddings)


def fit_comment_topics(
    texts: list[str],
    embedding_model: Any,
    n_topics: int = 10,
    top_n: int = 10,
) -> tuple[BERTopic | None, pd.DataFrame]:
    """Treina BERTopic em comentários e retorna modelo + DataFrame de tópicos.

    O agrupamento é adaptado ao tamanho do dataset: o número de tópicos é
    limitado a metade dos textos (sem exceder `n_topics`) e usa-se KMeans em
    vez do HDBSCAN padrão — em conjuntos pequenos de comentários o HDBSCAN
    (min_cluster_size=10) marca tudo como outlier e o resultado fica vazio.
    A redução de dimensionalidade é desativada (`_NoOpReducer`), pois o UMAP
    padrão é instável com poucas amostras.
    """
    cleaned = [text for text in texts if text and text.strip()]
    if len(cleaned) < _MIN_DOCS_FOR_TOPICS:
        logger.warning(
            "Textos insuficientes para tópicos. Pulando etapa.",
            extra={"texts_count": len(cleaned), "min_docs": _MIN_DOCS_FOR_TOPICS},
        )
        empty = pd.DataFrame(columns=TOPIC_COLUMNS)
        return None, empty

    n_effective = max(1, min(n_topics, len(cleaned) // 2))

    topic_model = BERTopic(
        embedding_model=embedding_model,
        umap_model=_NoOpReducer(),
        hdbscan_model=KMeans(n_clusters=n_effective, n_init=10, random_state=42),
        vectorizer_model=CountVectorizer(
            stop_words=list(_LABEL_STOP_WORDS), ngram_range=(1, 2)
        ),
        verbose=False,
    )
    topic_model.fit(cleaned)

    keywords_df = extract_topic_keywords(topic_model, top_n=top_n)
    logger.info(
        "Tópicos gerados.",
        extra={
            "texts_count": len(cleaned),
            "topics_count": keywords_df["topic_id"].nunique() if not keywords_df.empty else 0,
        },
    )
    return topic_model, keywords_df


def extract_topic_keywords(topic_model: BERTopic, top_n: int = 10) -> pd.DataFrame:
    """Extrai keywords de cada tópico treinado."""
    rows = []
    topic_info = topic_model.get_topic_info()

    for topic_id in topic_info["Topic"]:
        if topic_id == -1:
            continue  # outlier topic
        keywords = topic_model.get_topic(topic_id)
        if not keywords:
            continue
        label = topic_info[topic_info["Topic"] == topic_id]["Name"].values[0]
        for word, score in keywords[:top_n]:
            if not word or not str(word).strip():
                continue  # padding do BERTopic: ("", 1e-05) quando faltam termos
            rows.append(
                {
                    "topic_id": topic_id,
                    "topic_label": label,
                    "keyword": word,
                    "importancia_no_topico": score,
                }
            )

    # Com colunas explícitas: pd.DataFrame([]) sem colunas gera um CSV sem
    # cabeçalho ("\n"), que quebra pd.read_csv (EmptyDataError).
    return pd.DataFrame(rows, columns=TOPIC_COLUMNS)
