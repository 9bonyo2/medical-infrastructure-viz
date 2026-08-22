import os
import pandas as pd

# 현재 파일(preprocess.py) 기준 최상위 프로젝트 루트 디렉토리 탐색
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))

# 정제된 데이터가 저장된 실제 경로
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "pediatric")


def load_raw_csv_files() -> tuple[pd.DataFrame, pd.DataFrame]:
    """data/pediatric 폴더 내의 가공된 CSV 파일들을 로드합니다."""
    
    # 1. 출생아수 및 합계출산율 CSV 경로 우선순위
    birth_paths = [
        os.path.join(DATA_DIR, "연도별_출생아수_합계출산율.csv"),
        os.path.join(DATA_DIR, "연도별_출생아수_합계출산율_2.csv"),
        os.path.join(PROJECT_ROOT, "data", "연도별_출생아수_합계출산율.csv"),
    ]

    # 2. 소아청소년과 기관수 CSV 경로 우선순위
    ped_paths = [
        os.path.join(DATA_DIR, "연도별_소아청소년과_기관수_평균.csv"),
        os.path.join(DATA_DIR, "연도별_소아청소년과_기관수_평균_2.csv"),
        os.path.join(PROJECT_ROOT, "data", "연도별_소아청소년과_기관수_평균.csv"),
    ]

    df_birth = None
    for path in birth_paths:
        if os.path.exists(path):
            df_birth = pd.read_csv(path, header=[0, 1])
            break

    df_ped = None
    for path in ped_paths:
        if os.path.exists(path):
            df_ped = pd.read_csv(path)
            break

    if df_birth is None or df_ped is None:
        raise FileNotFoundError(
            "필요한 CSV 데이터를 찾을 수 없습니다. collection.py를 먼저 실행해 주세요."
        )

    return df_birth, df_ped


def process_and_merge_data(
    df_birth: pd.DataFrame, df_ped: pd.DataFrame
) -> pd.DataFrame:
    """출생아 수 및 소아청소년과 기관 수 데이터를 2015~2024년 범위로 전처리하고 병합합니다."""
    sido_col = df_birth.columns[0]
    records = []

    for _, row in df_birth.iterrows():
        sido_name = row[sido_col]
        for year in df_birth.columns.levels[0]:
            if year == "연도별":
                continue
            try:
                yr_int = int(year)
                # 2015년~2024년 필터링
                if not (2015 <= yr_int <= 2024):
                    continue

                birth_count = row[(year, "출생아수")]
                fertility_rate = row[(year, "합계출산율")]
                records.append(
                    {
                        "연도별": yr_int,
                        "시도별": str(sido_name).strip(),
                        "출생아수": float(birth_count),
                        "합계출산율": float(fertility_rate),
                    }
                )
            except (KeyError, ValueError):
                continue

    df_birth_long = pd.DataFrame(records)

    df_ped["연도별"] = df_ped["연도별"].astype(int)
    df_ped["시도별"] = df_ped["시도별"].astype(str).str.strip()

    # 2015년~2024년 필터링
    df_ped = df_ped[(df_ped["연도별"] >= 2015) & (df_ped["연도별"] <= 2024)]

    df_merged = pd.merge(
        df_birth_long, df_ped, on=["연도별", "시도별"], how="inner"
    )
    df_merged.rename(
        columns={"소아청소년과": "소아청소년과_기관수"}, inplace=True
    )

    return df_merged


def get_preprocessed_data() -> pd.DataFrame:
    """원시 데이터 로드부터 전처리/병합까지의 파이프라인 실행 함수입니다."""
    df_birth, df_ped = load_raw_csv_files()
    return process_and_merge_data(df_birth, df_ped)