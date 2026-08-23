# ============================================================
# 1. 라이브러리 불러오기
# 발표 설명: 파일 경로 처리, 데이터 분석, 통계 분석, 그래프 및
# Streamlit 화면 구성을 위해 필요한 라이브러리를 불러옵니다.
# ============================================================
from pathlib import Path

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

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
AGING_PATH = BASE_DIR / "data" / "aging" / "processed" / "aging_master.csv"
EMERGENCY_PATH = BASE_DIR / "data" / "emergency" / "raw" / "emergency_results_2016_2024_api.csv"

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


def require_columns(df, columns, filename):
    """CSV에 분석 필수 컬럼이 모두 있는지 검사합니다."""
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(f"{filename}에 필요한 컬럼이 없습니다: {missing}")


# 데이터가 바뀌지 않았다면 다시 읽지 않도록 Streamlit 캐시에 저장합니다.
@st.cache_data
def load_data():
    """두 CSV를 읽고 전처리한 뒤 공통 분석 연도와 함께 반환합니다."""
    # 먼저 파일 존재 여부를 확인해 경로 오류를 이해하기 쉽게 보여줍니다.
    if not AGING_PATH.exists():
        raise FileNotFoundError(f"고령화 데이터 파일을 찾을 수 없습니다: {AGING_PATH}")
    if not EMERGENCY_PATH.exists():
        raise FileNotFoundError(f"응급의료 데이터 파일을 찾을 수 없습니다: {EMERGENCY_PATH}")

    # utf-8-sig는 한글 CSV의 글자 깨짐을 줄이기 위한 인코딩 설정입니다.
    aging = pd.read_csv(AGING_PATH, encoding="utf-8-sig")
    emergency = pd.read_csv(EMERGENCY_PATH, encoding="utf-8-sig")

    # 분석 전에 필요한 컬럼이 실제 데이터에 존재하는지 검증합니다.
    require_columns(
        aging,
        ["시도", "기준연도", "총인구수", "고령인구수_65세이상", "고령인구비율"],
        "aging_master.csv",
    )
    require_columns(
        emergency,
        ["C2_NM", "DT", "PRD_DE", "C1_NM"],
        "emergency_results_2016_2024_api.csv",
    )

    # 문자로 읽힌 숫자를 계산 가능한 숫자형으로 바꿉니다.
    # 변환할 수 없는 값은 오류 대신 NaN(결측치)으로 처리합니다.
    aging["기준연도"] = pd.to_numeric(aging["기준연도"], errors="coerce")
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

    # 고령화 자료와 응급의료 자료 양쪽에 모두 존재하는 연도만 선택지로 사용합니다.
    available_years = sorted(
        set(aging["기준연도"].dropna().astype(int))
        & set(emergency["PRD_DE"].dropna().astype(int))
    )
    if not available_years:
        raise ValueError("고령화 자료와 응급의료 자료에 공통 연도가 없습니다.")

    return aging, emergency, available_years


def build_analysis_data(aging, emergency, year):
    """선택 연도의 두 데이터를 지역별로 결합하고 분석 지표를 만듭니다."""
    # 고령화 데이터에서 선택 연도와 분석에 필요한 컬럼만 남깁니다.
    aging_year = aging[aging["기준연도"] == year].copy()
    aging_year = aging_year[
        ["시도_정리", "총인구수", "고령인구수_65세이상", "고령인구비율"]
    ].drop_duplicates(subset=["시도_정리"])

    # 응급의료 데이터도 선택 연도만 추출합니다.
    # 전국 합계는 제외하고, 전체 결과(합계)와 다른 병원 이송(전원)만 사용합니다.
    emergency_year = emergency[
        (emergency["PRD_DE"] == year)
        & (emergency["C2_NM"] != "전체")
        & (emergency["C1_NM"].isin(["합계", "전원"]))
    ].copy()

    # 행으로 들어 있던 '합계'와 '전원'을 각각의 열로 변환합니다.
    # 결과적으로 지역별 전체 응급진료 건수와 전원 건수를 한 행에서 비교할 수 있습니다.
    emergency_year = (
        emergency_year.pivot_table(
            index="C2_NM", columns="C1_NM", values="DT", aggfunc="sum"
        )
        .reset_index()
        .rename(
            columns={
                "C2_NM": "시도",
                "합계": "응급진료결과계",
                "전원": "응급진료후전원건수",
            }
        )
    )
    emergency_year.columns.name = None

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

