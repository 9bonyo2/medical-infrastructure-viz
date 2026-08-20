"""
[고령화 파트] 시도별 노인복지시설 현황 수집

출처: 공공데이터포털(data.go.kr) - 보건복지부_노인복지 이용시설 현황_시설 종류별_시도별
데이터셋 페이지: https://www.data.go.kr/data/15127876/fileData.do
수집 방법: 원본 첨부파일 CSV 직접 다운로드 (로그인/서비스키 불필요, 정적 파일)
포함 항목: 시도, 연도(2015~2024)별
  - 노인여가복지시설: 경로당 수, 노인복지관 수  <- "노인복지센터 개수" 지표로 사용
  - 재가노인복지시설: 방문요양/주야간보호/단기보호/방문목욕/방문간호/재가노인지원 서비스별 시설수·정원·현원
  - 노인보호전문기관 수, 노인일자리지원기관 수

실행: python -m src.collect.collect_senior_facilities
"""
import time
from io import BytesIO

import pandas as pd
import requests

from src.aging.collect.common import RAW_DIR, get_logger

logger = get_logger(__name__)

# data.go.kr 파일데이터 상세 페이지에서 확인한 첨부파일 직접 다운로드 URL
# (파일데이터는 공공데이터포털 정책상 로그인 없이 다운로드 가능)
FILE_URL = (
    "https://www.data.go.kr/cmm/cmm/fileDownload.do"
    "?atchFileId=FILE_000000003633129&fileDetailSn=1&insertDataPrcus=N"
)
SOURCE_PAGE = "https://www.data.go.kr/data/15127876/fileData.do"
OUTPUT_PATH = RAW_DIR / "senior_welfare_facilities_raw.csv"


def collect(timeout: int = 20, max_retries: int = 3) -> pd.DataFrame:
    """data.go.kr에서 노인복지시설 현황 CSV를 내려받아 DataFrame으로 반환한다."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    last_err = None
    for attempt in range(1, max_retries + 1):
        started = time.time()
        try:
            logger.info(f"[시도 {attempt}/{max_retries}] 노인복지시설 현황 다운로드 시작: {FILE_URL}")
            resp = requests.get(FILE_URL, headers=headers, timeout=timeout)
            resp.raise_for_status()
            # 원본 파일은 EUC-KR(CP949) 인코딩으로 제공됨
            df = pd.read_csv(BytesIO(resp.content), encoding="cp949")
            elapsed = time.time() - started
            logger.info(
                f"수집 성공 - 행 수: {len(df)}, 열 수: {len(df.columns)}, 소요시간: {elapsed:.2f}s"
            )
            return df
        except Exception as e:  # noqa: BLE001
            last_err = e
            logger.warning(f"수집 실패(시도 {attempt}/{max_retries}): {e}")
            time.sleep(1.5 * attempt)

    logger.error(f"노인복지시설 현황 수집 최종 실패: {last_err}")
    raise RuntimeError(f"노인복지시설 현황 데이터 수집 실패: {last_err}")


def save(df: pd.DataFrame) -> None:
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    logger.info(f"저장 완료: {OUTPUT_PATH} ({len(df)}행)")


def main() -> None:
    df = collect()
    save(df)


if __name__ == "__main__":
    main()
