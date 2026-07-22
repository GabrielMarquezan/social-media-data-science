import re
import unicodedata

import pandas as pd

_CTA_PATTERN = r"\b(?:link na bio|clique|swipe up|saiba mais|confira|confere|acesse|veja mais|compre agora|garanta o seu|participe|inscreva-se|cadastre-se)\b"

_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F700-\U0001F77F"  # alchemical symbols
    "\U0001F780-\U0001F7FF"  # Geometric Shapes
    "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    "\U0001FA00-\U0001FA6F"  # Chess Symbols
    "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    "\U00002702-\U000027B0"  # Dingbats
    "\U000024C2-\U0001F251"
    "]",
    flags=re.UNICODE,
)


def caption_word_count(caption: pd.Series) -> pd.Series:
    return caption.fillna("").str.split().str.len()


def caption_char_count(caption: pd.Series) -> pd.Series:
    return caption.fillna("").str.len()


def caption_emoji_count(caption: pd.Series) -> pd.Series:
    return caption.fillna("").apply(lambda text: len(_EMOJI_PATTERN.findall(text)))


def has_hashtags(hashtags: pd.Series) -> pd.Series:
    return hashtags.apply(lambda value: bool(value and len(value) > 0))


def has_mentions(mentions: pd.Series) -> pd.Series:
    return mentions.apply(lambda value: bool(value and len(value) > 0))


def _normalize_text(text: str) -> str:
    """Remove acentos para matching mais tolerante de CTA."""
    return (
        unicodedata.normalize("NFKD", text)
        .encode("ASCII", "ignore")
        .decode("ASCII")
    )


def has_cta(caption: pd.Series) -> pd.Series:
    return (
        caption.fillna("")
        .apply(_normalize_text)
        .str.contains(_CTA_PATTERN, regex=True, case=False, na=False)
    )


def hashtag_count(hashtags: pd.Series) -> pd.Series:
    return hashtags.apply(lambda value: len(value) if isinstance(value, list) else 0)


def mention_count(mentions: pd.Series) -> pd.Series:
    return mentions.apply(lambda value: len(value) if isinstance(value, list) else 0)
