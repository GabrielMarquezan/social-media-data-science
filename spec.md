# Specification: social media data processor

This document defines how the system must work. It is intended for an AI agent that will implement the remaining parts of the project and maintain the existing ones.

## 1. Overview

The system extracts public data from Instagram posts, processes it with NLP and statistical methods, and presents the results to the user through a web interface running on localhost.

The current implementation already contains the backend pipeline. The next agent must build the **Streamlit web interface** that wraps the existing pipeline and exposes its outputs to the user.

### Goals

- Allow users to provide multiple Instagram post URLs.
- Run the full pipeline on demand.
- Show progress to the user in real time.
- List previous runs.
- Display and download generated outputs (XLSX, CSVs, PNGs).
- Visualize charts and tables inside the interface.

## 2. High-level architecture

The system is composed of three layers:

1. **Web interface** (to be implemented): Streamlit app running on localhost.
2. **Orchestration layer** (existing): `social_media.src.main` coordinates extraction, pipeline, and exports.
3. **Processing layer** (existing): a sequence of pure pipeline steps that transform `dict[str, DataFrame]` into `dict[str, DataFrame]`.

### Data flow

```text
User links (Streamlit UI)
    │
    ▼
social_media.src.main
    │
    ├── extract/apify.py      → data/raw_{run_id}.json
    │
    ├── pipeline/steps/*      → DataFrames (posts, comments, timing, ...)
    │
    └── exporters/*           → output/{run_id}/
                                    ├── metrics.xlsx
                                    ├── charts/*.png
                                    └── *.csv
```

### Runtime contract

- `main.py` is a single async function that:
  - Creates a run id.
  - Loads configuration and logging.
  - Reads links from a file or list.
  - Extracts data from Apify.
  - Runs the pipeline.
  - Exports the results.
- The web interface may call `main.main()` or, preferably, invoke the same functions as `main.py` while streaming progress to the UI.

## 3. Web interface (Streamlit)

### Technology

- **Streamlit** only.
- No additional frontend frameworks or CSS libraries required.
- Use standard Streamlit widgets and session state.

### Required views

#### 3.1 Input view

- A text area where users paste one Instagram post URL per line.
- A button to start the run.
- Validate that every non-empty line looks like an Instagram URL (`https://www.instagram.com/p/{shortcode}/...`).
- If validation fails, show a clear error and do not start the run.

#### 3.2 Progress view

- While a run is active, display real-time progress updates.
- At minimum, show the following phases:
  - Extraction started (Apify actor call)
  - Extraction completed (number of items downloaded)
  - Pipeline running (current step name)
  - Export completed
  - Finished
- The interface must remain responsive. Use `asyncio`, `threading`, or Streamlit's async support to avoid blocking the main thread. The exact concurrency model is left to the implementing agent.
- If a phase fails, show the error message and stop.

#### 3.3 Results view

- After a run finishes, show the generated artifacts:
  - `metrics.xlsx` with a download button.
  - All CSV files with download buttons.
  - All PNG charts rendered inline.
  - Key tables (posts, comments, top terms, topics) rendered as interactive dataframes.
- Display the run id and the output directory path.

#### 3.4 Past runs view

- List previous runs by reading `output/{run_id}/` directories.
- For each past run, show:
  - Run id
  - Timestamp (from directory creation time or a metadata file if present)
  - Number of posts/comments processed
  - Buttons to download `metrics.xlsx` and view charts/tables
- If a run is incomplete (missing outputs), mark it as failed or incomplete.

#### 3.5 Navigation

- Use a sidebar or tabs to switch between:
  - New run
  - Results of the latest run
  - Past runs
- The latest run should be automatically opened after completion.

### Session and state

- Use Streamlit's `st.session_state` to keep:
  - The current list of links
  - The current run id
  - The current progress messages
  - The latest run output metadata
- Avoid recomputing the pipeline on every widget interaction.

### Error handling

- Display user-friendly error messages in the UI.
- Do not expose raw stack traces unless the user explicitly asks for them.
- On failure, keep the input links in the text area so the user can retry.

### Logging

- The existing logging system writes structured JSON or text logs to stderr.
- The web interface should capture progress messages and show them in the UI.
- It must not replace the existing logging configuration; instead, it may read logs or subscribe to a progress callback.

## 4. Configuration and environment

### Required environment variable

- `APIFY_API_KEY`: API key for Apify.

