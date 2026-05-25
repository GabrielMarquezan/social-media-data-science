import pandas as pd
import json
import asyncio
from apify_client import ApifyClientAsync
from dotenv import load_dotenv
import os
from uuid import uuid4
from pathlib import Path

from src.extrai_posts_excel import generate_excel_for_each_post
from src.analyze_data import analyze

load_dotenv()

TOKEN = os.getenv("APIFY_API_KEY")  
ACTOR_ID = 'apify/instagram-scraper'

async def main() -> None:
    # Recebe os links
    links = []
    with open("links.txt", "r") as links_file:
        links = links_file.readlines()

    # Faz a request

    request_input = {
        "addParentData": False,
        "directUrls": links,
        "resultsLimit": 100,
        "resultsType": "posts",
        "searchLimit": 10,
        "searchType": "hashtag"
    }
        
    apify_client = ApifyClientAsync(TOKEN)

    actor_client = apify_client.actor(ACTOR_ID)
    call_result = await actor_client.call(run_input=request_input)

    if call_result is None:
        print('Actor run failed.')
        return

    run_client = actor_client.last_run()
    dataset_client = run_client.dataset()
    dataset_data = await dataset_client.list_items()

    # Faz a análise

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