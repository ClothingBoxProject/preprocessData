import re
import time
import csv
import requests

BASE_URL = "https://www.woowarhanclean.com/search"
KEYWORD = "버리는 방법"

PARAMS_BASE = {
    "type": "all",
    "sort": "consensus_desc",
    "keyword": KEYWORD,
}

PAGE_PARAM = "page"  # 필요하면 여기만 바꾸세요: "page" / "p" / "q_page" 등
START_PAGE = 1
SLEEP_SEC = 0.4

IDX_RE = re.compile(r"[?&]idx=(\d+)\b")

def fetch_html(page: int) -> str:
    params = dict(PARAMS_BASE)
    params[PAGE_PARAM] = page
    r = requests.get(BASE_URL, params=params, timeout=20, headers={
        "User-Agent": "Mozilla/5.0",
    })
    r.raise_for_status()
    return r.text

def extract_idxs(html: str) -> list[str]:
    # 페이지 HTML 내의 모든 idx=숫자 추출
    return IDX_RE.findall(html)

def main():
    all_idxs = set()
    page = START_PAGE

    while True:
        html = fetch_html(page)
        idxs = extract_idxs(html)

        # 이 페이지에서 새 idx가 없으면 종료(페이지 끝)
        new = 0
        for x in idxs:
            if x not in all_idxs:
                all_idxs.add(x)
                new += 1

        print(f"page={page}  found={len(idxs)}  new={new}  total_unique={len(all_idxs)}")
        if new == 0:
            break
        page += 1
        time.sleep(SLEEP_SEC)

    # 저장
    out_txt = "crawling_index.txt"
    with open(out_txt, "w", encoding="utf-8") as f:
        for x in sorted(all_idxs, key=int):
            f.write(x + "\n")

    out_csv = "crawling_index.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["idx"])
        for x in sorted(all_idxs, key=int):
            w.writerow([x])

    print(f"\nDONE: unique idx count = {len(all_idxs)}")
    print(f"Saved: {out_txt}, {out_csv}")

if __name__ == "__main__":
    main()