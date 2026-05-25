import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import pandas as pd

COLUMN_CONFIG = {
    "posts": [
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
    ],
    "comments": [
        "texto_comentario",
        "owner_username",
        "timestamp",
        "replies",
        "likescount",
    ],
    "owners": [
        "owner_id",
        "owner_username",
        "is_verified",
        "profile_pic_url",
    ],
}

FILE_PATTERNS = {
    "post": "post_{shortcode}.xlsx",
    "comments": "comments_{shortcode}.xlsx",
    "owners": "commentOwner_{shortcode}.xlsx",
}


SHORTCODE_PATTERN = re.compile(r"/p/([A-Za-z0-9_-]+)/")


# ============================================================================
# EXTRACTORS & NORMALIZERS
# ============================================================================


def extract_shortcode(post: Dict[str, Any], index: int) -> str:
    """Extract shortcode from post URL; fallback to shortCode or indexed name."""
    url = post.get("url")
    if isinstance(url, str):
        match = SHORTCODE_PATTERN.search(url)
        if match:
            return match.group(1)

    short_code = post.get("shortCode") or post.get("shortcode")
    if isinstance(short_code, str) and short_code.strip():
        return short_code.strip()

    return f"post_{index + 1:04d}"


def normalize_list(values: Any, separator: str = " | ") -> str:
    """Serialize list values into a readable string for Excel cells.
    
    Handles dicts by extracting username/full_name/id, or falls back to JSON string.
    Filters out empty values.
    """
    if not isinstance(values, list) or not values:
        return ""

    normalized: List[str] = []
    for item in values:
        if isinstance(item, dict):
            # Prefer human-readable identifiers if available.
            preferred_identifier = item.get("username") or item.get("full_name") or item.get("id")
            if preferred_identifier is None:
                normalized.append(json.dumps(item, ensure_ascii=False))
            else:
                normalized.append(str(preferred_identifier).strip())
        else:
            normalized.append(str(item).strip())

    return separator.join(value for value in normalized if value)


def serialize_replies(comment: Dict[str, Any]) -> str:
    """Serialize comment replies to JSON string for Excel storage."""
    replies = comment.get("replies", [])
    if not isinstance(replies, list):
        return "[]"
    return json.dumps(replies, ensure_ascii=False)


