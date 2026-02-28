import re
import csv
import time
from pathlib import Path
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup

BASE_DETAIL_URL = "https://www.woowarhanclean.com/review_ha-waste/"
SLEEP_SEC = 0.4
TIMEOUT = 25

IDX_RE = re.compile(r"^\d+$")

def read_idxs_from_txt(path: str) -> List[str]:
    idxs = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        if IDX_RE.match(s):
            idxs.append(s)
    return idxs


def read_idxs_from_csv(path: str, col: str = "idx") -> List[str]: # csv 파일에서 idx 읽어오기
    idxs = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if col not in reader.fieldnames:
            raise ValueError(f"CSV에 '{col}' 컬럼이 없습니다. columns={reader.fieldnames}")
        for row in reader:
            s = (row.get(col) or "").strip()
            if IDX_RE.match(s):
                idxs.append(s)
    return idxs


def fetch_html(session: requests.Session, idx: str) -> str:
    params = {"idx": idx, "bmode": "view"}
    r = session.get(BASE_DETAIL_URL, params=params, timeout=TIMEOUT) # 상세페이지로 GET 요청
    r.raise_for_status()
    return r.text


def extract_title(soup: BeautifulSoup) -> str:
    # 1) og:title 우선
    og = soup.select_one('meta[property="og:title"]')
    if og and og.get("content"):
        return og["content"].strip()

    # 2) <title>
    if soup.title and soup.title.string:
        return soup.title.string.strip()

    return ""


def extract_main_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    # 본문 컨테이너: class에 _comment_body_ 가 포함된 div
    body = soup.select_one('div[class*="_comment_body_"]')
    if body is None:
        body = soup.select_one(".board_txt_area") or soup.select_one(".board_view")

    if body is None:
        return ""

    # 이미지/줄바꿈 태그 제거
    for tag in body.select("img, br, script, style"):
        tag.decompose()

    # 텍스트 추출 (줄바꿈 유지)
    text = body.get_text(separator="\n", strip=True)

    # 빈 줄 정리
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]  # 빈 줄 제거
    cleaned = "\n".join(lines)
    return cleaned


def crawl_idxs(
    idxs: List[str],
    out_csv: str = "detail_texts.csv",
    out_failed: str = "failed_idxs.txt",
    max_retries: int = 2,
):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    })

    failed = []

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["idx", "url", "title", "text"])

        for i, idx in enumerate(idxs, start=1):
            url = f"{BASE_DETAIL_URL}?idx={idx}&bmode=view"

            ok = False
            last_err: Optional[str] = None

            for attempt in range(max_retries + 1):
                try:
                    html = fetch_html(session, idx)
                    soup = BeautifulSoup(html, "lxml")
                    title = extract_title(soup)
                    text = extract_main_text(html)

                    if not text: # 본문이 비면 실패로 기록
                        raise RuntimeError("본문 텍스트 추출 실패(셀렉터 미매칭 또는 본문 비어있음)")

                    w.writerow([idx, url, title, text])
                    ok = True
                    break

                except Exception as e:
                    last_err = repr(e)
                    time.sleep(0.8 * (attempt + 1))

            print(f"[{i}/{len(idxs)}] idx={idx} -> {'OK' if ok else 'FAIL'}"
                  + ("" if ok else f"  err={last_err}"))

            if not ok:
                failed.append(idx)

            time.sleep(SLEEP_SEC)

    if failed:
        Path(out_failed).write_text("\n".join(failed) + "\n", encoding="utf-8")
        print(f"\nFAILED count={len(failed)} saved to {out_failed}")

    print(f"\nDONE saved to {out_csv}")


if __name__ == "__main__":
    # idxs = ["16050098"]
    idxs = read_idxs_from_csv("crawling_index.csv", col="idx")

    # crawl_idxs(idxs, out_csv="woowarhanclean_detail_texts.csv")
    crawl_idxs(idxs, out_csv="crawling_detailed.csv")