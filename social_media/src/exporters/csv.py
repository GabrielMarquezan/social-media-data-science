import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

_CSV_FILES: dict[str, str] = {
    "caption_top_terms": "caption_top_terms.csv",
    "comment_top_terms": "comment_top_terms.csv",
    "comment_topics": "comment_topics.csv",
    "sentiment_term_comparison": "sentiment_term_comparison.csv",
}


def export_csvs(
    dfs: dict[str, pd.DataFrame],
    output_dir: Path,
) -> list[Path]:
    """Exporta DataFrames de NLP como arquivos CSV."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    saved: list[Path] = []
    for key, filename in _CSV_FILES.items():
        df = dfs.get(key)
        if df is None or not isinstance(df, pd.DataFrame):
            logger.warning("DataFrame '%s' não encontrado; pulando CSV.", key)
            continue

        path = output_dir / filename
        df.to_csv(path, index=False, encoding="utf-8")
        saved.append(path)

    logger.info(
        "CSVs exportados.",
        extra={"output_dir": str(output_dir), "files": [p.name for p in saved]},
    )
    return saved
