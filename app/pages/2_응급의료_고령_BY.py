# ============================================================
# 1. 라이브러리 불러오기
# 발표 설명: 파일 경로 처리, 데이터 분석, 통계 분석, 그래프 및
# Streamlit 화면 구성을 위해 필요한 라이브러리를 불러옵니다.
# ============================================================
from pathlib import Path
import json

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 팀 프로젝트에서 공통으로 사용하는 디자인·사이드바·화면 구성 함수입니다.
from utils.style import inject_base_style
from utils.nav import render_sidebar
from utils.components import (
    kpi_row,
    region_panel,
    correlation_trend_chart,
    small_multiples_grid,
)
from utils.sample_data import (
    get_emergency_kpis,
    get_region_vulnerability_df,
    get_correlation_trend_df,
    get_small_multiples_df,
)
# Pearson은 직선적인 상관관계, Spearman은 순위 기반 상관관계를 계산합니다.
from scipy.stats import pearsonr, spearmanr

# ============================================================
# 2. Streamlit 페이지 기본 설정
# set_page_config는 한 페이지에서 한 번만, 첫 Streamlit 명령으로 실행합니다.
# ============================================================
st.set_page_config(page_title="응급의료 균형 분석", page_icon="🚑", layout="wide")

# 팀 공통 CSS를 적용하고 현재 페이지가 선택된 사이드바를 출력합니다.
inject_base_style()
render_sidebar(active_key="emergency_by")

# TODO(팀): 아래는 고령화 페이지와 동일한 레이아웃의 템플릿입니다.
#   utils/sample_data.py 에 응급의료 전용 데이터 함수를 추가한 뒤
#   get_correlation_trend_df / get_small_multiples_df 자리를 교체해주세요.

# st.markdown('<div class="page-title">인구 고령화 대비 응급의료 수용능력 분석</div>', unsafe_allow_html=True)

# st.set_page_config(
#     page_title="고령화 대비 응급의료 수용능력",
#     page_icon="🏥",
#     layout="wide",
# )

# ============================================================
# 3. 데이터 파일 경로와 지역명 기준 설정
# 현재 파일은 app/pages 안에 있으므로 parents[2]가 프로젝트 최상위입니다.
# ============================================================
BASE_DIR = Path(__file__).resolve().parents[2]
# 고령화 데이터와 응급의료 데이터의 실제 CSV 위치를 조합합니다.
AGING_PATH = BASE_DIR / "data" / "aging" / "processed" / "aging_panel_2015_2024.csv"
EMERGENCY_2015_PATH = (
    BASE_DIR / "data" / "emergency" / "processed" / "emergency_results_2015_processed.csv"
)
EMERGENCY_PATH = BASE_DIR / "data" / "emergency" / "raw" / "emergency_results_2016_2024_api.csv"

GEOJSON_PATH = (
    BASE_DIR
    / "data"
    / "aging"
    / "raw"
    / "skorea_sido_boundary.geojson"
)

# 데이터마다 '서울특별시', '서울'처럼 표기가 다르므로 짧은 명칭으로 통일합니다.
REGION_MAPPING = {
    "서울특별시": "서울", "부산광역시": "부산", "대구광역시": "대구",
    "인천광역시": "인천", "광주광역시": "광주", "대전광역시": "대전",
    "울산광역시": "울산", "세종특별자치시": "세종", "경기도": "경기",
    "강원도": "강원", "강원특별자치도": "강원", "충청북도": "충북",
    "충청남도": "충남", "전라북도": "전북", "전북특별자치도": "전북",
    "전라남도": "전남", "경상북도": "경북", "경상남도": "경남",
    "제주도": "제주", "제주특별자치도": "제주",
}

# 분석용 짧은 지역명을 GeoJSON의 정식 지역명으로 변환합니다.
MAP_REGION_MAPPING = {
    "서울": "서울특별시",
    "부산": "부산광역시",
    "대구": "대구광역시",
    "인천": "인천광역시",
    "광주": "광주광역시",
    "대전": "대전광역시",
    "울산": "울산광역시",
    "세종": "세종특별자치시",
    "경기": "경기도",
    "강원": "강원도",
    "충북": "충청북도",
    "충남": "충청남도",
    "전북": "전라북도",
    "전남": "전라남도",
    "경북": "경상북도",
    "경남": "경상남도",
    "제주": "제주특별자치도",
}

