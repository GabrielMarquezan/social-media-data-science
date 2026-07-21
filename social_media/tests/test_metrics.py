import numpy as np
import pandas as pd
import pytest

from social_media.src.metrics.caption import (
    caption_char_count,
    caption_emoji_count,
    caption_word_count,
    hashtag_count,
    has_cta,
    has_hashtags,
    has_mentions,
    mention_count,
)
from social_media.src.metrics.comment import is_qualified, is_question, word_count
from social_media.src.metrics.engagement import (
    comments_per_like,
    comments_per_view,
    engagement_rate,
    num_comentarios,
    num_likes,
)
from social_media.src.metrics.timing import (
    aggregate_by_hour,
    aggregate_by_weekday,
    post_hour,
    post_period,
    post_weekday,
)


class TestEngagement:
    def test_num_likes(self) -> None:
        df = pd.DataFrame({"likes_count": [10, 20, None]})
        result = num_likes(df)
        assert result[:2].tolist() == [10.0, 20.0]
        assert np.isnan(result.iloc[2])

    def test_num_comentarios(self) -> None:
        df = pd.DataFrame({"comments_count": [5, 0, None]})
        result = num_comentarios(df)
        assert result[:2].tolist() == [5.0, 0.0]
        assert np.isnan(result.iloc[2])

    def test_engagement_rate(self) -> None:
        likes = pd.Series([10, 20, 5, 0])
        comments = pd.Series([5, 10, 0, 0])
        views = pd.Series([100, 0, None, 50])
        result = engagement_rate(likes, comments, views)
        assert result[0] == 0.15
        assert np.isnan(result[1])
        assert np.isnan(result[2])
        assert result[3] == 0.0

    def test_comments_per_view(self) -> None:
        comments = pd.Series([10, 5, 0, 3])
        views = pd.Series([100, 0, None, 50])
        result = comments_per_view(comments, views)
        assert result[0] == 0.1
        assert np.isnan(result[1])
        assert np.isnan(result[2])
        assert result[3] == 0.06

    def test_comments_per_like(self) -> None:
        comments = pd.Series([10, 5, 0, 3])
        likes = pd.Series([100, 0, None, 50])
        result = comments_per_like(comments, likes)
        assert result[0] == 0.1
        assert np.isnan(result[1])
        assert np.isnan(result[2])
        assert result[3] == 0.06


class TestCaption:
    def test_caption_word_count(self) -> None:
        series = pd.Series(["hello world", "", None])
        result = caption_word_count(series)
        assert result.tolist() == [2, 0, 0]

    def test_caption_char_count(self) -> None:
        series = pd.Series(["abc", "", None])
        result = caption_char_count(series)
        assert result.tolist() == [3, 0, 0]

    def test_caption_emoji_count(self) -> None:
        series = pd.Series(["olá 😀😀", "sem emoji", None, "🔥 um 🔥 dois 🔥"])
        result = caption_emoji_count(series)
        assert result.tolist() == [2, 0, 0, 3]

    def test_has_hashtags(self) -> None:
        series = pd.Series([["a", "b"], [], None])
        result = has_hashtags(series)
        assert result.tolist() == [True, False, False]

    def test_has_mentions(self) -> None:
        series = pd.Series([["user"], [], None])
        result = has_mentions(series)
        assert result.tolist() == [True, False, False]

    def test_has_cta(self) -> None:
        series = pd.Series(
            [
                "Clique aqui!",
                "link na bio",
                "saiba mais sobre o produto",
                "apenas um texto",
                None,
            ]
        )
        result = has_cta(series)
        assert result.tolist() == [True, True, True, False, False]

    def test_has_cta_ignores_accents(self) -> None:
        series = pd.Series(
            [
                "clíque aqui",
                "saiba máis",
                "confirá o link",
                "texto sem cta",
            ]
        )
        result = has_cta(series)
        assert result.tolist() == [True, True, True, False]

    def test_hashtag_count(self) -> None:
        series = pd.Series([["a", "b"], [], None, "não lista"])
        result = hashtag_count(series)
        assert result.tolist() == [2, 0, 0, 0]

    def test_mention_count(self) -> None:
        series = pd.Series([["a", "b", "c"], [], None])
        result = mention_count(series)
        assert result.tolist() == [3, 0, 0]


class TestComment:
    def test_word_count(self) -> None:
        series = pd.Series(["uma duas três", "", None])
        result = word_count(series)
        assert result.tolist() == [3, 0, 0]

    def test_is_qualified(self) -> None:
        series = pd.Series([10, 5, 4, 0])
        result = is_qualified(series, min_words=5)
        assert result.tolist() == [True, True, False, False]

    def test_is_question(self) -> None:
        series = pd.Series(["Como vai?", "Tudo bem", None, "?"])
        result = is_question(series)
        assert result.tolist() == [True, False, False, True]


class TestTiming:
    def test_post_hour(self) -> None:
        series = pd.Series(pd.to_datetime(
            ["2024-01-15 10:30:00", "2024-01-15 23:00:00"]
        ))
        result = post_hour(series)
        assert result.tolist() == [10, 23]

    def test_post_weekday(self) -> None:
        # 2024-01-15 é segunda-feira
        series = pd.Series(pd.to_datetime(["2024-01-15", "2024-01-21"]))
        result = post_weekday(series)
        assert result.tolist() == [0, 6]

    def test_post_period(self) -> None:
        series = pd.Series(pd.to_datetime(
            ["2024-01-15 03:00:00", "2024-01-15 09:00:00", "2024-01-15 14:00:00", "2024-01-15 20:00:00"]
        ))
        result = post_period(series)
        assert result.tolist() == ["Madrugada", "Manhã", "Tarde", "Noite"]

    def test_aggregate_by_hour(self) -> None:
        posts = pd.DataFrame(
            {
                "post_hour": [10, 10, 11],
                "likes_count": [10, 20, 30],
                "comments_count": [1, 2, 3],
                "comments_per_like": [0.1, 0.1, 0.1],
            }
        )
        result = aggregate_by_hour(posts)
        assert result["posts"].tolist() == [2, 1]
        assert result["avg_likes"].tolist() == [15.0, 30.0]

    def test_aggregate_by_weekday(self) -> None:
        posts = pd.DataFrame(
            {
                "post_weekday": [0, 0, 1],
                "likes_count": [10, 30, 20],
                "comments_count": [1, 3, 2],
                "comments_per_like": [0.1, 0.1, 0.1],
            }
        )
        result = aggregate_by_weekday(posts)
        assert result["posts"].tolist() == [2, 1]
        assert result["avg_likes"].tolist() == [20.0, 20.0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