def iter_comment_thread(comment: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    """Yield a comment and recursively yield all nested replies (depth-first)."""
    yield comment
    replies = comment.get("replies", [])
    if not isinstance(replies, list):
        return

    for reply in replies:
        if isinstance(reply, dict):
            yield from iter_comment_thread(reply)


def owner_key(owner: Dict[str, Any]) -> Optional[str]:
    """Generate unique key for owner (prioritizes id, then username)."""
    owner_id = owner.get("id")
    if owner_id is not None and str(owner_id).strip():
        return f"id:{owner_id}"

    username = owner.get("username")
    if username is not None and str(username).strip():
        return f"username:{username}"

    return None


# ============================================================================
# DATA COLLECTION
# ============================================================================


def collect_post_row(post: Dict[str, Any]) -> Dict[str, Any]:
    """Extract post data into a dictionary matching COLUMN_CONFIG['posts']."""
    coauthors = post.get("coauthorProducers", [])

    row = {
        "legenda_post": post.get("caption", ""),
        "coautores": normalize_list(coauthors),
        "num_comentarios": post.get("commentsCount"),
        "hashtags": normalize_list(post.get("hashtags", [])),
        "comentarios_habilitados": post.get("isCommentsDisabled") is False,
        "num_likes": post.get("likesCount"),
        "mencoes": normalize_list(post.get("mentions", [])),
        "nome_owner": post.get("ownerFullName", ""),
        "timestamp": post.get("timestamp", ""),
        "tipo": post.get("type", ""),
        "url": post.get("url", ""),
        "visualizacoes": post.get("videoViewCount", post.get("videoPlayCount")),
        "duracao_video": post.get("videoDuration"),
        "localizacao": post.get("locationName", ""),
    }

    return row


def collect_comments_and_owners(post: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Extract comments and owners from post, deduplicating owners by key.
    
    Returns:
        (comment_rows, owner_rows) tuples ready for Excel export
    """
    comments = post.get("latestComments", [])
    if not isinstance(comments, list):
        comments = []

    comment_rows: List[Dict[str, Any]] = []
    owner_rows: List[Dict[str, Any]] = []
    seen_owner_keys: Set[str] = set()

    for comment in comments:
        if not isinstance(comment, dict):
            continue

        comment_rows.append(
            {
                "texto_comentario": comment.get("text", ""),
                "owner_username": comment.get("ownerUsername", ""),
                "timestamp": comment.get("timestamp", ""),
                "replies": serialize_replies(comment),
                "likescount": comment.get("likesCount"),
            }
        )

        for node in iter_comment_thread(comment):
            owner = node.get("owner")
            if not isinstance(owner, dict):
                continue

            owner_id_key = owner_key(owner)
            if owner_id_key is None or owner_id_key in seen_owner_keys:
                continue

            seen_owner_keys.add(owner_id_key)
            owner_rows.append(
                {
                    "owner_id": owner.get("id"),
                    "owner_username": owner.get("username", ""),
                    "is_verified": owner.get("is_verified"),
                    "profile_pic_url": owner.get("profile_pic_url", ""),
                }
            )

    return comment_rows, owner_rows


# ============================================================================
# I/O UTILITIES
# ============================================================================


def ensure_output_dir(output_root: Path, shortcode: str) -> Path:
    """Create and return directory for post output."""
    post_dir = output_root / shortcode
    post_dir.mkdir(parents=True, exist_ok=True)
    return post_dir


def should_export_comment_files(post: Dict[str, Any]) -> bool:
    """Check if post has comments (by count or latestComments list)."""
    comment_count = post.get("commentsCount")
    if comment_count is not None:
        try:
            return int(comment_count) > 0
        except (TypeError, ValueError):
            pass

    comments = post.get("latestComments", [])
    return isinstance(comments, list) and len(comments) > 0


def remove_file_if_exists(file_path: Path) -> None:
    """Delete file if it exists."""
    if file_path.exists() and file_path.is_file():
        file_path.unlink()


# ============================================================================
# EXCEL EXPORT
# ============================================================================


def _write_excel_files(
    post_dir: Path,
    shortcode: str,
    post_row: Dict[str, Any],
    comment_rows: List[Dict[str, Any]],
    owner_rows: List[Dict[str, Any]],
    post: Dict[str, Any],
) -> None:
    """Write Excel files for post, comments, and owners.
    
    Uses centralized COLUMN_CONFIG for column definitions.
    Creates comment/owner files only if post has comments.
    """
    post_file = post_dir / FILE_PATTERNS["post"].format(shortcode=shortcode)
    comments_file = post_dir / FILE_PATTERNS["comments"].format(shortcode=shortcode)
    owners_file = post_dir / FILE_PATTERNS["owners"].format(shortcode=shortcode)

    # Always write post file
    pd.DataFrame([post_row], columns=COLUMN_CONFIG["posts"]).to_excel(post_file, index=False)

    # Write comment/owner files only if post has comments
    if should_export_comment_files(post):
        pd.DataFrame(comment_rows, columns=COLUMN_CONFIG["comments"]).to_excel(
            comments_file, index=False
        )
        pd.DataFrame(owner_rows, columns=COLUMN_CONFIG["owners"]).to_excel(
            owners_file, index=False
        )
    else:
        # Keep output consistent: only post file when no comments
        remove_file_if_exists(comments_file)
        remove_file_if_exists(owners_file)


def export_post_files(post: Dict[str, Any], index: int, output_root: Path) -> str:
    """Export a single post with its comments and owners to Excel files.
    
    Args:
        post: Post data dictionary
        index: Post index (for fallback shortcode generation)
        output_root: Root directory for output
    
    Returns:
        Shortcode of exported post
    """
    shortcode = extract_shortcode(post, index)
    post_dir = ensure_output_dir(output_root, shortcode)

    post_row = collect_post_row(post)
    comment_rows, owner_rows = collect_comments_and_owners(post)

    _write_excel_files(post_dir, shortcode, post_row, comment_rows, owner_rows, post)

    return shortcode


# ============================================================================
# MAIN PIPELINE
# ============================================================================


def generate_excel_for_each_post(input_path: Path, output_root: Path) -> None:
    """Load posts from JSON file and export each to Excel.
    
    Args:
        input_path: Path to JSON file (single post or list of posts)
        output_root: Directory to create post subdirectories
    
    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If JSON structure is invalid
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Arquivo de entrada nao encontrado: {input_path}")

    output_root.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        posts = [data]
    elif isinstance(data, list):
        posts = data
    else:
        raise ValueError("O JSON deve conter uma lista de posts ou um unico objeto de post.")

    exported = 0
    for idx, post in enumerate(posts):
        if not isinstance(post, dict):
            continue
        export_post_files(post, idx, output_root)
        exported += 1

    print(f"Posts processados: {exported}")
    print(f"Arquivos gerados em: {output_root.resolve()}")


# ============================================================================
# CLI
# ============================================================================


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Gera arquivos Excel por post a partir de dados.json"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("dados.json"),
        help="Caminho do arquivo JSON de entrada",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data"),
        help="Diretorio de saida para as pastas por shortcode",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    generate_excel_for_each_post(args.input, args.output_dir)