def require_columns(df, columns, filename):
    """CSV에 분석 필수 컬럼이 모두 있는지 검사합니다."""
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(f"{filename}에 필요한 컬럼이 없습니다: {missing}")


# 데이터가 바뀌지 않았다면 다시 읽지 않도록 Streamlit 캐시에 저장합니다.
@st.cache_data
def load_data():
    """2015~2024년 고령화·응급의료 패널 데이터를 만들어 반환합니다."""
    # 먼저 파일 존재 여부를 확인해 경로 오류를 이해하기 쉽게 보여줍니다.
    if not AGING_PATH.exists():
        raise FileNotFoundError(f"고령화 데이터 파일을 찾을 수 없습니다: {AGING_PATH}")
    if not EMERGENCY_PATH.exists():
        raise FileNotFoundError(f"응급의료 데이터 파일을 찾을 수 없습니다: {EMERGENCY_PATH}")
    if not EMERGENCY_2015_PATH.exists():
        raise FileNotFoundError(f"2015년 응급의료 데이터 파일을 찾을 수 없습니다: {EMERGENCY_2015_PATH}")

    # utf-8-sig는 한글 CSV의 글자 깨짐을 줄이기 위한 인코딩 설정입니다.
    aging = pd.read_csv(AGING_PATH, encoding="utf-8-sig")
    emergency = pd.read_csv(EMERGENCY_PATH, encoding="utf-8-sig")
    emergency_2015 = pd.read_csv(EMERGENCY_2015_PATH, encoding="utf-8-sig")

    # 분석 전에 필요한 컬럼이 실제 데이터에 존재하는지 검증합니다.
    require_columns(
        aging,
        ["시도", "연도", "총인구수", "고령인구수_65세이상", "고령인구비율"],
        "aging_panel_2015_2024.csv",
    )
    require_columns(
        emergency,
        ["C2_NM", "DT", "PRD_DE", "C1_NM"],
        "emergency_results_2016_2024_api.csv",
    )
    require_columns(
        emergency_2015,
        ["연도", "시도", "응급진료결과계", "응급진료후전원건수"],
        "emergency_results_2015_processed.csv",
    )

    # 문자로 읽힌 숫자를 계산 가능한 숫자형으로 바꿉니다.
    # 변환할 수 없는 값은 오류 대신 NaN(결측치)으로 처리합니다.
    aging["연도"] = pd.to_numeric(aging["연도"], errors="coerce")
    aging["고령인구비율"] = pd.to_numeric(aging["고령인구비율"], errors="coerce")
    aging["총인구수"] = pd.to_numeric(aging["총인구수"], errors="coerce")
    aging["고령인구수_65세이상"] = pd.to_numeric(
        aging["고령인구수_65세이상"], errors="coerce"
    )
    # 두 데이터가 지역명으로 정확하게 병합되도록 명칭을 통일합니다.
    aging["시도_정리"] = aging["시도"].replace(REGION_MAPPING)

    emergency["PRD_DE"] = pd.to_numeric(emergency["PRD_DE"], errors="coerce")
    emergency["DT"] = pd.to_numeric(emergency["DT"], errors="coerce")
    emergency["C2_NM"] = emergency["C2_NM"].replace(REGION_MAPPING)

    # 2016~2024 원자료에서 지역·연도별 합계와 전원 건수를 열 형태로 변환합니다.
    emergency_panel = (
        emergency[
            (emergency["C2_NM"] != "전체")
            & (emergency["C1_NM"].isin(["합계", "전원"]))
        ]
        .pivot_table(
            index=["PRD_DE", "C2_NM"],
            columns="C1_NM",
            values="DT",
            aggfunc="sum",
        )
        .reset_index()
        .rename(
            columns={
                "PRD_DE": "연도",
                "C2_NM": "시도",
                "합계": "응급진료결과계",
                "전원": "응급진료후전원건수",
            }
        )
    )
    emergency_panel.columns.name = None

    # 별도 형식인 2015년 자료를 동일한 컬럼 구조로 맞춰 2016~2024 자료와 결합합니다.
    emergency_2015 = emergency_2015[emergency_2015["시도"] != "전체"].copy()
    emergency_2015["연도"] = pd.to_numeric(emergency_2015["연도"], errors="coerce")
    emergency_2015["시도"] = emergency_2015["시도"].replace(REGION_MAPPING)
    for column in ["응급진료결과계", "응급진료후전원건수"]:
        emergency_2015[column] = pd.to_numeric(emergency_2015[column], errors="coerce")

    emergency_panel = pd.concat(
        [
            emergency_2015[["연도", "시도", "응급진료결과계", "응급진료후전원건수"]],
            emergency_panel[["연도", "시도", "응급진료결과계", "응급진료후전원건수"]],
        ],
        ignore_index=True,
    )

    # 고령화 자료와 응급의료 자료 양쪽에 모두 존재하는 연도만 선택지로 사용합니다.
    available_years = sorted(
        set(aging["연도"].dropna().astype(int))
        & set(emergency_panel["연도"].dropna().astype(int))
    )
    if not available_years:
        raise ValueError("고령화 자료와 응급의료 자료에 공통 연도가 없습니다.")

    return aging, emergency_panel, available_years


