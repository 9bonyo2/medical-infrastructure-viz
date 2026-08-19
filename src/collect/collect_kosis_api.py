"""
[고령화 파트] KOSIS Open API를 통한 공식 고령인구 지표 수집

collect_aging_population.py(행안부 웹 스크래핑) 결과를 KOSIS 공식 통계와 교차검증하고,
KOSIS가 직접 제공하는 "노인 천명당 노인여가복지시설수" 지표까지 함께 확보한다.

*** 실제로 사용한 테이블 (KOSIS Open API 통합검색으로 확인/검증 완료) ***
  1) DT_1YL20631 (orgId=101, e-지방지표) : 고령인구비율(시도/시/군/구)
     - 2024년 시도별 수치를 jumin.mois.go.kr 스크래핑 결과와 대조한 결과 완전히 일치함
       (예: 서울 65세이상인구 1,813,648명 / 전체인구 9,331,828명 / 19.4% 로 동일)
  2) DT_1YL20961 (orgId=101, e-지방지표) : 노인 천명당 노인여가복지시설수(시도/시/군/구)
     - 경로당+노인복지관 합계를 60세이상인구 기준으로 정규화한 KOSIS 공식 지표
     - 우리가 preprocess_aging.py에서 직접 계산한 "인구10만명당 노인복지관수"와 같은 취지의
       공식 벤치마크로 사용 가능

  ※ DT_117N_B00003(보건복지부 노인복지시설현황)은 Open API로 지역(시도) 분류 축을 조회하는
    파라미터 조합을 찾지 못했다(objL2=ALL 요청 시 "err":"21" 응답). 이 데이터는 이미
    collect_senior_facilities.py(data.go.kr 원본 파일)로 더 상세하게(시설유형별) 확보되어 있어
    Open API로는 별도 재수집하지 않는다.

*** 사용 전 준비 ***
1. KOSIS Open API 인증키 발급: https://kosis.kr/openapi/index/index.jsp (로그인 > 인증키 신청)
2. 환경변수로 설정 (키 값을 코드에 직접 넣지 말 것)
   PowerShell:  $env:KOSIS_API_KEY = "발급받은키"
   bash:        export KOSIS_API_KEY="발급받은키"

실행: python -m src.collect.collect_kosis_api [--year 2024]
"""
import argparse
import os
import time

import pandas as pd
import requests

from src.collect.common import RAW_DIR, get_logger, standardize_sido

logger = get_logger(__name__)

API_URL = "https://kosis.kr/openapi/Param/statisticsParameterData.do"

AGING_RATIO_OUT = RAW_DIR / "kosis_aging_ratio_raw.csv"
FACILITY_DENSITY_OUT = RAW_DIR / "kosis_facility_density_raw.csv"

# 시도(2단계 행정구역) 수준 행만 골라내기 위한 코드 집합.
# 대부분 2자리 코드(11=서울 ...)이나, 2025~2026년 광주·전남 행정구역 통합 반영으로
# 광주(1224)·전남(1236)만 4자리 상위코드로 분류되어 있어 별도로 포함한다.
SIDO_CODES = {
    "11", "21", "22", "23", "25", "26", "29",
    "31", "32", "33", "34", "35", "37", "38", "39",
    "1224", "1236",
}

TABLES = {
    "aging_ratio": {"orgId": "101", "tblId": "DT_1YL20631"},
    "facility_density": {"orgId": "101", "tblId": "DT_1YL20961"},
}


def _fetch(table_key: str, year: str, timeout: int = 20, max_retries: int = 3) -> pd.DataFrame:
    api_key = os.environ.get("KOSIS_API_KEY")
    if not api_key:
        raise RuntimeError(
            "환경변수 KOSIS_API_KEY가 설정되지 않았습니다. "
            "KOSIS Open API 인증키를 발급받아 설정한 뒤 다시 실행하세요."
        )

    org_tbl = TABLES[table_key]
    params = {
        "method": "getList",
        "apiKey": api_key,
        "itmId": "ALL",
        "objL1": "ALL",
        "objL2": "", "objL3": "", "objL4": "",
        "format": "json",
        "jsonVD": "Y",
        "prdSe": "Y",
        "startPrdDe": year,
        "endPrdDe": year,
        **org_tbl,
    }

    last_err = None
    for attempt in range(1, max_retries + 1):
        started = time.time()
        try:
            logger.info(f"[시도 {attempt}/{max_retries}] KOSIS API 요청: {org_tbl['tblId']} ({year}년)")
            resp = requests.get(API_URL, params=params, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()

            if isinstance(data, dict):
                raise RuntimeError(f"KOSIS API 오류: {data.get('errMsg', data)}")

            df = pd.DataFrame(data)
            elapsed = time.time() - started
            logger.info(f"수집 성공 - 원본 행 수: {len(df)}, 소요시간: {elapsed:.2f}s")
            return df
        except Exception as e:  # noqa: BLE001
            last_err = e
            logger.warning(f"수집 실패(시도 {attempt}/{max_retries}): {e}")
            time.sleep(1.5 * attempt)

    logger.error(f"KOSIS API 수집 최종 실패({table_key}): {last_err}")
    raise RuntimeError(f"KOSIS API 수집 실패({table_key}): {last_err}")


def _to_sido_wide(df: pd.DataFrame) -> pd.DataFrame:
    """시도 레벨 행만 필터링 후 ITM_NM(지표명)을 컬럼으로 피벗."""
    sido_df = df[df["C1"].isin(SIDO_CODES)].copy()
    sido_df["시도"] = sido_df["C1_NM"].apply(standardize_sido)
    sido_df["DT"] = pd.to_numeric(sido_df["DT"], errors="coerce")
    # ITM_NM에 <br> 태그가 섞여 있어 정리
    sido_df["지표명"] = sido_df["ITM_NM"].str.replace("<br>", "", regex=False).str.replace("＜br＞", "", regex=False)

    wide = sido_df.pivot_table(index="시도", columns="지표명", values="DT", aggfunc="first").reset_index()
    return wide


def main() -> None:
    parser = argparse.ArgumentParser(description="KOSIS Open API 고령인구 지표 수집")
    parser.add_argument("--year", default="2024")
    args = parser.parse_args()

    aging_raw = _fetch("aging_ratio", args.year)
    aging_wide = _to_sido_wide(aging_raw)
    aging_wide.to_csv(AGING_RATIO_OUT, index=False, encoding="utf-8-sig")
    logger.info(f"저장 완료: {AGING_RATIO_OUT} ({len(aging_wide)}행, {list(aging_wide.columns)})")

    density_raw = _fetch("facility_density", args.year)
    density_wide = _to_sido_wide(density_raw)
    density_wide.to_csv(FACILITY_DENSITY_OUT, index=False, encoding="utf-8-sig")
    logger.info(f"저장 완료: {FACILITY_DENSITY_OUT} ({len(density_wide)}행, {list(density_wide.columns)})")


if __name__ == "__main__":
    main()
