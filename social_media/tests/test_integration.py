import json
from pathlib import Path

import openpyxl
import pytest

from social_media.src.config import build_config
from social_media.src.dependencies import Dependencies
from social_media.src.domain.sentiment import SentimentResult
from social_media.src.exporters.png import export_charts
from social_media.src.exporters.xlsx import build_quality_report, export_xlsx
from social_media.src.pipeline.runner import run_pipeline
from social_media.src.pipeline.steps.comment_features import comment_features_step
from social_media.src.pipeline.steps.content_type import content_type_step
from social_media.src.pipeline.steps.nlp_sentiment_terms import nlp_sentiment_terms_step
from social_media.src.pipeline.steps.nlp_terms import nlp_terms_step
from social_media.src.pipeline.steps.nlp_topics import nlp_topics_step
from social_media.src.pipeline.steps.parse import parse_step
from social_media.src.pipeline.steps.post_conversation import post_conversation_step
from social_media.src.pipeline.steps.post_features import post_features_step
from social_media.src.pipeline.steps.timing import timing_step

FIXTURES_DIR = Path(__file__).parent / "fixtures"

_EXPECTED_CSVS = {
    "caption_top_terms.csv",
    "comment_top_terms.csv",
    "comment_topics.csv",
    "sentiment_term_comparison.csv",
}

_EXPECTED_PNGS = {
    "likes_comments_timeline.png",
    "top_posts_engagement.png",
    "posts_by_type.png",
    "caption_word_count_vs_engagement.png",
    "engagement_heatmap_hour_weekday.png",
    "avg_likes_comments_by_weekday.png",
}


def load_fixture(name: str) -> list[dict]:
    with open(FIXTURES_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


def build_test_config():
    return build_config(apify_token="test-token")


def _make_mock_nlp():
    """Retorna um mock de nlp que lematiza mantendo tokens em minúsculas."""
    from unittest.mock import MagicMock

    nlp = MagicMock()

    def mock_pipe(texts, batch_size=None):
        for text in texts:
            doc = MagicMock()
            tokens = text.split()
            token_mocks = []
            for token in tokens:
                tm = MagicMock()
                tm.lemma_ = token
                tm.is_stop = False
                tm.is_punct = False
                tm.is_space = False
                token_mocks.append(tm)
            doc.__iter__ = lambda self, _tokens=token_mocks: iter(_tokens)
            yield doc

    nlp.pipe = mock_pipe
    return nlp


def _make_mock_embedding_model():
    from unittest.mock import MagicMock

    model = MagicMock()
    model.encode = MagicMock(return_value=[[0.0] * 384])
    return model


def run_full_pipeline(fixture_name: str):
    config = build_test_config()
    deps = Dependencies()
    deps.sentiment_analyzer = lambda text: SentimentResult(
        label="positivo" if "bom" in text.lower() else "neutro",
        score=0.8 if "bom" in text.lower() else 0.5,
    )
    deps._spacy_nlp = _make_mock_nlp()
    deps._embedding_model = _make_mock_embedding_model()

    initial = {"raw_json_path": FIXTURES_DIR / fixture_name}
    steps = [
        parse_step,
        post_features_step,
        comment_features_step,
        post_conversation_step,
        content_type_step,
        timing_step,
        nlp_terms_step,
        nlp_topics_step,
        nlp_sentiment_terms_step,
    ]
    return run_pipeline(steps, initial, config, deps)


def test_full_pipeline_end_to_end() -> None:
    dfs = run_full_pipeline("synthetic_posts.json")

    assert "posts" in dfs
    assert "comments" in dfs
    assert "timing_by_hour" in dfs
    assert "timing_by_weekday" in dfs
    assert "content_by_type" in dfs
    assert len(dfs["posts"]) == 3


def test_export_xlsx(tmp_path: Path) -> None:
    dfs = run_full_pipeline("synthetic_posts.json")
    config = build_test_config()
    output_path = export_xlsx(dfs, tmp_path, config)

    assert output_path.exists()

    workbook = openpyxl.load_workbook(output_path)
    expected_sheets = {
        "Posts",
        "Comments",
        "Timing_Hour",
        "Timing_Weekday",
        "Content_By_Type",
        "Quality",
        "Caption_Top_Terms",
        "Comment_Top_Terms",
        "Comment_Topics",
        "Sentiment_Terms",
    }
    assert set(workbook.sheetnames) == expected_sheets

    posts_sheet = workbook["Posts"]
    header = [cell.value for cell in posts_sheet[1]]
    assert "num_likes" in header
    assert "comments_per_like" in header

    quality_sheet = workbook["Quality"]
    quality_checks = [cell.value for cell in quality_sheet["A"]][1:]
    assert "total_posts" in quality_checks
    assert "comments_coverage_ratio" in quality_checks


def test_build_quality_report_returns_checks() -> None:
    dfs = run_full_pipeline("synthetic_posts.json")
    report = build_quality_report(dfs)
    assert not report.empty
    assert "check" in report.columns
    assert "value" in report.columns
    assert "status" in report.columns


def test_export_charts(tmp_path: Path) -> None:
    dfs = run_full_pipeline("synthetic_posts.json")
    config = build_test_config()
    chart_dir = tmp_path / "charts"

    saved_paths = export_charts(dfs, chart_dir, config)
    saved_names = {p.name for p in saved_paths}

    assert saved_names == _EXPECTED_PNGS
    for path in saved_paths:
        assert path.exists()
        assert path.stat().st_size > 0


def test_export_csvs(tmp_path: Path) -> None:
    from social_media.src.exporters.csv import export_csvs

    dfs = run_full_pipeline("synthetic_posts.json")
    paths = export_csvs(dfs, tmp_path)
    assert {p.name for p in paths} == _EXPECTED_CSVS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
