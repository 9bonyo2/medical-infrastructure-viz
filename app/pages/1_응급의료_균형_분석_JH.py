import os
import sys
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
# ================================================================
APP_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = APP_DIR.parent

for p in [APP_DIR, ROOT_DIR]:
    if str(p) not in sys.path:
        sys.path.append(str(p))
# ================================================================
from utils.style import inject_base_style, COLORS
from utils.nav import render_sidebar
from utils.components import (
    kpi_row,
    region_panel,
    correlation_trend_chart,
    small_multiples_grid,
)
from utils.sample_data import (
    get_region_vulnerability_df,
    get_correlation_trend_df,
    get_small_multiples_df,
)
# ================================================================
from emergency.emergency_jh.src.config import (
    DOCTOR_DIR,
    DOCTOR_MAP_DIR,
    EMERGENCY_DIR,
    EMERGENCY_MAP_DIR,
    POPULATION_DIR,
    TIME_DIR,
    TIME_MAP_DIR,
)
from emergency.emergency_jh.src.analysis import analysis as mv
from emergency.emergency_jh.src.collect import collect as dc
# ================================================================
YEAR_LIST = list(range(2015, 2025))

load_dotenv(ROOT_DIR / ".env")
api_key = os.getenv("KOSIS_API_KEY")

st.set_page_config(page_title="응급의료 균형 분석", page_icon="🚑", layout="wide")
mv.ensure_all_years_data(api_key, YEAR_LIST)

EMERGENCY_SUBTOPICS = {
    "🏥 인구 대비 기관 수": {
        "map_func": mv.create_emergency_map,
        "html_file": lambda yr: EMERGENCY_MAP_DIR / f"emer{yr}.html",
        "desc": "인구 10만 명당 설치된 응급의료기관 수",
        "metric_col": "10만명당_기관수",
        "unit": "개",
        "vulnerable_type": "lowest",  # 수치가 가장 낮은 5곳
    },
    "👨‍⚕️ 인구 대비 전문의 수": {
        "map_func": mv.create_doctor_map,
        "html_file": lambda yr: DOCTOR_MAP_DIR / f"doc{yr}.html",
        "desc": "인구 10만 명당 활동 중인 응급의학 전문의 수",
        "metric_col": "10만명당_전문의수",
        "unit": "명",
        "vulnerable_type": "lowest",  # 수치가 가장 낮은 5곳
    },
    "⏱️ 상위기관당 지연 환자수": {
        "map_func": mv.create_time_map,
        "html_file": lambda yr: TIME_MAP_DIR / f"time{yr}.html",
        "desc": "상위 응급의료기관 1곳당 2시간 이상 지연 도착 환자수",
        "metric_col": "상위기관당_지연환자수",
        "unit": "명",
        "vulnerable_type": "highest",  # 환자 수가 가장 많은 5곳
    },
}

def ensure_and_render_map(topic_key, year):

    info = EMERGENCY_SUBTOPICS[topic_key]
    html_path = info["html_file"](year)

    if not html_path.exists() and info["map_func"]:
        with st.spinner(f"🗺️ {year}년 Folium 지도를 생성 중입니다..."):
            info["map_func"](data_year=year)

    if html_path.exists():
        with open(html_path, "r", encoding="utf-8") as f:
            components.html(f.read(), height=430)
    else:
        region_panel(get_region_vulnerability_df())

