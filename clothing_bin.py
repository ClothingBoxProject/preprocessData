import csv
import json
from datetime import datetime

CSV_PATH = "./data/clothing_bin.csv"
JSON_PATH = "./data/clothing_bin.json"

def to_float(s: str):
    s = (s or "").strip()
    return float(s) if s else None

def to_int(s: str):
    s = (s or "").strip()
    return int(s) if s else None

def normalize_date(s: str):
    s = (s or "").strip()
    if not s:
        return None
    # 날짜만 있는 경우
    try:
        d = datetime.strptime(s, "%Y-%m-%d")
        return d.strftime("%Y-%m-%dT%H:%M:%S")
    except ValueError:
        # 이미 ISO이거나 다른 포맷이면 그대로 두거나 추가 파싱
        return s

def convert(csv_path: str, json_path: str):
    items = []
    with open(csv_path, "r", encoding="cp949", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            item = {
                "bin_id": to_int(row.get("연번")),
                "district": (row.get("행정동") or "").strip(),
                "latitude": to_float(row.get("위도")),
                "longitude": to_float(row.get("경도")),
                "address": (row.get("주소") or "").strip(),
                "modified_at": normalize_date(row.get("데이터기준일자")),
            }
            if item["bin_id"] is None and not item["address"]:
                continue
            items.append(item)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    print(f"OK: {len(items)} rows -> {json_path}")

if __name__ == "__main__":
    convert(CSV_PATH, JSON_PATH)