def build_analysis_data(aging, emergency, year):
    """선택 연도의 두 데이터를 지역별로 결합하고 분석 지표를 만듭니다."""
    # 고령화 데이터에서 선택 연도와 분석에 필요한 컬럼만 남깁니다.
    aging_year = aging[aging["연도"] == year].copy()
    aging_year = aging_year[
        ["시도_정리", "총인구수", "고령인구수_65세이상", "고령인구비율"]
    ].drop_duplicates(subset=["시도_정리"])

    # 이미 같은 구조로 결합한 응급의료 패널에서 선택 연도만 추출합니다.
    emergency_year = emergency[emergency["연도"] == year].copy()

    # 특정 연도에 합계 또는 전원 컬럼이 없어도 코드가 멈추지 않게 보완합니다.
    for column in ["응급진료결과계", "응급진료후전원건수"]:
        if column not in emergency_year.columns:
            emergency_year[column] = np.nan

    # 전원율 = 다른 병원으로 옮긴 건수 / 전체 응급진료 결과 × 100
    emergency_year["응급진료후전원율"] = (
        emergency_year["응급진료후전원건수"]
        / emergency_year["응급진료결과계"]
        * 100
    )
    # 비전원율 = 100 - 전원율
    # 이 분석에서는 지역 내에서 진료가 유지된 정도를 보는 '탐색적 대리지표'로 사용합니다.
    emergency_year["응급진료비전원율"] = 100 - emergency_year["응급진료후전원율"]

    # 정리한 지역명을 기준으로 고령화 데이터와 응급의료 데이터를 내부 조인합니다.
    # inner 조인이므로 양쪽 데이터에 모두 존재하는 지역만 결과에 남습니다.
    result = aging_year.merge(
        emergency_year,
        left_on="시도_정리",
        right_on="시도",
        how="inner",
    ).rename(columns={"고령인구비율": "고령화율"})

    # 상관분석에 필요한 두 값이 없는 지역을 제외하고 각각의 중앙값을 구합니다.
    result = result.dropna(subset=["고령화율", "응급진료비전원율"]).copy()
    aging_median = result["고령화율"].median()
    capacity_median = result["응급진료비전원율"].median()

    # 중앙값을 기준으로 지역을 4개 그룹으로 분류합니다.
    # 핵심 그룹은 '고령화는 높지만 비전원율은 낮은 지역'으로 우선 점검 대상입니다.
    result["지역분류"] = np.select(
        [
            (result["고령화율"] >= aging_median)
            & (result["응급진료비전원율"] < capacity_median),
            (result["고령화율"] >= aging_median)
            & (result["응급진료비전원율"] >= capacity_median),
            (result["고령화율"] < aging_median)
            & (result["응급진료비전원율"] < capacity_median),
        ],
        ["고령화 높음·비전원율 낮음", "고령화 높음·비전원율 높음", "고령화 낮음·비전원율 낮음"],
        default="고령화 낮음·비전원율 높음",
    )
    return result, aging_median, capacity_median


