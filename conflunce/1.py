import requests
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CONFLUENCE_URL = "https://conflunce.whrhkj.com"
PAGE_ID = 134845156
USERNAME = "your_account"
PASSWORD = "your_password"


def get_confluence_h1_list(page_id: int):
    api_url = f"{CONFLUENCE_URL}/rest/api/content/{page_id}"
    params = {"expand": "body.storage"}
    resp = requests.get(
        api_url,
        params=params,
        auth=(USERNAME, PASSWORD),
        verify=False,
        timeout=30
    )
    if resp.status_code != 200:
        print(f"请求失败 {resp.status_code}: {resp.text}")
        return None

    data = resp.json()
    page_title = data["title"]
    html = data["body"]["storage"]["value"]
    soup = BeautifulSoup(html, "html.parser")

    # 获取正文全部一级标题 <h1>
    h1_tags = soup.find_all("h1")
    h1_list = []
    for tag in h1_tags:
        text = tag.get_text(strip=True)
        h1_list.append(text)

    res = {
        "page_title": page_title,   # confluence页面本身标题
        "page_id": page_id,
        "body_h1_count": len(h1_list),
        "body_h1_list": h1_list
    }
    return res


if __name__ == "__main__":
    ret = get_confluence_h1_list(PAGE_ID)
    if ret:
        print(f"Confluence页面标题：{ret['page_title']}")
        print(f"正文一级标题数量：{ret['body_h1_count']}")
        print("====正文H1一级标题列表====")
        for idx, h1_text in enumerate(ret["body_h1_list"], start=1):
            print(f"{idx}. {h1_text}")
