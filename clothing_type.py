import csv
import json
import re

CSV_PATH = "./data/clothing_type.csv"
JSON_PATH = "./data/clothing_type.json"

# 카테고리 → ID 매핑 (원하는 순서로 고정)
CATEGORY_TO_ID = {
    "모자": 1,
    "상의": 2,
    "하의": 3,
    "아우터": 4,
    "스타킹": 5,
    "양말": 6,
    "신발": 7,
    "액세서리": 8,
    "가방": 9,
    "속옷": 10,
    "이불": 11,
    "기타": 12,
}

# 혹시 CSV에 공백/다른 표기가 섞였을 때 정규화(필요하면 추가)
def normalize_category(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", "", s)  # 중간 공백 제거 (예: "액 세 서 리" 같은 케이스)
    return s

def open_with_fallback(path: str):
    # 자주 쓰는 순서: utf-8-sig -> cp949 -> euc-kr -> utf-8
    for enc in ("utf-8-sig", "cp949", "euc-kr", "utf-8"):
        try:
            f = open(path, "r", encoding=enc, newline="")
            f.readline()
            f.seek(0)
            return f, enc
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("unknown", b"", 0, 1, "No suitable encoding found")

def convert(csv_path: str, json_path: str):
    items = []
    unknown_categories = {}

    f, enc = open_with_fallback(csv_path)
    print(f"[INFO] opened CSV with encoding={enc}")

    with f:
        reader = csv.DictReader(f)

        # 헤더 확인(문제 생기면 여기 출력 보고 키 수정)
        # print("[DEBUG] fieldnames:", reader.fieldnames)

        detail_id = 1
        for row in reader:
            item_name = (row.get("item_name") or "").strip()
            category_raw = normalize_category(row.get("category"))
            one_line = (row.get("one_line") or "").strip()
            how_to_throw = (row.get("how_to_throw") or "").strip()
            caution = (row.get("caution") or "").strip()
            url = (row.get("url") or "").strip()

            # 빈 줄 스킵
            if not item_name and not category_raw and not one_line and not how_to_throw and not caution and not url:
                continue

            category_id = CATEGORY_TO_ID.get(category_raw)
            if category_id is None:
                # 모르는 카테고리는 기타(12)로 넣거나, 아예 에러로 처리할 수도 있음
                unknown_categories[category_raw] = unknown_categories.get(category_raw, 0) + 1
                category_id = CATEGORY_TO_ID["기타"]

            items.append({
                "detail_id": detail_id,
                "item_name": item_name,
                "category_id": category_id,
                "one_line": one_line,
                "how_to_throw": how_to_throw,
                "caution": caution,
                "url": url,
            })
            detail_id += 1

    with open(json_path, "w", encoding="utf-8") as out:
        json.dump(items, out, ensure_ascii=False, indent=2)

    print(f"OK: {len(items)} rows -> {json_path}")

    if unknown_categories:
        print("[WARN] Unknown categories found (mapped to '기타'):")
        for k, v in unknown_categories.items():
            print(f"  - '{k}': {v} rows")

if __name__ == "__main__":
    convert(CSV_PATH, JSON_PATH)