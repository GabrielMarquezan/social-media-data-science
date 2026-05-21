import argparse
import importlib
import json
import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd


EXPECTED_POST_COLUMNS = [
	"legenda_post",
	"coautores",
	"num_comentarios",
	"hashtags",
	"comentarios_habilitados",
	"num_likes",
	"mencoes",
	"nome_owner",
	"timestamp",
	"tipo",
	"url",
	"visualizacoes",
	"duracao_video",
	"localizacao",
]

EXPECTED_COMMENT_COLUMNS = [
	"texto_comentario",
	"owner_username",
	"timestamp",
	"replies",
	"likescount",
]

EXPECTED_OWNER_COLUMNS = [
	"owner_id",
	"owner_username",
	"is_verified",
	"profile_pic_url",
]

WEEKDAY_MAP_PT = {
	"Monday": "segunda",
	"Tuesday": "terca",
	"Wednesday": "quarta",
	"Thursday": "quinta",
	"Friday": "sexta",
	"Saturday": "sabado",
	"Sunday": "domingo",
}

WEEKDAY_ORDER = ["segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo"]

CTA_PATTERN = re.compile(
	r"\b(comente|comentem|salve|salvar|compartilhe|compartilhem|marque|marquem|"
	r"envie|enviem|curta|curtam|siga|sigam|inscreva|inscrevam|clique|acesse)\b",
	flags=re.IGNORECASE,
)

QUESTION_PATTERN = re.compile(
	r"\?|\b(quem|quando|onde|como|qual|quais|por\s+que|porque|sera|duvida)\b",
	flags=re.IGNORECASE,
)

EMOJI_PATTERN = re.compile(
	"["
	"\U0001F300-\U0001F5FF"
	"\U0001F600-\U0001F64F"
	"\U0001F680-\U0001F6FF"
	"\U0001F700-\U0001F77F"
	"\U0001F780-\U0001F7FF"
	"\U0001F900-\U0001F9FF"
	"\U0001FA00-\U0001FAFF"
	"\u2600-\u26FF"
	"\u2700-\u27BF"
	"]",
	flags=re.UNICODE,
)

PORTUGUESE_STOPWORDS = {
	"a",
	"ao",
	"aos",
	"aquela",
	"aquelas",
	"aquele",
	"aqueles",
	"aqui",
	"as",
	"ate",
	"com",
	"como",
	"da",
	"das",
	"de",
	"delas",
	"dele",
	"deles",
	"depois",
	"do",
	"dos",
	"e",
	"ela",
	"elas",
	"ele",
	"eles",
	"em",
	"entre",
	"era",
	"essa",
	"essas",
	"esse",
	"esses",
	"esta",
	"estas",
	"este",
	"estes",
	"eu",
	"foi",
	"ha",
	"isso",
	"isto",
	"ja",
	"la",
	"mais",
	"mas",
	"me",
	"mesmo",
	"meu",
	"minha",
	"na",
	"nas",
	"nao",
	"nem",
	"no",
	"nos",
	"nossa",
	"nosso",
	"o",
	"os",
	"ou",
	"para",
	"pela",
	"pelas",
	"pelo",
	"pelos",
	"por",
	"pra",
	"que",
	"quem",
	"se",
	"sem",
	"ser",
	"seu",
	"sua",
	"suas",
	"tambem",
	"te",
	"tem",
	"tendo",
	"tenho",
	"ter",
	"teu",
	"teve",
	"tu",
	"um",
	"uma",
	"voces",
	"voce",
}

POSITIVE_WORDS = {
	"adoro",
	"adorei",
	"amei",
	"bom",
	"boa",
	"excelente",
	"fantastico",
	"incrivel",
	"legal",
	"lindo",
	"maravilhoso",
	"otimo",
	"parabens",
	"perfeito",
	"show",
	"top",
}

NEGATIVE_WORDS = {
	"absurdo",
	"chato",
	"horrivel",
	"odio",
	"odiei",
	"pessimo",
	"problema",
	"ruim",
	"triste",
	"vergonha",
}

ANGER_WORDS = {
	"absurdo",
	"odio",
	"odiei",
	"ridiculo",
	"raiva",
	"irritado",
	"vergonha",
	"indignado",
}

ENTHUSIASM_WORDS = {
	"amei",
	"adorei",
	"incrivel",
	"parabens",
	"show",
	"top",
	"maravilhoso",
	"lindo",
	"demais",
	"sensacional",
}

DOUBT_WORDS = {
	"como",
	"quando",
	"onde",
	"por",
	"porque",
	"qual",
	"quais",
	"duvida",
	"alguem",
	"sabe",
}

CHART_THEME = {
	"figure_facecolor": "#ffffff",
	"axes_facecolor": "#f9fafb",
	"grid_color": "#d1d5db",
	"spine_color": "#9ca3af",
	"text_primary": "#111827",
	"text_secondary": "#4b5563",
	"text_muted": "#6b7280",
	"primary": "#1f77b4",
	"secondary": "#0ea5a4",
	"accent": "#2563eb",
	"good": "#16a34a",
	"warning": "#d97706",
	"danger": "#dc2626",
	"neutral": "#9ca3af",
}

RANK_COLORS = [
	"#0b6e4f",
	"#15803d",
	"#65a30d",
	"#ca8a04",
	"#ea580c",
	"#dc2626",
]

HOUR_PERIOD_COLORS = {
	"madrugada": "#94a3b8",
	"manha": "#60a5fa",
	"tarde": "#fb923c",
	"noite": "#818cf8",
	"desconhecido": "#9ca3af",
}


@dataclass
class AnalysisContext:
	data_dir: Path
	output_dir: Path
	tables_dir: Path
	charts_dir: Path
	qualified_word_threshold: int
	timezone: str
	top_n: int


def get_matplotlib_pyplot() -> Any:
	try:
		return importlib.import_module("matplotlib.pyplot")
	except Exception:
		return None


def ensure_output_dirs(output_dir: Path) -> Tuple[Path, Path]:
	tables_dir = output_dir / "tables"
	charts_dir = output_dir / "charts"
	output_dir.mkdir(parents=True, exist_ok=True)
	tables_dir.mkdir(parents=True, exist_ok=True)
	charts_dir.mkdir(parents=True, exist_ok=True)
	return tables_dir, charts_dir


def find_file_by_prefix(folder: Path, prefix: str) -> Optional[Path]:
	matches = sorted(folder.glob(f"{prefix}*.xlsx"))
	if matches:
		return matches[0]
	return None


def list_columns(file_path: Optional[Path]) -> List[str]:
	if file_path is None:
		return []
	try:
		return list(pd.read_excel(file_path, nrows=0).columns)
	except Exception:
		return []


def identify_dataset_structure(data_dir: Path) -> Tuple[pd.DataFrame, Dict[str, Any]]:
	rows: List[Dict[str, Any]] = []

	post_schema_variants: Counter = Counter()
	comments_schema_variants: Counter = Counter()
	owners_schema_variants: Counter = Counter()

	for folder in sorted(data_dir.iterdir()):
		if not folder.is_dir():
			continue

		shortcode = folder.name
		post_file = find_file_by_prefix(folder, "post_")
		comments_file = find_file_by_prefix(folder, "comments_")
		owners_file = find_file_by_prefix(folder, "commentOwner_")

		post_cols = list_columns(post_file)
		comments_cols = list_columns(comments_file)
		owners_cols = list_columns(owners_file)

		if post_cols:
			post_schema_variants[tuple(post_cols)] += 1
		if comments_cols:
			comments_schema_variants[tuple(comments_cols)] += 1
		if owners_cols:
			owners_schema_variants[tuple(owners_cols)] += 1

		rows.append(
			{
				"shortcode": shortcode,
				"has_post": post_file is not None,
				"has_comments": comments_file is not None,
				"has_owners": owners_file is not None,
				"post_file": str(post_file) if post_file else "",
				"comments_file": str(comments_file) if comments_file else "",
				"owners_file": str(owners_file) if owners_file else "",
				"post_columns": " | ".join(post_cols),
				"comments_columns": " | ".join(comments_cols),
				"owners_columns": " | ".join(owners_cols),
			}
		)

	structure_df = pd.DataFrame(rows)

	summary = {
		"total_shortcodes": int(len(structure_df)),
		"shortcodes_with_post": int(structure_df["has_post"].sum()) if not structure_df.empty else 0,
		"shortcodes_with_comments": int(structure_df["has_comments"].sum()) if not structure_df.empty else 0,
		"shortcodes_with_owners": int(structure_df["has_owners"].sum()) if not structure_df.empty else 0,
		"shortcodes_without_comments": int((~structure_df["has_comments"]).sum())
		if not structure_df.empty
		else 0,
		"post_schema_variants": [
			{"count": count, "columns": list(cols)}
			for cols, count in post_schema_variants.most_common()
		],
		"comments_schema_variants": [
			{"count": count, "columns": list(cols)}
			for cols, count in comments_schema_variants.most_common()
		],
		"owners_schema_variants": [
			{"count": count, "columns": list(cols)}
			for cols, count in owners_schema_variants.most_common()
		],
	}

	return structure_df, summary


def ensure_columns(df: pd.DataFrame, expected: Iterable[str]) -> pd.DataFrame:
	df = df.copy()
	for col in expected:
		if col not in df.columns:
			df[col] = np.nan
	return df


def safe_read_excel(file_path: Optional[Path]) -> pd.DataFrame:
	if file_path is None:
		return pd.DataFrame()
	return pd.read_excel(file_path)


def load_dataset(structure_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, List[str]]:
	posts_frames: List[pd.DataFrame] = []
	comments_frames: List[pd.DataFrame] = []
	owners_frames: List[pd.DataFrame] = []
	warnings: List[str] = []

	for row in structure_df.to_dict("records"):
		shortcode = row["shortcode"]

		if not row["has_post"]:
			warnings.append(f"Shortcode {shortcode}: sem arquivo post_*.xlsx")
			continue

		post_file = Path(row["post_file"]) if row["post_file"] else None
		comments_file = Path(row["comments_file"]) if row["comments_file"] else None
		owners_file = Path(row["owners_file"]) if row["owners_file"] else None

		try:
			post_df = safe_read_excel(post_file)
			post_df = ensure_columns(post_df, EXPECTED_POST_COLUMNS)
			post_df["shortcode"] = shortcode
			posts_frames.append(post_df)
		except Exception as exc:
			warnings.append(f"Shortcode {shortcode}: erro lendo post ({exc})")
			continue

		try:
			comments_df = safe_read_excel(comments_file)
			if comments_df.empty and comments_file is None:
				comments_df = pd.DataFrame(columns=EXPECTED_COMMENT_COLUMNS)
			comments_df = ensure_columns(comments_df, EXPECTED_COMMENT_COLUMNS)
			comments_df["shortcode"] = shortcode
			comments_frames.append(comments_df)
		except Exception as exc:
			warnings.append(f"Shortcode {shortcode}: erro lendo comments ({exc})")

		try:
			owners_df = safe_read_excel(owners_file)
			if owners_df.empty and owners_file is None:
				owners_df = pd.DataFrame(columns=EXPECTED_OWNER_COLUMNS)
			owners_df = ensure_columns(owners_df, EXPECTED_OWNER_COLUMNS)
			owners_df["shortcode"] = shortcode
			owners_frames.append(owners_df)
		except Exception as exc:
			warnings.append(f"Shortcode {shortcode}: erro lendo commentOwner ({exc})")

	posts = pd.concat(posts_frames, ignore_index=True) if posts_frames else pd.DataFrame(columns=EXPECTED_POST_COLUMNS + ["shortcode"])
	comments = pd.concat(comments_frames, ignore_index=True) if comments_frames else pd.DataFrame(columns=EXPECTED_COMMENT_COLUMNS + ["shortcode"])
	owners = pd.concat(owners_frames, ignore_index=True) if owners_frames else pd.DataFrame(columns=EXPECTED_OWNER_COLUMNS + ["shortcode"])

	return posts, comments, owners, warnings