def build_yearly_trend(aging, emergency):
    """전국 합계를 기준으로 2015~2024년 두 지표의 연도별 추세를 계산합니다."""
    aging_yearly = (
        aging.groupby("연도", as_index=False)[["총인구수", "고령인구수_65세이상"]]
        .sum()
    )
    aging_yearly["전국_고령화율"] = (
        aging_yearly["고령인구수_65세이상"] / aging_yearly["총인구수"] * 100
    )

    emergency_yearly = (
        emergency.groupby("연도", as_index=False)[["응급진료결과계", "응급진료후전원건수"]]
        .sum()
    )
    emergency_yearly["전국_응급진료비전원율"] = 100 - (
        emergency_yearly["응급진료후전원건수"]
        / emergency_yearly["응급진료결과계"]
        * 100
    )

    return aging_yearly[["연도", "전국_고령화율"]].merge(
        emergency_yearly[["연도", "전국_응급진료비전원율"]],
        on="연도",
        how="inner",
    ).sort_values("연도")

@st.cache_data
def load_sido_geojson():
    """시도 경계 GeoJSON 파일을 불러옵니다."""

    if not GEOJSON_PATH.exists():
        raise FileNotFoundError(
            f"지도 경계 파일을 찾을 수 없습니다: {GEOJSON_PATH}"
        )

    with open(GEOJSON_PATH, encoding="utf-8") as file:
        return json.load(file)

# ============================================================
# 4. Streamlit 화면 구성 및 분석 실행
# ============================================================
st.title("인구 고령화 대비 응급의료 수용능력 분석")
st.caption("시도별 고령화율과 응급진료 후 전원자료를 결합한 상관분석")

# 데이터 로딩 오류가 발생하면 빨간 안내문을 보여주고 페이지 실행을 중단합니다.
try:
    aging_df, emergency_df, years = load_data()
except Exception as error:
    st.error(str(error))
    st.stop()

# KPI 카드 한 칸과 비슷한 너비로, 화면 오른쪽에서 분석 연도를 선택합니다.
year_spacer, year_filter_col = st.columns([3, 1])
with year_filter_col:
    selected_year = st.selectbox(
        "분석 연도",
        options=years,
        index=len(years) - 1,
    )

selected_df, selected_aging_median, selected_capacity_median = build_analysis_data(
    aging_df, emergency_df, selected_year
)

# 지역이 3개 미만이면 상관계수의 의미가 약하므로 분석을 중단합니다.
if len(selected_df) < 3:
    st.warning(
        f"{selected_year}년 병합 결과가 {len(selected_df)}개 지역뿐이어서 "
        "상관분석이 어렵습니다."
    )
    st.dataframe(selected_df, use_container_width=True, hide_index=True)
    st.stop()

# 선택 연도의 카드용 상관계수를 계산합니다.
selected_pearson_r, selected_pearson_p = pearsonr(
    selected_df["고령화율"],
    selected_df["응급진료비전원율"],
)

# 선택 연도의 고령화율은 높고 비전원율은 낮은 지역을 추출합니다.
selected_vulnerable = selected_df[
    selected_df["지역분류"] == "고령화 높음·비전원율 낮음"
].copy()

# KPI 카드 하나를 출력하는 함수
# 이 페이지 파일 안에서만 사용하므로 components.py 수정 불필요
def render_kpi_card(icon, label, value, unit=""):
    card_html = (
        f'<div class="kpi-card">'
        f'<div class="kpi-card-header">'
        f'<span class="kpi-label">{label}</span>'
        f'<span class="kpi-icon">{icon}</span>'
        f'</div>'
        f'<div class="kpi-value">'
        f'{value}<span class="kpi-unit">{unit}</span>'
        f'</div>'
        f'</div>'
    )

    st.markdown(card_html, unsafe_allow_html=True)

# 핵심 결과 4개를 KPI 카드 형태로 한 줄에 표시합니다.
c1, c2, c3, c4 = st.columns(4)
with c1:
    render_kpi_card(
        icon="📉",
        label="Pearson 상관계수",
        value=f"{selected_pearson_r:.3f}",
    )

