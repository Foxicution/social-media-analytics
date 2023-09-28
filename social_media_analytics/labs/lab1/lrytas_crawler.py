from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from httpx import Response, get
from lxml.etree import HTML
from selenium.webdriver import Firefox, FirefoxOptions

data = []
crawled_links = set()
BASE_URL = "https://www.lrytas.lt{}"


def make_request(url: str) -> Response:
    crawled_links.add(url)
    cookies = {
        "auth.strategy": "strapi_facebook",
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/116.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Sec-GPC": "1",
    }
    return get(url, cookies=cookies, headers=headers)


def process_article_page(url: str) -> dict:
    try:
        options = FirefoxOptions()
        options.add_argument("--headless")
        driver = Firefox(options=options)  # Fixed this line as well
        driver.get(url)
        tree = HTML(driver.page_source)
    
        article_data = {
            "article_name": tree.xpath("//h1[@class='LArticleHeadline__title']")[0].text.strip(),
            "url": url,
            "article_author": [author.text.strip() for author in tree.xpath("//a[@class='LArticleHeader__author']")],
            "article_date": date_elements[0].text.strip()
            if (date_elements := tree.xpath("//h5[@class='LArticleHeader__dates']"))
            else "N/A",
            "comment_count": "N/A",
            "reactions": {
                "thumbs_up": (elements := tree.xpath("//div[@class='LArticleEmotions__count']"))[0].text.strip(),
                "two_fingers_up": elements[1].text.strip(),
                "thumbs_down": elements[2].text.strip(),
            },
        }

        driver.quit()
        return article_data
    except Exception:
        print(f"Failed for {url}")

def process_search_page(page: Response) -> list[str]:
    if page in crawled_links:
        return [], []
    if page.status_code == 301 or page.status_code == 302 or page.status_code == 307:
        return process_search_page(page.headers["Location"])
    elif page.status_code != 200:
        print(f"Page {page.url} gave back a {page.response}")
        return [], []
    tree = HTML(page.text)
    with ThreadPoolExecutor(12) as pool:
        page_data = list(pool.map(process_article_page, [BASE_URL.format(path) for path in tree.xpath("//h2[@class='LPostContent__title']/a/@href")]))
    
    return [url for path in tree.xpath("//div[@class='LPagination__item']/a/@href") if (url := BASE_URL.format(path)) not in crawled_links], page_data



if __name__ == "__main__":
    links = ["https://www.lrytas.lt/search?q=vakcinavimas"]
    while links:
        print(f"Processing {len(links)}")
        new_links = []
        for link in links:
            next_links, page_data = process_search_page(make_request(link))
            new_links.extend(next_links)
            data.extend(page_data)
        links = set(new_links)
        
    print(data)
    pd.DataFrame([d for d in data if d]).to_csv("test.csv")