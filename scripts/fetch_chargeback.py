#!/usr/bin/env python3
"""
fetch_chargeback.py — Google Sheets 차지백 데이터 자동 수집

시트에서 차지백 로그를 읽어 주간 단위로 집계한 뒤 JSON 출력.
보고서 생성 스크립트에서 import 또는 stdout JSON으로 활용.

사용법:
    # 전체 데이터 출력
    python scripts/fetch_chargeback.py

    # 특정 주간만 (FEB W3)
    python scripts/fetch_chargeback.py --week "FEB W3"

    # 두 주간 비교 (WoW)
    python scripts/fetch_chargeback.py --wow "FEB W2" "FEB W3"

    # 날짜 범위 직접 지정
    python scripts/fetch_chargeback.py --range 2026-02-14 2026-02-20

셋업:
    1. pip install -r scripts/requirements.txt
    2. Google Cloud Console → Sheets API 활성화
    3. 서비스 계정 생성 → JSON 키 다운로드
    4. secrets/google_credentials.json 에 배치
    5. 시트에 서비스 계정 이메일 뷰어 권한 공유
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    print(
        "필수 패키지 미설치. 다음 명령어를 실행하세요:\n"
        "  pip install gspread google-auth",
        file=sys.stderr,
    )
    sys.exit(1)

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

SHEET_ID = "1u2OgvNyKDCGCucGmRKxPHmJ5cA4-F5uLzYeZehKssEg"
GID = 1816273055

CREDENTIALS_PATH = Path(__file__).resolve().parent.parent / "secrets" / "google_credentials.json"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]

# 주간 범위 정의 (토~금 기준)
WEEK_RANGES = {
    "JAN W3": ("2026-01-17", "2026-01-23"),
    "JAN W4": ("2026-01-24", "2026-01-30"),
    "FEB W1": ("2026-01-31", "2026-02-06"),
    "FEB W2": ("2026-02-07", "2026-02-13"),
    "FEB W3": ("2026-02-14", "2026-02-20"),
    "FEB W4": ("2026-02-21", "2026-02-27"),
    "MAR W1": ("2026-02-28", "2026-03-06"),
}


# ──────────────────────────────────────────────
# Sheet access
# ──────────────────────────────────────────────


def get_client():
    """서비스 계정으로 gspread 클라이언트 생성."""
    if not CREDENTIALS_PATH.exists():
        print(
            f"인증 파일 없음: {CREDENTIALS_PATH}\n"
            "셋업 가이드:\n"
            "  1. Google Cloud Console → 서비스 계정 생성\n"
            "  2. JSON 키 다운로드\n"
            "  3. secrets/google_credentials.json 에 배치\n"
            "  4. 시트에 서비스 계정 이메일 뷰어 권한 공유",
            file=sys.stderr,
        )
        sys.exit(1)

    creds = Credentials.from_service_account_file(
        str(CREDENTIALS_PATH), scopes=SCOPES
    )
    return gspread.authorize(creds)


def find_worksheet(spreadsheet, gid):
    """gid로 워크시트 검색."""
    for ws in spreadsheet.worksheets():
        if ws.id == gid:
            return ws
    raise ValueError(f"gid={gid}에 해당하는 워크시트를 찾을 수 없습니다.")


def fetch_all_rows(client):
    """시트에서 전체 데이터를 읽어 dict 리스트로 반환."""
    spreadsheet = client.open_by_key(SHEET_ID)
    worksheet = find_worksheet(spreadsheet, GID)
    return worksheet.get_all_records()


# ──────────────────────────────────────────────
# Column detection (자동 감지)
# ──────────────────────────────────────────────

# 컬럼명 후보 매핑 — 시트 컬럼명이 바뀌어도 유연하게 대응
COLUMN_ALIASES = {
    "date": ["date", "날짜", "일자", "chargeback date", "cb date", "발생일"],
    "amount": ["amount", "금액", "피해액", "chargeback amount", "cb amount", "합계"],
    "currency": ["currency", "통화", "화폐"],
    "provider": ["provider", "pg", "결제사", "payment provider", "pg사", "payment method"],
    "product": ["product", "상품", "product type", "상품유형", "플랜"],
    "reason": ["reason", "사유", "chargeback reason", "cb reason", "유형"],
    "market": ["market", "마켓", "language", "언어"],
}


def detect_columns(headers):
    """헤더에서 컬럼 역할을 자동 매핑."""
    mapping = {}
    lower_headers = [h.strip().lower() for h in headers]

    for role, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            for idx, header in enumerate(lower_headers):
                if alias == header or alias in header:
                    mapping[role] = headers[idx]
                    break
            if role in mapping:
                break

    return mapping


# ──────────────────────────────────────────────
# Date parsing
# ──────────────────────────────────────────────

DATE_FORMATS = [
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%m/%d/%Y",
    "%m/%d/%y",
    "%d/%m/%Y",
    "%Y.%m.%d",
]


def parse_date(date_str):
    """여러 형식의 날짜 문자열을 파싱."""
    if not date_str:
        return None
    date_str = str(date_str).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def parse_amount(amount_str):
    """금액 문자열 → float 변환. $, ₩, 쉼표 등 제거."""
    if not amount_str:
        return 0.0
    s = str(amount_str).strip()
    s = s.replace("$", "").replace("₩", "").replace("¥", "").replace(",", "").replace(" ", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


# ──────────────────────────────────────────────
# Aggregation
# ──────────────────────────────────────────────


def filter_by_range(rows, col_map, start_date, end_date):
    """날짜 범위 내 행만 필터."""
    date_col = col_map.get("date")
    if not date_col:
        print("날짜 컬럼을 감지하지 못했습니다. 시트 컬럼명을 확인하세요.", file=sys.stderr)
        sys.exit(1)

    filtered = []
    for row in rows:
        d = parse_date(row.get(date_col, ""))
        if d and start_date <= d <= end_date:
            filtered.append(row)
    return filtered


def aggregate(rows, col_map):
    """필터된 행을 집계."""
    amount_col = col_map.get("amount")
    currency_col = col_map.get("currency")
    provider_col = col_map.get("provider")
    product_col = col_map.get("product")
    reason_col = col_map.get("reason")
    market_col = col_map.get("market")

    total_count = len(rows)
    total_amount = 0.0

    by_provider = {}
    by_currency = {}
    by_product = {}
    by_reason = {}
    by_market = {}

    for row in rows:
        amt = parse_amount(row.get(amount_col, 0)) if amount_col else 0.0
        total_amount += amt

        if provider_col:
            p = str(row.get(provider_col, "Unknown")).strip() or "Unknown"
            entry = by_provider.setdefault(p, {"count": 0, "amount": 0.0})
            entry["count"] += 1
            entry["amount"] += amt

        if currency_col:
            c = str(row.get(currency_col, "Unknown")).strip() or "Unknown"
            entry = by_currency.setdefault(c, {"count": 0, "amount": 0.0})
            entry["count"] += 1
            entry["amount"] += amt

        if product_col:
            pr = str(row.get(product_col, "Unknown")).strip() or "Unknown"
            entry = by_product.setdefault(pr, {"count": 0, "amount": 0.0})
            entry["count"] += 1
            entry["amount"] += amt

        if reason_col:
            r = str(row.get(reason_col, "Unknown")).strip() or "Unknown"
            entry = by_reason.setdefault(r, {"count": 0, "amount": 0.0})
            entry["count"] += 1
            entry["amount"] += amt

        if market_col:
            m = str(row.get(market_col, "Unknown")).strip() or "Unknown"
            entry = by_market.setdefault(m, {"count": 0, "amount": 0.0})
            entry["count"] += 1
            entry["amount"] += amt

    result = {
        "total_count": total_count,
        "total_amount": round(total_amount, 2),
    }

    if by_provider:
        result["by_provider"] = dict(sorted(by_provider.items(), key=lambda x: -x[1]["count"]))
    if by_currency:
        result["by_currency"] = dict(sorted(by_currency.items(), key=lambda x: -x[1]["count"]))
    if by_product:
        result["by_product"] = dict(sorted(by_product.items(), key=lambda x: -x[1]["count"]))
    if by_reason:
        result["by_reason"] = dict(sorted(by_reason.items(), key=lambda x: -x[1]["count"]))
    if by_market:
        result["by_market"] = dict(sorted(by_market.items(), key=lambda x: -x[1]["count"]))

    return result


def compute_wow(current, previous):
    """Week-over-Week 변화 계산."""
    wow = {
        "count_change": current["total_count"] - previous["total_count"],
        "count_pct": round(
            (current["total_count"] - previous["total_count"])
            / max(previous["total_count"], 1)
            * 100,
            1,
        ),
        "amount_change": round(current["total_amount"] - previous["total_amount"], 2),
        "amount_pct": round(
            (current["total_amount"] - previous["total_amount"])
            / max(previous["total_amount"], 0.01)
            * 100,
            1,
        ),
    }

    # 결제사별 비중 변화
    if "by_provider" in current and "by_provider" in previous:
        provider_wow = {}
        all_providers = set(current.get("by_provider", {}).keys()) | set(
            previous.get("by_provider", {}).keys()
        )
        for p in all_providers:
            cur_pct = (
                current["by_provider"].get(p, {}).get("count", 0)
                / max(current["total_count"], 1)
                * 100
            )
            prev_pct = (
                previous["by_provider"].get(p, {}).get("count", 0)
                / max(previous["total_count"], 1)
                * 100
            )
            provider_wow[p] = round(cur_pct - prev_pct, 1)
        wow["provider_share_change"] = provider_wow

    return wow


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────


def resolve_week(week_name):
    """주간 이름 → (start_date, end_date) 변환."""
    week_name = week_name.upper().strip()
    if week_name not in WEEK_RANGES:
        available = ", ".join(sorted(WEEK_RANGES.keys()))
        print(f"알 수 없는 주간: {week_name}\n사용 가능: {available}", file=sys.stderr)
        sys.exit(1)
    start_str, end_str = WEEK_RANGES[week_name]
    return (
        datetime.strptime(start_str, "%Y-%m-%d").date(),
        datetime.strptime(end_str, "%Y-%m-%d").date(),
    )


def main():
    parser = argparse.ArgumentParser(
        description="Google Sheets 차지백 데이터 수집 · 주간 집계"
    )
    parser.add_argument(
        "--week", type=str, help='주간 이름 (예: "FEB W3")'
    )
    parser.add_argument(
        "--wow", nargs=2, metavar=("PREV", "CURR"), help='WoW 비교 (예: "FEB W2" "FEB W3")'
    )
    parser.add_argument(
        "--range", nargs=2, metavar=("START", "END"), help="날짜 범위 (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--cumulative", type=str, help='월 누적 (예: "2026-02" → 2월 전체)'
    )
    parser.add_argument(
        "--raw", action="store_true", help="필터 없이 전체 데이터 출력"
    )
    parser.add_argument(
        "--pretty", action="store_true", help="JSON 포맷팅 출력"
    )
    args = parser.parse_args()

    # 인증 & 데이터 읽기
    client = get_client()
    print("시트 데이터 읽는 중...", file=sys.stderr)
    rows = fetch_all_rows(client)
    print(f"총 {len(rows)}행 로드 완료.", file=sys.stderr)

    if not rows:
        print("시트에 데이터가 없습니다.", file=sys.stderr)
        sys.exit(1)

    # 컬럼 자동 감지
    headers = list(rows[0].keys())
    col_map = detect_columns(headers)
    print(f"컬럼 매핑: {col_map}", file=sys.stderr)

    indent = 2 if args.pretty else None

    # Raw 모드
    if args.raw:
        print(json.dumps(rows, ensure_ascii=False, indent=indent, default=str))
        return

    # WoW 비교 모드
    if args.wow:
        prev_start, prev_end = resolve_week(args.wow[0])
        curr_start, curr_end = resolve_week(args.wow[1])

        prev_rows = filter_by_range(rows, col_map, prev_start, prev_end)
        curr_rows = filter_by_range(rows, col_map, curr_start, curr_end)

        prev_agg = aggregate(prev_rows, col_map)
        curr_agg = aggregate(curr_rows, col_map)
        wow = compute_wow(curr_agg, prev_agg)

        output = {
            "mode": "wow",
            "previous": {"week": args.wow[0], "range": f"{prev_start}~{prev_end}", **prev_agg},
            "current": {"week": args.wow[1], "range": f"{curr_start}~{curr_end}", **curr_agg},
            "wow_change": wow,
        }
        print(json.dumps(output, ensure_ascii=False, indent=indent, default=str))
        return

    # 날짜 범위 결정
    if args.week:
        start_date, end_date = resolve_week(args.week)
        label = args.week
    elif args.range:
        start_date = datetime.strptime(args.range[0], "%Y-%m-%d").date()
        end_date = datetime.strptime(args.range[1], "%Y-%m-%d").date()
        label = f"{start_date}~{end_date}"
    elif args.cumulative:
        year, month = args.cumulative.split("-")
        start_date = datetime(int(year), int(month), 1).date()
        if int(month) == 12:
            end_date = datetime(int(year) + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(int(year), int(month) + 1, 1).date() - timedelta(days=1)
        label = f"{args.cumulative} 누적"
    else:
        # 기본: 최근 2주
        today = datetime.now().date()
        # 가장 가까운 지난 금요일 찾기
        days_since_fri = (today.weekday() - 4) % 7
        last_friday = today - timedelta(days=days_since_fri)
        start_date = last_friday - timedelta(days=13)  # 2주 전 토요일
        end_date = last_friday
        label = f"최근 2주 ({start_date}~{end_date})"

    # 집계
    filtered = filter_by_range(rows, col_map, start_date, end_date)
    result = aggregate(filtered, col_map)
    output = {
        "mode": "weekly",
        "label": label,
        "range": f"{start_date}~{end_date}",
        **result,
    }
    print(json.dumps(output, ensure_ascii=False, indent=indent, default=str))


if __name__ == "__main__":
    main()