with c2:
    render_kpi_card(
        icon="🧪",
        label="p-value",
        value=f"{selected_pearson_p:.3f}",
    )

with c3:
    render_kpi_card(
        icon="📍",
        label="분석 지역",
        value=len(selected_df),
        unit="개",
    )

with c4:
    render_kpi_card(
        icon="⚠️",
        label="우선 점검 지역",
        value=len(selected_vulnerable),
        unit="개",
    )

st.write("")

# ============================================================
# 5. 선택 연도 응급진료 비전원율 지도와 우선 점검 TOP 3
# ============================================================

# 분석 데이터의 짧은 지역명을 지도 파일의 정식 지역명으로 변환합니다.
map_df = selected_df.copy()
map_df["시도_지도"] = map_df["시도"].map(MAP_REGION_MAPPING)

try:
    sido_geojson = load_sido_geojson()
except Exception as error:
    st.warning(str(error))
    sido_geojson = None

if sido_geojson is not None:
    # 선택 연도의 시도별 응급진료 비전원율 지도
    map_fig = px.choropleth(
        map_df,
        geojson=sido_geojson,
        locations="시도_지도",
        featureidkey="properties.name",
        color="응급진료비전원율",
        hover_name="시도",
        hover_data={
            "시도_지도": False,
            "고령화율": ":.2f",
            "응급진료후전원율": ":.2f",
            "응급진료비전원율": ":.2f",
        },
        color_continuous_scale="Blues",
        labels={
            "고령화율": "고령화율(%)",
            "응급진료후전원율": "전원율(%)",
            "응급진료비전원율": "비전원율(%)",
        },
    )

    # 지도 크기를 대한민국 시도 경계에 맞춥니다.
    map_fig.update_geos(
        fitbounds="locations",
        visible=False,
    )

    map_fig.update_layout(
        height=430,
        margin={
            "l": 0,
            "r": 0,
            "t": 10,
            "b": 0,
        },
        coloraxis_colorbar={
            "title": "비전원율(%)",
            "thickness": 12,
            "len": 0.65,
        },
    )

    # 고령화율이 높으면서 비전원율이 낮은 지역 중 TOP 3
    vulnerable_top3 = (
        selected_vulnerable.sort_values(
            ["응급진료비전원율", "고령화율"],
            ascending=[True, False],
        )
        .head(3)[
            [
                "시도",
                "고령화율",
                "응급진료비전원율",
            ]
        ]
        .copy()
    )

    # 표의 첫 번째 열에 순위를 추가합니다.
    vulnerable_top3.insert(
        0,
        "순위",
        range(1, len(vulnerable_top3) + 1),
    )

    # 지도와 TOP 3 표를 좌우로 배치합니다.
    map_col, summary_col = st.columns([1.7, 1])

    with map_col:
        with st.container(border=True):
            st.markdown(
                f"##### {selected_year}년 시도별 응급진료 비전원율"
            )

            st.plotly_chart(
                map_fig,
                use_container_width=True,
                config={"displayModeBar": False},
            )

    with summary_col:
        with st.container(border=True):
            st.markdown(
                f"##### {selected_year}년 우선 점검 지역 TOP 3"
            )

            st.dataframe(
                vulnerable_top3,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "순위": st.column_config.NumberColumn(
                        "순위",
                        format="%d",
                    ),
                    "시도": st.column_config.TextColumn(
                        "시도",
                    ),
                    "고령화율": st.column_config.NumberColumn(
                        "고령화율",
                        format="%.2f%%",
                    ),
                    "응급진료비전원율":
                        st.column_config.NumberColumn(
                            "비전원율",
                            format="%.2f%%",
                        ),
                },
            )

            st.markdown(
                """
                비전원율이 낮을수록 응급진료 후 다른 병원으로
                옮겨진 환자 비율이 높다는 의미입니다.

                고령화율이 중앙값 이상인 지역 중 비전원율이
                가장 낮은 3개 지역을 우선 점검 대상으로
                표시했습니다.
                """
            )

st.write("")
# ============================================================
# 6. 2015~2024년 전국 고령화율·응급진료 비전원율 변화
# 두 지표의 값 범위가 달라 왼쪽·오른쪽 Y축을 각각 사용합니다.
# ============================================================
trend_df = build_yearly_trend(aging_df, emergency_df)

