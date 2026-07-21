import logging
from typing import Any

import pandas as pd
from bertopic import BERTopic

logger = logging.getLogger(__name__)


def fit_comment_topics(
    texts: list[str],
    embedding_model: Any,
    n_topics: int = 10,
    top_n: int = 10,
) -> tuple[BERTopic | None, pd.DataFrame]:
    """Treina BERTopic em comentários e retorna modelo + DataFrame de tópicos."""
    cleaned = [text for text in texts if text and text.strip()]
    if len(cleaned) < n_topics:
        logger.warning(
            "Textos insuficientes para %d tópicos. Pulando tópicos.", n_topics
        )
        empty = pd.DataFrame(
            columns=["topic_id", "topic_label", "keyword", "score"]
        )
        return None, empty

    topic_model = BERTopic(
        embedding_model=embedding_model,
        nr_topics=n_topics,
        verbose=False,
    )
    topic_model.fit(cleaned)

    keywords_df = extract_topic_keywords(topic_model, top_n=top_n)
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
            rows.append(
                {
                    "topic_id": topic_id,
                    "topic_label": label,
                    "keyword": word,
                    "score": score,
                }
            )

    return pd.DataFrame(rows)