def normalize_username(value: Any) -> str:
	if value is None or (isinstance(value, float) and math.isnan(value)):
		return ""
	return str(value).strip().lower()


def parse_serialized_list(value: Any) -> List[str]:
	if value is None or (isinstance(value, float) and math.isnan(value)):
		return []
	if isinstance(value, list):
		return [str(item).strip() for item in value if str(item).strip()]

	text = str(value).strip()
	if not text:
		return []

	if "|" in text:
		parts = [part.strip() for part in text.split("|")]
		return [part for part in parts if part]

	return [text]


def normalize_hashtag(tag: str) -> str:
	cleaned = tag.strip().lower()
	if not cleaned:
		return ""
	if not cleaned.startswith("#"):
		cleaned = f"#{cleaned}"
	return cleaned


def strip_accents(value: str) -> str:
	return "".join(c for c in unicodedata.normalize("NFKD", value) if not unicodedata.combining(c))


def tokenize_text(text: Any) -> List[str]:
	raw = "" if text is None else str(text)
	raw = strip_accents(raw.lower())
	tokens = re.findall(r"[a-z0-9_]+", raw)
	return [token for token in tokens if len(token) > 2 and token not in PORTUGUESE_STOPWORDS]


def count_words(text: Any) -> int:
	tokens = re.findall(r"\b\w+\b", "" if text is None else str(text), flags=re.UNICODE)
	return len(tokens)


def count_emojis(text: Any) -> int:
	raw = "" if text is None else str(text)
	return len(EMOJI_PATTERN.findall(raw))


def score_sentiment(text: Any) -> Tuple[str, int]:
	tokens = set(tokenize_text(text))
	positive_score = len(tokens & POSITIVE_WORDS)
	negative_score = len(tokens & NEGATIVE_WORDS)
	score = positive_score - negative_score
	if score > 0:
		return "positivo", score
	if score < 0:
		return "negativo", score
	return "neutro", score


def detect_emotion(text: Any) -> str:
	raw = strip_accents("" if text is None else str(text).lower())
	tokens = set(tokenize_text(raw))

	anger_score = len(tokens & ANGER_WORDS)
	enthusiasm_score = len(tokens & ENTHUSIASM_WORDS)
	doubt_score = len(tokens & DOUBT_WORDS)

	if "?" in raw:
		doubt_score += 1

	scores = {
		"raiva": anger_score,
		"entusiasmo": enthusiasm_score,
		"duvida": doubt_score,
	}
	best_label = max(scores, key=scores.get)
	if scores[best_label] == 0:
		return "neutra"
	return best_label


def parse_replies_cell(value: Any) -> List[Dict[str, Any]]:
	if value is None or (isinstance(value, float) and math.isnan(value)):
		return []

	if isinstance(value, list):
		return [item for item in value if isinstance(item, dict)]

	text = str(value).strip()
	if not text or text == "[]":
		return []

	try:
		parsed = json.loads(text)
	except json.JSONDecodeError:
		return []

	if isinstance(parsed, list):
		return [item for item in parsed if isinstance(item, dict)]
	if isinstance(parsed, dict):
		return [parsed]
	return []


def reply_tree_stats(replies: List[Dict[str, Any]], depth: int = 1) -> Tuple[int, int]:
	total = 0
	max_depth = 0

	for reply in replies:
		if not isinstance(reply, dict):
			continue
		total += 1
		max_depth = max(max_depth, depth)
		child_replies = reply.get("replies", [])
		if isinstance(child_replies, list) and child_replies:
			child_total, child_depth = reply_tree_stats(child_replies, depth + 1)
			total += child_total
			max_depth = max(max_depth, child_depth)

	return total, max_depth


def safe_percent_lift(with_feature: float, without_feature: float) -> float:
	if pd.isna(without_feature) or without_feature == 0:
		return np.nan
	return ((with_feature - without_feature) / abs(without_feature)) * 100


def build_post_features(posts: pd.DataFrame, timezone: str) -> pd.DataFrame:
	posts = posts.copy()

	numeric_cols = ["num_likes", "num_comentarios", "visualizacoes", "duracao_video"]
	for col in numeric_cols:
		posts[col] = pd.to_numeric(posts[col], errors="coerce")

	posts["timestamp"] = pd.to_datetime(posts["timestamp"], errors="coerce", utc=True)
	posts["post_timestamp"] = posts["timestamp"].dt.tz_convert(timezone)
	posts["post_hour"] = posts["post_timestamp"].dt.hour
	posts["post_weekday"] = posts["post_timestamp"].dt.day_name().map(WEEKDAY_MAP_PT)

	posts["post_period"] = posts["post_hour"].apply(hour_to_period)

	posts["hashtags_list"] = posts["hashtags"].apply(parse_serialized_list)
	posts["hashtags_list_norm"] = posts["hashtags_list"].apply(
		lambda values: [normalize_hashtag(v) for v in values if normalize_hashtag(v)]
	)
	posts["mentions_list"] = posts["mencoes"].apply(parse_serialized_list)
	posts["coauthors_list"] = posts["coautores"].apply(parse_serialized_list)

	posts["has_hashtags"] = posts["hashtags_list_norm"].apply(lambda values: len(values) > 0)
	posts["has_mentions"] = posts["mentions_list"].apply(lambda values: len(values) > 0)
	posts["has_coauthors"] = posts["coauthors_list"].apply(lambda values: len(values) > 0)
	posts["has_location"] = posts["localizacao"].fillna("").astype(str).str.strip().ne("")

	posts["hashtag_count"] = posts["hashtags_list_norm"].apply(len)
	posts["mention_count"] = posts["mentions_list"].apply(len)
	posts["coauthor_count"] = posts["coauthors_list"].apply(len)

	posts["legenda_post"] = posts["legenda_post"].fillna("").astype(str)
	posts["caption_word_count"] = posts["legenda_post"].apply(count_words)
	posts["caption_char_count"] = posts["legenda_post"].str.len()
	posts["caption_emoji_count"] = posts["legenda_post"].apply(count_emojis)
	posts["caption_cta_count"] = posts["legenda_post"].apply(lambda text: len(CTA_PATTERN.findall(text)))
	posts["has_cta"] = posts["caption_cta_count"] > 0

	total_interactions = posts["num_likes"].fillna(0) + posts["num_comentarios"].fillna(0)
	valid_views = posts["visualizacoes"].where(posts["visualizacoes"] > 0)

	posts["engagement_rate"] = total_interactions / valid_views
	posts["comments_per_view"] = posts["num_comentarios"] / valid_views
	posts["likes_per_view"] = posts["num_likes"] / valid_views
	posts["interactions_total"] = total_interactions
	posts["retention_proxy"] = posts["comments_per_view"]

	posts["tipo"] = posts["tipo"].fillna("desconhecido").astype(str)

	return posts


def hour_to_period(hour_value: Any) -> str:
	if pd.isna(hour_value):
		return "desconhecido"
	hour = int(hour_value)
	if 5 <= hour < 12:
		return "manha"
	if 12 <= hour < 18:
		return "tarde"
	if 18 <= hour < 23:
		return "noite"
	return "madrugada"


def build_comment_features(comments: pd.DataFrame, qualified_word_threshold: int, timezone: str) -> pd.DataFrame:
	comments = comments.copy()

	comments["texto_comentario"] = comments["texto_comentario"].fillna("").astype(str)
	comments["owner_username_norm"] = comments["owner_username"].apply(normalize_username)
	comments["timestamp"] = pd.to_datetime(comments["timestamp"], errors="coerce", utc=True)
	comments["comment_timestamp"] = comments["timestamp"].dt.tz_convert(timezone)

	comments["word_count"] = comments["texto_comentario"].apply(count_words)
	comments["is_qualified"] = comments["word_count"] > qualified_word_threshold
	comments["is_question"] = comments["texto_comentario"].apply(
		lambda text: bool(QUESTION_PATTERN.search(text))
	)

	sentiment_pairs = comments["texto_comentario"].apply(score_sentiment)
	comments["sentiment_label"] = sentiment_pairs.apply(lambda value: value[0])
	comments["sentiment_score"] = sentiment_pairs.apply(lambda value: value[1])

	comments["emotion_label"] = comments["texto_comentario"].apply(detect_emotion)

	comments["replies_list"] = comments["replies"].apply(parse_replies_cell)
	reply_stats = comments["replies_list"].apply(reply_tree_stats)
	comments["replies_total"] = reply_stats.apply(lambda value: value[0])
	comments["reply_depth_max"] = reply_stats.apply(lambda value: value[1])

	comments["likescount"] = pd.to_numeric(comments["likescount"], errors="coerce")

	return comments


def add_comment_delay_features(comments: pd.DataFrame, posts: pd.DataFrame) -> pd.DataFrame:
	comments = comments.copy()
	post_timestamps = posts[["shortcode", "post_timestamp"]].drop_duplicates("shortcode")
	comments = comments.merge(post_timestamps, on="shortcode", how="left")

	comments["delay_hours"] = (
		comments["comment_timestamp"] - comments["post_timestamp"]
	).dt.total_seconds() / 3600
	comments.loc[comments["delay_hours"] < 0, "delay_hours"] = np.nan
	comments["delay_hour_bucket"] = comments["delay_hours"].apply(
		lambda value: np.nan if pd.isna(value) else int(value)
	)
	return comments


def add_verified_commenter_flags(comments: pd.DataFrame, owners: pd.DataFrame) -> pd.DataFrame:
	comments = comments.copy()
	owners = owners.copy()

	owners["owner_username_norm"] = owners["owner_username"].apply(normalize_username)
	owner_lookup = (
		owners[["shortcode", "owner_username_norm", "is_verified"]]
		.dropna(subset=["owner_username_norm"])  # ignore rows without username
		.drop_duplicates(["shortcode", "owner_username_norm"])
	)

	comments = comments.merge(
		owner_lookup,
		on=["shortcode", "owner_username_norm"],
		how="left",
	)
	comments["is_verified"] = comments["is_verified"].fillna(False).astype(bool)
	return comments


