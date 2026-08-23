"""
[고령화 파트 · 서연] 격차점수 기반 취약지역 TOP5

기존 utils/sample_data.py 의 get_top5_vulnerable_df()(시군구 예시 더미)는 건드리지 않고,
이 파일에서 실제 격차점수(2015~2024 고령화 속도 대비 공급 증가 부족 정도)로 별도 랭킹을 만든다.
※ 시군구 단위 실데이터가 없어 시도(17개) 단위로 표시한다.

기존 utils/components.top5_ranking_panel() 컴포넌트는 그대로 재사용(수정 없음).
"""
from pathlib import Path

import pandas as pd
import streamlit as st

from utils.components import top5_ranking_panel

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "aging" / "processed"


@st.cache_data
def load_growth_gap_df() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "growth_gap_2015_2024_sy.csv")


def get_aging_top5_df() -> pd.DataFrame:
    """top5_ranking_panel()이 기대하는 rank/region/score 컬럼 형태로 변환."""
    df = load_growth_gap_df().sort_values("격차점수", ascending=False).head(5).reset_index(drop=True)
    df["rank"] = df.index + 1
    df["region"] = df["시도"]
    df["score"] = df["격차점수"].round(2)
    return df[["rank", "region", "score"]]


def render_vulnerable_top5_section() -> None:
    top5_ranking_panel(
        get_aging_top5_df(),
        title="고령화 파트 취약지역 TOP 5",
        tag="격차점수 · 2015~2024",
        unit_label="격차점수",
    )
    st.caption(
        "격차점수 = z(고령화 증가폭) − z(고령인구10만명당 공급 증가율). "
        "클수록 고령화는 빨리 진행됐는데 노인복지시설·요양병원 공급 증가는 못 따라간 지역입니다. "
        "(다른 파트 지표가 합류하기 전까지는 고령화 파트 단독 지수입니다.)"
    )
