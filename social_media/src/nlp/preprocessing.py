import re
from typing import Any

_URL_PATTERN = re.compile(r"https?://\S+")
_MENTION_PATTERN = re.compile(r"@\w+")
_HASHTAG_PATTERN = re.compile(r"#(\w+)")
_MULTIPLE_SPACES = re.compile(r"\s+")
_SPACE_BEFORE_PUNCT = re.compile(r"\s+([.!?,:;])")


def clean_text(text: str) -> str:
    """Remove URLs, menções, normaliza hashtags e espaços."""
    if not text:
        return ""
    text = _URL_PATTERN.sub("", text)
    text = _MENTION_PATTERN.sub("", text)
    text = _HASHTAG_PATTERN.sub(r"\1", text)
    text = _SPACE_BEFORE_PUNCT.sub(r"\1", text)
    text = _MULTIPLE_SPACES.sub(" ", text)
    return text.strip().lower()


def lemmatize_texts(texts: list[str], nlp: Any) -> list[list[str]]:
    """Lematiza uma lista de textos e retorna tokens por documento."""
    processed: list[list[str]] = []
    for doc in nlp.pipe(texts, batch_size=64):
        tokens = [
            token.lemma_.lower()
            for token in doc
            if not token.is_stop and not token.is_punct and not token.is_space
        ]
        processed.append(tokens)
    return processed
