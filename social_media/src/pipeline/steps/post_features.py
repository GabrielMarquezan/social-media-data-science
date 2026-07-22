import pandas as pd

from social_media.src.config import Config
from social_media.src.dependencies import Dependencies
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
from social_media.src.metrics.engagement import (
    comments_per_like,
    comments_per_view,
    engagement_rate,
    num_comentarios,
    num_likes,
)


def post_features_step(
    dfs: dict[str, pd.DataFrame], config: Config, deps: Dependencies
) -> dict[str, pd.DataFrame]:
    """Adiciona features de engajamento e legenda ao DataFrame `posts`."""
    posts = dfs["posts"].copy()

    posts["num_likes"] = num_likes(posts)
    posts["num_comentarios"] = num_comentarios(posts)
    posts["engagement_rate"] = engagement_rate(
        posts["likes_count"], posts["comments_count"], posts["views"]
    )
    posts["comments_per_view"] = comments_per_view(
        posts["comments_count"], posts["views"]
    )
    posts["comments_per_like"] = comments_per_like(
        posts["comments_count"], posts["likes_count"]
    )

    posts["caption_word_count"] = caption_word_count(posts["caption"])
    posts["caption_char_count"] = caption_char_count(posts["caption"])
    posts["caption_emoji_count"] = caption_emoji_count(posts["caption"])
    posts["has_hashtags"] = has_hashtags(posts["hashtags"])
    posts["has_mentions"] = has_mentions(posts["mentions"])
    posts["has_cta"] = has_cta(posts["caption"])
    posts["hashtag_count"] = hashtag_count(posts["hashtags"])
    posts["mention_count"] = mention_count(posts["mentions"])

    dfs = dict(dfs)
    dfs["posts"] = posts
    return dfs
