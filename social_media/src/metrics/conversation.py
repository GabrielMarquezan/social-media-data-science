import numpy as np
import pandas as pd


def discussion_index(comments: pd.DataFrame) -> pd.Series:
    """Respostas / comentários top-level por post.

    Retorna uma Series indexada por `post_id`.
    """
    top_level = comments[comments["parent_id"].isna()]
    replies = comments[comments["parent_id"].notna()]

    top_counts = top_level.groupby("post_id").size()
    reply_counts = replies.groupby("post_id").size()

    index = top_counts.index.union(reply_counts.index)
    return pd.Series(
        np.where(
            top_counts.reindex(index).fillna(0) > 0,
            reply_counts.reindex(index).fillna(0) / top_counts.reindex(index).fillna(0),
            np.nan,
        ),
        index=index,
    )


def avg_reply_depth(comments: pd.DataFrame) -> pd.Series:
    """Profundidade média das respostas por post."""
    replies = comments[comments["parent_id"].notna()]
    if replies.empty:
        return pd.Series(dtype="float64")
    return replies.groupby("post_id")["depth"].mean()


def max_reply_depth(comments: pd.DataFrame) -> pd.Series:
    """Profundidade máxima das respostas por post."""
    replies = comments[comments["parent_id"].notna()]
    if replies.empty:
        return pd.Series(dtype="float64")
    return replies.groupby("post_id")["depth"].max()


def qualified_comment_rate(comments: pd.DataFrame) -> pd.Series:
    """% de comentários qualificados por post."""
    total = comments.groupby("post_id").size()
    qualified = comments[comments["is_qualified"].fillna(False)].groupby("post_id").size()
    index = total.index.union(qualified.index)
    return pd.Series(
        np.where(
            total.reindex(index).fillna(0) > 0,
            qualified.reindex(index).fillna(0) / total.reindex(index).fillna(0),
            np.nan,
        ),
        index=index,
    )


def question_comment_rate(comments: pd.DataFrame) -> pd.Series:
    """% de comentários com perguntas por post."""
    total = comments.groupby("post_id").size()
    questions = comments[comments["is_question"].fillna(False)].groupby("post_id").size()
    index = total.index.union(questions.index)
    return pd.Series(
        np.where(
            total.reindex(index).fillna(0) > 0,
            questions.reindex(index).fillna(0) / total.reindex(index).fillna(0),
            np.nan,
        ),
        index=index,
    )


def sentiment_shares(comments: pd.DataFrame) -> pd.DataFrame:
    """Shares de sentimento (positivo/neutro/negativo) por post.

    Retorna um DataFrame com colunas
    `sent_positivo_share`, `sent_neutro_share`, `sent_negativo_share`
    indexado por `post_id`.
    """
    total = comments.groupby("post_id").size()
    shares = (
        comments.groupby(["post_id", "sentiment_label"])
        .size()
        .unstack(fill_value=0)
    )
    for label in ("positivo", "neutro", "negativo"):
        if label not in shares.columns:
            shares[label] = 0

    shares = shares[["positivo", "neutro", "negativo"]]
    shares_rate = shares.div(total, axis=0)
    shares_rate.columns = [
        "sent_positivo_share",
        "sent_neutro_share",
        "sent_negativo_share",
    ]
    return shares_rate