def render_vulnerability_bar_chart(topic_key: str, year: int):
    """선택된 주제 및 연도 데이터 기반 취약 지역 Top 5 가로 막대 그래프 렌더링"""
    info = EMERGENCY_SUBTOPICS[topic_key]
    metric_col = info["metric_col"]
    unit = info["unit"]
    is_lowest_vulnerable = (info["vulnerable_type"] == "lowest")

    # 주제별 데이터프레임 로드
    try:
        df = info["map_func"](data_year=year)
    except Exception:
        df = None

    if df is None or not isinstance(df, pd.DataFrame) or metric_col not in df.columns:
        st.info("📊 취약 지역 데이터를 불러오는 중입니다...")
        return

    # 취약도 기준 정렬 (낮을수록 취약 vs 높을수록 취약)
    sorted_df = df.sort_values(by=metric_col, ascending=is_lowest_vulnerable).head(5)
    # 가로 막대 그래프 시각화를 위해 순서 반전 (1위가 맨 위에 오도록)
    plot_df = sorted_df.iloc[::-1].copy()

    # Plotly 가로 막대 그래프 생성
    color_scale = [
        [0.0, "#93C5FD"],
        [1.0, COLORS["accent_blue"]]
    ] if is_lowest_vulnerable else [
        [0.0, "#FCA5A5"],
        [1.0, COLORS["accent_red"]]
    ]

    fig = px.bar(
        plot_df,
        x=metric_col,
        y="지역",
        orientation="h",
        text=plot_df[metric_col].apply(lambda x: f"{x:,.2f}{unit}"),
        color=metric_col,
        color_continuous_scale=color_scale
    )

    fig.update_traces(
        textposition="outside",
        textfont=dict(size=12, color=COLORS["text_dark"], family="Pretendard, sans-serif"),
        cliponaxis=False,
        marker=dict(line=dict(width=1, color=COLORS["border"])),
    )

    fig.update_layout(
        height=437,
        margin=dict(l=10, r=55, t=10, b=10),
        xaxis=dict(
            title=dict(text=f"{metric_col} ({unit})", font=dict(size=12, color=COLORS["text_muted"])),
            tickfont=dict(size=11, color=COLORS["text_muted"]),
            gridcolor=COLORS["border"],
            zeroline=False,
        ),
        yaxis=dict(
            tickfont=dict(size=12, color=COLORS["text_dark"], family="Pretendard, sans-serif"),
        ),
        coloraxis_showscale=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        bargap=0.28,
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
# ================================================================

inject_base_style()
render_sidebar(active_key="emergency")

header_left, header_right = st.columns([4, 1])
with header_left:
    st.markdown('<div class="page-title">응급의료 균형 분석</div>', unsafe_allow_html=True)
with header_right:
    selected_year = st.selectbox(
        "기준 연도",
        options=YEAR_LIST,
        index=len(YEAR_LIST) - 1,  # 2024년 기본 선택
        key="main_emergency_year_select",
    )

# TODO(팀): 아래는 고령화 페이지와 동일한 레이아웃의 템플릿입니다.
#   utils/sample_data.py 에 응급의료 전용 데이터 함수를 추가한 뒤
#   get_correlation_trend_df / get_small_multiples_df 자리를 교체해주세요.

live_kpis = mv.calculate_emergency_kpis(selected_year)

kpi_row(
    live_kpis,
    icon_map={
        "facility_per_100k": ("🏥", "인구 10만 명당 응급의료기관 수 평균"),
        "doctor_per_100k": ("👨‍⚕️", "인구 10만 명당 응급의학 전문의 수 평균"),
        "delayed_patients": ("⏱️", "2시간 이상 지연 도착 환자수 합계"),
        "delayed_per_center": ("🚨", "총 상위 응급기관당 지연도착 환자수 합계"),
    },
)

st.write("")

subtopic_names = list(EMERGENCY_SUBTOPICS.keys())
main_tabs = st.tabs(subtopic_names)

for tab, topic_key in zip(main_tabs, subtopic_names):
    with tab:
        curr_topic = EMERGENCY_SUBTOPICS[topic_key]
        criteria_text = "공급 최하위 5곳" if curr_topic["vulnerable_type"] == "lowest" else "지연부담 최다 5곳"
        
        # 탭 내부를 좌(지도) / 우(Top 5 차트)로 분할
        left, right = st.columns([1.6, 1.4], gap="medium")
        
        with left:
            with st.container(border=True):
                st.markdown(
                    f'<div class="panel-title" style="margin-bottom:4px;">'
                    f'전국 공간 시각화 <span class="panel-tag">{selected_year}년</span></div>',
                    unsafe_allow_html=True,
                )
                st.caption(f"📌 {curr_topic['desc']}")
                ensure_and_render_map(topic_key, year=selected_year)
                
        with right:
            with st.container(border=True):
                st.markdown(
                    f'<div class="panel-title" style="margin-bottom:4px;">'
                    f'취약 지역 Top 5 <span class="panel-tag">{criteria_text}</span></div>',
                    unsafe_allow_html=True,
                )
                st.caption(f"🚨 전국 17개 시·도 중 인프라가 가장 취약한 상위 5개 지역입니다.")
                render_vulnerability_bar_chart(topic_key, year=selected_year)

st.write("")

with st.container(border=True):
    st.markdown(
        '<div class="panel-title">연도별 지도 핵심 지표 간 상관계수 추이 (2015~2024)</div>',
        unsafe_allow_html=True,
    )

    trend_df = mv.get_emergency_correlation_trend(YEAR_LIST)

    if not trend_df.empty:
        import plotly.graph_objects as go

        fig = go.Figure()

        # 지표별 시리즈명, p-value 컬럼, 색상, 표시 레이블 매핑
        configs = [
            ("기관수-전문의수", "p_fac_doc", "#2F6FED", "10만명당 기관수 ↔ 10만명당 전문의수"),
            ("기관수-지연환자", "p_fac_delay", "#10B981", "10만명당 기관수 ↔ 기관당 지연환자"),
            ("전문의수-지연환자", "p_doc_delay", "#F59E0B", "10만명당 전문의수 ↔ 기관당 지연환자"),
        ]

        for r_col, p_col, color, display_name in configs:
            hover_text = [
                f"<b>{yr}년 {display_name}</b><br>"
                f"상관계수 (r): {r:.3f}<br>"
                f"p-value: {p:.4f} " + (
                    "<span style='color:#10B981;'>(p<0.05 유의)</span>"
                    if p is not None and p < 0.05
                    else "<span style='color:#6B7280;'>(p≥0.05)</span>"
                )
                if pd.notnull(r) and pd.notnull(p)
                else f"<b>{yr}년</b><br>데이터 없음"
                for yr, r, p in zip(trend_df["year"], trend_df[r_col], trend_df[p_col])
            ]

            fig.add_trace(
                go.Scatter(
                    x=trend_df["year"],
                    y=trend_df[r_col],
                    mode="lines+markers",
                    name=display_name,
                    line=dict(color=color, width=2.5),
                    marker=dict(size=7),
                    hovertext=hover_text,
                    hoverinfo="text",
                )
            )

        fig.update_layout(
            height=380,
            margin=dict(l=10, r=20, t=30, b=10),
            xaxis=dict(
                tickmode="linear",
                tick0=2015,
                dtick=1,
                gridcolor="#E5E7EB",
            ),
            yaxis=dict(
                title="Pearson r (상관계수)",
                zeroline=True,
                zerolinecolor="#9CA3AF",
                zerolinewidth=1.2,
                gridcolor="#E5E7EB",
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
            ),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Pretendard, Malgun Gothic, sans-serif", size=12),
        )

        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.caption(
            "그래프 캡션: 상단 3개 지도에서 시각화한 17개 시·도 표준화 지표(10만 명당 기관/전문의 수, 기관당 지연환자수) 간의 피어슨 상관계수(r) 및 유의확률(p-value) 추이입니다."
        )
    else:
        st.info("데이터를 수집하는 중이거나 상관계수를 계산할 수 없습니다.")