import json
import logging
from pathlib import Path

from apify_client import ApifyClientAsync

from social_media.src.config import Config

logger = logging.getLogger(__name__)


async def extract(links: list[str], config: Config, run_id: str) -> Path:
    """Extrai posts do Instagram via Apify e salva o dataset bruto em disco.

    Args:
        links: Lista de URLs de posts do Instagram.
        config: Configuração da aplicação.
        run_id: Identificador da execução atual.

    Returns:
        Caminho do arquivo JSON salvo.

    Raises:
        RuntimeError: Se a chamada ao ator retornar None.
    """
    config.data_dir.mkdir(parents=True, exist_ok=True)
    output_path = config.data_dir / f"raw_{run_id}.json"

    run_input = {
        "addParentData": False,
        "directUrls": links,
        "resultsLimit": config.results_limit,
        "resultsType": "posts",
    }

    logger.info(
        "Iniciando extração via Apify.",
        extra={
            "actor": config.apify_actor,
            "run_id": run_id,
            "links_count": len(links),
            "results_limit": config.results_limit,
        },
    )

    apify_client = ApifyClientAsync(config.apify_token)
    actor_client = apify_client.actor(config.apify_actor)
    call_result = await actor_client.call(run_input=run_input)

    if call_result is None:
        logger.error("A chamada ao ator Apify retornou None.", extra={"actor": config.apify_actor})
        raise RuntimeError(f"Falha na chamada do ator Apify '{config.apify_actor}'.")

    run_client = actor_client.last_run()
    dataset_client = run_client.dataset()

    items = []
    limit = 250
    offset = 0

    while True:
        page = await dataset_client.list_items(limit=limit, offset=offset)
        items.extend(page.items)
        if len(page.items) < limit:
            break
        offset += limit

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=4, ensure_ascii=False)

    logger.info(
        "Extração concluída.",
        extra={
            "run_id": run_id,
            "output_path": str(output_path),
            "items_count": len(items),
        },
    )
    return output_path
