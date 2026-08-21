"""
[고령화 파트] 시도별 고령인구(65세 이상) 및 고령인구비율 — 2015~2024 연도별 시계열 수집

collect_aging_population.py의 collect()를 연도별로 반복 호출해 12월 스냅샷을 모은다
(노인복지시설 시계열·병원 시계열과 동일하게 매년 12월 기준으로 맞춰 비교 가능하게 함).

주의: 2025~2026년 사이 일부 시도 행정구역 통합(광주-전남 등)이 있어 2015~2024는
통합 이전 17개 시도 체계로 안정적으로 비교 가능하다(그래서 조회 범위를 2024년까지로 한정).

실행: python -m src.aging.collect.collect_aging_population_timeseries [--start 2015 --end 2024]
"""
import argparse
import time

import pandas as pd

from src.aging.collect.collect_aging_population import collect
from src.aging.collect.common import RAW_DIR, get_logger

logger = get_logger(__name__)

OUTPUT_PATH = RAW_DIR / "aging_population_timeseries_raw.csv"


def collect_range(start_year: int, end_year: int, month: str = "12") -> pd.DataFrame:
    frames = []
    for year in range(start_year, end_year + 1):
        logger.info(f"=== {year}년 {month}월 고령인구 통계 수집 시작 ===")
        df = collect(str(year), month)
        df["연도"] = year
        frames.append(df)
        time.sleep(1)  # 연속 요청 사이 최소 간격
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="시도별 고령인구 통계 연도별(2015~2024) 스크래핑")
    parser.add_argument("--start", type=int, default=2015)
    parser.add_argument("--end", type=int, default=2024)
    parser.add_argument("--month", default="12")
    args = parser.parse_args()

    df = collect_range(args.start, args.end, args.month)
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    logger.info(f"저장 완료: {OUTPUT_PATH} ({len(df)}행, {args.start}~{args.end}년)")


if __name__ == "__main__":
    main()
