"""
[고령화 파트] Streamlit 대시보드
- 시도별 고령인구비율 / 노인복지센터(노인복지관) 수를 한국 지도에 표시
- 고령인구비율 vs 노인복지관 수(인구 규모 보정) 상관관계 시각화
- 노인복지시설 연도별(2015~2024) 추이

실행: streamlit run app/streamlit_app.py
"""
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.aging.analysis.correlation import CORR_PAIRS, compute_correlations, interpret  # noqa: E402
from src.aging.collect.common import PROCESSED_DIR, load_korea_geojson  # noqa: E402

st.set_page_config(page_title="고령화 파트 | 지역별 고령인구·노인복지센터 분석", page_icon="👵", layout="wide")

# ── 색상 (dataviz 원칙: 수치형=단일 색조 sequential, 다크/라이트 모두 대비 확보) ──
SEQUENTIAL_SCALE = "Blues"   # 지도·막대: 값이 클수록 진한 파랑 (단일 색조)
ACCENT = "#2563eb"           # 산점도 포인트/추세선 강조색


@st.cache_data
def load_data():
    master = pd.read_csv(PROCESSED_DIR / "aging_master.csv")
    timeseries = pd.read_csv(PROCESSED_DIR / "senior_facilities_timeseries.csv")
    geo = load_korea_geojson()
    return master, timeseries, geo


master, timeseries, geo = load_data()

METRIC_OPTIONS = {
    "고령인구비율 (%)": "고령인구비율",
    "노인복지관 수 (개소)": "노인복지관수",
    "인구 10만명당 노인복지관 수": "인구10만명당_노인복지관수",
    "고령인구 1만명당 노인복지관 수": "고령인구1만명당_노인복지관수",
    "경로당 수 (개소)": "경로당수",
}

# ── 헤더 ──────────────────────────────────────────────────────────────
st.title("👵 지역별 고령화 · 노인복지센터 분석")
st.caption(
    "지역별 의료 인프라 격차 분석 프로젝트 — 고령화 파트 | "
    "기준연도 2024 | 출처: 행정안전부 주민등록인구통계, 공공데이터포털(보건복지부 노인복지시설현황)"
)

tab_map, tab_corr, tab_trend, tab_data = st.tabs(
    ["🗺️ 지역 지도", "📈 상관관계 분석", "📊 연도별 추이", "🧾 데이터"]
)

# ── 탭 1: 지도 ───────────────────────────────────────────────────────
with tab_map:
    col_ctrl, col_map = st.columns([1, 3])

    with col_ctrl:
        metric_label = st.radio("지도에 표시할 지표", list(METRIC_OPTIONS.keys()), index=0)
        metric_col = METRIC_OPTIONS[metric_label]
        st.markdown("---")
        st.metric("전국 평균 고령인구비율", f"{master['고령인구비율'].mean():.1f}%")
        st.metric("전국 노인복지관 합계", f"{int(master['노인복지관수'].sum()):,}개소")
        top_region = master.sort_values(metric_col, ascending=False).iloc[0]
        st.metric(f"{metric_label} 1위", f"{top_region['시도']} ({top_region[metric_col]:,})")

    with col_map:
        fig_map = px.choropleth_mapbox(
            master,
            geojson=geo,
            locations="시도",
            featureidkey="properties.sido",
            color=metric_col,
            color_continuous_scale=SEQUENTIAL_SCALE,
            mapbox_style="carto-positron",
            center={"lat": 36.0, "lon": 127.7},
            zoom=5.7,
            opacity=0.85,
            hover_name="시도",
            hover_data={
                "고령인구비율": ":.1f",
                "노인복지관수": True,
                "인구10만명당_노인복지관수": ":.2f",
                "시도": False,
            },
            labels={metric_col: metric_label},
        )
        fig_map.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            height=560,
            coloraxis_colorbar=dict(title=metric_label),
        )
        st.plotly_chart(fig_map, width='stretch')

    st.markdown("##### 시도별 순위")
    fig_bar = px.bar(
        master.sort_values(metric_col, ascending=True),
        x=metric_col, y="시도", orientation="h",
        color=metric_col, color_continuous_scale=SEQUENTIAL_SCALE,
        labels={metric_col: metric_label, "시도": ""},
    )
    fig_bar.update_layout(height=520, coloraxis_showscale=False, margin=dict(l=0, r=10, t=10, b=0))
    st.plotly_chart(fig_bar, width='stretch')

# ── 탭 2: 상관관계 ────────────────────────────────────────────────────
with tab_corr:
    st.markdown("### 고령인구 vs 노인복지센터(노인복지관) 수 상관관계")
    corr_result = compute_correlations(master)

    pick = st.selectbox(
        "분석할 지표 쌍 선택",
        options=list(range(len(CORR_PAIRS))),
        format_func=lambda i: CORR_PAIRS[i][2],
    )
    x_col, y_col, desc = CORR_PAIRS[pick]
    row = corr_result.iloc[pick]

    c1, c2, c3 = st.columns(3)
    c1.metric("Pearson r", f"{row['pearson_r']:.3f}")
    c2.metric("p-value", f"{row['pearson_p']:.4f}")
    c3.metric("해석", interpret(row["pearson_r"]))

    fig_scatter = px.scatter(
        master, x=x_col, y=y_col, text="시도",
        trendline="ols",
        labels={x_col: x_col, y_col: y_col},
        color_discrete_sequence=[ACCENT],
    )
    fig_scatter.update_traces(textposition="top center", marker=dict(size=11))
    fig_scatter.update_layout(height=520, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig_scatter, width='stretch')

    st.caption(
        "⚠️ 절대량 기준(고령인구비율 vs 노인복지관 수)은 인구 규모가 큰 지역(경기·서울 등)이 "
        "시설 수도 많아지는 규모 효과로 상관관계가 왜곡될 수 있어, 인구 10만명당으로 보정한 지표를 "
        "함께 확인하는 것을 권장합니다."
    )

    with st.expander("전체 상관분석 결과 테이블"):
        st.dataframe(corr_result, width='stretch')

# ── 탭 3: 연도별 추이 ──────────────────────────────────────────────────
with tab_trend:
    st.markdown("### 노인복지관 수 연도별 추이 (2015~2024)")
    sel_regions = st.multiselect(
        "시도 선택 (복수 선택 가능)",
        options=sorted(timeseries["시도"].unique()),
        default=["서울특별시", "경기도", "부산광역시"],
    )
    trend_df = timeseries[timeseries["시도"].isin(sel_regions)] if sel_regions else timeseries

    fig_trend = px.line(
        trend_df.sort_values("연도"), x="연도", y="노인여가복지시설_복지관", color="시도",
        markers=True, labels={"노인여가복지시설_복지관": "노인복지관 수(개소)"},
    )
    fig_trend.update_layout(height=480, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig_trend, width='stretch')

# ── 탭 4: 데이터 테이블 ─────────────────────────────────────────────────
with tab_data:
    st.markdown("### 분석용 마스터 테이블 (2024년 기준)")
    st.dataframe(master, width='stretch')
    st.download_button(
        "CSV 다운로드", master.to_csv(index=False).encode("utf-8-sig"),
        file_name="aging_master.csv", mime="text/csv",
    )

    st.markdown("### 노인복지시설 시계열 원자료 (2015~2024)")
    st.dataframe(timeseries, width='stretch')
