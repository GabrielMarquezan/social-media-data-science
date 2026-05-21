import pandas as pd
import json
import asyncio
from apify_client import ApifyClientAsync
from dotenv import load_dotenv
import os
from uuid import uuid4
from pathlib import Path

from extrai_posts_excel import generate_excel_for_each_post
from analyze_data import analyze

load_dotenv()

TOKEN = os.getenv("APIFY_API_KEY")  

# Recebe links de posts separados em um por linha
# Faz requisição pra API do Apify e aguarda resultado
# Gera resultados em csv
# Faz a análise e fornece as métricas

async def main() -> None:
    links = []
    with open("links.txt", "r") as links_file:
        links = links_file.readlines()

    request_input = {
        "addParentData": False,
        "directUrls": links,
        "resultsLimit": 100,
        "resultsType": "posts",
        "searchLimit": 10,
        "searchType": "hashtag"
    }
        
    apify_client = ApifyClientAsync(TOKEN)

    actor_client = apify_client.actor('apify/instagram-scraper')
    call_result = await actor_client.call(run_input=request_input)

    if call_result is None:
        print('Actor run failed.')
        return

    run_client = actor_client.last_run()
    dataset_client = run_client.dataset()
    dataset_data = await dataset_client.list_items()

    run_id = uuid4()

    os.makedirs(f"data/{run_id}", exist_ok=True)

    json_path = Path(f"data/{run_id}/{run_id}.json")
    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(dataset_data.items, file, indent=4, ensure_ascii=False)

    current_data_dir = Path(f"data/{run_id}/posts")

    generate_excel_for_each_post(json_path, output_root=current_data_dir)
    analyze(data_dir=current_data_dir, output_dir=Path(f"data/{run_id}/analysis_output"))


if __name__ == '__main__':
    asyncio.run(main())