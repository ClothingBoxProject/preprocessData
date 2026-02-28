# import os
# import re
# import time
# import hashlib
# from pathlib import Path

# import requests
# from openpyxl import load_workbook


# HEADERS = {
#     "Authorization": lambda key: f"Client-ID {key}",
#     "Accept-Version": "v1",
#     "User-Agent": "Mozilla/5.0",
# }

# API_URL = "https://api.unsplash.com/search/photos"


# def safe_name(s: str, max_len: int = 80) -> str:
#     """윈도우 파일명 안전하게"""
#     s = s.strip()
#     s = re.sub(r'[\\/:*?"<>|]+', "_", s)
#     s = re.sub(r"\s+", " ", s)
#     return s[:max_len] if len(s) > max_len else s


# def read_item_names_from_xlsx(xlsx_path: str, col_name: str = "item_name", sheet_name: str | None = None):
#     wb = load_workbook(xlsx_path, read_only=True, data_only=True)
#     ws = wb[sheet_name] if sheet_name else wb.active

#     rows = ws.iter_rows(values_only=True)
#     header = next(rows)
#     if not header:
#         raise RuntimeError("엑셀 헤더가 비어있습니다.")

#     # 컬럼 인덱스 찾기
#     try:
#         idx = [str(x).strip() if x is not None else "" for x in header].index(col_name)
#     except ValueError:
#         raise RuntimeError(f"'{col_name}' 컬럼을 찾지 못했습니다. 현재 헤더: {header}")

#     items = []
#     for r in rows:
#         if r and idx < len(r):
#             v = r[idx]
#             if v is None:
#                 continue
#             v = str(v).strip()
#             if v:
#                 items.append(v)

#     # 중복 제거(순서 유지)
#     seen = set()
#     uniq = []
#     for x in items:
#         if x not in seen:
#             seen.add(x)
#             uniq.append(x)

#     return uniq


# def search_unsplash_images(query: str, per_page: int = 30, page: int = 1) -> list[dict]:
#     if not UNSPLASH_ACCESS_KEY:
#         raise RuntimeError("환경변수 UNSPLASH_ACCESS_KEY 를 설정하세요.")

#     params = {
#         "query": query,
#         "page": page,
#         "per_page": per_page,
#         "lang": "ko",
#     }
#     headers = {
#         "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}",
#         "Accept-Version": "v1",
#         "User-Agent": "Mozilla/5.0",
#     }

#     r = requests.get(API_URL, params=params, headers=headers, timeout=30)
#     r.raise_for_status()
#     data = r.json()

#     results = []
#     for item in data.get("results", []):
#         results.append({
#             "id": item.get("id"),
#             # 다운로드에 쓸 url(regular가 무난)
#             "img_url": item["urls"].get("regular") or item["urls"].get("small") or item["urls"].get("full"),
#             "user": item["user"]["name"],
#             "photo_link": item["links"]["html"],
#             "user_link": item["user"]["links"]["html"],
#         })
#     return results


# def download_image(url: str, out_path: Path, sleep: float = 0.2):
#     out_path.parent.mkdir(parents=True, exist_ok=True)
#     headers = {"User-Agent": "Mozilla/5.0"}

#     rr = requests.get(url, headers=headers, stream=True, timeout=60)
#     rr.raise_for_status()

#     with open(out_path, "wb") as f:
#         for chunk in rr.iter_content(chunk_size=1024 * 64):
#             if chunk:
#                 f.write(chunk)

#     time.sleep(sleep)


# def crawl_from_xlsx(
#     xlsx_path: str,
#     out_dir: str = "unsplash_photos",
#     col_name: str = "item_name",
#     sheet_name: str | None = None,
#     photos_per_item: int = 10,     # ✅ item 하나당 저장할 사진 수
#     per_page: int = 30,            # Unsplash API 페이지당 결과 수
#     max_pages: int = 5,            # ✅ item 하나당 최대 몇 페이지까지 넘길지
#     sleep_between_items: float = 0.3,
# ):
#     items = read_item_names_from_xlsx(xlsx_path, col_name=col_name, sheet_name=sheet_name)
#     print(f"[INFO] item_name 개수: {len(items)}")

