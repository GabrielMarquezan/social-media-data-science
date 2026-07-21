import logging
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from social_media.src.charts.captions import plot_caption_word_count_vs_engagement
from social_media.src.charts.overview import (
    plot_likes_comments_timeline,
    plot_posts_by_type,
    plot_top_posts_engagement,
)
from social_media.src.charts.timing import (
    plot_avg_likes_comments_by_weekday,
    plot_engagement_heatmap_hour_weekday,
)
from social_media.src.config import Config

logger = logging.getLogger(__name__)

_CHARTS: list[tuple[str, str, callable]] = [
    ("likes_comments_timeline", "posts", plot_likes_comments_timeline),
    ("top_posts_engagement", "posts", plot_top_posts_engagement),
    ("posts_by_type", "posts", plot_posts_by_type),
    ("caption_word_count_vs_engagement", "posts", plot_caption_word_count_vs_engagement),
    ("engagement_heatmap_hour_weekday", "posts", plot_engagement_heatmap_hour_weekday),
    ("avg_likes_comments_by_weekday", "timing_by_weekday", plot_avg_likes_comments_by_weekday),
]


def export_charts(
    dfs: dict[str, pd.DataFrame],
    output_dir: Path,
    config: Config,
) -> list[Path]:
    """Gera e salva os gráficos do MVP como arquivos PNG.

    Args:
        dfs: Dicionário de DataFrames gerados pelo pipeline.
        output_dir: Diretório onde os PNGs serão salvos.
        config: Configuração da aplicação.

    Returns:
        Lista de caminhos dos arquivos PNG salvos.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    saved_paths: list[Path] = []

    for file_name, df_key, plot_func in _CHARTS:
        df = dfs.get(df_key)
        if df is None or not isinstance(df, pd.DataFrame):
            logger.warning("DataFrame '%s' não encontrado; pulando gráfico '%s'.", df_key, file_name)
            continue

        output_path = output_dir / f"{file_name}.png"
        if file_name == "top_posts_engagement":
            fig = plot_func(df, config.top_posts_limit)
        else:
            fig = plot_func(df)
        fig.savefig(output_path, bbox_inches="tight", dpi=config.chart_dpi)
        plt.close(fig)
        saved_paths.append(output_path)
        logger.debug("Gráfico salvo: %s", output_path)

    logger.info(
        "PNG exportados com sucesso.",
        extra={"output_dir": str(output_dir), "charts": [p.name for p in saved_paths]},
    )
    return saved_paths
