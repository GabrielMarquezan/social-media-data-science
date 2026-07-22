from typing import Any

import pandas as pd


def extract_top_terms(
    texts: list[str],
    nlp: Any,
    keybert_model: Any,
    top_n: int = 20,
) -> pd.DataFrame:
    """Extrai top terms usando KeyBERT sobre textos lematizados."""
    from keybert import KeyBERT

    from social_media.src.nlp.preprocessing import clean_text, lemmatize_texts

    cleaned = [clean_text(text) for text in texts if clean_text(text)]
    if not cleaned:
        return pd.DataFrame(columns=["term", "score", "count"])

    lemmatized_docs = lemmatize_texts(cleaned, nlp)
    joined_docs = [" ".join(tokens) for tokens in lemmatized_docs if tokens]

    if not joined_docs:
        return pd.DataFrame(columns=["term", "score", "count"])

    kw_model = KeyBERT(model=keybert_model)
    keywords = kw_model.extract_keywords(
        joined_docs,
        keyphrase_ngram_range=(1, 2),
        stop_words="portuguese",
        top_n=top_n,
    )

    scores: dict[str, float] = {}
    counts: dict[str, int] = {}
    for doc_keywords in keywords:
        for term, score in doc_keywords:
            scores[term] = scores.get(term, 0.0) + score
            counts[term] = counts.get(term, 0) + 1

    if not scores:
        return pd.DataFrame(columns=["term", "score", "count"])

    df = pd.DataFrame(
        [
            {"term": term, "score": scores[term], "count": counts[term]}
            for term in scores
        ]
    )
    return df.sort_values("score", ascending=False).head(top_n).reset_index(drop=True)