trend_fig = make_subplots(specs=[[{"secondary_y": True}]])
trend_fig.add_trace(
    go.Scatter(
        x=trend_df["연도"],
        y=trend_df["전국_고령화율"],
        name="전국 고령화율",
        mode="lines+markers+text",
        text=[f"{value:.1f}%" for value in trend_df["전국_고령화율"]],
        textposition="top center",
        line={"color": "#3B82F6", "width": 3},
        marker={"size": 8},
        hovertemplate="%{x}년<br>고령화율 %{y:.2f}%<extra></extra>",
    ),
    secondary_y=False,
)
trend_fig.add_trace(
    go.Scatter(
        x=trend_df["연도"],
        y=trend_df["전국_응급진료비전원율"],
        name="전국 응급진료 비전원율",
        mode="lines+markers+text",
        text=[f"{value:.2f}%" for value in trend_df["전국_응급진료비전원율"]],
        textposition="bottom center",
        line={"color": "#EF4444", "width": 3},
        marker={"size": 8},
        hovertemplate="%{x}년<br>비전원율 %{y:.2f}%<extra></extra>",
    ),
    secondary_y=True,
)
trend_fig.update_layout(
    height=440,
    hovermode="x unified",
    legend={
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "x": 0,
    },
    margin={"l": 30, "r": 30, "t": 45, "b": 30},
)
trend_fig.update_xaxes(title_text="연도", dtick=1)
trend_fig.update_yaxes(title_text="전국 고령화율(%)", secondary_y=False)
trend_fig.update_yaxes(title_text="전국 응급진료 비전원율(%)", secondary_y=True)

with st.container(border=True):
    st.markdown(
        "##### 2015~2024년 인구 고령화 대비 응급의료 수용능력 변화"
    )
    st.plotly_chart(
        trend_fig,
        use_container_width=True,
        config={"displayModeBar": False},
    )

st.markdown(
    """
<div style="margin-top:8px; padding:14px 18px; background-color:#f5f9ff; border:1px solid #dbeafe; border-left:4px solid #3b82f6; border-radius:8px; color:#334155; font-size:14px; line-height:1.75;">
📌 <span style="color:#2563eb; font-weight:700;">지난 10년간 전국 고령화율</span>은 <span style="color:#2563eb; font-weight:700;">13.1%</span>에서 <span style="color:#2563eb; font-weight:700;">20.0%</span>로 크게 상승했습니다.<br>
반면, 응급실 진료 후 다른 병원으로 옮겨지지 않은 환자 비율은 <span style="color:#2563eb; font-weight:700;">98.54%</span>에서 <span style="color:#2563eb; font-weight:700;">98.27%</span>로 소폭 낮아졌습니다.<br><br>
즉, <span style="color:#2563eb; font-weight:700;">고령인구는 계속 증가했지만 응급환자가 지역 내에서 진료를 마치는 비율은 개선되지 않았습니다.</span><br>
다만 비전원율의 변화 폭은 작으므로, 고령화가 비전원율 하락의 직접적인 원인이라고 단정할 수는 없습니다.
</div>
    """,
    unsafe_allow_html=True,
)
st.write("")
# ============================================================
# 6. 2024년 산점도 작성
# X축은 고령화율, Y축은 응급진료 비전원율입니다.
# 점 크기는 진료 건수, 색은 전원율을 나타냅니다.
# ============================================================
# 산점도와 이후 분석표는 2024년 데이터로 고정합니다.
scatter_year = 2024
df, aging_median, capacity_median = build_analysis_data(
    aging_df,
    emergency_df,
    scatter_year,
)

if len(df) < 3:
    st.warning("2024년 병합 지역이 부족하여 산점도를 표시할 수 없습니다.")
    st.stop()

# 2024년 산점도 해석에 사용할 상관계수를 별도로 계산합니다.
pearson_r, pearson_p = pearsonr(
    df["고령화율"],
    df["응급진료비전원율"],
)
spearman_r, spearman_p = spearmanr(
    df["고령화율"],
    df["응급진료비전원율"],
)

