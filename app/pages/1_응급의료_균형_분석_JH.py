import os
import sys
import json
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
import utils.components as uc
from utils.components import (
    kpi_row,
    top5_ranking_panel,
    region_panel,
)
# ================================================================
from src.emergency.config import (
    GEOJSON_PATH,
    DOCTOR_DIR,
    DOCTOR_MAP_DIR,
    EMERGENCY_DIR,
    EMERGENCY_MAP_DIR,
    POPULATION_DIR,
    TIME_DIR,
    TIME_MAP_DIR,
)
from src.emergency.analysis import analysis as mv
from src.emergency.collect import collect as dc

# ================================================================

YEAR_LIST = list(range(2015, 2025))

load_dotenv(ROOT_DIR / ".env")
api_key = os.getenv("KOSIS_API_KEY")

st.set_page_config(page_title="응급의료 균형 분석", page_icon="🚑", layout="wide")
mv.ensure_all_years_data(api_key, YEAR_LIST)

EMERGENCY_SUBTOPICS = {
    "인구 대비 기관 수": {
        "map_func": mv.create_emergency_map,
        "html_file": lambda yr: EMERGENCY_MAP_DIR / f"emer{yr}.html",
        "desc": "인구 10만 명당 설치된 응급의료기관 수",
        "metric_col": "10만명당_기관수",
        "unit": "개",
        "vulnerable_type": "lowest",  # 수치가 가장 낮은 5곳
    },
    "인구 대비 전문의 수": {
        "map_func": mv.create_doctor_map,
        "html_file": lambda yr: DOCTOR_MAP_DIR / f"doc{yr}.html",
        "desc": "인구 10만 명당 활동 중인 응급의학 전문의 수",
        "metric_col": "10만명당_전문의수",
        "unit": "명",
        "vulnerable_type": "lowest",  # 수치가 가장 낮은 5곳
    },
    "상위기관당 지연 환자수": {
        "map_func": mv.create_time_map,
        "html_file": lambda yr: TIME_MAP_DIR / f"time{yr}.html",
        "desc": "상위 응급의료기관 1곳당 2시간 이상 지연 도착 환자수",
        "metric_col": "상위기관당_지연환자수",
        "unit": "명",
        "vulnerable_type": "highest",  # 환자 수가 가장 많은 5곳
    },
}

def ensure_and_render_map(topic_key: str, year: int):

    info = EMERGENCY_SUBTOPICS[topic_key]
    html_path = info["html_file"](year)

    if not html_path.exists() and info["map_func"]:
        with st.spinner(f"🗺️ {year}년 Folium 지도를 생성 중입니다..."):
            info["map_func"](data_year=year)

    if html_path.exists():
        with open(html_path, "r", encoding="utf-8") as f:
            components.html(f.read(), height=430)
    else:
        st.info("해당 연도의 지도 파일을 불러올 수 없습니다.")

def prepare_top5_ranking(raw_df: pd.DataFrame, metric_col: str, vulnerable_type: str) -> pd.DataFrame:

    df = raw_df.copy()
    min_v = df[metric_col].min()
    max_v = df[metric_col].max()

    if max_v > min_v:
        if vulnerable_type == "lowest":
            df["score"] = ((max_v - df[metric_col]) / (max_v - min_v) * 100).round(1)
        else:
            df["score"] = ((df[metric_col] - min_v) / (max_v - min_v) * 100).round(1)
    else:
        df["score"] = 50.0

    df["region"] = df["지역"].astype(str)
    top5 = df.sort_values(by="score", ascending=False).head(5).copy()
    top5["rank"] = range(1, len(top5) + 1)
    return top5[["rank", "region", "score"]]
# ================================================================

inject_base_style()
render_sidebar(active_key="emergency_jh")

header_left, header_right = st.columns([4, 1])
with header_left:
    st.markdown('<div class="page-title">응급의료 균형 분석</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size: 13px; color: #6B7280; margin-top: 4px; margin-bottom: 12px;">'
        '전국 17개 시·도의 인구 대비 응급의료 인프라 공급 수준과 중증 응급환자 이송 지연 현황을 종합 분석합니다.'
        '</div>',
        unsafe_allow_html=True,
    )
