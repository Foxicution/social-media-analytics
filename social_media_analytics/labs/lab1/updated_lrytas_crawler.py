import pandas as pd
from httpx import get
from concurrent.futures import ThreadPoolExecutor
from function_pipes import pipeline
from itertools import chain

BASE_URL = "https://www.lrytas.lt{}"
DATE_FROM = "2021-01-01"
TERM = "vakcinavimas"


def get_raw_data(page: int) -> dict:
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/116.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Origin': 'https://www.lrytas.lt',
        'Connection': 'keep-alive',
        'Referer': 'https://www.lrytas.lt/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'Sec-GPC': '1',
    }    
    params = {
        'count': '12',
        'kw_count': '12',
        'order': 'pubfromdate-',
        'page': str(page),
        'dfrom': DATE_FROM,
        'q_text': TERM,
    }
    try:
        return get(
            'https://kolumbus-api.lrytas.lt/api_dev/fe/search/0/',
            params=params,
            headers=headers
        ).json()
    except Exception:
        print(f"Failed to get raw data for {page}")

def handle_raw_data(raw_data: dict) -> dict:
    return raw_data['articles']

if __name__ == "__main__":
    first_page = get_raw_data(0)
    with ThreadPoolExecutor(10) as pool:
        data = list(pool.map(pipeline(get_raw_data, handle_raw_data), range(1, int(first_page['totalPages'])))) + [handle_raw_data(first_page)]

    pd.DataFrame(list(chain.from_iterable(data))).to_csv("lrytas_data_fixed.csv")
