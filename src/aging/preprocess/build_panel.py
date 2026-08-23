"""
[고령화 파트] 2015~2024 연도별 패널 마스터 테이블 생성

기존 aging_master.csv(2024년 단일연도 횡단면)와 별개로, 연도별 상관계수 추이를 보기 위해
(시도 x 연도) 패널 데이터를 만든다.

입력:
  - data/aging/processed/senior_facilities_timeseries.csv (2015~2024, 노인복지시설_합계)
  - data/aging/raw/hospital_by_type_raw.csv               (2015~2024, 요양병원)
  - data/aging/raw/aging_population_timeseries_raw.csv    (2015~2024, 고령인구수_65세이상 등)

출력:
  - data/aging/processed/aging_panel_2015_2024.csv
    (시도, 연도, 고령인구비율, 고령인구10만명당_노인복지시설수, 고령인구10만명당_요양병원수 등)

실행: python -m src.aging.preprocess.build_panel
"""
import pandas as pd

from src.aging.collect.common import PROCESSED_DIR, RAW_DIR, get_logger, standardize_sido

logger = get_logger(__name__)

FACILITY_TS = PROCESSED_DIR / "senior_facilities_timeseries.csv"
HOSPITAL_RAW = RAW_DIR / "hospital_by_type_raw.csv"
POPULATION_TS_RAW = RAW_DIR / "aging_population_timeseries_raw.csv"
PANEL_OUT = PROCESSED_DIR / "aging_panel_2015_2024.csv"


def build_panel(start_year: int = 2015, end_year: int = 2024) -> pd.DataFrame:
    facility = pd.read_csv(FACILITY_TS)[["시도", "연도", "노인복지시설_합계"]]

    hospital = pd.read_csv(HOSPITAL_RAW)[["시도", "연도", "요양병원"]].rename(
        columns={"요양병원": "요양병원수"}
    )

    population = pd.read_csv(POPULATION_TS_RAW)
    population["시도"] = population["시도"].apply(standardize_sido)
    population = population[["시도", "연도", "총인구수", "고령인구수_65세이상", "고령인구비율"]]

    panel = population.merge(facility, on=["시도", "연도"], how="inner").merge(
        hospital, on=["시도", "연도"], how="inner"
    )

    missing_years = set(range(start_year, end_year + 1)) - set(panel["연도"].unique())
    if missing_years:
        logger.warning(f"패널에서 누락된 연도: {sorted(missing_years)}")

    panel = panel[(panel["연도"] >= start_year) & (panel["연도"] <= end_year)]

    panel["고령인구10만명당_노인복지시설수"] = round(
        panel["노인복지시설_합계"] / panel["고령인구수_65세이상"] * 100_000, 2
    )
    panel["고령인구10만명당_요양병원수"] = round(
        panel["요양병원수"] / panel["고령인구수_65세이상"] * 100_000, 2
    )

    cols = [
        "시도", "연도", "총인구수", "고령인구수_65세이상", "고령인구비율",
        "노인복지시설_합계", "요양병원수",
        "고령인구10만명당_노인복지시설수", "고령인구10만명당_요양병원수",
    ]
    return panel[cols].sort_values(["연도", "고령인구비율"], ascending=[True, False]).reset_index(drop=True)


def main() -> None:
    panel = build_panel()
    panel.to_csv(PANEL_OUT, index=False, encoding="utf-8-sig")
    years = f"{panel['연도'].min()}~{panel['연도'].max()}"
    logger.info(f"저장 완료: {PANEL_OUT} ({len(panel)}행, {years}년, 시도 {panel['시도'].nunique()}개)")


if __name__ == "__main__":
    main()
