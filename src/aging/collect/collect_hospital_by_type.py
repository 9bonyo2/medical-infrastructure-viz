"""
[고령화 파트] 시도별 병원·의원 수(의료기관 종류별) 수집 — 요양병원 시계열 확보용

출처: 공공데이터포털(data.go.kr) - 보건복지부_병원 및 의원 수_의료기관 종류별_시도별
데이터셋 페이지: https://www.data.go.kr/data/15127855/fileData.do
수집 방법: 원본 첨부파일 CSV 직접 다운로드 (로그인/서비스키 불필요, 정적 파일)
포함 항목: 연도(2015~2024), 시도별
  - 병의원: 종합병원, 요양병원 <- "고령인구 10만명당 요양병원 수" 지표로 사용, 일반병원, 의원
  - 특수병원: 결핵, 한센, 정신
  - 치과병 의원, 한방병 의원, 부속의원, 조산원

collect_kosis_api.py(KOSIS Open API, DT_MIRE01)로 받은 2024년 4분기 요양병원 수(전국 1,342개소,
시도별 수치 포함)와 교차검증한 결과 완전히 일치함을 확인했다(같은 원천기관: 건강보험심사평가원).
KOSIS 쪽은 2016년 1분기부터만 조회 가능한 반면, 이 데이터는 **2015년부터** 있어 연도별 시계열
분석(2015~2024)에는 이 출처를 사용한다.

실행: python -m src.aging.collect.collect_hospital_by_type
"""
import time
from io import BytesIO

import pandas as pd
import requests

from src.aging.collect.common import RAW_DIR, get_logger, standardize_sido

logger = get_logger(__name__)

# data.go.kr 파일데이터 상세 페이지의 실제 다운로드 API(/tcs/dss/selectFileDataDownload.do)가
# 반환하는 atchFileId로 직접 다운로드한다 (페이지에 노출된 og:image용 atchFileId와는 다르므로 주의).
FILE_URL = (
    "https://www.data.go.kr/cmm/cmm/fileDownload.do"
    "?atchFileId=FILE_000000003632294&fileDetailSn=1&insertDataPrcus=N"
)
SOURCE_PAGE = "https://www.data.go.kr/data/15127855/fileData.do"
OUTPUT_PATH = RAW_DIR / "hospital_by_type_raw.csv"

COLUMN_NAMES = [
    "연도", "시도",
    "종합병원", "요양병원", "일반병원", "의원",
    "결핵병원", "한센병원", "정신병원",
    "치과병원", "치과의원", "한방병원", "한의원",
    "부속의원", "조산원",
]


def collect(timeout: int = 20, max_retries: int = 3) -> pd.DataFrame:
    """data.go.kr에서 의료기관 종류별 시도별 현황 CSV를 내려받아 DataFrame으로 반환한다."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": SOURCE_PAGE,
    }

    last_err = None
    for attempt in range(1, max_retries + 1):
        started = time.time()
        try:
            logger.info(f"[시도 {attempt}/{max_retries}] 병원·의원 현황 다운로드 시작: {FILE_URL}")
            resp = requests.get(FILE_URL, headers=headers, timeout=timeout)
            resp.raise_for_status()
            # 원본 파일은 EUC-KR(CP949) 인코딩으로 제공됨
            df = pd.read_csv(BytesIO(resp.content), encoding="cp949")
            df.columns = COLUMN_NAMES
            elapsed = time.time() - started
            logger.info(
                f"수집 성공 - 행 수: {len(df)}, 열 수: {len(df.columns)}, 소요시간: {elapsed:.2f}s"
            )
            return df
        except Exception as e:  # noqa: BLE001
            last_err = e
            logger.warning(f"수집 실패(시도 {attempt}/{max_retries}): {e}")
            time.sleep(1.5 * attempt)

    logger.error(f"병원·의원 현황 수집 최종 실패: {last_err}")
    raise RuntimeError(f"병원·의원 현황 데이터 수집 실패: {last_err}")


def save(df: pd.DataFrame) -> None:
    df = df.copy()
    df["시도"] = df["시도"].apply(standardize_sido)
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    years = f"{df['연도'].min()}~{df['연도'].max()}"
    logger.info(f"저장 완료: {OUTPUT_PATH} ({len(df)}행, {years}년)")


def main() -> None:
    df = collect()
    save(df)


if __name__ == "__main__":
    main()
