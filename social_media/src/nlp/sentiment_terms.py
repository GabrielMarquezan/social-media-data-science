from typing import Any

import pandas as pd

from social_media.src.nlp.preprocessing import clean_text, lemmatize_texts


def extract_sentiment_terms(
    comments_df: pd.DataFrame,
    nlp: Any,
    top_n: int = 10,
) -> pd.DataFrame:
    """Retorna termos mais frequentes em comentários positivos e negativos."""
    if comments_df.empty or "sentiment_label" not in comments_df.columns:
        return pd.DataFrame(columns=["term", "sentiment", "count"])

    rows = []
    for sentiment in ("positivo", "negativo"):
        subset = comments_df[comments_df["sentiment_label"] == sentiment]
        if subset.empty:
            continue

        texts = subset["text"].fillna("").tolist()
        cleaned = [clean_text(text) for text in texts if clean_text(text)]
        if not cleaned:
            continue

        tokenized = lemmatize_texts(cleaned, nlp)
        all_terms: list[str] = []
        for tokens in tokenized:
            all_terms.extend(tokens)

        if not all_terms:
            continue

        term_counts = pd.Series(all_terms).value_counts().head(top_n)
        for term, count in term_counts.items():
            rows.append({"term": term, "sentiment": sentiment, "count": int(count)})

    return pd.DataFrame(rows)
