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
        return pd.DataFrame(columns=["term", "relevancia", "count"])

    lemmatized_docs = lemmatize_texts(cleaned, nlp)
    joined_docs = [" ".join(tokens) for tokens in lemmatized_docs if tokens]

    if not joined_docs:
        return pd.DataFrame(columns=["term", "relevancia", "count"])

    kw_model = KeyBERT(model=keybert_model)
    keywords = kw_model.extract_keywords(
        joined_docs,
        keyphrase_ngram_range=(1, 2),
        # stop_words=None: o CountVectorizer do sklearn não tem lista embutida
        # em português ("portuguese" gera ValueError, que o KeyBERT engole e
        # retorna []). Stop words já foram removidas em lemmatize_texts.
        stop_words=None,
        top_n=top_n,
    )

    # Com exatamente 1 documento, o KeyBERT retorna uma lista "achatada" de
    # tuplas [(term, score), ...] em vez de [[(term, score), ...]].
    if keywords and isinstance(keywords[0], tuple):
        keywords = [keywords]

    scores: dict[str, float] = {}
    counts: dict[str, int] = {}
    for doc_keywords in keywords:
        for term, score in doc_keywords:
            scores[term] = scores.get(term, 0.0) + score
            counts[term] = counts.get(term, 0) + 1

    if not scores:
        return pd.DataFrame(columns=["term", "relevancia", "count"])

    df = pd.DataFrame(
        [
            {"term": term, "relevancia": scores[term], "count": counts[term]}
            for term in scores
        ]
    )
    return df.sort_values("relevancia", ascending=False).head(top_n).reset_index(drop=True)