def compute_mode_int(series: pd.Series) -> float:
	valid = series.dropna()
	if valid.empty:
		return np.nan
	return float(valid.value_counts().idxmax())


def build_conversation_metrics(posts: pd.DataFrame, comments: pd.DataFrame) -> pd.DataFrame:
	if comments.empty:
		empty = posts[["shortcode"]].copy()
		empty["observed_comments"] = 0
		empty["observed_replies"] = 0
		empty["discussion_index"] = 0.0
		empty["avg_reply_depth"] = 0.0
		empty["max_reply_depth"] = 0.0
		empty["isolated_comment_rate"] = np.nan
		empty["qualified_comment_rate"] = np.nan
		empty["question_comment_rate"] = np.nan
		empty["avg_comment_delay_h"] = np.nan
		empty["median_comment_delay_h"] = np.nan
		empty["first_comment_delay_h"] = np.nan
		empty["peak_comment_delay_h"] = np.nan
		empty["sent_positivo_share"] = np.nan
		empty["sent_neutro_share"] = np.nan
		empty["sent_negativo_share"] = np.nan
		empty["emotion_raiva_share"] = np.nan
		empty["emotion_entusiasmo_share"] = np.nan
		empty["emotion_duvida_share"] = np.nan
		empty["emotion_neutra_share"] = np.nan
		return empty

	base = comments.groupby("shortcode").agg(
		observed_comments=("texto_comentario", "size"),
		observed_replies=("replies_total", "sum"),
		avg_reply_depth=("reply_depth_max", "mean"),
		max_reply_depth=("reply_depth_max", "max"),
		isolated_comment_rate=("replies_total", lambda value: float((value == 0).mean())),
		qualified_comment_rate=("is_qualified", "mean"),
		question_comment_rate=("is_question", "mean"),
		avg_comment_delay_h=("delay_hours", "mean"),
		median_comment_delay_h=("delay_hours", "median"),
		first_comment_delay_h=("delay_hours", "min"),
	)

	base["discussion_index"] = base["observed_replies"] / base["observed_comments"].replace(0, np.nan)

	peak_delay = comments.groupby("shortcode")["delay_hour_bucket"].apply(compute_mode_int)
	base["peak_comment_delay_h"] = peak_delay

	sentiment_counts = (
		comments.pivot_table(
			index="shortcode",
			columns="sentiment_label",
			values="texto_comentario",
			aggfunc="count",
			fill_value=0,
		)
		.rename(columns={"positivo": "sent_positivo", "neutro": "sent_neutro", "negativo": "sent_negativo"})
	)
	sentiment_total = sentiment_counts.sum(axis=1).replace(0, np.nan)
	for col, final_name in [
		("sent_positivo", "sent_positivo_share"),
		("sent_neutro", "sent_neutro_share"),
		("sent_negativo", "sent_negativo_share"),
	]:
		base[final_name] = sentiment_counts.get(col, 0) / sentiment_total

	emotion_counts = comments.pivot_table(
		index="shortcode",
		columns="emotion_label",
		values="texto_comentario",
		aggfunc="count",
		fill_value=0,
	)
	emotion_total = emotion_counts.sum(axis=1).replace(0, np.nan)
	for emotion in ["raiva", "entusiasmo", "duvida", "neutra"]:
		base[f"emotion_{emotion}_share"] = emotion_counts.get(emotion, 0) / emotion_total

	base = base.reset_index()
	return base


def build_community_metrics(comments: pd.DataFrame) -> pd.DataFrame:
	if comments.empty:
		return pd.DataFrame(
			columns=[
				"shortcode",
				"unique_commenters",
				"recurring_unique_commenters",
				"community_index",
				"recurring_comment_share",
				"new_commenter_share",
			]
		)

	comments = comments.copy()
	comments_non_empty = comments[comments["owner_username_norm"].ne("")].copy()

	if comments_non_empty.empty:
		result = comments[["shortcode"]].drop_duplicates()
		result["unique_commenters"] = 0
		result["recurring_unique_commenters"] = 0
		result["community_index"] = np.nan
		result["recurring_comment_share"] = np.nan
		result["new_commenter_share"] = np.nan
		return result

	commenter_post_counts = comments_non_empty.groupby("owner_username_norm")["shortcode"].nunique()
	recurring_users = set(commenter_post_counts[commenter_post_counts > 1].index)

	comments_non_empty["is_recurring_user"] = comments_non_empty["owner_username_norm"].isin(recurring_users)

	comments_with_time = comments_non_empty.sort_values("post_timestamp")
	first_shortcode_by_user = comments_with_time.drop_duplicates("owner_username_norm").set_index(
		"owner_username_norm"
	)["shortcode"]

	comments_non_empty["first_shortcode"] = comments_non_empty["owner_username_norm"].map(first_shortcode_by_user)
	comments_non_empty["is_new_commenter"] = comments_non_empty["first_shortcode"] == comments_non_empty["shortcode"]

	community_rows: List[Dict[str, Any]] = []
	for shortcode, group in comments_non_empty.groupby("shortcode"):
		unique_commenters = set(group["owner_username_norm"])
		recurring_unique = {user for user in unique_commenters if user in recurring_users}

		unique_count = len(unique_commenters)
		recurring_unique_count = len(recurring_unique)

		community_rows.append(
			{
				"shortcode": shortcode,
				"unique_commenters": unique_count,
				"recurring_unique_commenters": recurring_unique_count,
				"community_index": (
					recurring_unique_count / unique_count if unique_count > 0 else np.nan
				),
				"recurring_comment_share": float(group["is_recurring_user"].mean()),
				"new_commenter_share": float(group["is_new_commenter"].mean()),
			}
		)

	return pd.DataFrame(community_rows)


