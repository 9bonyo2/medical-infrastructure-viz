"""
[고령화 파트] 전처리

입력:
  - data/raw/senior_welfare_facilities_raw.csv (2015~2024, 시도별 노인복지시설 현황)
  - data/raw/aging_population_raw.csv          (2024-12 기준, 시도별 고령인구)

전처리 원칙 (팀 기획서 "3. 데이터 분석 방법론 > 전처리 계획" 준수):
  1. 시도명 표준화: "서울 Seoul" -> "서울특별시" 등 (common.standardize_sido)
  2. 수치형 변환 및 단위 통일: 콤마 제거·정수/실수 변환, 인구 10만명당 비율 지표 생성
  3. 결측치 처리: 시설 수 결측(NaN)은 "시설 없음(0)"으로 대체하고 로그 기록.
     단, 시도 자체가 통째로 빠진 경우는 대체하지 않고 제외 후 경고.
  4. 중복 제거 기준: (시도 + 연도) 조합 기준 중복 행 제거
  5. 연도 통일: 두 데이터의 최신 공통 연도(기본 2024년)로 스냅샷을 맞춰 병합
     (업무보고서 리스크 대응계획 "데이터 연도 불일치 -> 2024년 단단년도 통일" 반영)

출력:
  - data/processed/senior_facilities_timeseries.csv : 노인복지시설 연도별 추이(2015~2024, 시도별)
  - data/processed/aging_master.csv                 : 상관관계 분석용 최신연도 마스터 테이블
                                                        (시도, 총인구수, 고령인구수, 고령인구비율,
                                                         노인복지관수, 인구10만명당 노인복지관수 등)

실행: python -m src.preprocess.preprocess_aging
"""
import argparse

import pandas as pd

from src.collect.common import PROCESSED_DIR, RAW_DIR, get_logger, standardize_sido

logger = get_logger(__name__)

FACILITY_RAW = RAW_DIR / "senior_welfare_facilities_raw.csv"
POPULATION_RAW = RAW_DIR / "aging_population_raw.csv"

TIMESERIES_OUT = PROCESSED_DIR / "senior_facilities_timeseries.csv"
MASTER_OUT = PROCESSED_DIR / "aging_master.csv"

# 결측치 대체 시 0으로 채워도 되는 "시설/서비스 수" 계열 컬럼 (없으면 실제로 0곳인 경우가 대부분)
FACILITY_COUNT_COLS = [
    "노인여가복지시설_경로당", "노인여가복지시설_복지관",
    "재가노인복지시설_방문요양서비스_시설수", "재가노인복지시설_주야간보호서비스_시설수",
    "재가노인복지시설_단기보호서비스_시설수", "재가노인복지시설_방문목욕서비스_시설수",
    "재가노인복지시설_방문간호서비스_시설수", "재가노인복지시설_재가노인지원서비스_시설수",
    "노인보호전문기관_시설수", "노인일자리지원기관_시설수",
]


def load_facility_timeseries() -> pd.DataFrame:
    df = pd.read_csv(FACILITY_RAW)
    df["시도"] = df["시도"].apply(standardize_sido)

    before = len(df)
    df = df.drop_duplicates(subset=["시도", "연도"], keep="last")
    if len(df) != before:
        logger.info(f"중복 제거: {before - len(df)}건 제거 (시도+연도 기준)")

    missing_before = df[FACILITY_COUNT_COLS].isna().sum().sum()
    if missing_before:
        logger.info(f"결측치 {missing_before}건을 0으로 대체 (시설 없음으로 간주)")
    df[FACILITY_COUNT_COLS] = df[FACILITY_COUNT_COLS].fillna(0).astype(int)

    df["노인복지시설_합계"] = df[FACILITY_COUNT_COLS].sum(axis=1)
    return df


def load_population(latest_year: int) -> pd.DataFrame:
    df = pd.read_csv(POPULATION_RAW)
    df["시도"] = df["시도"].apply(standardize_sido)

    missing = df[df[["총인구수", "고령인구수_65세이상"]].isna().any(axis=1)]
    if len(missing):
        logger.warning(f"인구 데이터 결측 시도 {len(missing)}건 제외: {missing['시도'].tolist()}")
        df = df.dropna(subset=["총인구수", "고령인구수_65세이상"])

    df = df.drop_duplicates(subset=["시도"], keep="last")
    df["기준연도"] = latest_year
    return df


def build_master(facility_ts: pd.DataFrame, population: pd.DataFrame, latest_year: int) -> pd.DataFrame:
    facility_latest = facility_ts[facility_ts["연도"] == latest_year].copy()

    missing_sido = set(population["시도"]) ^ set(facility_latest["시도"])
    if missing_sido:
        logger.warning(f"두 데이터 간 시도 불일치(교집합 제외): {missing_sido}")

    master = population.merge(
        facility_latest[["시도", "노인여가복지시설_경로당", "노인여가복지시설_복지관", "노인복지시설_합계"]],
        on="시도",
        how="inner",
    ).rename(columns={"노인여가복지시설_복지관": "노인복지관수", "노인여가복지시설_경로당": "경로당수"})

    # 단위 통일 및 파생 지표 (인구 10만명당 비율로 지역 규모 차이를 보정)
    master["인구10만명당_노인복지관수"] = round(master["노인복지관수"] / master["총인구수"] * 100_000, 2)
    master["고령인구1만명당_노인복지관수"] = round(
        master["노인복지관수"] / master["고령인구수_65세이상"] * 10_000, 2
    )
    master["인구10만명당_경로당수"] = round(master["경로당수"] / master["총인구수"] * 100_000, 2)

    cols = [
        "시도", "기준연도", "총인구수", "고령인구수_65세이상", "고령인구비율",
        "노인복지관수", "경로당수", "노인복지시설_합계",
        "인구10만명당_노인복지관수", "고령인구1만명당_노인복지관수", "인구10만명당_경로당수",
    ]
    master = master[cols].sort_values("고령인구비율", ascending=False).reset_index(drop=True)
    return master


def main() -> None:
    parser = argparse.ArgumentParser(description="고령화 파트 데이터 전처리")
    parser.add_argument("--year", type=int, default=2024, help="분석 기준연도(두 데이터 공통 스냅샷)")
    args = parser.parse_args()

    logger.info("노인복지시설 시계열 데이터 전처리 시작")
    facility_ts = load_facility_timeseries()
    facility_ts.to_csv(TIMESERIES_OUT, index=False, encoding="utf-8-sig")
    logger.info(f"저장 완료: {TIMESERIES_OUT} ({len(facility_ts)}행)")

    logger.info("고령인구 데이터 전처리 시작")
    population = load_population(args.year)

    logger.info(f"{args.year}년 기준 마스터 테이블 생성")
    master = build_master(facility_ts, population, args.year)
    master.to_csv(MASTER_OUT, index=False, encoding="utf-8-sig")
    logger.info(f"저장 완료: {MASTER_OUT} ({len(master)}행)")


if __name__ == "__main__":
    main()
