from pathlib import Path
from unittest.mock import patch

import pandas as pd

from social_media.src.ui.runs import (
    get_run_info,
    list_runs,
    resolve_output_dir,
)


def _write_metrics_xlsx(run_dir: Path, posts: int, comments: int) -> Path:
    xlsx_path = run_dir / "metrics.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        pd.DataFrame({"id": range(posts)}).to_excel(writer, sheet_name="Posts", index=False)
        pd.DataFrame({"id": range(comments)}).to_excel(
            writer, sheet_name="Comentários", index=False
        )
    return xlsx_path


def _make_complete_run(output_dir: Path, run_id: str) -> Path:
    run_dir = output_dir / run_id
    (run_dir / "charts").mkdir(parents=True)
    _write_metrics_xlsx(run_dir, posts=3, comments=5)
    (run_dir / "charts" / "posts_by_type.png").write_bytes(b"png-fake")
    (run_dir / "caption_top_terms.csv").write_text("term,score\na,1\n", encoding="utf-8")
    return run_dir


def test_get_run_info_complete(tmp_path: Path) -> None:
    run_dir = _make_complete_run(tmp_path, "run-complete")

    info = get_run_info(run_dir)

    assert info.run_id == "run-complete"
    assert info.complete is True
    assert info.posts_count == 3
    assert info.comments_count == 5
    assert info.xlsx_path is not None and info.xlsx_path.name == "metrics.xlsx"
    assert len(info.chart_files) == 1
    assert len(info.csv_files) == 1
    assert info.created_at is not None


def test_get_run_info_incomplete(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-incomplete"
    run_dir.mkdir()

    info = get_run_info(run_dir)

    assert info.complete is False
    assert info.posts_count is None
    assert info.comments_count is None
    assert info.xlsx_path is None
    assert info.chart_files == []
    assert info.csv_files == []


def test_list_runs_returns_all_sorted_desc(tmp_path: Path) -> None:
    _make_complete_run(tmp_path, "run-a")
    (tmp_path / "run-b").mkdir()

    runs = list_runs(tmp_path)

    assert {run.run_id for run in runs} == {"run-a", "run-b"}
    assert runs[0].created_at >= runs[1].created_at
    by_id = {run.run_id: run for run in runs}
    assert by_id["run-a"].complete is True
    assert by_id["run-b"].complete is False


def test_list_runs_missing_dir(tmp_path: Path) -> None:
    assert list_runs(tmp_path / "nao-existe") == []


def test_resolve_output_dir_falls_back_without_token() -> None:
    with patch(
        "social_media.src.ui.runs.build_config", side_effect=ValueError("sem token")
    ):
        result = resolve_output_dir()
    assert result == Path("output").resolve()


def test_resolve_output_dir_uses_config(tmp_path: Path) -> None:
    from social_media.src.config import build_config

    config = build_config(apify_token="test-token", output_dir=tmp_path / "saida")
    with patch("social_media.src.ui.runs.build_config", return_value=config):
        result = resolve_output_dir()
    assert result == (tmp_path / "saida").resolve()
