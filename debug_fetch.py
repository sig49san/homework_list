import requests
from bs4 import BeautifulSoup

ID = "16548190"
base_url = f"http://ereter.net/iidxplayerdata/{ID}/level"

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/113.0.0.0 Safari/537.36",
}

for i in range(1, 4):
    url = f"{base_url}/{i}"
    print("=====\nURL:", url)

    try:
        r_default = requests.get(url, timeout=10)
        print("default status:", r_default.status_code)
    except Exception as e:
        print("default request failed:", e)
        r_default = None

    try:
        r_hdr = requests.get(url, headers=headers, timeout=10)
        print("with UA status:", r_hdr.status_code)
    except Exception as e:
        print("header request failed:", e)
        r_hdr = None

    def check_and_report(resp, label):
        if not resp:
            print(label, "no response")
            return
        text = resp.text
        print(label, "len:", len(text))
        snippet = text[:500]
        print(label, "snippet:\n", snippet)
        soup = BeautifulSoup(text, "html.parser")
        table = soup.find("table", class_="table condensed")
        print(label, "table found:", bool(table))

    print("--- default ---")
    check_and_report(r_default, "default")
    print("--- with UA ---")
    check_and_report(r_hdr, "withUA")

print("done")
