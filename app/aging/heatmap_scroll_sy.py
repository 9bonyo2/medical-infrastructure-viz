"""
[고령화 파트 · 서연] 연도별 지역 지도 가로 스크롤 뷰 (2015~2024)

기존 페이지의 지도(utils/components.region_bubble_chart)와 같은 GeoJSON 기반 방식으로
연도별 지도를 만들고, 가로 스크롤 필름스트립 형태로 10개년을 한 화면에서 넘겨볼 수 있게 한다.
※ utils/components.py 는 수정하지 않고, 그 안의 geojson 로딩 헬퍼만 재사용(import)한다.

데이터: data/aging/processed/aging_panel_2015_2024.csv
실행 전 준비: pip install kaleido (Plotly 정적 이미지 export용)
"""
import base64
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from utils.components import _load_sido_geojson, _normalize_region_name

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "aging" / "processed"

METRIC_OPTIONS = {
    "노인복지시설": "고령인구10만명당_노인복지시설수",
    "요양병원": "고령인구10만명당_요양병원수",
}


@st.cache_data
def load_panel_df() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "aging_panel_2015_2024.csv")


def _build_year_figure(year_df: pd.DataFrame, color_col: str, cmin: float, cmax: float) -> go.Figure:
    geojson = _load_sido_geojson()
    plot_df = year_df.copy()
    plot_df["__geo_name"] = plot_df["시도"].map(_normalize_region_name)

    fig = px.choropleth(
        plot_df,
        geojson=geojson,
        locations="__geo_name",
        featureidkey="properties.name",
        color=color_col,
        color_continuous_scale=["#12B886", "#F2C94C", "#E5484D"],
        range_color=(cmin, cmax),
    )
    fig.update_traces(marker_line_width=0.6, marker_line_color="white")
    fig.update_geos(fitbounds="locations", visible=False, projection_type="mercator")
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=230, width=220,
        coloraxis_showscale=False,
        paper_bgcolor="white",
    )
    return fig


@st.cache_data(show_spinner="연도별 지도 생성 중...")
def _build_year_images(metric_col: str) -> dict:
    panel = load_panel_df()
    # 10개년 공통 색상 범위로 고정해야 연도 간 비교가 왜곡되지 않음
    cmin, cmax = float(panel[metric_col].min()), float(panel[metric_col].max())
    images = {}
    for year in sorted(panel["연도"].unique()):
        year_df = panel[panel["연도"] == year]
        fig = _build_year_figure(year_df, metric_col, cmin, cmax)
        png_bytes = fig.to_image(format="png", scale=1)
        images[int(year)] = base64.b64encode(png_bytes).decode("ascii")
    return images


def render_year_slider_mapview() -> None:
    """연도별(2015~2024) 지역 지도를 st.slider로 한 해씩 넘겨보는 뷰 (메인 패널 상단 배치용).

    가로 스크롤 필름스트립(render_year_scroll_mapview) 대신, Streamlit 내장 슬라이더로
    연도를 고르면 해당 연도 지도 1장을 인터랙티브(Plotly, hover 가능)하게 보여준다.
    """
    st.markdown(
        '<div class="panel-title" style="margin-bottom:6px;">'
        '시도별 지도 — 연도 슬라이더 (2015~2024)</div>',
        unsafe_allow_html=True,
    )

    ctrl_col, _ = st.columns([1, 2])
    with ctrl_col:
        metric_label = st.radio(
            "지표 선택", list(METRIC_OPTIONS.keys()), horizontal=True, key="slider_metric_sy",
            label_visibility="collapsed",
        )
    metric_col = METRIC_OPTIONS[metric_label]

    year = st.slider(
        "연도", min_value=2015, max_value=2024, value=2024, step=1, key="slider_year_sy",
    )

    panel = load_panel_df()
    # 10개년 공통 색상 범위로 고정해야 슬라이더로 연도를 넘길 때 색이 왜곡되지 않음
    cmin, cmax = float(panel[metric_col].min()), float(panel[metric_col].max())
    year_df = panel[panel["연도"] == year]

    fig = _build_year_figure(year_df, metric_col, cmin, cmax)
    fig.update_traces(
        hovertemplate="<b>%{location}</b><br>" + metric_label + ": %{z:,.1f}<extra></extra>"
    )
    fig.update_layout(height=440, width=None, coloraxis_showscale=True,
                       margin=dict(l=0, r=0, t=10, b=0),
                       coloraxis_colorbar=dict(title=metric_label, thickness=12))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.caption(f"{year}년 · '{metric_label}' 기준 (색상 범위는 2015~2024 공통 기준으로 고정)")


def render_year_scroll_mapview() -> None:
    """연도별(2015~2024) 지역 지도를 가로 스크롤 필름스트립으로 렌더링."""
    st.markdown(
        '<div class="panel-title" style="margin-bottom:10px;">'
        '시도별 지도 — 연도별 가로 스크롤 (2015~2024)</div>',
        unsafe_allow_html=True,
    )
    metric_label = st.radio(
        "지표 선택", list(METRIC_OPTIONS.keys()), horizontal=True, key="scroll_metric_sy",
        label_visibility="collapsed",
    )
    metric_col = METRIC_OPTIONS[metric_label]

    images = _build_year_images(metric_col)

    cards_html = "".join(
        f"""
        <div style="flex:0 0 auto; text-align:center;">
            <div style="font-weight:700; font-size:13px; margin-bottom:4px; color:#1A1F2B;">{year}년</div>
            <img src="data:image/png;base64,{b64}"
                 style="width:220px; border:1px solid #E7E9EE; border-radius:10px;" />
        </div>
        """
        for year, b64 in images.items()
    )
    # st.markdown(마크다운 파서)은 base64 이미지처럼 매우 긴 단일 라인 HTML을 제대로
    # 인식하지 못하고 텍스트로 그대로 노출하는 경우가 있어, 순수 HTML iframe인
    # components.html()을 사용한다(마크다운 파싱을 거치지 않아 안전).
    components.html(
        f"""
        <div style="display:flex; gap:14px; overflow-x:auto; padding:6px 2px 14px 2px;
                    font-family:'Segoe UI', sans-serif;">
            {cards_html}
        </div>
        """,
        height=300,
        scrolling=False,
    )
    st.caption(
        "← 옆으로 스크롤하면 2015~2024년 지도를 순서대로 볼 수 있습니다. "
        f"'{metric_label}' 색상 범위는 10개년 공통 기준으로 고정했습니다."
    )
