import logging
from copy import copy
from pathlib import Path

import pandas as pd

from social_media.src.config import Config

logger = logging.getLogger(__name__)

_SHEET_CONFIG: dict[str, dict[str, str | None]] = {
    "posts": {"sheet_name": "Posts", "index": False},
    "comments": {"sheet_name": "Comments", "index": False},
    "timing_by_hour": {"sheet_name": "Timing_Hour", "index": False},
    "timing_by_weekday": {"sheet_name": "Timing_Weekday", "index": False},
    "content_by_type": {"sheet_name": "Content_By_Type", "index": False},
    "quality": {"sheet_name": "Quality", "index": False},
    "caption_top_terms": {"sheet_name": "Caption_Top_Terms", "index": False},
    "comment_top_terms": {"sheet_name": "Comment_Top_Terms", "index": False},
    "comment_topics": {"sheet_name": "Comment_Topics", "index": False},
    "sentiment_term_comparison": {"sheet_name": "Sentiment_Terms", "index": False},
}


def build_quality_report(dfs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Relatório de qualidade de dados com checks principais."""
    posts = dfs.get("posts")
    comments = dfs.get("comments")
    rows: list[dict[str, object]] = []

    if posts is None or posts.empty:
        return pd.DataFrame(rows)

    total_posts = len(posts)
    rows.append({"check": "total_posts", "value": total_posts, "status": "ok"})

    # Posts sem visualizações válidas (relevante apenas para vídeos/reels)
    no_views = posts["views"].isna() | (posts["views"] == 0)
    no_views_count = int(no_views.sum())
    rows.append(
        {
            "check": "posts_without_valid_views",
            "value": no_views_count,
            "status": "warning" if no_views_count > 0 else "ok",
        }
    )

    # Posts sem timestamp
    no_ts = posts["timestamp"].isna()
    no_ts_count = int(no_ts.sum())
    rows.append(
        {
            "check": "posts_without_timestamp",
            "value": no_ts_count,
            "status": "warning" if no_ts_count > 0 else "ok",
        }
    )

    if comments is None or comments.empty:
        rows.append({"check": "total_comments", "value": 0, "status": "ok"})
        return pd.DataFrame(rows)

    total_comments = len(comments)
    rows.append({"check": "total_comments", "value": total_comments, "status": "ok"})

    # Comentários sem texto
    empty_text = comments["text"].fillna("").str.strip().eq("")
    empty_text_count = int(empty_text.sum())
    rows.append(
        {
            "check": "comments_without_text",
            "value": empty_text_count,
            "status": "warning" if empty_text_count > 0 else "ok",
        }
    )

    # Discrepância entre comentários carregados e comments_count esperado
    top_level = comments[comments["parent_id"].isna()]
    loaded_by_post = top_level.groupby("post_id").size()
    expected_by_post = posts.set_index("id")["comments_count"]
    merged = pd.DataFrame(
        {"loaded": loaded_by_post, "expected": expected_by_post}
    ).fillna(0)
    merged["diff"] = merged["loaded"] - merged["expected"]
    discrepancies = int((merged["diff"].abs() > 0).sum())
    rows.append(
        {
            "check": "posts_with_comment_count_discrepancy",
            "value": discrepancies,
            "status": "warning" if discrepancies > 0 else "ok",
        }
    )

    # Cobertura geral de comentários (comentários carregados / esperados)
    total_expected = merged["expected"].sum()
    coverage = merged["loaded"].sum() / total_expected if total_expected > 0 else 1.0
    rows.append(
        {
            "check": "comments_coverage_ratio",
            "value": round(coverage, 4),
            "status": "warning" if coverage < 1.0 else "ok",
        }
    )

    return pd.DataFrame(rows)


def export_xlsx(
    dfs: dict[str, pd.DataFrame],
    output_dir: Path,
    config: Config,
) -> Path:
    """Exporta os DataFrames do pipeline para um arquivo XLSX estilizado.

    Args:
        dfs: Dicionário de DataFrames gerados pelo pipeline.
        output_dir: Diretório onde o arquivo será salvo.
        config: Configuração da aplicação.

    Returns:
        Caminho do arquivo XLSX salvo.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "metrics.xlsx"

    sheet_order = [
        ("posts", "Posts"),
        ("comments", "Comments"),
        ("timing_by_hour", "Timing_Hour"),
        ("timing_by_weekday", "Timing_Weekday"),
        ("content_by_type", "Content_By_Type"),
        ("quality", "Quality"),
        ("caption_top_terms", "Caption_Top_Terms"),
        ("comment_top_terms", "Comment_Top_Terms"),
        ("comment_topics", "Comment_Topics"),
        ("sentiment_term_comparison", "Sentiment_Terms"),
    ]

    dfs = dict(dfs)
    if "quality" not in dfs or dfs["quality"] is None:
        dfs["quality"] = build_quality_report(dfs)

    with pd.ExcelWriter(output_path, engine=config.xlsx_engine) as writer:  # type: ignore[call-overload]
        for key, sheet_name in sheet_order:
            df = dfs.get(key)
            if df is None or not isinstance(df, pd.DataFrame):
                logger.warning("DataFrame '%s' não encontrado; pulando aba '%s'.", key, sheet_name)
                continue
            df = _make_datetimes_excel_compatible(df)
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            _style_worksheet(writer, sheet_name, df)

    logger.info(
        "XLSX exportado com sucesso.",
        extra={"output_path": str(output_path), "sheets": [s for _, s in sheet_order]},
    )
    return output_path


def _make_datetimes_excel_compatible(df: pd.DataFrame) -> pd.DataFrame:
    """Converte colunas datetime com timezone para timezone-naive (Excel não suporta tz)."""
    df = df.copy()
    for column in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[column]):
            if df[column].dt.tz is not None:
                df[column] = df[column].dt.tz_convert(None)
    return df


def _style_worksheet(
    writer: pd.ExcelWriter,
    sheet_name: str,
    df: pd.DataFrame,
) -> None:
    """Aplica estilos básicos à planilha: negrito, autofit, filtros e freeze panes."""
    worksheet = writer.sheets[sheet_name]

    # Cabeçalhos em negrito
    for cell in worksheet[1]:
        new_font = copy(cell.font)
        new_font.bold = True
        cell.font = new_font

    # Autoajuste de largura das colunas
    for column in worksheet.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            value = cell.value
            if value is not None:
                cell_length = len(str(value))
                if cell_length > max_length:
                    max_length = cell_length
        adjusted_width = min(max(max_length + 2, 10), 50)
        worksheet.column_dimensions[column_letter].width = adjusted_width

    # Filtros e freeze panes na primeira linha
    max_row = worksheet.max_row
    max_col = worksheet.max_column
    if max_row > 0 and max_col > 0:
        worksheet.auto_filter.ref = f"A1:{worksheet.cell(row=1, column=max_col).coordinate}"
    worksheet.freeze_panes = "A2"
