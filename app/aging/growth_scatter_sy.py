"""
[고령화 파트 · 서연] 지역별 고령화 속도 vs 공급 증가 속도 산점도

기존 utils/*, pages/* 는 수정하지 않고 이 파일 하나로 완결되도록 작성했습니다.
2_고령화와_노인의료_분석.py 에서 render_growth_scatter_section() 만 import해서 호출하면 됩니다.

데이터: data/aging/processed/growth_gap_2015_2024.csv
  (생성: python -m src.aging.analysis.growth_and_gap)
"""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "aging" / "processed"


@st.cache_data
def load_growth_gap_df() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "growth_gap_2015_2024_sy.csv")


def render_growth_scatter_section() -> None:
    """지역별 '고령화 증가폭'과 '고령인구 10만명당 공급 증가율'을 비교하는 산점도.

    격차점수(고령화 속도 대비 공급 증가 부족 정도)를 색상(발산형: 파랑=안전~빨강=취약)과
    크기로 함께 표현한다.
    """
    df = load_growth_gap_df()

    st.markdown(
        '<div class="panel-title" style="margin-bottom:6px;">'
        '지역별 고령화 속도 vs 공급 증가 속도 (2015→2024)</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "점이 클수록/붉을수록 격차점수(취약도)가 높습니다. 모든 지역이 y<0에 위치 — "
        "고령인구 1인당 노인복지시설·요양병원 공급은 10년간 전국 모든 시도에서 감소했습니다."
    )

    size_vals = df["격차점수"] - df["격차점수"].min() + 0.5

    fig = go.Figure()
    fig.add_hline(y=df["공급_증가율_평균"].mean(), line_dash="dash", line_color="#C9CDD6", line_width=1)
    fig.add_vline(x=df["고령화_증가폭"].mean(), line_dash="dash", line_color="#C9CDD6", line_width=1)
    fig.add_trace(
        go.Scatter(
            x=df["고령화_증가폭"],
            y=df["공급_증가율_평균"],
            mode="markers+text",
            text=df["시도"],
            textposition="top center",
            textfont=dict(size=10),
            marker=dict(
                size=size_vals,
                sizemode="area",
                sizeref=2.0 * size_vals.max() / (34 ** 2),
                sizemin=6,
                color=df["격차점수"],
                colorscale="RdBu_r",
                cmid=0,
                showscale=True,
                colorbar=dict(title="격차점수", thickness=12),
                line=dict(width=1, color="white"),
            ),
            customdata=df[["격차점수"]],
            hovertemplate=(
                "<b>%{text}</b><br>고령화 증가폭: %{x:.2f}%p"
                "<br>공급 증가율: %{y:.1f}%<br>격차점수: %{customdata[0]:.2f}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        height=460,
        margin=dict(l=10, r=10, t=20, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(title="고령화 증가폭 (2015→2024, %p)", gridcolor="#F0F1F5"),
        yaxis=dict(
            title="고령인구 10만명당 공급 증가율 (2015→2024, 시설·요양병원 평균, %)",
            gridcolor="#F0F1F5", zeroline=True, zerolinecolor="#D8DAE3",
        ),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
