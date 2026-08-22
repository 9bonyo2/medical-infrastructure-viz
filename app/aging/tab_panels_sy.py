"""
[고령화 파트 · 서연] KPI 박스 아래 탭바(4개) — 좌측 지도뷰 / 우측 분석뷰

우리가 진행한 4가지 분석을 각각 탭 하나씩으로 구성한다. 탭마다 데이터·시각화 특성에 맞춰
좌측(지도뷰)·우측(분석뷰)을 다르게 구성했다:

  1) 취약지역 Top5 분석      — 지도: 격차점수 히트맵 / 분석: 시도별 랭킹(TOP5 카드 + 전체 순위표)
  2) 지역별 증가 속도        — 지도: 증가율 히트맵(시설/요양병원 전환) / 분석: 시도별 막대그래프
  3) 노인복지시설 상관관계    — 지도: 연도 선택 가능한 시설 수준 지도 / 분석: 산점도(추세선+r/p)
  4) 요양병원 상관관계        — 지도: 연도 선택 가능한 요양병원 수준 지도 / 분석: 산점도(추세선+r/p)

기존 utils/components.py, utils/sample_data.py 는 수정하지 않고 공개 함수(region_panel)만
재사용한다. 2_고령화와_노인의료_분석.py 에서는 render_*_tab() 함수 4개만 import해서 쓰면 된다.
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy import stats

from utils.components import region_panel, top5_ranking_panel

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "aging" / "processed"

GROWTH_METRIC_OPTIONS = {
    "노인복지시설": {"level": "고령인구10만명당_노인복지시설수", "growth": "시설_증가율"},
    "요양병원": {"level": "고령인구10만명당_요양병원수", "growth": "요양병원_증가율"},
}


# ── 공용 데이터 로더 ────────────────────────────────────────────────────
@st.cache_data
def load_panel_df() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "aging_panel_2015_2024.csv")


@st.cache_data
def load_growth_gap_df() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "growth_gap_2015_2024_sy.csv")


@st.cache_data
def load_correlation_by_year_df() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "correlation_by_year.csv")


def _size_col_from_panel(df: pd.DataFrame, year: int = 2024) -> pd.DataFrame:
    """지도 버블 크기용 고령인구수_65세이상 컬럼을 연도 기준으로 병합."""
    panel_year = load_panel_df()
    panel_year = panel_year[panel_year["연도"] == year][["시도", "고령인구수_65세이상"]]
    return df.merge(panel_year, on="시도", how="left")


# ══════════════════════════════════════════════════════════════════════
# 탭 1) 취약지역 Top5 분석 — 지도: 격차점수 / 분석: 시도별 랭킹
# ══════════════════════════════════════════════════════════════════════
def render_top5_tab() -> None:
    gap_df = load_growth_gap_df()
    map_df = _size_col_from_panel(gap_df)

    left, right = st.columns([2, 1], gap="medium")
    with left:
        with st.container(border=True):
            region_panel(
                map_df,
                title="전국 의료 취약도 현황",
                tag="격차점수 · 2015~2024",
                color_col="격차점수",
                size_col="고령인구수_65세이상",
                color_label="격차점수",
                legend_low="안전(공급이 고령화 속도를 따라감)",
                legend_high="취약(공급이 고령화 속도를 못 따라감)",
            )
            st.caption(
                "격차점수 = z(고령화 증가폭) − z(고령인구10만명당 공급 증가율). "
                "클수록 고령화 속도 대비 노인복지시설·요양병원 공급 증가가 뒤처진 지역입니다."
            )

    with right:
        with st.container(border=True):
            top5 = gap_df.sort_values("격차점수", ascending=False).head(5).reset_index(drop=True)
            top5["rank"] = top5.index + 1
            top5["region"] = top5["시도"]
            top5["score"] = top5["격차점수"].round(2)
            top5_ranking_panel(
                top5[["rank", "region", "score"]],
                title="의료 취약지역 TOP 5",
                tag="격차점수 · 2015~2024",
                unit_label="격차점수",
            )

        st.write("")
        with st.container(border=True):
            st.markdown('<div class="panel-title" style="margin-bottom:8px;">시도별 전체 순위</div>',
                        unsafe_allow_html=True)
            ranking_all = gap_df.sort_values("격차점수", ascending=False).reset_index(drop=True)
            ranking_all.index = ranking_all.index + 1
            st.dataframe(
                ranking_all[["시도", "격차점수", "고령화_증가폭", "공급_증가율_평균"]]
                .rename(columns={"고령화_증가폭": "고령화 증가폭(%p)", "공급_증가율_평균": "공급 증가율(%)"}),
                use_container_width=True, height=360,
            )


# ══════════════════════════════════════════════════════════════════════
# 탭 2) 지역별 증가 속도 — 지도: 증가율 / 분석: 시도별 막대그래프
# ══════════════════════════════════════════════════════════════════════
def render_growth_rate_tab() -> None:
    gap_df = load_growth_gap_df()

    metric_label = st.radio(
        "지표 선택", list(GROWTH_METRIC_OPTIONS.keys()), horizontal=True, key="growth_rate_metric_sy",
    )
    growth_col = GROWTH_METRIC_OPTIONS[metric_label]["growth"]

    left, right = st.columns([2, 1], gap="medium")
    with left:
        with st.container(border=True):
            map_df = _size_col_from_panel(gap_df)
            region_panel(
                map_df,
                title=f"전국 {metric_label} 증가율 현황 (2015→2024)",
                tag="고령인구10만명당 기준",
                color_col=growth_col,
                size_col="고령인구수_65세이상",
                color_label=f"{metric_label} 증가율(%)",
                legend_low="감소",
                legend_high="증가",
            )
            st.caption(f"고령인구 10만명당 {metric_label} 수가 2015년 대비 2024년에 몇 % 늘거나 줄었는지를 지역별로 표시했습니다.")

    with right:
        with st.container(border=True):
            st.markdown(
                f'<div class="panel-title" style="margin-bottom:8px;">시도별 {metric_label} 증가율</div>',
                unsafe_allow_html=True,
            )
            bar_df = gap_df[["시도", growth_col]].sort_values(growth_col, ascending=True)
            colors = ["#E5484D" if v >= 0 else "#2F6FED" for v in bar_df[growth_col]]

            fig = go.Figure(
                go.Bar(
                    x=bar_df[growth_col], y=bar_df["시도"], orientation="h",
                    marker_color=colors,
                    text=[f"{v:.1f}%" for v in bar_df[growth_col]],
                    textposition="outside",
                )
            )
            fig.update_layout(
                height=520, margin=dict(l=10, r=30, t=10, b=10),
                plot_bgcolor="white", paper_bgcolor="white",
                xaxis=dict(title="증가율(%)", gridcolor="#F0F1F5", zeroline=True, zerolinecolor="#D8DAE3"),
                yaxis=dict(title=None),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.caption("모든 지역이 음수(-)라는 것은, 고령인구 1인당 공급이 10년간 전국에서 줄었다는 뜻입니다.")


# ══════════════════════════════════════════════════════════════════════
# 탭 3·4 공용: 상관관계 탭 — 지도: 연도 선택 가능한 수준 지도 / 분석: 산점도
# ══════════════════════════════════════════════════════════════════════
def _render_corr_tab(metric_label: str, metric_col: str, unit: str, key_prefix: str) -> None:
    panel = load_panel_df()
    corr_year_df = load_correlation_by_year_df()

    year = st.selectbox(
        "연도", options=list(range(2015, 2025)), index=9, key=f"{key_prefix}_year_sy",
    )
    year_df = panel[panel["연도"] == year]

    left, right = st.columns([2, 1], gap="medium")
    with left:
        with st.container(border=True):
            region_panel(
                year_df,
                title=f"전국 {metric_label} 현황",
                tag=f"{year}년",
                color_col=metric_col,
                size_col="고령인구수_65세이상",
                color_label=f"{metric_label}({unit})",
                legend_low="낮음",
                legend_high="높음",
            )

    with right:
        with st.container(border=True):
            x = year_df["고령인구비율"].to_numpy(float)
            y = year_df[metric_col].to_numpy(float)
            r, p = stats.pearsonr(x, y)

            st.markdown(
                f'<div class="panel-title" style="margin-bottom:4px;">고령인구비율 vs {metric_label}</div>',
                unsafe_allow_html=True,
            )
            st.caption(f"{year}년 · Pearson r = {r:.3f} ({'유의' if p < 0.05 else '유의하지 않음'}, p={p:.3f})")

            fig = px.scatter(
                year_df, x="고령인구비율", y=metric_col, text="시도", trendline="ols",
                color_discrete_sequence=["#2F6FED"],
            )
            fig.update_traces(textposition="top center", marker=dict(size=9))
            fig.update_layout(
                height=440, margin=dict(l=10, r=10, t=10, b=10),
                plot_bgcolor="white", paper_bgcolor="white",
                xaxis=dict(title="고령인구비율(%)", gridcolor="#F0F1F5"),
                yaxis=dict(title=f"{metric_label}({unit})", gridcolor="#F0F1F5"),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            # 연도별 r 추이(참고)
            trend = corr_year_df[corr_year_df["y"] == metric_col].sort_values("연도")
            if not trend.empty:
                st.caption(
                    f"연도별 추이: {trend.iloc[0]['연도']}년 r={trend.iloc[0]['pearson_r']:.2f} "
                    f"→ {trend.iloc[-1]['연도']}년 r={trend.iloc[-1]['pearson_r']:.2f}"
                )


def render_facility_corr_tab() -> None:
    _render_corr_tab("노인복지시설", "고령인구10만명당_노인복지시설수", "개", "facility_corr")


def render_hospital_corr_tab() -> None:
    _render_corr_tab("요양병원", "고령인구10만명당_요양병원수", "개", "hospital_corr")