### Optional environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APIFY_ACTOR` | `apify/instagram-scraper` | Apify actor used for extraction |
| `RESULTS_LIMIT` | `100` | Maximum results per link |
| `QUALIFIED_COMMENT_MIN_WORDS` | `5` | Minimum words for a comment to be considered qualified |
| `SENTIMENT_MODEL` | `nlptown/bert-base-multilingual-uncased-sentiment` | Transformers model for sentiment |
| `LOG_LEVEL` | `DEBUG` | Logging level |
| `LOG_FORMAT` | `json` | Log format (`json` or `text`) |
| `TOP_POSTS_LIMIT` | `10` | Number of top posts in charts |
| `CHART_DPI` | `150` | PNG resolution |
| `XLSX_ENGINE` | `openpyxl` | Excel engine |
| `SPACY_MODEL` | `pt_core_news_sm` | spaCy model |
| `BERTOPIC_EMBEDDING_MODEL` | `paraphrase-multilingual-MiniLM-L12-v2` | Embedding model for BERTopic |
| `NLP_TOP_TERMS_LIMIT` | `20` | Number of top terms to extract |
| `NLP_TOPIC_COUNT` | `10` | Number of topics to generate |
| `NLP_TOPIC_TERMS_LIMIT` | `10` | Terms per topic |
| `NLP_SENTIMENT_TERMS_LIMIT` | `10` | Terms per sentiment |

### Loading order

- `build_config()` reads from environment variables first, then optional function arguments.
- A `.env` file must be supported through `python-dotenv` (already configured).

## 5. Domain models

### Post

A frozen dataclass representing an Instagram post.

- `id`: unique identifier
- `type`: post type (e.g., Image, Video, Sidecar)
- `short_code`: short code from the URL
- `caption`: caption text
- `hashtags`: list of hashtags
- `mentions`: list of mentions
- `url`: post URL
- `comments_count`: total comments
- `first_comment`: first comment text
- `latest_comments`: list of `Comment`
- `likes_count`: number of likes
- `timestamp`: publication datetime
- `owner`: `Author`
- `product_type`: product type
- `views`: view count (for videos)
- `video_duration`: duration in seconds (for videos)

### Comment

A frozen dataclass representing a comment or reply.

- `id`: unique identifier
- `text`: comment text
- `owner`: `Author`
- `timestamp`: datetime
- `likes_count`: number of likes
- `replies_count`: number of replies
- `replies`: list of nested `Comment`

### Author

- `id`: identifier
- `username`: username
- `full_name`: full name
- `is_verified`: verified status
- `profile_pic_url`: profile picture URL

### SentimentResult

- `label`: one of `positivo`, `neutro`, `negativo`
- `score`: float between 0 and 1

## 6. Data extraction

### Actor input

```python
{
    "addParentData": False,
    "directUrls": [list of links],
    "resultsLimit": config.results_limit,
    "resultsType": "posts",
}
```

### Actor output

- The actor returns a list of JSON items.
- Each item is saved as-is to `data/raw_{run_id}.json`.
- If the actor call fails, raise a `RuntimeError` with a clear message.

### Pagination

- Iterate through the dataset using `limit` and `offset` until fewer items than the limit are returned.

### Error handling

- If `call()` returns `None`, raise `RuntimeError`.
- Log the actor name, run id, number of links, and results limit.

## 7. Pipeline

### Pipeline contract

```python
Step = Callable[
    [dict[str, pd.DataFrame], Config, Dependencies],
    dict[str, pd.DataFrame]
]
```

- Each step receives a dictionary of DataFrames, a `Config`, and `Dependencies`.
- Each step returns a new dictionary of DataFrames.
- Steps must be pure and tolerate missing or malformed data.
- The runner logs the shape of each DataFrame before and after each step.

### Default step order

1. `parse_step`
2. `post_features_step`
3. `comment_features_step`
4. `post_conversation_step`
5. `content_type_step`
6. `timing_step`
7. `nlp_terms_step`
8. `nlp_topics_step`
9. `nlp_sentiment_terms_step`

### Step contracts

#### parse_step

- Input: `{"raw_json_path": Path}`
- Reads the JSON file and converts it to domain objects using `parsers/apify.py`.
- Outputs:
  - `posts`: DataFrame with one row per post
  - `comments`: DataFrame with one row per comment or reply, including `post_id`, `parent_id`, and `depth`

#### post_features_step

- Input/Output: mutates `posts`
- Adds columns:
  - `num_likes`, `num_comentarios`
  - `engagement_rate`: `(likes + comments) / views` when `views > 0`
  - `comments_per_view`: `comments / views` when `views > 0`
  - `comments_per_like`: `comments / likes` when `likes > 0`
  - `caption_word_count`, `caption_char_count`, `caption_emoji_count`
  - `has_hashtags`, `has_mentions`, `has_cta`, `hashtag_count`, `mention_count`

