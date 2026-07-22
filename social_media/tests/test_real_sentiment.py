import tempfile
from pathlib import Path

import pytest

from social_media.src.config import build_config
from social_media.src.dependencies import build_dependencies
from social_media.src.exporters.png import export_charts
from social_media.src.exporters.xlsx import export_xlsx
from social_media.src.pipeline.runner import run_pipeline
from social_media.src.pipeline.steps.comment_features import comment_features_step
from social_media.src.pipeline.steps.content_type import content_type_step
from social_media.src.pipeline.steps.parse import parse_step
from social_media.src.pipeline.steps.post_conversation import post_conversation_step
from social_media.src.pipeline.steps.post_features import post_features_step
from social_media.src.pipeline.steps.timing import timing_step

REAL_FIXTURE = Path(__file__).parents[2] / "data" / "post.json"


@pytest.mark.slow
@pytest.mark.skipif(not REAL_FIXTURE.exists(), reason="Amostra real não encontrada")
def test_real_data_pipeline_with_real_sentiment_analyzer() -> None:
    """Valida que o sentiment analyzer real popula labels/scores sem erros de cache."""
    config = build_config(apify_token="test-token")
    deps = build_dependencies(config)

    initial = {"raw_json_path": REAL_FIXTURE}
    steps = [
        parse_step,
        post_features_step,
        comment_features_step,
        post_conversation_step,
        content_type_step,
        timing_step,
    ]
    dfs = run_pipeline(steps, initial, config, deps)

    comments = dfs["comments"]
    assert not comments.empty
    assert "sentiment_label" in comments.columns
    assert "sentiment_score" in comments.columns
    assert comments["sentiment_label"].notna().all()
    assert comments["sentiment_score"].notna().all()
    assert set(comments["sentiment_label"].unique()).issubset(
        {"positivo", "neutro", "negativo"}
    )

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        xlsx_path = export_xlsx(dfs, tmp_path, config)
        chart_paths = export_charts(dfs, tmp_path / "charts", config)
        assert xlsx_path.exists()
        assert len(chart_paths) == 6


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "slow"])
