import pandas as pd
import json
import asyncio
from apify_client import ApifyClientAsync
from dotenv import load_dotenv
import os
from uuid import uuid4
from pathlib import Path

load_dotenv()

TOKEN = os.getenv("APIFY_API_KEY")  
ACTORS = ["apify/instagram-post-scraper", "apify/instagram-comment-scraper"]
ACTOR = "apify/instagram-scraper"

async def main() -> None:
    links = []
    with open("links.txt", "r") as links_file:
        links = links_file.readlines()

    request = {
        "addParentData": False,
        "directUrls": links,
        "resultsLimit": 100,
        "resultsType": "posts",
        "searchLimit": 10,
        "searchType": "hashtag"
    }

    # por post: 0.0017
    # por comentario: 0.0026 
    # Total com scrapers especificos: 0.0026 x 15 + 0.0017 = 0.0407
    # Scraper generalista: 0.0027

    apify_client = ApifyClientAsync(TOKEN)

    actor_client = apify_client.actor(ACTOR)
    call_result = await actor_client.call(run_input=request)

    if call_result is None:
        print('Actor run failed.')
        return

    run_client = actor_client.last_run()
    dataset_client = run_client.dataset()
    dataset_data = await dataset_client.list_items()

    # Faz a análise

    run_id = uuid4()

    os.makedirs(f"data", exist_ok=True)

    json_path = Path(f"data/comments.json")
    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(dataset_data.items, file, indent=4, ensure_ascii=False)

    current_data_dir = Path(f"data/{run_id}/posts")


if __name__ == '__main__':
    asyncio.run(main())