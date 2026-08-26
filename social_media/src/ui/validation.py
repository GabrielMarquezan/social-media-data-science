"""Validação de URLs de posts e reels do Instagram para a interface web."""

import re

# Formatos aceitos: https://www.instagram.com/p/{shortcode}/ (post) e
# https://www.instagram.com/reel/{shortcode}/ (reel). Shortcode aceita letras,
# dígitos, underscore e hífen; barra final e query string são permitidos.
INSTAGRAM_POST_RE = re.compile(
    r"^https://www\.instagram\.com/(p|reel|reels)/[A-Za-z0-9_-]+/?([?#].*)?$"
)

EXPECTED_FORMAT = (
    "https://www.instagram.com/p/{shortcode}/ ou "
    "https://www.instagram.com/reel/{shortcode}/"
)


def parse_links(text: str) -> list[str]:
    """Converte o texto da área de entrada em uma lista de links.

    Remove espaços das extremidades e ignora linhas vazias.
    """
    return [line.strip() for line in text.splitlines() if line.strip()]


def find_invalid_links(links: list[str]) -> list[str]:
    """Retorna as URLs que não correspondem ao formato de post do Instagram."""
    return [link for link in links if not INSTAGRAM_POST_RE.match(link)]
