import numpy as np
import pandas as pd

from social_media.src.metrics.conversation import (
    avg_reply_depth,
    discussion_index,
    max_reply_depth,
    qualified_comment_rate,
    question_comment_rate,
    sentiment_shares,
)


def test_discussion_index() -> None:
    comments = pd.DataFrame(
        {
            "post_id": ["p1", "p1", "p1", "p2", "p2"],
            "parent_id": [None, None, "c1", None, "c4"],
            "depth": [0, 0, 1, 0, 1],
        }
    )
    comments.index = ["c1", "c2", "c3", "c4", "c5"]
    result = discussion_index(comments)
    assert result.loc["p1"] == 0.5  # 1 reply / 2 top-level
    assert result.loc["p2"] == 1.0  # 1 reply / 1 top-level


def test_avg_reply_depth() -> None:
    comments = pd.DataFrame(
        {
            "post_id": ["p1", "p1", "p1", "p2"],
            "parent_id": [None, "c1", "c1", None],
            "depth": [0, 1, 2, 0],
        }
    )
    comments.index = ["c1", "c2", "c3", "c4"]
    result = avg_reply_depth(comments)
    assert result.loc["p1"] == 1.5  # (1 + 2) / 2
    assert "p2" not in result.index


def test_max_reply_depth() -> None:
    comments = pd.DataFrame(
        {
            "post_id": ["p1", "p1", "p1"],
            "parent_id": [None, "c1", "c2"],
            "depth": [0, 1, 2],
        }
    )
    comments.index = ["c1", "c2", "c3"]
    result = max_reply_depth(comments)
    assert result.loc["p1"] == 2


def test_qualified_comment_rate() -> None:
    comments = pd.DataFrame(
        {
            "post_id": ["p1", "p1", "p1", "p2"],
            "is_qualified": [True, False, True, False],
        }
    )
    result = qualified_comment_rate(comments)
    assert result.loc["p1"] == 2 / 3
    assert result.loc["p2"] == 0.0


def test_question_comment_rate() -> None:
    comments = pd.DataFrame(
        {
            "post_id": ["p1", "p1", "p2"],
            "is_question": [True, False, True],
        }
    )
    result = question_comment_rate(comments)
    assert result.loc["p1"] == 0.5
    assert result.loc["p2"] == 1.0


def test_sentiment_shares() -> None:
    comments = pd.DataFrame(
        {
            "post_id": ["p1", "p1", "p1", "p1", "p2"],
            "sentiment_label": ["positivo", "positivo", "neutro", "negativo", "positivo"],
        }
    )
    result = sentiment_shares(comments)
    assert result.loc["p1", "sent_positivo_share"] == 0.5
    assert result.loc["p1", "sent_neutro_share"] == 0.25
    assert result.loc["p1", "sent_negativo_share"] == 0.25
    assert result.loc["p2", "sent_positivo_share"] == 1.0
    assert result.loc["p2", "sent_neutro_share"] == 0.0


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
