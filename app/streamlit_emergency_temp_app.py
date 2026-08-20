# ====================== 실행 되는지 시험하는 파일입니다. =======================

import os
import sys
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.emergency.analysis import visualize_by_map as mv
from src.emergency.collect import collect_emergency as dc
from src.emergency.config import (
    DOCTOR_DIR,
    DOCTOR_MAP_DIR,
    EMERGENCY_DIR,
    EMERGENCY_MAP_DIR,
    POPULATION_DIR,
    TIME_DIR,
    TIME_MAP_DIR,
)

year_list = [2015,2016,2017,2018,2019,2020,2021,2022,2023,2024]

# 웹 앱 레이아웃 설정
st.set_page_config(page_title="응급의료 지표 분석 대시보드", layout="wide")

st.markdown(
    "<style>section[data-testid='stSidebar']{width:420px !important; min-width:420px !important;}</style>",
    unsafe_allow_html=True,
)

TOPICS = {
    "🏥 인구 대비 응급의료기관 수": {
        "check_files": lambda yr: [
            POPULATION_DIR / f"pop{yr}.csv",
            EMERGENCY_DIR / f"emer{yr}.csv",
        ],
        "map_func": mv.create_emergency_map,
        "html_file": lambda yr: EMERGENCY_MAP_DIR / f"emer{yr}.html",
        "target_col": "10만명당_기관수",
        "desc": "인구 10만 명당 설치된 응급의료기관 수를 분석합니다.",
    },
    "👨‍⚕️ 인구 대비 응급전문의 수": {
        "check_files": lambda yr: [
            POPULATION_DIR / f"pop{yr}.csv",
            DOCTOR_DIR / f"doc{yr}.csv",
        ],
        "map_func": mv.create_doctor_map,
        "html_file": lambda yr: DOCTOR_MAP_DIR / f"doc{yr}.html",
        "target_col": "10만명당_전문의수",
        "desc": "인구 10만 명당 활동 중인 응급의학 전문의 수를 분석합니다.",
    },
    "⏱️ 상위기관당 지연 환자수": {
        "check_files": lambda yr: [
            EMERGENCY_DIR / f"emer{yr}.csv",
            TIME_DIR / f"time{yr}.csv",
        ],
        "map_func": mv.create_time_map,
        "html_file": lambda yr: TIME_MAP_DIR / f"time{yr}.html",
        "target_col": "상위기관당_지연환자수",
        "desc": "상위 응급의료기관(권역·지역센터) 1곳당 2시간 이상 지연 도착 환자수를 분석합니다.",
    },
}

# CSV 파일 존재 여부 확인 및 자동 생성 함수
def ensure_files_for_topic(year, required_file_paths):
    missing = [path for path in required_file_paths if not path.exists()]
    if missing:
        with st.spinner(f"🔍 {year}년 데이터를 KOSIS API에서 수집 중입니다..."):
            load_dotenv()
            api_key = os.getenv("KOSIS_API_KEY")
            if not api_key:
                st.error(
                    "[에러] .env 파일에 KOSIS_API_KEY가 설정되어 있지 않습니다."
                )
                return False
            try:
                if any("pop" in f.name for f in missing):
                    dc.get_population(api_key, year)

                if any("emer" in f.name for f in missing):
                    dc.get_emergency(api_key, year)

                if any("doc" in f.name for f in missing):
                    dc.get_doctor(api_key, year)

                if any("time" in f.name for f in missing):
                    dc.get_time(api_key, year)

                st.toast(f"{year}년 데이터 수집 완료")
                return True
            
            except Exception as e:
                st.error(f"[에러] 데이터 수집 실패: {e}")
                return False
            
    return True

# --- 사이드바 제어판 ---
st.sidebar.title("🎛️ 제어판")
selected_topic_name = st.sidebar.radio("📌 분석 주제 선택", list(TOPICS.keys()), index=0)
current_topic = TOPICS[selected_topic_name]

st.sidebar.markdown("---")
selected_year = st.sidebar.select_slider("📅 기준 연도 선택", options=year_list, value=2024)

# --- 메인 화면 렌더링 ---
st.title(f"{selected_topic_name} ({selected_year}년)")
st.caption(current_topic["desc"])

required_files = current_topic["check_files"](selected_year)

if ensure_files_for_topic(selected_year, required_files):
    # 1. 지도 생성과 동시에 계산 완료된 df 받기
    df = current_topic["map_func"](data_year=selected_year)
    html_path = current_topic["html_file"](selected_year)

    map_col, data_col = st.columns([1.5, 1.0])

    with map_col:
        st.subheader("🗺️ 지역별 시각화 지도")
        if html_path.exists():
            with open(html_path, "r", encoding="utf-8") as f:
                components.html(f.read(), height=600)
        else:
            st.error("지도 시각화 파일을 불러올 수 없습니다.")

    with data_col:
        st.subheader("📋 지역별 상세 데이터")
        target_col = current_topic["target_col"]
        if df is not None and target_col in df.columns:
            clean_df = df[[col for col in df.columns if "표시" not in col]]
            sorted_df = clean_df.sort_values(
                by=target_col, ascending=False
            ).reset_index(drop=True)
            st.dataframe(sorted_df, use_container_width=True, height=550)
