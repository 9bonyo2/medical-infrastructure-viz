import pandas as pd
import streamlit as st

from pediatric.analysis import (
    build_period_supply_scores,
    build_period_vulnerable_top5,
    build_selected_year_supply_scores,
    build_selected_year_supply_summary,
)
from pediatric.config import ANALYSIS_END_YEAR, ANALYSIS_START_YEAR, METRIC_LABELS


CLINIC_METRIC = "의원1개당전문의수"
CHILD_METRIC = "아동1만명당전문의수"


def _show_insight_card(title: str, body: str) -> None:
    """테두리가 있는 짧은 핵심 인사이트 카드를 표시한다."""
    with st.container(border=True):
        st.markdown(f"💡 **{title}**")
        st.markdown(body)


def _build_change_range(
    data: pd.DataFrame,
    selected_regions: list[str],
    metric: str,
) -> pd.DataFrame:
    """선택 지역별 분석 기간 내 최댓값-최솟값을 계산한다."""
    metric_data = data.loc[
        data["지역"].isin(selected_regions),
        ["시점", "지역", metric],
    ].dropna()
    summary = (
        metric_data.groupby("지역")[metric]
        .agg(최솟값="min", 최댓값="max", 데이터수="count")
        .reset_index()
    )
    summary = summary[summary["데이터수"] >= 2].copy()
    summary["변화폭"] = summary["최댓값"] - summary["최솟값"]
    return summary


def show_global_kpis(data: pd.DataFrame, selected_year: int) -> None:
    """선택 연도와 전체 기간의 공급 우세·취약 1위 지역을 표시한다."""
    selected_scores = build_selected_year_supply_scores(data, selected_year)
    period_scores = build_period_supply_scores(data)

    selected_best = "계산 불가"
    selected_vulnerable = "계산 불가"
    period_best = "계산 불가"
    period_vulnerable = "계산 불가"

    if selected_scores is not None and not selected_scores.empty:
        selected_best = str(selected_scores.iloc[-1]["지역"])
        selected_vulnerable = str(selected_scores.iloc[0]["지역"])
    if period_scores is not None and not period_scores.empty:
        period_best = str(period_scores.iloc[-1]["지역"])
        period_vulnerable = str(period_scores.iloc[0]["지역"])

    year_column, region_column, clinic_column, child_column = st.columns(4)
    with year_column:
        with st.container(border=True, key="global-kpi-year-card"):
            st.metric(
                f"{selected_year}년 소아과 공급 우세지역 🏥",
                selected_best,
            )
    with region_column:
        with st.container(border=True, key="global-kpi-region-card"):
            st.metric(
                f"{selected_year}년 소아과 공급 취약지역 ⚠️",
                selected_vulnerable,
            )
    with clinic_column:
        with st.container(border=True, key="global-kpi-clinic-card"):
            st.metric(
                "10년간 소아과 공급 우세지역 📈",
                period_best,
            )
    with child_column:
        with st.container(border=True, key="global-kpi-child-card"):
            st.metric(
                "10년간 소아과 공급 취약지역 📉",
                period_vulnerable,
            )


def show_supply_capacity_summary(data: pd.DataFrame, selected_year: int) -> None:
    """지도 오른쪽에 중앙값과 선택 연도·전체 기간 취약 TOP 5를 표시한다."""
    selected_summary = build_selected_year_supply_summary(data, selected_year)
    period_vulnerable_top5 = build_period_vulnerable_top5(data)

    if selected_summary is None:
        st.warning(f"{selected_year}년 공급역량 요약을 만들 수 없습니다.")
        return

    clinic_median, child_median, selected_vulnerable_top5 = selected_summary
    clinic_column, child_column = st.columns(2)
    with clinic_column:
        st.metric("의원 1개당 전문의 수 중앙값", f"{clinic_median:.2f}명")
    with child_column:
        st.metric("아동 1만 명당 전문의 수 중앙값", f"{child_median:.2f}명")

    st.markdown(f"**{selected_year}년 소아과 의료취약 지역 TOP 5**")
    st.dataframe(selected_vulnerable_top5, width="stretch", height=210)

    period_label = f"{ANALYSIS_START_YEAR}~{ANALYSIS_END_YEAR}년"
    st.markdown(f"**{period_label} 소아과 의료취약 지역 TOP 5**")
    if period_vulnerable_top5 is None:
        st.warning(f"{period_label} 의료취약 지역을 계산할 데이터가 없습니다.")
    else:
        st.dataframe(period_vulnerable_top5, width="stretch", height=210)

    st.caption(
        "공급역량점수는 의원당 전문의 수 백분위 40%와 아동 1만 명당 "
        "전문의 수 백분위 60%를 결합한 상대평가 점수입니다. 점수가 낮을수록 "
        "의료취약 순위가 높습니다."
    )


