import asyncio
import logging
from pathlib import Path
from uuid import uuid4

from social_media.src.config import build_config
from social_media.src.dependencies import build_dependencies
from social_media.src.exporters.png import export_charts
from social_media.src.exporters.xlsx import export_xlsx
from social_media.src.extract.apify import extract
from social_media.src.log import configure_logging, set_run_id
from social_media.src.pipeline.runner import run_pipeline
from social_media.src.pipeline.steps.comment_features import comment_features_step
from social_media.src.pipeline.steps.content_type import content_type_step
from social_media.src.pipeline.steps.nlp_sentiment_terms import nlp_sentiment_terms_step
from social_media.src.pipeline.steps.nlp_terms import nlp_terms_step
from social_media.src.pipeline.steps.nlp_topics import nlp_topics_step
from social_media.src.pipeline.steps.parse import parse_step
from social_media.src.pipeline.steps.post_conversation import post_conversation_step
from social_media.src.pipeline.steps.post_features import post_features_step
from social_media.src.pipeline.steps.timing import timing_step

logger = logging.getLogger(__name__)

STEPS = [
    parse_step,
    post_features_step,
    comment_features_step,
    post_conversation_step,
    content_type_step,
    timing_step,
    nlp_terms_step,
    nlp_topics_step,
    nlp_sentiment_terms_step,
]


def read_links(path: Path) -> list[str]:
    """Lê o arquivo de links, removendo linhas vazias."""
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de links não encontrado: {path}")

    with open(path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    logger.info("Links carregados.", extra={"links_count": len(lines), "path": str(path)})
    return lines


async def main() -> None:
    run_id = str(uuid4())
    set_run_id(run_id)

    config = build_config()
    configure_logging(config.log_level, config.log_format)

    logger.info("Iniciando execução.", extra={"run_id": run_id})

    deps = build_dependencies(config)

    links = read_links(Path("links.txt"))
    raw_json_path = await extract(links, config, run_id)

    initial_dfs = {"raw_json_path": raw_json_path}
    dfs = run_pipeline(STEPS, initial_dfs, config, deps)

    output_root = config.output_dir / run_id
    export_xlsx(dfs, output_root, config)
    export_charts(dfs, output_root / "charts", config)

    logger.info(
        "Execução finalizada.",
        extra={"run_id": run_id, "output_root": str(output_root)},
    )


if __name__ == "__main__":
    asyncio.run(main())
