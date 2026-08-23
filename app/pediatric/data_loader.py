"""소아과 공급 지표 CSV 로딩과 전처리."""

from io import BytesIO

import pandas as pd
import streamlit as st

from pediatric.config import DATA_PATH, REQUIRED_COLUMNS


@st.cache_data
def read_csv_bytes(file_bytes: bytes) -> pd.DataFrame:
    """UTF-8 또는 CP949 CSV를 읽고 분석에 필요한 열을 정리한다."""
    last_error = None

    for encoding in ("utf-8-sig", "utf-8", "cp949"):
        try:
            data = pd.read_csv(BytesIO(file_bytes), encoding=encoding)
            break
        except UnicodeDecodeError as error:
            last_error = error
    else:
        raise last_error

    data.columns = data.columns.str.strip()
    missing = REQUIRED_COLUMNS.difference(data.columns)
    if missing:
        raise ValueError(f"필수 열이 없습니다: {', '.join(sorted(missing))}")

    data["지역"] = data["지역"].astype("string").str.strip()
    data["시점"] = pd.to_numeric(
        data["시점"].astype(str).str.extract(r"(\d{4})")[0],
        errors="coerce",
    )

    for column in ("의원1개당전문의수", "아동1만명당전문의수"):
        data[column] = pd.to_numeric(
            data[column].astype(str).str.replace(",", "", regex=False),
            errors="coerce",
        )

    return (
        data.dropna(subset=["시점", "지역"])
        .assign(시점=lambda frame: frame["시점"].astype(int))
        .sort_values(["시점", "지역"])
        .reset_index(drop=True)
    )


def load_data() -> pd.DataFrame:
    """app/data/ped_stats.csv를 자동으로 읽는다."""
    if not DATA_PATH.is_file():
        st.error(f"CSV 파일을 찾을 수 없습니다: {DATA_PATH}")
        st.caption("`app/data/ped_stats.csv` 경로에 파일이 있는지 확인해 주세요.")
        st.stop()

    return read_csv_bytes(DATA_PATH.read_bytes())