#     base = Path(out_dir)
#     base.mkdir(parents=True, exist_ok=True)

#     for item_i, item_name in enumerate(items, 1):
#         q = item_name
#         folder = base / safe_name(q)

#         saved = 0
#         used_photo_ids = set()

#         print(f"\n[{item_i}/{len(items)}] query='{q}' -> {folder}")

#         for page in range(1, max_pages + 1):
#             try:
#                 results = search_unsplash_images(q, per_page=per_page, page=page)
#             except requests.HTTPError as e:
#                 print(f"[ERROR] API 호출 실패: {e}")
#                 break

#             if not results:
#                 print("[INFO] 더 이상 결과 없음")
#                 break

#             for rank, it in enumerate(results, 1):
#                 if saved >= photos_per_item:
#                     break

#                 pid = it.get("id")
#                 img_url = it.get("img_url")
#                 if not img_url or not pid:
#                     continue
#                 if pid in used_photo_ids:
#                     continue
#                 used_photo_ids.add(pid)

#                 # 파일명: 순번 + photo id + 해시(안전)
#                 h = hashlib.sha1(img_url.encode("utf-8")).hexdigest()[:8]
#                 filename = f"{saved+1:02d}_{pid}_{h}.jpg"
#                 out_path = folder / filename

#                 if out_path.exists():
#                     saved += 1
#                     continue

#                 try:
#                     download_image(img_url, out_path)
#                     saved += 1
#                     print(f"  [OK] {saved}/{photos_per_item} {out_path.name}")
#                 except Exception as e:
#                     print(f"  [FAIL] {img_url} -> {e}")

#             if saved >= photos_per_item:
#                 break

#         if saved == 0:
#             print("  [WARN] 저장된 이미지가 없습니다 (검색 결과/다운로드 실패)")

#         time.sleep(sleep_between_items)


# if __name__ == "__main__":
#     xlsx_path = "./filtered_postprocessed.xlsx"  # <-- 너의 엑셀 경로
#     out_dir = "./unsplash_photos"  # <-- 저장할 폴더 경로

#     crawl_from_xlsx(
#         xlsx_path=xlsx_path,
#         out_dir=out_dir,
#         col_name="item_name",
#         sheet_name=None,       # 시트 지정하려면 "Sheet1" 같은 이름
#         photos_per_item=10,    # item 당 10장
#         per_page=30,
#         max_pages=5,
#     )

import os
import re
import time
import hashlib
from pathlib import Path

import requests
from openpyxl import load_workbook

UNSPLASH_ACCESS_KEY = "eqBM1VfsIji-SoozJiq3bwN5gCr6AkRSxMN4BMCvx8E" # 환경변수로 넣는 걸 추천
API_URL = "https://api.unsplash.com/search/photos"

def safe_name(s: str, max_len: int = 80) -> str:
    s = str(s).strip()
    s = re.sub(r'[\\/:*?"<>|]+', "_", s)
    s = re.sub(r"\s+", " ", s)
    return s[:max_len]


def read_item_names_from_xlsx_range(
    xlsx_path: str,
    col_name: str = "item_name",
    sheet_name: str | None = None,
    start_excel_row: int = 2,  # ✅ 엑셀 실제 행 번호(1부터, 헤더 포함). 기본은 2(헤더 다음)
):
    wb = load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb[sheet_name] if sheet_name else wb.active

    # 헤더는 1행이라고 가정
    header = [c.value for c in ws[1]]
    header_norm = [str(x).strip() if x is not None else "" for x in header]

    if col_name not in header_norm:
        raise RuntimeError(f"'{col_name}' 컬럼을 찾지 못했습니다. 현재 헤더: {header_norm}")

    idx = header_norm.index(col_name) + 1  # openpyxl은 1-based column

    items = []
    # ✅ start_excel_row ~ 마지막행까지
    for r in range(start_excel_row, ws.max_row + 1):
        v = ws.cell(row=r, column=idx).value
        if v is None:
            continue
        v = str(v).strip()
        if v:
            items.append((r, v))  # (엑셀행번호, item_name)

    return items