def show_trend_analysis_summary(
    data: pd.DataFrame,
    selected_regions: list[str],
) -> None:
    """두 지표의 지역별 연도 추세를 핵심 인사이트 카드로 요약한다."""
    trend_data = data.loc[
        data["지역"].isin(selected_regions),
        ["시점", "지역", CLINIC_METRIC, CHILD_METRIC],
    ].dropna(how="all", subset=[CLINIC_METRIC, CHILD_METRIC])

    if trend_data.empty:
        st.warning("선택한 지역에 대한 분석 데이터가 없습니다.")
        return

    first_year = int(trend_data["시점"].min())
    last_year = int(trend_data["시점"].max())
    st.markdown("#### 핵심 인사이트")
    st.caption(
        f"분석 기간 {first_year}–{last_year}년 · 선택 지역 "
        f"{len(selected_regions)}개"
    )

    insight_columns = st.columns(2, gap="medium")
    for column, metric in zip(insight_columns, (CLINIC_METRIC, CHILD_METRIC)):
        label = METRIC_LABELS[metric]
        change_summary = _build_change_range(data, selected_regions, metric)
        with column:
            if change_summary.empty:
                _show_insight_card(
                    f"{label} 변화폭",
                    "변화폭을 계산하려면 지역별로 두 개 연도 이상의 값이 필요합니다.",
                )
                continue

            max_row = change_summary.loc[change_summary["변화폭"].idxmax()]
            min_row = change_summary.loc[change_summary["변화폭"].idxmin()]
            _show_insight_card(
                f"{label} 변화폭 최대",
                f"**{max_row['지역']}**가 **{max_row['변화폭']:.2f}명**으로 "
                "기간 중 변동 폭이 가장 컸습니다. 시작값과 종료값을 함께 "
                "확인해야 증가인지 감소인지 판단할 수 있습니다.",
            )
            _show_insight_card(
                f"{label} 변화폭 최소",
                f"**{min_row['지역']}**가 **{min_row['변화폭']:.2f}명**으로 "
                "기간 중 가장 안정적인 흐름을 보였습니다.",
            )

    st.caption(
        "변화폭은 분석 기간 중 최댓값에서 최솟값을 뺀 값입니다. 변화폭이 "
        "크다는 사실만으로 공급 수준이 개선됐다고 해석할 수는 없습니다."
    )


def _largest_yearly_increase(
    data: pd.DataFrame,
    selected_year: int,
    metric: str,
) -> tuple[str, float] | None:
    """선택 연도의 전년 대비 증가가 가장 큰 지역을 반환한다."""
    current = (
        data[data["시점"] == selected_year][["지역", metric]]
        .drop_duplicates("지역")
        .dropna()
        .rename(columns={metric: "현재값"})
    )
    previous = (
        data[data["시점"] == selected_year - 1][["지역", metric]]
        .drop_duplicates("지역")
        .dropna()
        .rename(columns={metric: "전년값"})
    )
    changes = current.merge(previous, on="지역", how="inner")
    if changes.empty:
        return None
    changes["증감"] = changes["현재값"] - changes["전년값"]
    row = changes.loc[changes["증감"].idxmax()]
    return str(row["지역"]), float(row["증감"])


def show_year_comparison_summary(data: pd.DataFrame, selected_year: int) -> None:
    """선택 연도의 두 지표 지역 비교를 핵심 인사이트 카드로 요약한다."""
    year_data = data[data["시점"] == selected_year].drop_duplicates("지역").copy()
    if year_data.empty:
        st.warning(f"{selected_year}년 분석 요약을 만들 수 없습니다.")
        return

    st.markdown("#### 핵심 인사이트")
    st.caption(f"{selected_year}년 {year_data['지역'].nunique()}개 시도 데이터 기준")

    insight_columns = st.columns(2, gap="medium")
    for column, metric in zip(insight_columns, (CLINIC_METRIC, CHILD_METRIC)):
        label = METRIC_LABELS[metric]
        metric_data = year_data.dropna(subset=[metric])
        with column:
            if metric_data.empty:
                _show_insight_card(label, "분석 가능한 데이터가 없습니다.")
                continue

            average = metric_data[metric].mean()
            max_row = metric_data.loc[metric_data[metric].idxmax()]
            min_row = metric_data.loc[metric_data[metric].idxmin()]
            above_count = int((metric_data[metric] >= average).sum())
            _show_insight_card(
                f"{label} 전국 평균",
                f"전국 평균은 **{average:.2f}명**이며, 평균 이상 지역은 "
                f"**{above_count}개**입니다.",
            )
            _show_insight_card(
                f"{label} 지역 격차",
                f"가장 높은 지역은 **{max_row['지역']} "
                f"({max_row[metric]:.2f}명)**, 가장 낮은 지역은 "
                f"**{min_row['지역']} ({min_row[metric]:.2f}명)**입니다.",
            )

    minimum_year = int(data["시점"].min())
    if selected_year > minimum_year:
        clinic_change = _largest_yearly_increase(data, selected_year, CLINIC_METRIC)
        child_change = _largest_yearly_increase(data, selected_year, CHILD_METRIC)
        change_messages = []
        if clinic_change:
            change_messages.append(
                f"의원당 전문의 수: **{clinic_change[0]} "
                f"({clinic_change[1]:+.2f}명)**"
            )
        if child_change:
            change_messages.append(
                f"아동 1만 명당 전문의 수: **{child_change[0]} "
                f"({child_change[1]:+.2f}명)**"
            )
        if change_messages:
            st.info("전년 대비 증가 최대 지역 · " + " / ".join(change_messages))

    st.caption(
        "전국 평균과 최대·최소 지역은 선택 연도 값으로 계산합니다. 전년 대비 "
        "결과는 직전 연도 데이터가 있는 경우에만 표시됩니다."
    )