def build_audience_metrics(owners: pd.DataFrame, comments: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
	owners = owners.copy()
	owners["owner_username_norm"] = owners["owner_username"].apply(normalize_username)
	owners["is_verified"] = owners["is_verified"].fillna(False).astype(bool)

	owner_summary = pd.DataFrame(
		[
			{
				"total_owner_rows": int(len(owners)),
				"owners_unicos": int(owners["owner_username_norm"].replace("", np.nan).dropna().nunique()),
				"percent_verified": float(owners["is_verified"].mean()) if not owners.empty else np.nan,
				"dados_followers_disponiveis": False,
				"dados_privacidade_disponiveis": False,
			}
		]
	)

	comments_non_empty = comments[comments["owner_username_norm"].ne("")].copy()
	top_commenters = (
		comments_non_empty.groupby("owner_username_norm")
		.agg(
			comentarios=("texto_comentario", "size"),
			posts_distintos=("shortcode", "nunique"),
			comentarios_qualificados=("is_qualified", "sum"),
			taxa_perguntas=("is_question", "mean"),
		)
		.reset_index()
		.sort_values(["comentarios", "posts_distintos"], ascending=False)
	)

	return owner_summary, top_commenters


def aggregate_by_type(posts: pd.DataFrame) -> pd.DataFrame:
	metrics = [
		"num_likes",
		"num_comentarios",
		"visualizacoes",
		"engagement_rate",
		"comments_per_view",
		"qualified_comment_rate",
		"discussion_index",
		"community_index",
		"new_commenter_share",
	]

	metrics_available = [metric for metric in metrics if metric in posts.columns]

	counts = posts.groupby("tipo")["shortcode"].count().rename("posts").reset_index()
	means = posts.groupby("tipo")[metrics_available].mean().reset_index()
	by_type = counts.merge(means, on="tipo", how="left")
	by_type = by_type.sort_values("posts", ascending=False)
	return by_type


def build_video_duration_table(posts: pd.DataFrame) -> pd.DataFrame:
	videos = posts[(posts["duracao_video"].notna()) & (posts["visualizacoes"].notna())].copy()
	if videos.empty:
		return pd.DataFrame(
			[
				{
					"video_posts": 0,
					"corr_duracao_visualizacoes": np.nan,
					"corr_duracao_comments_per_view": np.nan,
					"media_duracao": np.nan,
					"mediana_duracao": np.nan,
				}
			]
		)

	return pd.DataFrame(
		[
			{
				"video_posts": int(len(videos)),
				"corr_duracao_visualizacoes": videos["duracao_video"].corr(videos["visualizacoes"]),
				"corr_duracao_comments_per_view": videos["duracao_video"].corr(
					videos["comments_per_view"]
				),
				"media_duracao": float(videos["duracao_video"].mean()),
				"mediana_duracao": float(videos["duracao_video"].median()),
			}
		]
	)


def build_binary_feature_impact(posts: pd.DataFrame) -> pd.DataFrame:
	feature_cols = ["has_hashtags", "has_mentions", "has_coauthors", "has_location", "has_cta"]
	metric_cols = [
		"num_likes",
		"num_comentarios",
		"visualizacoes",
		"engagement_rate",
		"discussion_index",
		"qualified_comment_rate",
		"community_index",
		"new_commenter_share",
	]

	rows: List[Dict[str, Any]] = []
	for feature in feature_cols:
		if feature not in posts.columns:
			continue

		with_feature = posts[posts[feature] == True]
		without_feature = posts[posts[feature] == False]

		for metric in metric_cols:
			if metric not in posts.columns:
				continue

			with_value = with_feature[metric].mean() if not with_feature.empty else np.nan
			without_value = without_feature[metric].mean() if not without_feature.empty else np.nan

			rows.append(
				{
					"feature": feature,
					"metric": metric,
					"n_with": int(len(with_feature)),
					"n_without": int(len(without_feature)),
					"with_feature": with_value,
					"without_feature": without_value,
					"lift_pct": safe_percent_lift(with_value, without_value),
				}
			)

	return pd.DataFrame(rows)


def build_timing_tables(posts: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
	hour_table = posts.groupby("post_hour").agg(
		posts=("shortcode", "count"),
		avg_likes=("num_likes", "mean"),
		avg_comments=("num_comentarios", "mean"),
		avg_views=("visualizacoes", "mean"),
		avg_engagement_rate=("engagement_rate", "mean"),
		avg_qualified_comment_rate=("qualified_comment_rate", "mean"),
	)
	hour_table = hour_table.reset_index().sort_values("post_hour")

	weekday_table = posts.groupby("post_weekday").agg(
		posts=("shortcode", "count"),
		avg_likes=("num_likes", "mean"),
		avg_comments=("num_comentarios", "mean"),
		avg_views=("visualizacoes", "mean"),
		avg_engagement_rate=("engagement_rate", "mean"),
		avg_discussion_index=("discussion_index", "mean"),
	)
	weekday_table = weekday_table.reset_index()
	weekday_order_map = {day: idx for idx, day in enumerate(WEEKDAY_ORDER)}
	weekday_table["weekday_order"] = weekday_table["post_weekday"].map(weekday_order_map)
	weekday_table = weekday_table.sort_values("weekday_order").drop(columns=["weekday_order"])

	return hour_table, weekday_table


def build_hashtag_tables(posts: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
	hashtag_rows: List[Dict[str, Any]] = []
	post_hashtags: Dict[str, List[str]] = {}

	for row in posts.itertuples(index=False):
		tags = sorted(set(getattr(row, "hashtags_list_norm", [])))
		post_hashtags[row.shortcode] = tags
		for tag in tags:
			hashtag_rows.append(
				{
					"shortcode": row.shortcode,
					"hashtag": tag,
					"num_likes": getattr(row, "num_likes", np.nan),
					"num_comentarios": getattr(row, "num_comentarios", np.nan),
					"visualizacoes": getattr(row, "visualizacoes", np.nan),
					"engagement_rate": getattr(row, "engagement_rate", np.nan),
					"comments_per_view": getattr(row, "comments_per_view", np.nan),
					"qualified_comment_rate": getattr(row, "qualified_comment_rate", np.nan),
				}
			)

	if not hashtag_rows:
		return pd.DataFrame(), pd.DataFrame()

	hashtag_df = pd.DataFrame(hashtag_rows)
	hashtag_perf = hashtag_df.groupby("hashtag").agg(
		posts=("shortcode", "nunique"),
		avg_likes=("num_likes", "mean"),
		avg_comments=("num_comentarios", "mean"),
		avg_views=("visualizacoes", "mean"),
		avg_engagement_rate=("engagement_rate", "mean"),
		avg_comments_per_view=("comments_per_view", "mean"),
		avg_qualified_comment_rate=("qualified_comment_rate", "mean"),
	)
	hashtag_perf = hashtag_perf.reset_index().sort_values("posts", ascending=False)

	hashtag_perf["saturacao_interna"] = hashtag_perf["posts"].apply(classify_hashtag_saturation)

	pair_counter: Counter = Counter()
	for tags in post_hashtags.values():
		if len(tags) < 2:
			continue
		for pair in combinations(tags, 2):
			pair_counter[tuple(sorted(pair))] += 1

	pair_rows: List[Dict[str, Any]] = []
	for (tag_a, tag_b), count in pair_counter.items():
		mask = posts["hashtags_list_norm"].apply(
			lambda tags: tag_a in tags and tag_b in tags
		)
		subset = posts[mask]
		pair_rows.append(
			{
				"hashtag_a": tag_a,
				"hashtag_b": tag_b,
				"coocorrencias": int(count),
				"posts": int(subset["shortcode"].nunique()),
				"avg_comments": subset["num_comentarios"].mean(),
				"avg_engagement_rate": subset["engagement_rate"].mean(),
			}
		)

	cooccurrence_df = pd.DataFrame(pair_rows).sort_values("coocorrencias", ascending=False)
	return hashtag_perf, cooccurrence_df


def classify_hashtag_saturation(posts_count: int) -> str:
	if posts_count <= 1:
		return "nicho"
	if posts_count <= 3:
		return "media"
	return "alta"


def build_coauthor_table(posts: pd.DataFrame) -> pd.DataFrame:
	rows: List[Dict[str, Any]] = []
	for row in posts.itertuples(index=False):
		coauthors = getattr(row, "coauthors_list", [])
		for coauthor in coauthors:
			rows.append(
				{
					"shortcode": row.shortcode,
					"coautor": str(coauthor).strip().lower(),
					"num_comentarios": getattr(row, "num_comentarios", np.nan),
					"visualizacoes": getattr(row, "visualizacoes", np.nan),
					"engagement_rate": getattr(row, "engagement_rate", np.nan),
					"discussion_index": getattr(row, "discussion_index", np.nan),
					"qualified_comment_rate": getattr(row, "qualified_comment_rate", np.nan),
				}
			)

	if not rows:
		return pd.DataFrame()

	return (
		pd.DataFrame(rows)
		.groupby("coautor")
		.agg(
			posts=("shortcode", "nunique"),
			avg_comments=("num_comentarios", "mean"),
			avg_views=("visualizacoes", "mean"),
			avg_engagement_rate=("engagement_rate", "mean"),
			avg_discussion_index=("discussion_index", "mean"),
			avg_qualified_comment_rate=("qualified_comment_rate", "mean"),
		)
		.reset_index()
		.sort_values("posts", ascending=False)
	)


def top_terms_table(texts: Iterable[str], top_n: int, column_name: str = "termo") -> pd.DataFrame:
	counter: Counter = Counter()
	for text in texts:
		counter.update(tokenize_text(text))

	rows = [{column_name: term, "frequencia": count} for term, count in counter.most_common(top_n)]
	return pd.DataFrame(rows)


def topic_modeling_light(texts: Iterable[str], source: str, n_topics: int = 4, n_terms: int = 6) -> pd.DataFrame:
	cleaned_texts = [" ".join(tokenize_text(text)) for text in texts if count_words(text) >= 3]
	cleaned_texts = [text for text in cleaned_texts if text.strip()]

	if len(cleaned_texts) < 3:
		return pd.DataFrame(
			[
				{
					"source": source,
					"topic_id": "topico_1",
					"terms": "dados insuficientes",
					"metodo": "fallback",
				}
			]
		)

	try:
		sklearn_decomposition = importlib.import_module("sklearn.decomposition")
		sklearn_feature_extraction = importlib.import_module("sklearn.feature_extraction.text")

		LatentDirichletAllocation = getattr(
			sklearn_decomposition,
			"LatentDirichletAllocation",
		)
		CountVectorizer = getattr(sklearn_feature_extraction, "CountVectorizer")

		vectorizer = CountVectorizer(
			min_df=2,
			max_df=0.95,
			stop_words=list(PORTUGUESE_STOPWORDS),
		)
		matrix = vectorizer.fit_transform(cleaned_texts)

		if matrix.shape[1] == 0:
			raise ValueError("Sem termos apos vetorizar")

		components = max(1, min(n_topics, matrix.shape[0], matrix.shape[1]))
		model = LatentDirichletAllocation(
			n_components=components,
			random_state=42,
			learning_method="batch",
		)
		model.fit(matrix)

		feature_names = vectorizer.get_feature_names_out()
		rows: List[Dict[str, Any]] = []
		for idx, topic_weights in enumerate(model.components_):
			top_indexes = topic_weights.argsort()[::-1][:n_terms]
			top_terms = [feature_names[index] for index in top_indexes]
			rows.append(
				{
					"source": source,
					"topic_id": f"topico_{idx + 1}",
					"terms": ", ".join(top_terms),
					"metodo": "lda_sklearn",
				}
			)
		return pd.DataFrame(rows)

	except Exception:
		fallback_terms = top_terms_table(cleaned_texts, top_n=n_topics * n_terms, column_name="termo")
		rows = []
		terms = fallback_terms["termo"].tolist()
		for idx in range(n_topics):
			start = idx * n_terms
			end = start + n_terms
			chunk = terms[start:end]
			if not chunk:
				continue
			rows.append(
				{
					"source": source,
					"topic_id": f"topico_{idx + 1}",
					"terms": ", ".join(chunk),
					"metodo": "fallback_frequencia",
				}
			)
		if not rows:
			rows.append(
				{
					"source": source,
					"topic_id": "topico_1",
					"terms": "dados insuficientes",
					"metodo": "fallback_frequencia",
				}
			)
		return pd.DataFrame(rows)


def save_table(df: pd.DataFrame, path: Path) -> None:
	df.to_csv(path, index=False, encoding="utf-8", sep=";")


def build_chart_context(posts: pd.DataFrame, timezone: str) -> Dict[str, Any]:
	timestamps = pd.to_datetime(posts.get("post_timestamp"), errors="coerce")
	valid_ts = timestamps.dropna()

	if valid_ts.empty:
		period_label = "periodo indisponivel"
	else:
		period_label = f"{valid_ts.min().strftime('%d/%m/%Y')} a {valid_ts.max().strftime('%d/%m/%Y')}"

	return {
		"timezone": timezone,
		"period": period_label,
		"n_posts": int(posts["shortcode"].nunique()) if "shortcode" in posts.columns else int(len(posts)),
		"generated_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
	}


def chart_footer(chart_context: Dict[str, Any]) -> str:
	return (
		f"Timezone: {chart_context['timezone']} | "
		f"Periodo: {chart_context['period']} | "
		f"n posts: {chart_context['n_posts']} | "
		f"Gerado em: {chart_context['generated_at']}"
	)


def validate_chart_data(
	chart_name: str,
	df: pd.DataFrame,
	required_cols: List[str],
	min_rows: int = 1,
	dropna_cols: Optional[List[str]] = None,
) -> Tuple[bool, pd.DataFrame, str]:
	if df is None or df.empty:
		return False, pd.DataFrame(), f"{chart_name}: dataframe vazio"

	missing_cols = [col for col in required_cols if col not in df.columns]
	if missing_cols:
		return False, pd.DataFrame(), f"{chart_name}: colunas ausentes {missing_cols}"

	clean_df = df.copy()
	cols_to_drop = dropna_cols or required_cols
	before_rows = len(clean_df)
	clean_df = clean_df.dropna(subset=cols_to_drop)
	after_rows = len(clean_df)

	if after_rows < min_rows:
		return (
			False,
			pd.DataFrame(),
			f"{chart_name}: dados validos insuficientes ({after_rows}/{before_rows})",
		)

	removed_ratio = (before_rows - after_rows) / before_rows if before_rows > 0 else 0
	message = "ok"
	if removed_ratio > 0.2:
		message = f"{chart_name}: removidos {removed_ratio:.0%} de registros com NaN"

	return True, clean_df, message


def configure_matplotlib_style(plt: Any) -> None:
	plt.rcParams.update(
		{
			"axes.titlesize": 12,
			"axes.titleweight": "bold",
			"axes.labelsize": 10,
			"xtick.labelsize": 9,
			"ytick.labelsize": 9,
			"font.family": "DejaVu Sans",
			"figure.facecolor": CHART_THEME["figure_facecolor"],
			"axes.facecolor": CHART_THEME["axes_facecolor"],
		}
	)


def style_axis(ax: Any, grid_axis: str = "y") -> None:
	ax.grid(
		axis=grid_axis,
		linestyle="--",
		linewidth=0.7,
		color=CHART_THEME["grid_color"],
		alpha=0.8,
	)
	ax.set_axisbelow(True)

	for side in ["top", "right"]:
		ax.spines[side].set_visible(False)
	for side in ["left", "bottom"]:
		ax.spines[side].set_color(CHART_THEME["spine_color"])

	ax.tick_params(colors=CHART_THEME["text_secondary"])
	ax.xaxis.label.set_color(CHART_THEME["text_primary"])
	ax.yaxis.label.set_color(CHART_THEME["text_primary"])


def add_figure_decoration(fig: Any, title: str, subtitle: str, footer: str) -> None:
	fig.patch.set_facecolor(CHART_THEME["figure_facecolor"])
	fig.suptitle(
		title,
		x=0.01,
		y=0.985,
		ha="left",
		fontsize=14,
		fontweight="bold",
		color=CHART_THEME["text_primary"],
	)
	fig.text(
		0.01,
		0.94,
		subtitle,
		ha="left",
		fontsize=10,
		color=CHART_THEME["text_secondary"],
	)
	fig.text(
		0.01,
		0.015,
		footer,
		ha="left",
		fontsize=8,
		color=CHART_THEME["text_muted"],
	)


def add_bar_value_labels(ax: Any, bars: Any, fmt: str = "{:.1f}", horizontal: bool = False) -> None:
	if horizontal:
		x_min, x_max = ax.get_xlim()
		offset = (x_max - x_min) * 0.01
		for bar in bars:
			value = bar.get_width()
			if pd.isna(value):
				continue
			y = bar.get_y() + bar.get_height() / 2
			ax.text(
				value + offset,
				y,
				fmt.format(value),
				va="center",
				ha="left",
				fontsize=8,
				color=CHART_THEME["text_primary"],
			)
		return

	y_min, y_max = ax.get_ylim()
	offset = (y_max - y_min) * 0.015
	for bar in bars:
		value = bar.get_height()
		if pd.isna(value):
			continue
		x = bar.get_x() + bar.get_width() / 2
		ax.text(
			x,
			value + offset,
			fmt.format(value),
			ha="center",
			va="bottom",
			fontsize=8,
			color=CHART_THEME["text_primary"],
		)


def get_rank_colors(size: int) -> List[str]:
	if size <= 0:
		return []

	if size == 1:
		return [RANK_COLORS[0]]

	colors: List[str] = []
	max_index = len(RANK_COLORS) - 1
	for idx in range(size):
		scaled = int(round((idx / (size - 1)) * max_index))
		colors.append(RANK_COLORS[scaled])
	return colors


def truncate_label(text: Any, max_len: int = 34) -> str:
	label = str(text)
	if len(label) <= max_len:
		return label
	return f"{label[: max_len - 3]}..."


def build_chart_result(chart_id: str, file_path: Path, success: bool, message: str) -> Dict[str, Any]:
	return {
		"chart_id": chart_id,
		"file_name": file_path.name,
		"status": "success" if success else "failed",
		"message": message,
	}


def plot_post_type_avg_comments(
	by_type: pd.DataFrame,
	output_path: Path,
	chart_context: Dict[str, Any],
) -> Tuple[bool, str]:
	plt = get_matplotlib_pyplot()
	if plt is None:
		return False, "matplotlib indisponivel"

	valid, chart_df, message = validate_chart_data(
		"post_type_avg_comments",
		by_type,
		required_cols=["tipo", "num_comentarios", "posts"],
		min_rows=1,
	)
	if not valid:
		return False, message

	configure_matplotlib_style(plt)
	chart_df = chart_df.sort_values("num_comentarios", ascending=False).reset_index(drop=True)
	colors = get_rank_colors(len(chart_df))

	fig, ax = plt.subplots(figsize=(11.5, 6.2))
	bars = ax.bar(
		chart_df["tipo"].astype(str),
		chart_df["num_comentarios"],
		color=colors,
		edgecolor="#1f2937",
		linewidth=0.5,
	)

	style_axis(ax, grid_axis="y")
	ax.set_ylabel("Media de comentarios")
	ax.set_xlabel("Tipo de post")
	if chart_df["num_comentarios"].max() > 0:
		ax.set_ylim(0, chart_df["num_comentarios"].max() * 1.20)

	add_bar_value_labels(ax, bars, fmt="{:.1f}")

	for idx, row in chart_df.iterrows():
		ax.text(
			idx,
			-0.12,
			f"n={int(row['posts'])}",
			transform=ax.get_xaxis_transform(),
			ha="center",
			va="top",
			fontsize=8,
			color=CHART_THEME["text_muted"],
			clip_on=False,
		)

	add_figure_decoration(
		fig,
		title="Media de comentarios por tipo de post",
		subtitle="Ranking de formatos com anotacao de volume amostral por tipo",
		footer=chart_footer(chart_context),
	)

	fig.tight_layout(rect=(0, 0.07, 1, 0.90))
	fig.savefig(output_path, dpi=180)
	plt.close(fig)

	return True, message


def plot_timing_hour_avg_comments(
	hour_table: pd.DataFrame,
	output_path: Path,
	chart_context: Dict[str, Any],
) -> Tuple[bool, str]:
	plt = get_matplotlib_pyplot()
	if plt is None:
		return False, "matplotlib indisponivel"

	valid, chart_df, message = validate_chart_data(
		"timing_hour_avg_comments",
		hour_table,
		required_cols=["post_hour", "avg_comments", "posts"],
		min_rows=1,
	)
	if not valid:
		return False, message

	configure_matplotlib_style(plt)
	base_hours = pd.DataFrame({"post_hour": list(range(24))})
	merged = base_hours.merge(
		chart_df[["post_hour", "avg_comments", "posts"]],
		on="post_hour",
		how="left",
	)
	merged["avg_comments"] = merged["avg_comments"].fillna(0)
	merged["posts"] = merged["posts"].fillna(0).astype(int)
	merged["period"] = merged["post_hour"].apply(hour_to_period)

	fig, ax = plt.subplots(figsize=(14, 6.2))
	colors = [HOUR_PERIOD_COLORS.get(period, CHART_THEME["neutral"]) for period in merged["period"]]
	bars = ax.bar(
		merged["post_hour"],
		merged["avg_comments"],
		color=colors,
		edgecolor="#334155",
		linewidth=0.4,
	)

	style_axis(ax, grid_axis="y")
	ax.set_ylabel("Media de comentarios")
	ax.set_xlabel("Hora da publicacao")
	ax.set_xticks(list(range(24)))
	ax.set_xticklabels([f"{hour:02d}h" for hour in range(24)], rotation=0)

	valid_hours = merged[merged["posts"] > 0]
	if not valid_hours.empty:
		mean_comments = valid_hours["avg_comments"].mean()
		ax.axhline(
			mean_comments,
			color=CHART_THEME["danger"],
			linestyle="--",
			linewidth=1.2,
			label=f"Media geral ({mean_comments:.1f})",
		)

		peak = valid_hours.sort_values("avg_comments", ascending=False).iloc[0]
		peak_hour = int(peak["post_hour"])
		peak_value = float(peak["avg_comments"])
		peak_offset = max(peak_value * 0.08, 4)
		ax.annotate(
			f"Pico: {peak_hour:02d}h ({peak_value:.1f})",
			xy=(peak_hour, peak_value),
			xytext=(peak_hour + 0.5, peak_value + peak_offset),
			textcoords="data",
			fontsize=9,
			color=CHART_THEME["text_primary"],
			arrowprops={"arrowstyle": "->", "color": CHART_THEME["text_secondary"], "lw": 1},
		)
		ax.legend(loc="upper right", frameon=False, fontsize=8)

	for idx in valid_hours.sort_values("avg_comments", ascending=False).head(3).index:
		bar = bars[idx]
		ax.text(
			bar.get_x() + bar.get_width() / 2,
			bar.get_height() + max(valid_hours["avg_comments"].max() * 0.01, 1),
			f"{bar.get_height():.1f}",
			ha="center",
			va="bottom",
			fontsize=8,
			color=CHART_THEME["text_primary"],
		)

	add_figure_decoration(
		fig,
		title="Comentarios medios por hora de publicacao",
		subtitle="Escala 0-23h com destaque para o pico e linha de media global",
		footer=chart_footer(chart_context),
	)

	fig.tight_layout(rect=(0, 0.07, 1, 0.90))
	fig.savefig(output_path, dpi=180)
	plt.close(fig)

	return True, message


def plot_timing_weekday_avg_comments(
	weekday_table: pd.DataFrame,
	output_path: Path,
	chart_context: Dict[str, Any],
) -> Tuple[bool, str]:
	plt = get_matplotlib_pyplot()
	if plt is None:
		return False, "matplotlib indisponivel"

	valid, chart_df, message = validate_chart_data(
		"timing_weekday_avg_comments",
		weekday_table,
		required_cols=["post_weekday", "avg_comments", "posts"],
		min_rows=1,
	)
	if not valid:
		return False, message

	configure_matplotlib_style(plt)
	base = pd.DataFrame({"post_weekday": WEEKDAY_ORDER})
	merged = base.merge(
		chart_df[["post_weekday", "avg_comments", "posts"]],
		on="post_weekday",
		how="left",
	)
	merged["avg_comments"] = merged["avg_comments"].fillna(0)
	merged["posts"] = merged["posts"].fillna(0).astype(int)
	labels = merged["post_weekday"].str.capitalize()
	colors = [
		CHART_THEME["good"] if day in ["sabado", "domingo"] else CHART_THEME["primary"]
		for day in merged["post_weekday"]
	]

	fig, ax = plt.subplots(figsize=(12.5, 6.2))
	bars = ax.bar(labels, merged["avg_comments"], color=colors, edgecolor="#334155", linewidth=0.4)

	style_axis(ax, grid_axis="y")
	ax.set_ylabel("Media de comentarios")
	ax.set_xlabel("Dia da semana")

	valid_days = merged[merged["posts"] > 0]
	if not valid_days.empty:
		mean_comments = valid_days["avg_comments"].mean()
		ax.axhline(
			mean_comments,
			color=CHART_THEME["warning"],
			linestyle="--",
			linewidth=1.2,
			label=f"Media geral ({mean_comments:.1f})",
		)
		ax.legend(loc="upper right", frameon=False, fontsize=8)

	add_bar_value_labels(ax, bars, fmt="{:.1f}")

	for idx, row in merged.iterrows():
		ax.text(
			idx,
			-0.12,
			f"n={int(row['posts'])}",
			transform=ax.get_xaxis_transform(),
			ha="center",
			va="top",
			fontsize=8,
			color=CHART_THEME["text_muted"],
			clip_on=False,
		)

	add_figure_decoration(
		fig,
		title="Comentarios medios por dia da semana",
		subtitle="Sequencia completa de segunda a domingo com destaque para fim de semana",
		footer=chart_footer(chart_context),
	)

	fig.tight_layout(rect=(0, 0.07, 1, 0.90))
	fig.savefig(output_path, dpi=180)
	plt.close(fig)

	return True, message


def plot_top_hashtags_engagement(
	hashtag_perf: pd.DataFrame,
	output_path: Path,
	chart_context: Dict[str, Any],
	top_n: int = 8,
) -> Tuple[bool, str]:
	plt = get_matplotlib_pyplot()
	if plt is None:
		return False, "matplotlib indisponivel"

	valid, chart_df, message = validate_chart_data(
		"top_hashtags_engagement",
		hashtag_perf,
		required_cols=["hashtag", "avg_engagement_rate", "posts"],
		min_rows=1,
	)
	if not valid:
		return False, message

	configure_matplotlib_style(plt)
	chart_df = chart_df.sort_values("avg_engagement_rate", ascending=False).head(max(1, top_n))
	if chart_df.empty:
		return False, "top_hashtags_engagement: sem linhas apos filtro"

	chart_df = chart_df.sort_values("avg_engagement_rate", ascending=True).reset_index(drop=True)
	chart_df["label"] = chart_df["hashtag"].apply(truncate_label)
	colors = get_rank_colors(len(chart_df))

	fig, ax = plt.subplots(figsize=(12.5, 7.5))
	bars = ax.barh(
		chart_df["label"],
		chart_df["avg_engagement_rate"],
		color=colors,
		edgecolor="#334155",
		linewidth=0.4,
	)

	style_axis(ax, grid_axis="x")
	ax.set_xlabel("Engagement medio")
	ax.set_ylabel("Hashtag")

	x_max = float(chart_df["avg_engagement_rate"].max()) if not chart_df.empty else 0.0
	ax.set_xlim(0, x_max * 1.35 if x_max > 0 else 1)

	add_bar_value_labels(ax, bars, fmt="{:.2f}", horizontal=True)

	for bar, posts_count in zip(bars, chart_df["posts"]):
		ax.text(
			bar.get_width() + (ax.get_xlim()[1] * 0.10),
			bar.get_y() + bar.get_height() / 2,
			f"n={int(posts_count)}",
			va="center",
			ha="left",
			fontsize=8,
			color=CHART_THEME["text_muted"],
		)

	add_figure_decoration(
		fig,
		title="Top hashtags por engagement medio",
		subtitle="Barras horizontais para leitura executiva com volume por hashtag",
		footer=chart_footer(chart_context),
	)

	fig.tight_layout(rect=(0, 0.07, 1, 0.90))
	fig.savefig(output_path, dpi=180)
	plt.close(fig)

	return True, message


def plot_coauthor_impact_comments_views(
	posts: pd.DataFrame,
	output_path: Path,
	chart_context: Dict[str, Any],
) -> Tuple[bool, str]:
	plt = get_matplotlib_pyplot()
	if plt is None:
		return False, "matplotlib indisponivel"

	valid, chart_df, message = validate_chart_data(
		"coauthor_impact_comments_views",
		posts,
		required_cols=["has_coauthors", "num_comentarios", "visualizacoes", "shortcode"],
		min_rows=2,
		dropna_cols=["has_coauthors", "num_comentarios", "shortcode"],
	)
	if not valid:
		return False, message

	configure_matplotlib_style(plt)
	grouped = chart_df.groupby("has_coauthors").agg(
		avg_comments=("num_comentarios", "mean"),
		avg_views=("visualizacoes", "mean"),
		n_posts=("shortcode", "nunique"),
	)
	grouped = grouped.reindex([False, True])
	grouped["n_posts"] = grouped["n_posts"].fillna(0).astype(int)
	grouped["avg_comments"] = grouped["avg_comments"].fillna(0)
	grouped["avg_views"] = grouped["avg_views"].fillna(0)

	if grouped["n_posts"].sum() == 0:
		return False, "coauthor_impact_comments_views: sem dados validos"

	x_positions = np.arange(2)
	x_labels = [
		f"Sem coautor\n(n={int(grouped.loc[False, 'n_posts'])})",
		f"Com coautor\n(n={int(grouped.loc[True, 'n_posts'])})",
	]

	fig, axes = plt.subplots(1, 2, figsize=(13.8, 6.2), sharex=True)

	comment_bars = axes[0].bar(
		x_positions,
		[grouped.loc[False, "avg_comments"], grouped.loc[True, "avg_comments"]],
		color=[CHART_THEME["neutral"], CHART_THEME["good"]],
		edgecolor="#334155",
		linewidth=0.5,
	)
	style_axis(axes[0], grid_axis="y")
	axes[0].set_title("Comentarios")
	axes[0].set_ylabel("Media por post")
	axes[0].set_xticks(x_positions)
	axes[0].set_xticklabels(x_labels)
	add_bar_value_labels(axes[0], comment_bars, fmt="{:.1f}")

	view_bars = axes[1].bar(
		x_positions,
		[grouped.loc[False, "avg_views"], grouped.loc[True, "avg_views"]],
		color=[CHART_THEME["neutral"], CHART_THEME["accent"]],
		edgecolor="#334155",
		linewidth=0.5,
	)
	style_axis(axes[1], grid_axis="y")
	axes[1].set_title("Visualizacoes")
	axes[1].set_ylabel("Media por post")
	axes[1].set_xticks(x_positions)
	axes[1].set_xticklabels(x_labels)
	add_bar_value_labels(axes[1], view_bars, fmt="{:.1f}")

	comments_base = grouped.loc[False, "avg_comments"]
	comments_target = grouped.loc[True, "avg_comments"]
	views_base = grouped.loc[False, "avg_views"]
	views_target = grouped.loc[True, "avg_views"]

	if comments_base > 0:
		lift_comments = ((comments_target - comments_base) / comments_base) * 100
		axes[0].text(
			0.02,
			0.92,
			f"Lift: {lift_comments:+.1f}%",
			transform=axes[0].transAxes,
			fontsize=9,
			color=CHART_THEME["text_primary"],
			bbox={"facecolor": "#ecfdf5", "edgecolor": "#86efac", "boxstyle": "round,pad=0.3"},
		)
	if views_base > 0:
		lift_views = ((views_target - views_base) / views_base) * 100
		axes[1].text(
			0.02,
			0.92,
			f"Lift: {lift_views:+.1f}%",
			transform=axes[1].transAxes,
			fontsize=9,
			color=CHART_THEME["text_primary"],
			bbox={"facecolor": "#eff6ff", "edgecolor": "#93c5fd", "boxstyle": "round,pad=0.3"},
		)

	add_figure_decoration(
		fig,
		title="Impacto de coautoria em comentarios e visualizacoes",
		subtitle="Subplots separados para evitar distorcao de escala entre metricas",
		footer=chart_footer(chart_context),
	)

	fig.tight_layout(rect=(0, 0.07, 1, 0.90))
	fig.savefig(output_path, dpi=180)
	plt.close(fig)

	return True, message


def plot_quality_by_type(
	posts: pd.DataFrame,
	output_path: Path,
	chart_context: Dict[str, Any],
) -> Tuple[bool, str]:
	plt = get_matplotlib_pyplot()
	if plt is None:
		return False, "matplotlib indisponivel"

	valid, chart_df, message = validate_chart_data(
		"quality_by_type",
		posts,
		required_cols=["tipo", "qualified_comment_rate", "question_comment_rate", "shortcode"],
		min_rows=2,
		dropna_cols=["tipo", "shortcode"],
	)
	if not valid:
		return False, message

	configure_matplotlib_style(plt)
	agg = chart_df.groupby("tipo").agg(
		posts=("shortcode", "count"),
		qualified_comment_rate=("qualified_comment_rate", "mean"),
		question_comment_rate=("question_comment_rate", "mean"),
	)
	agg = agg.reset_index().dropna(subset=["qualified_comment_rate", "question_comment_rate"])
	if agg.empty:
		return False, "quality_by_type: sem metricas validas"

	agg["qualified_pct"] = agg["qualified_comment_rate"] * 100
	agg["question_pct"] = agg["question_comment_rate"] * 100
	agg = agg.sort_values("qualified_pct", ascending=False).reset_index(drop=True)

	x = np.arange(len(agg))
	width = 0.36
	labels = [f"{tipo}\n(n={int(n)})" for tipo, n in zip(agg["tipo"], agg["posts"])]

	fig, ax = plt.subplots(figsize=(12.5, 6.2))
	bars_q = ax.bar(
		x - width / 2,
		agg["qualified_pct"],
		width,
		label="Comentario qualificado (%)",
		color=CHART_THEME["secondary"],
		edgecolor="#334155",
		linewidth=0.4,
	)
	bars_p = ax.bar(
		x + width / 2,
		agg["question_pct"],
		width,
		label="Perguntas (%)",
		color=CHART_THEME["warning"],
		edgecolor="#334155",
		linewidth=0.4,
	)

	style_axis(ax, grid_axis="y")
	ax.set_xticks(x)
	ax.set_xticklabels(labels)
	ax.set_ylabel("Percentual (%)")
	ax.set_xlabel("Tipo de post")
	ax.legend(loc="upper right", frameon=False, fontsize=9)

	add_bar_value_labels(ax, bars_q, fmt="{:.1f}%")
	add_bar_value_labels(ax, bars_p, fmt="{:.1f}%")

	add_figure_decoration(
		fig,
		title="Qualidade da conversa por tipo de conteudo",
		subtitle="Comparativo entre comentario qualificado e comentarios com perguntas",
		footer=chart_footer(chart_context),
	)

	fig.tight_layout(rect=(0, 0.07, 1, 0.90))
	fig.savefig(output_path, dpi=180)
	plt.close(fig)

	return True, message


def plot_community_vs_quality(
	posts: pd.DataFrame,
	output_path: Path,
	chart_context: Dict[str, Any],
) -> Tuple[bool, str]:
	plt = get_matplotlib_pyplot()
	if plt is None:
		return False, "matplotlib indisponivel"

	valid, chart_df, message = validate_chart_data(
		"community_vs_quality",
		posts,
		required_cols=[
			"shortcode",
			"community_index",
			"qualified_comment_rate",
			"num_comentarios",
			"has_coauthors",
		],
		min_rows=3,
		dropna_cols=["community_index", "qualified_comment_rate"],
	)
	if not valid:
		return False, message

	configure_matplotlib_style(plt)
	chart_df = chart_df.copy()
	chart_df["community_pct"] = chart_df["community_index"] * 100
	chart_df["qualified_pct"] = chart_df["qualified_comment_rate"] * 100

	size_base = pd.to_numeric(chart_df["num_comentarios"], errors="coerce").fillna(0).clip(lower=1)
	if size_base.max() == size_base.min():
		size_scaled = pd.Series(np.repeat(120, len(size_base)), index=chart_df.index)
	else:
		size_scaled = pd.Series(
			60 + ((size_base - size_base.min()) / (size_base.max() - size_base.min())) * 260,
			index=chart_df.index,
		)

	fig, ax = plt.subplots(figsize=(12.5, 6.5))

	for has_coauthor, color, label in [
		(False, CHART_THEME["primary"], "Sem coautor"),
		(True, CHART_THEME["good"], "Com coautor"),
	]:
		subset = chart_df[chart_df["has_coauthors"] == has_coauthor]
		if subset.empty:
			continue
		sub_sizes = size_scaled.loc[subset.index]
		ax.scatter(
			subset["community_pct"],
			subset["qualified_pct"],
			s=sub_sizes,
			alpha=0.75,
			color=color,
			edgecolor="#1f2937",
			linewidth=0.5,
			label=label,
		)

	x_median = chart_df["community_pct"].median()
	y_median = chart_df["qualified_pct"].median()
	ax.axvline(x_median, linestyle="--", linewidth=1.0, color=CHART_THEME["text_muted"])
	ax.axhline(y_median, linestyle="--", linewidth=1.0, color=CHART_THEME["text_muted"])

	top_points = chart_df.sort_values("num_comentarios", ascending=False).head(3)
	for row in top_points.itertuples(index=False):
		ax.annotate(
			row.shortcode,
			xy=(row.community_pct, row.qualified_pct),
			xytext=(5, 5),
			textcoords="offset points",
			fontsize=8,
			color=CHART_THEME["text_primary"],
		)

	style_axis(ax, grid_axis="both")
	ax.set_xlabel("Indice de comunidade (%)")
	ax.set_ylabel("Comentarios qualificados (%)")
	ax.legend(loc="lower right", frameon=False, fontsize=9)

	add_figure_decoration(
		fig,
		title="Comunidade vs profundidade de interacao",
		subtitle="Cada ponto representa um post; tamanho proporcional ao volume de comentarios",
		footer=chart_footer(chart_context),
	)

	fig.tight_layout(rect=(0, 0.07, 1, 0.90))
	fig.savefig(output_path, dpi=180)
	plt.close(fig)

	return True, message


def format_number(value: Any, digits: int = 2) -> str:
	if value is None or pd.isna(value):
		return "n/a"
	return f"{value:.{digits}f}"


def best_row(table: pd.DataFrame, metric: str) -> Optional[pd.Series]:
	if table.empty or metric not in table.columns:
		return None
	subset = table.dropna(subset=[metric])
	if subset.empty:
		return None
	return subset.sort_values(metric, ascending=False).iloc[0]


def feature_metric_lift(feature_impact: pd.DataFrame, feature: str, metric: str) -> Optional[float]:
	subset = feature_impact[
		(feature_impact["feature"] == feature) & (feature_impact["metric"] == metric)
	]
	if subset.empty:
		return None
	value = subset.iloc[0]["lift_pct"]
	if pd.isna(value):
		return None
	return float(value)


def create_executive_report(
	ctx: AnalysisContext,
	structure_summary: Dict[str, Any],
	warnings: List[str],
	posts: pd.DataFrame,
	comments: pd.DataFrame,
	owners: pd.DataFrame,
	by_type: pd.DataFrame,
	video_table: pd.DataFrame,
	feature_impact: pd.DataFrame,
	hashtag_perf: pd.DataFrame,
	hashtag_cooccurrence: pd.DataFrame,
	hour_table: pd.DataFrame,
	weekday_table: pd.DataFrame,
	coauthor_table: pd.DataFrame,
	owner_summary: pd.DataFrame,
	top_commenters: pd.DataFrame,
	caption_topics: pd.DataFrame,
	comment_topics: pd.DataFrame,
	chart_manifest: pd.DataFrame,
) -> str:
	best_type_comments = best_row(by_type, "num_comentarios")
	best_type_engagement = best_row(by_type, "engagement_rate")

	best_hour_comments = best_row(hour_table, "avg_comments")
	best_hour_views = best_row(hour_table, "avg_views")

	best_weekday_comments = best_row(weekday_table, "avg_comments")

	coauthor_comment_lift = feature_metric_lift(feature_impact, "has_coauthors", "num_comentarios")
	coauthor_view_lift = feature_metric_lift(feature_impact, "has_coauthors", "visualizacoes")

	hashtag_comment_lift = feature_metric_lift(feature_impact, "has_hashtags", "num_comentarios")
	hashtag_engagement_lift = feature_metric_lift(feature_impact, "has_hashtags", "engagement_rate")

	mention_new_user_lift = feature_metric_lift(feature_impact, "has_mentions", "new_commenter_share")

	total_posts = len(posts)
	total_comments_observed = len(comments)
	total_unique_commenters = int(comments["owner_username_norm"].replace("", np.nan).dropna().nunique())

	top_hashtags_preview = hashtag_perf.head(ctx.top_n)
	top_commenters_preview = top_commenters.head(ctx.top_n)

	owner_row = owner_summary.iloc[0] if not owner_summary.empty else pd.Series(dtype=float)

	report_lines = [
		"# Relatorio Executivo de Analise de Posts",
		"",
		"## 1. Estrutura de dados identificada antes da analise",
		f"- Total de shortcodes analisados: {structure_summary.get('total_shortcodes', 0)}",
		f"- Pastas com post_*.xlsx: {structure_summary.get('shortcodes_with_post', 0)}",
		f"- Pastas com comments_*.xlsx: {structure_summary.get('shortcodes_with_comments', 0)}",
		f"- Pastas sem comentarios: {structure_summary.get('shortcodes_without_comments', 0)}",
		"- Estrutura validada: cada pasta pode conter post, comments e commentOwner conforme disponibilidade.",
		"",
		"## 2. Resumo da base",
		f"- Posts processados: {total_posts}",
		f"- Comentarios observados (latestComments): {total_comments_observed}",
		f"- Usuarios unicos comentando: {total_unique_commenters}",
		f"- Percentual de owners verificados: {format_number(owner_row.get('percent_verified', np.nan) * 100, 2)}%",
		"",
		"## 3. Metricas principais",
		"- Engajamento principal usado: (likes + comentarios) / visualizacoes (quando visualizacoes > 0).",
		"- Comentarios por visualizacao usado como proxy de profundidade.",
		"- Metricas de comunidade: indice de discussao, indice de comunidade, comentarios qualificados e taxa de perguntas.",
		"",
		"## 4. Respostas objetivas para decisao",
		"",
		"### 4.1 Que tipo de conteudo devo postar mais?",
	]

	if best_type_comments is not None:
		report_lines.append(
			f"- Maior media de comentarios: tipo {best_type_comments['tipo']} com {format_number(best_type_comments['num_comentarios'])} comentarios/post."
		)
	else:
		report_lines.append("- Nao foi possivel estimar media de comentarios por tipo.")

	if best_type_engagement is not None:
		report_lines.append(
			f"- Melhor engagement rate medio (com views): tipo {best_type_engagement['tipo']} com {format_number(best_type_engagement['engagement_rate'])}."
		)
	else:
		report_lines.append("- Nao foi possivel estimar engagement por tipo por falta de views validas.")

	report_lines.extend(
		[
			"",
			"### 4.2 Como aumentar comentarios (nao so likes)?",
			f"- Lift de comentarios com CTA: {format_number(feature_metric_lift(feature_impact, 'has_cta', 'num_comentarios'))}%.",
			f"- Lift de comentarios com coautoria: {format_number(coauthor_comment_lift)}%.",
			f"- Lift de comentarios com hashtags: {format_number(hashtag_comment_lift)}%.",
		]
	)

	if best_hour_comments is not None:
		report_lines.append(
			f"- Melhor hora para comentarios: {int(best_hour_comments['post_hour'])}h (media {format_number(best_hour_comments['avg_comments'])})."
		)
	if best_weekday_comments is not None:
		report_lines.append(
			f"- Melhor dia para comentarios: {best_weekday_comments['post_weekday']} (media {format_number(best_weekday_comments['avg_comments'])})."
		)

	report_lines.extend(
		[
			"",
			"### 4.3 Como atrair publico mais qualificado?",
			"- Nesta base, qualidade foi medida por: comentarios qualificados (> X palavras), taxa de perguntas e indice de comunidade.",
			f"- Lift de indice de comunidade com coautoria: {format_number(feature_metric_lift(feature_impact, 'has_coauthors', 'community_index'))}%.",
			f"- Lift de comentarios qualificados com CTA: {format_number(feature_metric_lift(feature_impact, 'has_cta', 'qualified_comment_rate'))}%.",
			f"- Lift de novos comentaristas com mencoes (proxy interno): {format_number(mention_new_user_lift)}%.",
			"",
			"### 4.4 Vale a pena usar coautores?",
			f"- Impacto medio em visualizacoes: {format_number(coauthor_view_lift)}%.",
			f"- Impacto medio em comentarios: {format_number(coauthor_comment_lift)}%.",
			"- Coautoria deve ser usada quando o objetivo for alcance e conversa; validar consistencia com mais posts.",
			"",
			"### 4.5 Qual o melhor horario?",
		]
	)

	if best_hour_comments is not None:
		report_lines.append(
			f"- Melhor hora para comentarios: {int(best_hour_comments['post_hour'])}h."
		)
	if best_hour_views is not None:
		report_lines.append(
			f"- Melhor hora para visualizacoes: {int(best_hour_views['post_hour'])}h."
		)
	if best_weekday_comments is not None:
		report_lines.append(f"- Melhor dia da semana: {best_weekday_comments['post_weekday']}.")

	report_lines.extend(
		[
			"",
			"### 4.6 Hashtags ajudam ou atrapalham?",
			f"- Lift de engagement com hashtags: {format_number(hashtag_engagement_lift)}%.",
			f"- Lift de comentarios com hashtags: {format_number(hashtag_comment_lift)}%.",
			"- Analise por hashtag individual e coocorrencia disponivel nas tabelas exportadas.",
			"",
			"## 5. NLP de legendas e comentarios (leve e rapido)",
			"- Legendas: tamanho, emojis, CTA e temas principais calculados.",
			"- Comentarios: sentimento (positivo/negativo/neutro), emocao (raiva/entusiasmo/duvida), perguntas e temas principais.",
			"",
			"## 6. Metricas nao mensuraveis com os dados atuais",
			"- Distribuicao de seguidores dos comentaristas: nao disponivel.",
			"- Privado vs publico: nao disponivel.",
			"- Relacao seguidor/seguindo: nao disponivel.",
			"- Tamanho da audiencia dos coautores: nao disponivel.",
			"",
			"## 7. Top hashtags (amostra)",
		]
	)

	if top_hashtags_preview.empty:
		report_lines.append("- Nao ha hashtags suficientes para ranking.")
	else:
		for row in top_hashtags_preview.itertuples(index=False):
			report_lines.append(
				f"- {row.hashtag}: posts={row.posts}, avg_comments={format_number(row.avg_comments)}, avg_engagement={format_number(row.avg_engagement_rate)}"
			)

	report_lines.extend(["", "## 8. Usuarios recorrentes (amostra)"])
	if top_commenters_preview.empty:
		report_lines.append("- Sem comentaristas suficientes para ranking.")
	else:
		for row in top_commenters_preview.itertuples(index=False):
			report_lines.append(
				f"- {row.owner_username_norm}: comentarios={int(row.comentarios)}, posts_distintos={int(row.posts_distintos)}, taxa_perguntas={format_number(row.taxa_perguntas)}"
			)

	report_lines.extend(
		[
			"",
			"## 9. Topicos de legenda",
		]
	)
	for row in caption_topics.itertuples(index=False):
		report_lines.append(f"- {row.topic_id}: {row.terms} ({row.metodo})")

	report_lines.extend(["", "## 10. Topicos de comentarios"])
	for row in comment_topics.itertuples(index=False):
		report_lines.append(f"- {row.topic_id}: {row.terms} ({row.metodo})")

	if warnings:
		report_lines.extend(["", "## 11. Avisos de qualidade de dados"])
		for warning in warnings:
			report_lines.append(f"- {warning}")

	report_lines.extend(["", "## 12. Pacote de graficos profissionais"])
	if chart_manifest.empty:
		report_lines.append("- Nenhum grafico foi exportado.")
	else:
		for row in chart_manifest.itertuples(index=False):
			report_lines.append(
				f"- {row.chart_id}: {row.status} ({row.file_name}) - {row.message}"
			)

	report_lines.extend(
		[
			"",
			"## 13. Arquivos gerados",
			f"- Tabelas CSV: {ctx.tables_dir}",
			f"- Graficos PNG: {ctx.charts_dir}",
		]
	)

	return "\n".join(report_lines)


def analyze(
		data_dir: Path = Path("data"), 
		output_dir: Path = Path("analysis_output"), 
		qualified_word_threshold: int = 6, 
		timezone: str = "America/Sao_Paulo",
		top_n: int = 10
	) -> None:
	tables_dir, charts_dir = ensure_output_dirs(output_dir)

	ctx = AnalysisContext(
		data_dir=data_dir,
		output_dir=output_dir,
		tables_dir=tables_dir,
		charts_dir=charts_dir,
		qualified_word_threshold=qualified_word_threshold,
		timezone=timezone,
		top_n=max(1, top_n),
	)
	if not ctx.data_dir.exists() or not ctx.data_dir.is_dir():
		raise FileNotFoundError(f"Diretorio de dados nao encontrado: {ctx.data_dir}")

	structure_df, structure_summary = identify_dataset_structure(ctx.data_dir)
	if structure_df.empty:
		raise ValueError("Nenhuma subpasta encontrada em data_dir para analise")

	save_table(structure_df, ctx.tables_dir / "dataset_structure_inventory.csv")
	with (ctx.output_dir / "dataset_structure_summary.json").open("w", encoding="utf-8") as fp:
		json.dump(structure_summary, fp, indent=2, ensure_ascii=False)

	posts_raw, comments_raw, owners_raw, warnings = load_dataset(structure_df)

	posts = build_post_features(posts_raw, timezone=ctx.timezone)
	comments = build_comment_features(
		comments_raw,
		qualified_word_threshold=ctx.qualified_word_threshold,
		timezone=ctx.timezone,
	)
	comments = add_comment_delay_features(comments, posts)
	comments = add_verified_commenter_flags(comments, owners_raw)

	conversation_metrics = build_conversation_metrics(posts, comments)
	posts = posts.merge(conversation_metrics, on="shortcode", how="left")

	community_metrics = build_community_metrics(comments)
	posts = posts.merge(community_metrics, on="shortcode", how="left")

	verified_rate_by_post = comments.groupby("shortcode")["is_verified"].mean().rename("verified_commenter_rate")
	posts = posts.merge(verified_rate_by_post, on="shortcode", how="left")

	comments_count_by_post = comments.groupby("shortcode").size().rename("comments_rows_loaded")
	posts = posts.merge(comments_count_by_post, on="shortcode", how="left")

	posts["comments_rows_loaded"] = posts["comments_rows_loaded"].fillna(0)
	posts["comments_coverage_ratio"] = (
		posts["comments_rows_loaded"] / posts["num_comentarios"].replace(0, np.nan)
	)

	warnings.extend(generate_quality_warnings(posts))

	by_type = aggregate_by_type(posts)
	video_table = build_video_duration_table(posts)
	feature_impact = build_binary_feature_impact(posts)
	hour_table, weekday_table = build_timing_tables(posts)
	hashtag_perf, hashtag_cooccurrence = build_hashtag_tables(posts)
	coauthor_table = build_coauthor_table(posts)
	owner_summary, top_commenters = build_audience_metrics(owners_raw, comments)

	caption_terms = top_terms_table(posts["legenda_post"].tolist(), top_n=ctx.top_n)
	comment_terms = top_terms_table(comments["texto_comentario"].tolist(), top_n=ctx.top_n)
	caption_topics = topic_modeling_light(posts["legenda_post"].tolist(), source="legenda")
	comment_topics = topic_modeling_light(comments["texto_comentario"].tolist(), source="comentarios")

	save_table(posts, ctx.tables_dir / "posts_enriched.csv")
	save_table(comments, ctx.tables_dir / "comments_enriched.csv")
	save_table(owners_raw, ctx.tables_dir / "owners_loaded.csv")

	save_table(by_type, ctx.tables_dir / "comparison_by_post_type.csv")
	save_table(video_table, ctx.tables_dir / "video_duration_vs_retention_proxy.csv")
	save_table(feature_impact, ctx.tables_dir / "feature_impact_table.csv")
	save_table(hour_table, ctx.tables_dir / "timing_by_hour.csv")
	save_table(weekday_table, ctx.tables_dir / "timing_by_weekday.csv")
	save_table(hashtag_perf, ctx.tables_dir / "hashtag_performance.csv")
	save_table(hashtag_cooccurrence, ctx.tables_dir / "hashtag_cooccurrence.csv")
	save_table(coauthor_table, ctx.tables_dir / "coauthor_performance.csv")
	save_table(owner_summary, ctx.tables_dir / "audience_owner_summary.csv")
	save_table(top_commenters, ctx.tables_dir / "top_commenters.csv")
	save_table(caption_terms, ctx.tables_dir / "caption_top_terms.csv")
	save_table(comment_terms, ctx.tables_dir / "comment_top_terms.csv")
	save_table(caption_topics, ctx.tables_dir / "caption_topics.csv")
	save_table(comment_topics, ctx.tables_dir / "comment_topics.csv")

	chart_context = build_chart_context(posts, timezone=ctx.timezone)
	chart_results: List[Dict[str, Any]] = []

	success, message = plot_post_type_avg_comments(
		by_type=by_type,
		output_path=ctx.charts_dir / "post_type_avg_comments.png",
		chart_context=chart_context,
	)
	chart_results.append(
		build_chart_result(
			chart_id="post_type_avg_comments",
			file_path=ctx.charts_dir / "post_type_avg_comments.png",
			success=success,
			message=message,
		)
	)

	success, message = plot_timing_hour_avg_comments(
		hour_table=hour_table,
		output_path=ctx.charts_dir / "timing_hour_avg_comments.png",
		chart_context=chart_context,
	)
	chart_results.append(
		build_chart_result(
			chart_id="timing_hour_avg_comments",
			file_path=ctx.charts_dir / "timing_hour_avg_comments.png",
			success=success,
			message=message,
		)
	)

	success, message = plot_timing_weekday_avg_comments(
		weekday_table=weekday_table,
		output_path=ctx.charts_dir / "timing_weekday_avg_comments.png",
		chart_context=chart_context,
	)
	chart_results.append(
		build_chart_result(
			chart_id="timing_weekday_avg_comments",
			file_path=ctx.charts_dir / "timing_weekday_avg_comments.png",
			success=success,
			message=message,
		)
	)

	success, message = plot_top_hashtags_engagement(
		hashtag_perf=hashtag_perf,
		output_path=ctx.charts_dir / "top_hashtags_engagement.png",
		chart_context=chart_context,
		top_n=min(ctx.top_n, 8),
	)
	chart_results.append(
		build_chart_result(
			chart_id="top_hashtags_engagement",
			file_path=ctx.charts_dir / "top_hashtags_engagement.png",
			success=success,
			message=message,
		)
	)

	success, message = plot_coauthor_impact_comments_views(
		posts=posts,
		output_path=ctx.charts_dir / "coauthor_impact_comments_views.png",
		chart_context=chart_context,
	)
	chart_results.append(
		build_chart_result(
			chart_id="coauthor_impact_comments_views",
			file_path=ctx.charts_dir / "coauthor_impact_comments_views.png",
			success=success,
			message=message,
		)
	)

	success, message = plot_quality_by_type(
		posts=posts,
		output_path=ctx.charts_dir / "quality_by_type.png",
		chart_context=chart_context,
	)
	chart_results.append(
		build_chart_result(
			chart_id="quality_by_type",
			file_path=ctx.charts_dir / "quality_by_type.png",
			success=success,
			message=message,
		)
	)

	success, message = plot_community_vs_quality(
		posts=posts,
		output_path=ctx.charts_dir / "community_vs_quality.png",
		chart_context=chart_context,
	)
	chart_results.append(
		build_chart_result(
			chart_id="community_vs_quality",
			file_path=ctx.charts_dir / "community_vs_quality.png",
			success=success,
			message=message,
		)
	)

	chart_manifest = pd.DataFrame(chart_results)
	save_table(chart_manifest, ctx.tables_dir / "chart_export_manifest.csv")

	failed_charts = chart_manifest[chart_manifest["status"] != "success"]
	if not failed_charts.empty:
		for row in failed_charts.itertuples(index=False):
			warnings.append(f"Grafico {row.chart_id} falhou: {row.message}")

	report_text = create_executive_report(
		ctx=ctx,
		structure_summary=structure_summary,
		warnings=warnings,
		posts=posts,
		comments=comments,
		owners=owners_raw,
		by_type=by_type,
		video_table=video_table,
		feature_impact=feature_impact,
		hashtag_perf=hashtag_perf,
		hashtag_cooccurrence=hashtag_cooccurrence,
		hour_table=hour_table,
		weekday_table=weekday_table,
		coauthor_table=coauthor_table,
		owner_summary=owner_summary,
		top_commenters=top_commenters,
		caption_topics=caption_topics,
		comment_topics=comment_topics,
		chart_manifest=chart_manifest,
	)

	report_path = ctx.output_dir / "executive_report.md"
	report_path.write_text(report_text, encoding="utf-8")

	print("Analise concluida com sucesso.")
	print(f"Posts processados: {len(posts)}")
	print(f"Comentarios processados: {len(comments)}")
	print(
		f"Graficos exportados: {(chart_manifest['status'] == 'success').sum()}/{len(chart_manifest)}"
	)
	print(f"Saida gerada em: {ctx.output_dir.resolve()}")


def generate_quality_warnings(posts: pd.DataFrame) -> List[str]:
	warnings: List[str] = []

	for row in posts.itertuples(index=False):
		loaded = getattr(row, "comments_rows_loaded", np.nan)
		expected = getattr(row, "num_comentarios", np.nan)
		if pd.notna(expected) and expected > 0 and pd.notna(loaded):
			ratio = loaded / expected if expected else np.nan
			if pd.notna(ratio) and ratio < 0.2:
				warnings.append(
					f"Shortcode {row.shortcode}: comments carregados ({int(loaded)}) bem abaixo de num_comentarios ({int(expected)})."
				)

		views = getattr(row, "visualizacoes", np.nan)
		if pd.isna(views) or views <= 0:
			warnings.append(
				f"Shortcode {row.shortcode}: sem visualizacoes validas para engagement por view."
			)

	return sorted(set(warnings))

if __name__ == "__main__":
	analyze()