#### comment_features_step

- Input/Output: mutates `comments`
- Adds columns:
  - `word_count`
  - `is_qualified`: `word_count >= config.qualified_comment_min_words`
  - `is_question`: contains `?`
  - `sentiment_label`: one of `positivo`, `neutro`, `negativo`
  - `sentiment_score`: float between 0 and 1
- If `comments` is empty, do not load the sentiment model.

#### post_conversation_step

- Input: `posts`, `comments`
- Output: mutates `posts`
- Adds conversation metrics per post:
  - `discussion_index`: replies / top-level comments
  - `avg_reply_depth`: average depth of replies
  - `max_reply_depth`: maximum depth of replies
  - `qualified_comment_rate`: fraction of qualified comments
  - `question_comment_rate`: fraction of comments with questions
  - `sent_positivo_share`, `sent_neutro_share`, `sent_negativo_share`: sentiment distributions

#### content_type_step

- Input: `posts`, `comments`
- Output: `content_by_type` DataFrame
- Aggregates metrics by `type`:
  - `posts`, `num_likes`, `num_comentarios`, `visualizacoes`
  - `avg_engagement_rate`, `avg_comments_per_view`
  - `avg_qualified_comment_rate`, `avg_discussion_index`
  - `community_index`, `new_commenter_share`

#### timing_step

- Input: `posts`
- Output: mutates `posts`; adds `timing_by_hour`, `timing_by_weekday`
- Adds columns:
  - `post_hour`: hour of day
  - `post_weekday`: 0=Monday, 6=Sunday
  - `post_period`: Madrugada, Manhã, Tarde, Noite

#### nlp_terms_step

- Input: `posts`, `comments`
- Output: `caption_top_terms`, `comment_top_terms`
- Uses spaCy + KeyBERT to extract top terms from captions and comments.

#### nlp_topics_step

- Input: `comments`
- Output: `comment_topics`
- Uses BERTopic to discover topics in comments.
- Returns columns: `topic_id`, `topic_label`, `keyword`, `score`

#### nlp_sentiment_terms_step

- Input: `comments`
- Output: `sentiment_term_comparison`
- Returns the most frequent terms in positive and negative comments.

## 8. Metrics definitions

### Engagement

- `engagement_rate`: `(likes + comments) / views` when views > 0, otherwise NaN
- `comments_per_view`: `comments / views` when views > 0, otherwise NaN
- `comments_per_like`: `comments / likes` when likes > 0, otherwise NaN

### Caption

- `caption_word_count`: number of words in `caption`
- `caption_char_count`: number of characters in `caption`
- `caption_emoji_count`: number of emoji characters
- `has_hashtags`: `hashtags` list is non-empty
- `has_mentions`: `mentions` list is non-empty
- `has_cta`: caption contains a call-to-action phrase (case-insensitive, accent-insensitive)
- `hashtag_count`: length of `hashtags`
- `mention_count`: length of `mentions`

### Conversation

- `discussion_index`: `replies / top_level_comments` per post
- `avg_reply_depth`: mean of `depth` for replies
- `max_reply_depth`: max of `depth` for replies
- `qualified_comment_rate`: `qualified_comments / total_comments` per post
- `question_comment_rate`: `question_comments / total_comments` per post
- sentiment shares: `label_count / total_comments` per post

### Content type

- `community_index`: recurring commenters / unique commenters, grouped by post type
- `new_commenter_share`: comments from users who only commented on one post, grouped by post type

### Timing

- `post_hour`: hour from timestamp
- `post_weekday`: weekday from timestamp, Monday=0
- `post_period`: time-of-day bucket
- Aggregations by hour or weekday include counts, averages of likes, comments, views, engagement, and conversation metrics.

## 9. NLP

### Preprocessing

- Remove URLs, mentions, and normalize hashtags.
- Convert text to lowercase and collapse whitespace.
- Lemmatize using spaCy, dropping stop words, punctuation, and spaces.

### Sentiment

- Default model: `nlptown/bert-base-multilingual-uncased-sentiment`.
- Map star labels (1–5) to `positivo`, `neutro`, `negativo`.
- Score is normalized to `[0, 1]`.
- Empty text returns `neutro` with score 0.5.

### Terms

- Use KeyBERT on lemmatized captions and comments.
- Extract 1- and 2-grams.
- Return columns: `term`, `score`, `count`.
- Limit results to `config.nlp_top_terms_limit`.

### Topics