with header_right:
    selected_year = st.selectbox(
        "기준 연도",
        options=YEAR_LIST,
        index=len(YEAR_LIST) - 1,  # 2024년 기본 선택
        key="main_emergency_year_select",
    )

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
        metric_col = curr_topic["metric_col"]
        
        # 실제 지표 데이터 로드
        try:
            raw_df = curr_topic["map_func"](data_year=selected_year)
        except Exception:
            raw_df = None

        # 탭 내부를 좌(지리적 버블 차트) / 우(취약 점수 Top 5 패널)로 배치
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
                if raw_df is not None and not raw_df.empty and metric_col in raw_df.columns:
                    top5_df = prepare_top5_ranking(
                        raw_df, 
                        metric_col, 
                        curr_topic["vulnerable_type"]
                    )
                    top5_ranking_panel(
                        top5_df,
                        title="응급의료 취약지역 TOP 5",
                        tag=f"{topic_key.split(' ')[1]} 기준",
                        unit_label="취약도 점수(0~100)"
                    )
                else:
                    st.info("해당 연도의 TOP 5 데이터를 불러올 수 없습니다.")

st.write("")

st.markdown(
    '<div class="panel-title" style="margin-bottom: 8px;">연도별 지도 핵심 지표 간 상관계수 추이 (2015~2024)</div>',
    unsafe_allow_html=True,
)

with st.container(border=True):

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
            plot_bgcolor="white",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Pretendard, Malgun Gothic, sans-serif", size=12),
        )

        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.caption(
            "그래프 캡션: 상단 3개 지도에서 시각화한 17개 시·도 표준화 지표(10만 명당 기관/전문의 수, 기관당 지연환자수) 간의 피어슨 상관계수(r) 및 유의확률(p-value) 추이입니다."
        )
    else:
        st.info("데이터를 수집하는 중이거나 상관계수를 계산할 수 없습니다.")

st.write("")

st.markdown(
        '<div class="panel-title" style="margin-bottom: 8px;">핵심 인사이트</div>',
        unsafe_allow_html=True,
    )

with st.container(border=True):
    
    # 1. 표준화 배경 안내
    st.info(
        "📌 **인구 10만 명당 표준화 지표 적용 이유**\n\n"
        "인구수가 많은 대도시(서울·경기 등)는 기관 수, 전문의 수, 지연 환자 수가 모두 커서 "
        "필연적으로 **양의 상관관계**가 발생합니다. 이러한 착시를 제거하고 지역별 실질적인 의료 인프라 수준을 "
        "비교하기 위해 인구 10만 명당 지표로 정규화하여 분석했습니다."
    )

    # 2. 1행: 초록선 (기관 수 ↔ 지연 환자수)
    with st.container(border=True):
        st.markdown("**① 인구 대비 기관 수 ↔ 기관당 지연 환자수** :green[🟢 초록선 | r ≈ -0.5 ~ -0.7 (p < 0.05 유의)]")
        st.markdown(
            "인구 대비 응급의료기관 수가 많을수록 기관당 지연 환자 수가 뚜렷하게 감소하는 **유의미한 음의 상관관계**를 보입니다. "
            "이는 응급의료기관의 물리적 분산 배치가 이송 지연을 완화하는 핵심 요인임을 보입니다."
        )

    # 3. 2행: 노랑선 (전문의 수 ↔ 지연 환자수)
    with st.container(border=True):
        st.markdown("**② 인구 대비 전문의 수 ↔ 기관당 지연 환자수** :orange[🟡 노랑선 | r ≈ +0.4 (p ≈ 0.1 경계선)]")
        st.markdown(
            "약한 양의 상관관계를 보이나 p-value가 0.1 근처로 통계적 신뢰도는 다소 애매합니다. "
            "전문의가 많을수록 지연이 늘어나는 역설적 양상은, **수술 및 처치가 가능한 전문의 밀집 대형병원(권역센터)으로 "
            "타 지역의 '응급실 뺑뺑이' 환자가 집중되어 발생하는 병목 현상** 때문으로 판단할 수 있습니다."
        )

    # 4. 3행: 파랑선 (기관 수 ↔ 전문의 수)
    with st.container(border=True):
        st.markdown("**③ 인구 대비 기관 수 ↔ 인구 대비 전문의 수** :blue[🔵 파랑선 | r ≈ 0.0 (p ≈ 0.7 비유의)]")
        st.markdown(
            "상관계수가 0에 가깝고 p-value가 0.7 수준으로 높아 **통계적으로 유의미한 관계가 없습니다.** "
            "이는 지역에 응급기관이 많아진다고 해서 전문의가 비례하여 배치되는 것이 아님을 확인할 수 있습니다. "
        )