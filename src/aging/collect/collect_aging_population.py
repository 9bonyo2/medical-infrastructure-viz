"""
[고령화 파트] 시도별 고령인구(65세 이상) 및 고령인구비율 웹 스크래핑

출처: 행정안전부 주민등록인구통계 (jumin.mois.go.kr) - 연령별 인구현황(월간)
페이지: https://jumin.mois.go.kr/ageStatMonth.do
수집 방법: requests로 검색조건(5세 단위 연령구간, 시도 단위, 조회월)을 POST 전송한 뒤
          응답 HTML의 통계표(id="contextTable")를 BeautifulSoup으로 파싱
          -> KOSIS 통계표는 SSO 로그인 세션이 필요해 정적 스크래핑이 불가능하여
             (statHtml 접속 시 302 로그인 리다이렉트 확인됨) 동일 기관(행정안전부) 산하의
             로그인 불필요 공개 통계 페이지를 사용한다. KOSIS 공식 지표는
             collect_kosis_api.py(Open API)로 보조 수집한다.

수집 항목: 시도별 총인구수, 65세 이상 인구수(5세 단위 연령구간 합산), 고령인구비율(%)

실행: python -m src.collect.collect_aging_population [--year 2026 --month 07]
"""
import argparse
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup

from src.aging.collect.common import RAW_DIR, get_logger, standardize_sido

logger = get_logger(__name__)

URL = "https://jumin.mois.go.kr/ageStatMonth.do"
OUTPUT_PATH = RAW_DIR / "aging_population_raw.csv"

# 연령구간(5세 단위) 라벨 순서 - contextTable의 "계" 그룹 헤더 순서와 동일
AGE_BAND_LABELS = [
    "0-4세", "5-9세", "10-14세", "15-19세", "20-24세", "25-29세", "30-34세",
    "35-39세", "40-44세", "45-49세", "50-54세", "55-59세", "60-64세",
    "65-69세", "70-74세", "75-79세", "80-84세", "85-89세", "90-94세", "95-99세",
    "100세 이상",
]
ELDERLY_FROM_INDEX = AGE_BAND_LABELS.index("65-69세")  # 이 인덱스부터 끝까지가 65세 이상


def _build_payload(year: str, month: str) -> dict:
    return {
        "sltOrgType": "1",       # 1: 시도 단위 조회
        "sltOrgLvl1": "A",       # A: 전체 시도
        "sltOrgLvl2": "",
        "gender": "sum",
        "sum": "sum",
        "sltUndefType": "",
        "searchYearStart": year,
        "searchMonthStart": month,
        "searchYearEnd": year,
        "searchMonthEnd": month,
        "sltOrderType": "1",
        "sltOrderValue": "ASC",
        "sltArgTypes": "5",      # 5세 단위 연령구간 (65세 이상을 정확히 합산하기 위함)
        "sltArgTypeA": "0",
        "sltArgTypeB": "100",
        "searchYearMonth": "month",
    }


def _parse_number(text: str) -> int:
    return int(text.replace(",", "").strip() or 0)


def collect(year: str, month: str, timeout: int = 20, max_retries: int = 3) -> pd.DataFrame:
    """행정안전부 주민등록인구통계에서 시도별 고령인구 현황을 스크래핑한다."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    payload = _build_payload(year, month)

    last_err = None
    html = None
    for attempt in range(1, max_retries + 1):
        started = time.time()
        try:
            logger.info(f"[시도 {attempt}/{max_retries}] {year}년 {month}월 고령인구 통계 요청")
            resp = requests.post(URL, data=payload, headers=headers, timeout=timeout)
            resp.raise_for_status()
            resp.encoding = "utf-8"
            html = resp.text
            elapsed = time.time() - started
            logger.info(f"응답 수신 성공, 소요시간: {elapsed:.2f}s")
            break
        except Exception as e:  # noqa: BLE001
            last_err = e
            logger.warning(f"요청 실패(시도 {attempt}/{max_retries}): {e}")
            time.sleep(1.5 * attempt)

    if html is None:
        logger.error(f"고령인구 통계 수집 최종 실패: {last_err}")
        raise RuntimeError(f"고령인구 통계 수집 실패: {last_err}")

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", id="contextTable")
    if table is None:
        raise RuntimeError("통계표(contextTable)를 찾을 수 없습니다. 페이지 구조가 변경되었을 수 있습니다.")

    tbody = table.find("tbody")
    rows = tbody.find_all("tr")

    records = []
    for row in rows:
        cells = [c.get_text(strip=True) for c in row.find_all(["th", "td"])]
        if len(cells) < 3 + len(AGE_BAND_LABELS):
            continue
        org_code, org_name = cells[0], cells[1]
        if org_code == "0000000000":
            continue  # 전국 합계 행은 제외 (시도별 데이터만 사용)

        total_pop = _parse_number(cells[2])
        age_band_values = [_parse_number(v) for v in cells[4 : 4 + len(AGE_BAND_LABELS)]]
        elderly_pop = sum(age_band_values[ELDERLY_FROM_INDEX:])
        aging_rate = round(elderly_pop / total_pop * 100, 2) if total_pop else None

        records.append(
            {
                "시도_원본": org_name,
                "시도": standardize_sido(org_name),
                "기준연월": f"{year}-{month}",
                "총인구수": total_pop,
                "고령인구수_65세이상": elderly_pop,
                "고령인구비율": aging_rate,
            }
        )

    df = pd.DataFrame(records)
    logger.info(f"파싱 완료 - 시도 수: {len(df)}행 (기대값 17행)")
    if len(df) != 17:
        logger.warning(f"예상 시도 수(17)와 다릅니다: {len(df)}행. 페이지 구조 확인 필요.")
    return df


def save(df: pd.DataFrame) -> None:
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    logger.info(f"저장 완료: {OUTPUT_PATH} ({len(df)}행)")


def main() -> None:
    parser = argparse.ArgumentParser(description="시도별 고령인구 통계 스크래핑")
    # 기본값: 2024-12. 노인복지시설 데이터(collect_senior_facilities)의 최신 연도가 2024년이라
    # 두 데이터를 같은 시점 기준으로 맞추기 위해 기본 조회월을 2024-12로 둔다.
    # 주의: 2025~2026년 사이 일부 시도 행정구역 통합(예: 광주-전남 통합특별시)이 발생해
    # 최신월을 그대로 쓰면 노인복지시설 데이터(2024년 기준, 통합 이전 17개 시도 체계)와
    # 시도 단위가 어긋난다. 최신 시점 데이터가 필요하면 --year/--month로 직접 지정할 것.
    parser.add_argument("--year", default="2024")
    parser.add_argument("--month", default="12")
    args = parser.parse_args()

    df = collect(args.year, args.month)
    save(df)


if __name__ == "__main__":
    main()