- Use BERTopic with a sentence-transformer embedding model.
- Number of topics: `config.nlp_topic_count`.
- Skip outliers (`topic_id == -1`).
- Return columns: `topic_id`, `topic_label`, `keyword`, `score`.

### Sentiment terms

- For `positivo` and `negativo` comments, count lemmatized terms.
- Return columns: `term`, `sentiment`, `count`.
- Limit results to `config.nlp_sentiment_terms_limit`.

## 10. Dependencies

The `Dependencies` class is a lazy factory for heavy models.

- `get_sentiment_analyzer()`: returns a callable `str -> SentimentResult`
- `get_spacy_nlp()`: returns the spaCy model
- `get_embedding_model()`: returns the sentence-transformer model

Models must be loaded only when first requested.

## 11. Exports

### XLSX

- File: `output/{run_id}/metrics.xlsx`
- Sheets:
  - Posts
  - Comments
  - Timing_Hour
  - Timing_Weekday
  - Content_By_Type
  - Quality
  - Caption_Top_Terms
  - Comment_Top_Terms
  - Comment_Topics
  - Sentiment_Terms
- Apply styling: bold headers, auto-fit columns, filters, freeze panes.
- Convert timezone-aware datetimes to naive before writing.

### CSV

- Files: `output/{run_id}/caption_top_terms.csv`, `comment_top_terms.csv`, `comment_topics.csv`, `sentiment_term_comparison.csv`

### PNG

- Directory: `output/{run_id}/charts/`
- Charts:
  - `likes_comments_timeline.png`
  - `top_posts_engagement.png`
  - `posts_by_type.png`
  - `caption_word_count_vs_engagement.png`
  - `engagement_heatmap_hour_weekday.png`
  - `avg_likes_comments_by_weekday.png`

### Quality report

- Included as the `Quality` sheet in the XLSX.
- Checks:
  - `total_posts`
  - `posts_without_valid_views`
  - `posts_without_timestamp`
  - `total_comments`
  - `comments_without_text`
  - `posts_with_comment_count_discrepancy`
  - `comments_coverage_ratio`
- Each check has a `value` and a `status` (`ok` or `warning`).

## 12. Error handling and resilience

- Parser must skip malformed posts and comments individually and log them.
- Pipeline steps must handle empty DataFrames gracefully.
- NLP steps must return empty DataFrames with the correct columns when no data is available.
- Charts must render a placeholder message when data is missing.
- Sentiment analysis failures must return a neutral default and log the error.

## 13. Logging

- Use the standard `logging` module.
- All log records must be structured with `extra={...}`.
- Format: JSON by default, optional text format.
- Include `run_id` in every log record.
- Suppress noisy third-party library logs.

## 14. Testing

- Run fast tests with `pytest social_media/tests -m "not slow"`.
- The slow test (`test_real_data_pipeline_with_real_sentiment_analyzer`) downloads the real sentiment model and is excluded from the fast cycle.
- All new code must be covered by tests.
- Prefer pure unit tests for new Streamlit components.

## 15. Deliverables for the next agent

1. Implement a Streamlit app in a new module (e.g., `social_media/src/app.py` or a separate `app.py` at the project root) that satisfies the requirements in Section 3.
2. Add a new entry point to run the interface, such as a script or a command like `streamlit run app.py`.
3. Ensure the interface can call the existing pipeline without duplicating logic.
4. Add progress reporting from the pipeline to the UI. This may require a lightweight callback or a queue; the exact mechanism is left to the implementing agent.
5. Keep the existing CLI (`python -m social_media.src.main`) working unchanged.
6. Add tests for the new Streamlit app.
7. Update the `README.md` and `AGENTS.md` with instructions for running the web interface. Do not modify this spec.

## 16. Constraints

- The system is Instagram-only for now.
- Do not change the existing Apify actor input contract.
- Do not remove the CLI entry point.
- Do not commit `.env` files or real data.
- Keep all subpackages under `social_media/src/` as namespace packages (no `__init__.py`).
- Use absolute imports `social_media.src.*`.
- Use type hints in all function signatures.
- Follow the existing code style.

## 17. File and directory conventions

- `links.txt`: default input file for the CLI
- `data/raw_{run_id}.json`: raw Apify output
- `output/{run_id}/`: all artifacts for a run
- `output/{run_id}/charts/`: PNG charts
- Generated files must be ignored by Git (`output/` and `data/raw_*.json` are already ignored).

## 18. Future considerations (out of scope)

- Support for other social networks (TikTok, X, etc.) is out of scope.
- Real-time scheduled collection is out of scope.
- User authentication is out of scope.
- Persistent database storage is out of scope.
