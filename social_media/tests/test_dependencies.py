from unittest.mock import MagicMock, patch

from social_media.src.config import build_config
from social_media.src.dependencies import Dependencies, build_dependencies
from social_media.src.domain.sentiment import SentimentResult


def test_build_dependencies_uses_config_sentiment_model() -> None:
    config = build_config(
        apify_token="test-token",
        sentiment_model="dummy/model-name",
    )
    deps = build_dependencies(config)
    assert deps.sentiment_model == "dummy/model-name"


def test_get_sentiment_analyzer_uses_stored_model_name() -> None:
    deps = Dependencies(sentiment_model="custom/model")

    # O analyzer carrega o pipeline de forma lazy; inspecionamos o closure
    # para garantir que o model_name configurado será usado, sem disparar
    # download de um modelo inexistente.
    analyzer = deps.get_sentiment_analyzer()
    closure_vars = {
        name: cell.cell_contents
        for name, cell in zip(analyzer.__code__.co_freevars, analyzer.__closure__ or ())
    }
    assert closure_vars.get("model_name") == "custom/model"


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