# 산점도 아래 우선 점검 표 역시 2024년 기준으로 유지합니다.
vulnerable = df[
    df["지역분류"] == "고령화 높음·비전원율 낮음"
].copy()

fig = px.scatter(
    df,
    x="고령화율",
    y="응급진료비전원율",
    size="응급진료결과계",
    color="응급진료후전원율",
    text="시도",
    hover_name="시도",
    hover_data={
        "총인구수": ":,.0f",
        "고령인구수_65세이상": ":,.0f",
        "고령화율": ":.2f",
        "응급진료결과계": ":,.0f",
        "응급진료후전원건수": ":,.0f",
        "응급진료후전원율": ":.2f",
        "응급진료비전원율": ":.2f",
        "지역분류": True,
    },
    color_continuous_scale="YlOrRd",
    labels={
        "고령화율": "고령인구비율(%)",
        "응급진료비전원율": "응급진료 비전원율(%)",
        "응급진료후전원율": "전원율(%)",
        "응급진료결과계": "응급진료 건수",
    },
    
)

fig.update_traces(
    textposition="top center",
    marker={"line": {"width": 1, "color": "white"}},
)

# NumPy의 1차 회귀식으로 전체 지역의 변화 경향을 나타내는 추세선을 계산합니다.
x = df["고령화율"].to_numpy()
y = df["응급진료비전원율"].to_numpy()
slope, intercept = np.polyfit(x, y, 1)
x_line = np.linspace(x.min(), x.max(), 100)

# 계산한 회귀선을 빨간색 점선으로 그래프에 추가합니다.
fig.add_trace(
    go.Scatter(
        x=x_line,
        y=slope * x_line + intercept,
        mode="lines",
        name="회귀선",
        line={"color": "#D62728", "width": 2, "dash": "dash"},
        hoverinfo="skip",
    )
)
# 수직·수평 회색선은 각각 고령화율과 비전원율의 중앙값입니다.
# 이 선을 기준으로 그래프가 4개 구역으로 나뉩니다.
fig.add_vline(x=aging_median, line_dash="dot", line_color="gray")
fig.add_hline(y=capacity_median, line_dash="dot", line_color="gray")
fig.update_layout(
    height=650,
    margin={"l": 30, "r": 30, "t": 35, "b": 30},
)

with st.container(border=True):
    st.markdown(
        "##### 2024년 고령화율 대비 응급진료 비전원율"
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": True},
    )

# ============================================================
# 7. 2024년 산점도 핵심 인사이트
# ============================================================

# 상관계수의 절댓값을 기준으로 관계의 강도를 쉬운 표현으로 바꿉니다.
abs_pearson = abs(pearson_r)
if abs_pearson >= 0.7:
    correlation_strength = "강한"
elif abs_pearson >= 0.4:
    correlation_strength = "중간 정도의"
elif abs_pearson >= 0.2:
    correlation_strength = "약한"
else:
    correlation_strength = "거의 없는"

correlation_direction = "음의" if pearson_r < 0 else "양의"

# 산점도에서 대표적으로 확인할 지역과 우선 점검 지역명을 추출합니다.
highest_aging_region = df.loc[df["고령화율"].idxmax()]
lowest_nontransfer_region = df.loc[df["응급진료비전원율"].idxmin()]
priority_region_names = ", ".join(
    vulnerable.sort_values("응급진료비전원율")["시도"].tolist()
)


def render_insight_card(icon, label, content):
    """산점도 핵심 인사이트를 파란 테두리 카드로 출력합니다."""
    st.markdown(
        f'''<div style="min-height:105px; padding:14px 16px; background:#ffffff; border:1px solid #dbeafe; border-left:4px solid #3b82f6; border-radius:8px; color:#334155; font-size:14px; line-height:1.65;">{icon} <span style="color:#2563eb; font-weight:700;">[{label}]</span> {content}</div>''',
        unsafe_allow_html=True,
    )