# 선택 가능한 연도 중 가장 최신 연도를 자동 사용
selected_year = years[-1]

# # 공통 연도 중 하나를 선택하며, 기본값은 가장 최신 연도입니다.
# selected_year = st.selectbox(
#     "분석 연도",
#     years,
#     index=len(years) - 1,
# )

df, aging_median, capacity_median = build_analysis_data(
    aging_df, emergency_df, selected_year
)

# 지역이 3개 미만이면 상관계수의 의미가 약하므로 분석을 중단합니다.
if len(df) < 3:
    st.warning(f"{selected_year}년 병합 결과가 {len(df)}개 지역뿐이어서 상관분석이 어렵습니다.")
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.stop()

# Pearson: 두 지표의 직선적인 관계와 통계적 유의성을 계산합니다.
pearson_r, pearson_p = pearsonr(df["고령화율"], df["응급진료비전원율"])
# Spearman: 실제 값 대신 순위를 기준으로 두 지표의 관계를 계산합니다.
spearman_r, spearman_p = spearmanr(df["고령화율"], df["응급진료비전원율"])

# 고령화율은 높고 비전원율은 낮은 지역만 우선 점검 대상으로 추출합니다.
vulnerable = df[
    df["지역분류"] == "고령화 높음·비전원율 낮음"
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
        value=f"{pearson_r:.3f}",
    )

with c2:
    render_kpi_card(
        icon="🧪",
        label="p-value",
        value=f"{pearson_p:.3f}",
    )

with c3:
    render_kpi_card(
        icon="📍",
        label="분석 지역",
        value=len(df),
        unit="개",
    )

with c4:
    render_kpi_card(
        icon="⚠️",
        label="우선 점검 지역",
        value=len(vulnerable),
        unit="개",
    )

st.write("")    
# ============================================================
# 5. 산점도 작성
# X축은 고령화율, Y축은 응급진료 비전원율입니다.
# 점 크기는 진료 건수, 색은 전원율을 나타냅니다.
# ============================================================
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
    title=f"{selected_year}년 고령화율 대비 응급진료 비전원율(유지율)",
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
fig.update_layout(height=650, margin={"l": 30, "r": 30, "t": 70, "b": 30})

with st.container(border=True):
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": True}
    )

# ============================================================
# 6. 분석 결과를 쉬운 문장으로 자동 해석
# 일반적으로 p-value가 0.05 미만이면 통계적으로 유의하다고 판단합니다.
# ============================================================
if pearson_p < 0.05:
    significance = "통계적으로 유의한 관계가 나타났습니다."
else:
    significance = "p-value가 0.05 이상이므로 통계적으로 유의하다고 단정하기 어렵습니다."

# 상관계수의 부호로 관계의 방향을 설명합니다.
# 음수이면 한 지표가 증가할 때 다른 지표가 감소하는 경향입니다.
if pearson_r < 0:
    direction = "고령화율이 높을수록 응급진료 비전원율이 낮아지는 경향"
else:
    direction = "고령화율이 높을수록 응급진료 비전원율도 높아지는 경향"

st.info(
    f"Pearson 상관계수는 {pearson_r:.3f}으로, {direction}이 관찰됐습니다. "
    f"{significance} Spearman 상관계수는 {spearman_r:.3f}입니다."
)

# ============================================================
# 7. 우선 점검 지역과 전체 분석 데이터 표 출력
# ============================================================
left, right = st.columns([1, 1.7])
with left:
   # 제목과 표 전체를 하나의 테두리 안에 배치
    with st.container(border=True):
        st.markdown("##### 🚩 우선 점검 지역")

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
        st.markdown("##### 📋 전체 분석 데이터")
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
csv_data = df.to_csv(index=False, encoding="utf-8-sig")
st.download_button(
    "분석 데이터 CSV 다운로드",
    data=csv_data,
    file_name=f"aging_emergency_capacity_{selected_year}.csv",
    mime="text/csv",
)
