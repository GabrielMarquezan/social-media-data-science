import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from social_media.src.config import build_config
from social_media.src.dependencies import Dependencies
from social_media.src.domain.sentiment import SentimentResult
from social_media.src.pipeline.runner import run_pipeline
from social_media.src.pipeline.steps.comment_features import comment_features_step
from social_media.src.pipeline.steps.content_type import content_type_step
from social_media.src.pipeline.steps.parse import parse_step
from social_media.src.pipeline.steps.post_conversation import post_conversation_step
from social_media.src.pipeline.steps.post_features import post_features_step
from social_media.src.pipeline.steps.timing import timing_step

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> list[dict]:
    with open(FIXTURES_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


def build_test_config() -> Any:
    return build_config(apify_token="test-token")


def test_run_pipeline_with_dummy_steps() -> None:
    def step_add_col(dfs, config, deps):
        dfs = dict(dfs)
        df = dfs["data"].copy()
        df["x"] = df["a"] * 2
        dfs["data"] = df
        return dfs

    initial = {"data": pd.DataFrame({"a": [1, 2, 3]})}
    result = run_pipeline([step_add_col], initial, build_test_config(), Dependencies())

    assert result["data"]["x"].tolist() == [2, 4, 6]


def test_parse_step() -> None:
    config = build_test_config()
    initial = {"raw_json_path": FIXTURES_DIR / "synthetic_posts.json"}
    result = parse_step(initial, config, Dependencies())

    assert "posts" in result
    assert "comments" in result
    assert len(result["posts"]) == 3
    assert len(result["comments"]) == 4  # 2 do image + 1 resposta + 1 do video

    comments = result["comments"]
    assert "parent_id" in comments.columns
    assert "depth" in comments.columns

    reply = comments[comments["text"] == "Uso o Lightroom."].iloc[0]
    parent = comments[comments["id"] == reply["parent_id"]].iloc[0]
    assert parent["text"] == "Você usa qual edição?"
    assert reply["depth"] == 1
    assert parent["depth"] == 0


def test_post_features_step() -> None:
    config = build_test_config()
    initial = {"raw_json_path": FIXTURES_DIR / "synthetic_posts.json"}
    dfs = parse_step(initial, config, Dependencies())
    dfs = post_features_step(dfs, config, Dependencies())

    posts = dfs["posts"]
    expected_cols = [
        "num_likes",
        "num_comentarios",
        "engagement_rate",
        "comments_per_view",
        "comments_per_like",
        "caption_word_count",
        "caption_char_count",
        "caption_emoji_count",
        "has_hashtags",
        "has_mentions",
        "has_cta",
        "hashtag_count",
        "mention_count",
    ]
    for col in expected_cols:
        assert col in posts.columns, f"Coluna {col} não encontrada"

    video = posts[posts["id"] == "vid_001"].iloc[0]
    assert video["engagement_rate"] == (120 + 1) / 1500
    assert video["comments_per_view"] == 1 / 1500

    image = posts[posts["id"] == "img_001"].iloc[0]
    assert image["comments_per_like"] == 2 / 42
    assert image["has_cta"] == True


def test_comment_features_step() -> None:
    config = build_test_config()
    deps = Dependencies()
    deps.sentiment_analyzer = lambda text: SentimentResult(
        label="positivo" if "bom" in text.lower() else "neutro",
        score=0.8 if "bom" in text.lower() else 0.5,
    )

    initial = {"raw_json_path": FIXTURES_DIR / "synthetic_posts.json"}
    dfs = parse_step(initial, config, Dependencies())
    dfs = comment_features_step(dfs, config, deps)

    comments = dfs["comments"]
    expected_cols = ["word_count", "is_qualified", "is_question", "sentiment_label", "sentiment_score"]
    for col in expected_cols:
        assert col in comments.columns, f"Coluna {col} não encontrada"

    question = comments[comments["text"].str.contains(r"\?", regex=True, na=False)]
    assert len(question) == 1
    assert question.iloc[0]["is_question"] == True


def test_timing_step() -> None:
    config = build_test_config()
    initial = {"raw_json_path": FIXTURES_DIR / "synthetic_posts.json"}
    dfs = parse_step(initial, config, Dependencies())
    dfs = post_features_step(dfs, config, Dependencies())
    dfs = timing_step(dfs, config, Dependencies())

    posts = dfs["posts"]
    assert "post_hour" in posts.columns
    assert "post_weekday" in posts.columns
    assert "post_period" in posts.columns

    assert "timing_by_hour" in dfs
    assert "timing_by_weekday" in dfs
    assert len(dfs["timing_by_hour"]) >= 1
    assert len(dfs["timing_by_weekday"]) >= 1


def test_full_pipeline() -> None:
    config = build_test_config()
    deps = Dependencies()
    deps.sentiment_analyzer = lambda text: SentimentResult(label="positivo", score=0.9)

    initial = {"raw_json_path": FIXTURES_DIR / "synthetic_posts.json"}
    steps = [parse_step, post_features_step, comment_features_step, timing_step]
    dfs = run_pipeline(steps, initial, config, deps)

    assert "posts" in dfs
    assert "comments" in dfs
    assert "timing_by_hour" in dfs
    assert "timing_by_weekday" in dfs
    assert len(dfs["posts"]) == 3


def test_comment_features_step_does_not_load_analyzer_when_empty() -> None:
    config = build_test_config()
    deps = Dependencies()  # sem sentiment_analyzer configurado

    initial = {"comments": pd.DataFrame(columns=["text"])}
    result = comment_features_step(initial, config, deps)

    comments = result["comments"]
    assert "word_count" in comments.columns
    assert "is_qualified" in comments.columns
    assert "is_question" in comments.columns
    assert "sentiment_label" in comments.columns
    assert "sentiment_score" in comments.columns
    assert comments.empty


def test_post_conversation_step() -> None:
    config = build_test_config()
    deps = Dependencies()
    deps.sentiment_analyzer = lambda text: SentimentResult(label="positivo", score=0.9)

    initial = {"raw_json_path": FIXTURES_DIR / "synthetic_posts.json"}
    dfs = parse_step(initial, config, deps)
    dfs = post_features_step(dfs, config, deps)
    dfs = comment_features_step(dfs, config, deps)
    dfs = post_conversation_step(dfs, config, deps)

    posts = dfs["posts"]
    expected_cols = [
        "discussion_index",
        "avg_reply_depth",
        "max_reply_depth",
        "qualified_comment_rate",
        "question_comment_rate",
        "sent_positivo_share",
        "sent_neutro_share",
        "sent_negativo_share",
    ]
    for col in expected_cols:
        assert col in posts.columns, f"Coluna {col} não encontrada"

    image = posts[posts["id"] == "img_001"].iloc[0]
    assert image["discussion_index"] == 1 / 2  # 1 reply / 2 top-level comments
    assert image["max_reply_depth"] == 1


def test_content_type_step() -> None:
    config = build_test_config()
    deps = Dependencies()
    deps.sentiment_analyzer = lambda text: SentimentResult(label="positivo", score=0.9)

    initial = {"raw_json_path": FIXTURES_DIR / "synthetic_posts.json"}
    dfs = parse_step(initial, config, deps)
    dfs = post_features_step(dfs, config, deps)
    dfs = comment_features_step(dfs, config, deps)
    dfs = post_conversation_step(dfs, config, deps)
    dfs = content_type_step(dfs, config, deps)

    assert "content_by_type" in dfs
    content = dfs["content_by_type"]
    assert "Image" in content["type"].values
    assert "Video" in content["type"].values
    assert "Sidecar" in content["type"].values
    assert "posts" in content.columns
    assert "avg_engagement_rate" in content.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