# ============================================================
# 8. 우선 점검 지역과 전체 분석 데이터 표 출력
# ============================================================
left, right = st.columns([1, 1.7])
with left:
   # 제목과 표 전체를 하나의 테두리 안에 배치
    with st.container(border=True):
        st.markdown("#####  우선 점검 지역")

        vulnerable_table = vulnerable[
            [
                "시도",
                "고령화율",
                "응급진료후전원율",
                "응급진료비전원율",
            ]
        ].copy()

        st.dataframe(
            vulnerable_table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "시도": st.column_config.TextColumn(
                    "시도",
                    width="small",
                ),
                "고령화율": st.column_config.NumberColumn(
                    "고령화율",
                    format="%.2f%%",
                ),
                "응급진료후전원율": st.column_config.NumberColumn(
                    "응급진료 후 전원율",
                    format="%.2f%%",
                ),
                "응급진료비전원율": st.column_config.NumberColumn(
                    "응급진료 비전원율",
                    format="%.2f%%",
                ),
            },
        )
    

with right:
    with st.container(border=True):
        st.markdown("#####  전체 분석 데이터")
        st.dataframe(
            df[
                [
                    "시도", "총인구수", "고령인구수_65세이상", "고령화율",
                    "응급진료결과계", "응급진료후전원건수", "응급진료후전원율",
                    "응급진료비전원율", "지역분류",
                ]
            ].sort_values("고령화율", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

# ============================================================
# 9. 표 데이터 아래 산점도 핵심 인사이트 출력
# ============================================================
st.markdown("#### 핵심 인사이트")

insight_col1, insight_col2 = st.columns(2)
with insight_col1:
    render_insight_card(
        "💡",
        "상관관계",
        f"Pearson 상관계수는 <b>{pearson_r:.3f}</b>으로, 고령화율이 높을수록 "
        f"응급진료 비전원율이 낮아지는 <b>{correlation_strength} "
        f"{correlation_direction} 관계</b>가 나타났습니다.",
    )

with insight_col2:
    render_insight_card(
        "💡",
        "통계적 해석",
        f"p-value는 <b>{pearson_p:.3f}</b>으로 0.05보다 큽니다. 따라서 이러한 "
        "경향은 관찰되지만, <b>통계적으로 확정된 관계라고 단정할 수는 없습니다.</b>",
    )

insight_col3, insight_col4 = st.columns(2)
with insight_col3:
    render_insight_card(
        "💡",
        "우선 점검 지역",
        f"고령화율이 높고 비전원율이 낮은 지역은 <b>{len(vulnerable)}개</b>이며, "
        f"해당 지역은 <b>{priority_region_names}</b>입니다.",
    )

with insight_col4:
    render_insight_card(
        "💡",
        "대표 지역",
        f"고령화율이 가장 높은 지역은 <b>{highest_aging_region['시도']} "
        f"{highest_aging_region['고령화율']:.2f}%</b>, 비전원율이 가장 낮은 지역은 "
        f"<b>{lowest_nontransfer_region['시도']} "
        f"{lowest_nontransfer_region['응급진료비전원율']:.2f}%</b>입니다.",
    )

st.write("")

# 사용자가 지표를 과도하게 해석하지 않도록 정의와 한계를 안내합니다.
with st.expander("지표 정의와 해석 시 주의사항"):
    st.markdown(
        """
        - **고령화율**: 전체 인구 중 65세 이상 인구의 비율입니다.
        - **응급진료 후 전원율**: 응급진료 결과가 전원인 건수 ÷ 전체 응급진료 결과 × 100입니다.
        - **응급진료 비전원율**: 100 − 응급진료 후 전원율입니다.
        - 점의 크기는 시도별 전체 응급진료 건수를 나타냅니다.
        - 점의 색이 진할수록 응급진료 후 전원율이 높습니다.
        - 응급진료 비전원율은 실제 수용 요청 대비 수용 성공률이 아니라, 지역별 응급의료 여건을 비교하기 위한 **탐색적 대리지표**입니다.
        - 상관관계는 인과관계를 의미하지 않습니다.
        """
    )

# 분석 결과를 한글이 깨지지 않는 CSV로 변환해 다운로드 버튼을 제공합니다.
# csv_data = df.to_csv(index=False, encoding="utf-8-sig")
# st.download_button(
#     "분석 데이터 CSV 다운로드",
#     data=csv_data,
#     file_name=f"aging_emergency_capacity_{selected_year}.csv",
#     mime="text/csv",
# )