def search_unsplash_images(query: str, per_page: int = 30, page: int = 1) -> list[dict]:
    if not UNSPLASH_ACCESS_KEY:
        raise RuntimeError("환경변수 UNSPLASH_ACCESS_KEY 를 설정하세요.")

    params = {"query": query, "page": page, "per_page": per_page, "lang": "ko"}
    headers = {
        "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}",
        "Accept-Version": "v1",
        "User-Agent": "Mozilla/5.0",
    }

    r = requests.get(API_URL, params=params, headers=headers, timeout=30)
    r.raise_for_status()
    data = r.json()

    results = []
    for item in data.get("results", []):
        results.append({
            "id": item.get("id"),
            "img_url": item["urls"].get("regular") or item["urls"].get("small") or item["urls"].get("full"),
        })
    return results


def download_image(url: str, out_path: Path, sleep: float = 0.2):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rr = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, stream=True, timeout=60)
    rr.raise_for_status()
    with open(out_path, "wb") as f:
        for chunk in rr.iter_content(chunk_size=1024 * 64):
            if chunk:
                f.write(chunk)
    time.sleep(sleep)


def crawl_from_xlsx_from_row50(
    xlsx_path: str,
    out_dir: str = "unsplash_photos",
    col_name: str = "item_name",
    sheet_name: str | None = None,
    start_excel_row: int = 50,   # ✅ 여기: 50행부터 끝까지
    photos_per_item: int = 10,
    per_page: int = 30,
    max_pages: int = 5,
):
    items = read_item_names_from_xlsx_range(
        xlsx_path=xlsx_path,
        col_name=col_name,
        sheet_name=sheet_name,
        start_excel_row=start_excel_row,
    )
    print(f"[INFO] 처리 대상: {len(items)}개 (엑셀 {start_excel_row}행부터)")

    base = Path(out_dir)
    base.mkdir(parents=True, exist_ok=True)

    for i, (excel_row, item_name) in enumerate(items, 1):
        q = item_name
        folder = base / safe_name(q)

        saved = 0
        used_ids = set()

        print(f"\n[{i}/{len(items)}] excel_row={excel_row} query='{q}'")

        for page in range(1, max_pages + 1):
            results = search_unsplash_images(q, per_page=per_page, page=page)
            if not results:
                break

            for it in results:
                if saved >= photos_per_item:
                    break
                pid = it.get("id")
                url = it.get("img_url")
                if not pid or not url or pid in used_ids:
                    continue
                used_ids.add(pid)

                h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
                out_path = folder / f"{saved+1:02d}_{pid}_{h}.jpg"

                if not out_path.exists():
                    try:
                        download_image(url, out_path)
                        saved += 1
                        print(f"  [OK] {saved}/{photos_per_item} -> {out_path.name}")
                    except Exception as e:
                        print(f"  [FAIL] {url} : {e}")

            if saved >= photos_per_item:
                break

        if saved == 0:
            print("  [WARN] 저장된 이미지 없음")


if __name__ == "__main__":
    xlsx_path = "./filtered_postprocessed.xlsx"  # ✅ 너의 엑셀 경로
    out_dir = "./unsplash_photos"  # ✅ 저장할 폴더 경로

    crawl_from_xlsx_from_row50(
        xlsx_path=xlsx_path,
        out_dir=out_dir,
        col_name="item_name",
        sheet_name=None,
        start_excel_row=50,     # ✅ 50행부터 끝까지
        photos_per_item=10,
        max_pages=5,
    )