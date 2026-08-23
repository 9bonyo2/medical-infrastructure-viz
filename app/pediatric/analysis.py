import pandas as pd

from pediatric.config import ANALYSIS_END_YEAR, ANALYSIS_START_YEAR


def add_supply_capacity_score(
    data: pd.DataFrame,
    clinic_metric: str,
    child_metric: str,
) -> pd.DataFrame:
    """두 지표의 백분위에 40:60 가중치를 적용해 공급역량 점수를 계산한다."""
    scored_data = data.copy()
    scored_data["의원당백분위"] = scored_data[clinic_metric].rank(pct=True)
    scored_data["아동대비백분위"] = scored_data[child_metric].rank(pct=True)
    scored_data["공급역량점수"] = (
        scored_data["의원당백분위"] * 0.4
        + scored_data["아동대비백분위"] * 0.6
    ) * 100
    return scored_data


def build_selected_year_supply_summary(
    data: pd.DataFrame,
    selected_year: int,
) -> tuple[float, float, pd.DataFrame] | None:
    """선택 연도의 중앙값과 소아과 의료취약 지역 TOP 5를 계산한다."""
    scored_data = build_selected_year_supply_scores(data, selected_year)
    if scored_data is None:
        return None

    clinic_median = scored_data["의원1개당전문의수"].median()
    child_median = scored_data["아동1만명당전문의수"].median()
    selected_vulnerable_top5 = scored_data.head(5).loc[:, ["지역"]].copy()
    selected_vulnerable_top5.index = selected_vulnerable_top5.index + 1
    selected_vulnerable_top5.index.name = "순위"

    return clinic_median, child_median, selected_vulnerable_top5


def build_selected_year_supply_scores(
    data: pd.DataFrame,
    selected_year: int,
) -> pd.DataFrame | None:
    """선택 연도의 모든 지역 공급역량 점수를 의료취약 순서로 계산한다."""
    selected_data = data.loc[
        data["시점"] == selected_year,
        ["지역", "의원1개당전문의수", "아동1만명당전문의수"],
    ].dropna().drop_duplicates("지역")

    if selected_data.empty:
        return None

    scored_data = add_supply_capacity_score(
        selected_data,
        "의원1개당전문의수",
        "아동1만명당전문의수",
    )
    return (
        scored_data.sort_values("공급역량점수", ascending=True)
        .reset_index(drop=True)
    )


def build_period_vulnerable_top5(data: pd.DataFrame) -> pd.DataFrame | None:
    """전체 분석 기간의 지역별 평균으로 의료취약 지역 TOP 5를 계산한다."""
    scored_average = build_period_supply_scores(data)
    if scored_average is None:
        return None

    vulnerable_top5 = scored_average.head(5)[["지역"]].copy()
    vulnerable_top5.index = vulnerable_top5.index + 1
    vulnerable_top5.index.name = "순위"

    return vulnerable_top5


def build_period_supply_scores(data: pd.DataFrame) -> pd.DataFrame | None:
    """전체 분석 기간의 지역별 평균 공급역량 점수를 취약 순으로 계산한다."""
    period_data = data.loc[
        data["시점"].between(ANALYSIS_START_YEAR, ANALYSIS_END_YEAR),
        ["시점", "지역", "의원1개당전문의수", "아동1만명당전문의수"],
    ].dropna().drop_duplicates(["시점", "지역"])

    expected_year_count = ANALYSIS_END_YEAR - ANALYSIS_START_YEAR + 1
    analysis_years = sorted(period_data["시점"].unique())
    if len(analysis_years) < expected_year_count:
        return None

    region_average = (
        period_data.groupby("지역")
        .agg(
            평균의원당전문의=("의원1개당전문의수", "mean"),
            평균아동대비전문의=("아동1만명당전문의수", "mean"),
            분석연도수=("시점", "nunique"),
        )
        .reset_index()
    )
    region_average = region_average[
        region_average["분석연도수"] == expected_year_count
    ].copy()

    if region_average.empty:
        return None

    scored_average = add_supply_capacity_score(
        region_average,
        "평균의원당전문의",
        "평균아동대비전문의",
    )
    return (
        scored_average.sort_values("공급역량점수", ascending=True)
        .reset_index(drop=True)
    )