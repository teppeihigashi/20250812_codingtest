# hyogo_bid_entaku_list.py
import requests
from bs4 import BeautifulSoup, NavigableString
import re

URL = "https://web.pref.hyogo.lg.jp/bid/bid_opn_01.html"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; hyogo-scraper/1.0)"}

def clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def pick_title_anchor(block):
    """ブロック内のリンクから最も名称らしいものを選ぶ"""
    links = block.find_all("a", href=True)
    scored = []
    for a in links:
        t = clean_text(a.get_text())
        if not t:
            continue
        score = len(t)
        if re.fullmatch(r"(詳細|PDF|リンク|こちら|Download|ダウンロード)", t):
            score -= 100
        scored.append((score, a, t))
    if not scored:
        return None, ""
    scored.sort(reverse=True, key=lambda x: x[0])
    return scored[0][1], scored[0][2]

def main():
    r = requests.get(URL, headers=HEADERS, timeout=20)
    r.raise_for_status()
    r.encoding = r.apparent_encoding
    soup = BeautifulSoup(r.text, "html.parser")

    hits = soup.find_all(string=lambda t: isinstance(t, NavigableString) and "公示日" in t)
    results = []

    for node in hits:
        parent = node.parent
        block = parent
        while block and block.name not in ("li", "div", "article", "section", "tr", "tbody"):
            block = block.parent
        if not block:
            continue

        ctx = clean_text(block.get_text(" "))
        m = re.search(r"公示日\s*[:：]?\s*(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日)", ctx)
        if not m:
            neigh = block.find_next_sibling() or block.find_next()
            neigh_text = clean_text(neigh.get_text(" ")) if neigh else ""
            ctx2 = ctx + " " + neigh_text
            m = re.search(r"公示日\s*[:：]?\s*(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日)", ctx2)
        if not m:
            continue
        pub = m.group(1)

        a, title = pick_title_anchor(block)
        if not a:
            extra = block.find_next("a")
            if extra:
                title = clean_text(extra.get_text())
                a = extra
        if not a or not title:
            continue
        if len(title) <= 2 or re.fullmatch(r"(詳細|PDF|こちら)", title):
            continue

        results.append((title, pub))

    seen = set()
    uniq = []
    for t, d in results:
        key = (t, d)
        if key not in seen:
            seen.add(key)
            uniq.append((t, d))

    for title, pub in uniq:
        print(title)
        print(pub)
        print()

if __name__ == "__main__":
    main()
