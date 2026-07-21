import pandas as pd


def word_count(text: pd.Series) -> pd.Series:
    return text.fillna("").str.split().str.len()


def is_qualified(word_count: pd.Series, min_words: int) -> pd.Series:
    return word_count >= min_words


def is_question(text: pd.Series) -> pd.Series:
    return text.fillna("").str.contains(r"\?", regex=True)
