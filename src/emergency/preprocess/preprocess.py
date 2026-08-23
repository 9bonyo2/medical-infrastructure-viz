import os
import pandas as pd
from src.emergency.config import (
    DOCTOR_DIR, EMERGENCY_DIR, POPULATION_DIR, TIME_DIR
)

# 2글자 지역명 매핑 딕셔너리
REGION_DICT = {
    '서울특별시': '서울',
    '부산광역시': '부산',
    '대구광역시': '대구',
    '인천광역시': '인천',
    '광주광역시': '광주',
    '대전광역시': '대전',
    '울산광역시': '울산',
    '세종특별자치시': '세종',
    '경기도': '경기',
    '강원도': '강원',
    '강원특별자치도': '강원',
    '충청북도': '충북',
    '충청남도': '충남',
    '전라북도': '전북',
    '전북특별자치도': '전북',
    '전라남도': '전남',
    '경상북도': '경북',
    '경상남도': '경남',
    '제주특별자치도': '제주',
    '제주도': '제주'
}

def to_csv_emergency(df, year):
    try:
        selected_df = df[['PRD_DE', 'C1_NM', 'C2_NM', 'DT']].\
            rename(columns={
                'PRD_DE': '연도',
                'C1_NM': '응급의료기관유형',
                'C2_NM': '지역',
                'DT': '기관수'
            })

        new_df = selected_df.loc[
            ((selected_df['연도'].astype(str) == str(year)) & 
             (selected_df['응급의료기관유형'] == '계') &
             (selected_df['지역'] != '전체')),
            ['지역', '기관수']].reset_index(drop=True).copy()

        top2 = selected_df[
            (selected_df["연도"].astype(str) == str(year)) & 
            (selected_df["응급의료기관유형"].isin(["권역응급의료센터", "지역응급의료센터"]))
        ]

        top2_sum = pd.to_numeric(top2['기관수'], errors="coerce").groupby(top2['지역']).sum().astype(int)
        new_df["상위2개기관수"] = new_df['지역'].map(top2_sum).fillna(0).astype(int)

        new_df['지역'] = new_df['지역'].astype(str)
        new_df['기관수'] = pd.to_numeric(new_df['기관수']).astype(int)


        EMERGENCY_DIR.mkdir(parents=True, exist_ok=True)
        output_file = EMERGENCY_DIR / f"emer{year}.csv"
        new_df.to_csv(output_file, index=False)
        print(f'emer{year}.csv creation success')
    
    except Exception as e:
        print(f'[error] {e}')
        return

def to_csv_population(df, year):
    try:
        selected_df = df[['PRD_DE', 'C1_NM', 'C2_NM', 'DT']].\
            rename(columns={
                'PRD_DE': '연도',
                'C1_NM': '지역',
                'C2_NM': '구분',
                'DT': '인구수'
            })
        
        new_df = selected_df.loc[
            ((selected_df['연도'].astype(str) == str(year)) & 
            (selected_df['지역'] != '전국') &
            (selected_df['구분'].isin(['합계', '계']))),
            ['지역', '인구수']].reset_index(drop=True).copy()
        
        new_df['지역'] = new_df['지역'].map(REGION_DICT)
        new_df['지역'] = new_df['지역'].astype(str)
        new_df['인구수'] = pd.to_numeric(new_df['인구수'], errors="coerce").fillna(0).astype(int)

        POPULATION_DIR.mkdir(parents=True, exist_ok=True)
        output_file = POPULATION_DIR / f"pop{year}.csv"
        new_df.to_csv(output_file, index=False)
        print(f'pop{year}.csv creation success')

    except Exception as e:
        print(f'[error] {e}')
        return

def to_csv_doctor(df, year):
    try:
        df_filtered = df[df["C1_NM"] == "전체"].copy()
        selected_df = df_filtered[['PRD_DE', 'C1_NM', 'C2_NM', 'DT']].\
            rename(columns={
                'PRD_DE': '연도',
                'C1_NM': '성별',
                'C2_NM': '지역',
                'DT': '응급의학_전문의수'
            })
        
        new_df = selected_df.loc[
            ((selected_df['연도'].astype(str) == str(year)) & 
            (selected_df['지역'] != '전체')),
            ['지역', '응급의학_전문의수']].reset_index(drop=True).copy()
        
        new_df['지역'] = new_df['지역'].astype(str)
        new_df['응급의학_전문의수'] = pd.to_numeric(new_df['응급의학_전문의수'],errors='coerce').fillna(0).astype(int)

        DOCTOR_DIR.mkdir(parents=True, exist_ok=True)
        output_file = DOCTOR_DIR / f"doc{year}.csv"
        new_df.to_csv(output_file, index=False)
        print(f'doc{year}.csv creation success')

    except Exception as e:
        print(f'[error] {e}')
        return

def to_csv_time(df, year):
    try:
        exclude_columns = ['TD_00','TD_01','TD_02','TD_09']
        df_filtered = df[~df["C1"].isin(exclude_columns)].copy()

        selected_df = df_filtered[['PRD_DE', 'C1', 'C2_NM', 'DT']].\
            rename(columns={
                'PRD_DE': '연도',
                'C1': '소요시간',
                'C2_NM': '지역',
                'DT': '환자수'
            })
        
        new_df = selected_df.loc[
            ((selected_df['연도'].astype(str) == str(year)) & 
            (selected_df['지역'] != '전체')),
            ['지역', '환자수']].reset_index(drop=True).copy()
        
        new_df['지역'] = new_df['지역'].astype(str)
        new_df['환자수'] = pd.to_numeric(new_df['환자수'],errors='coerce').fillna(0).astype(int)

        new_df = (
            new_df.groupby("지역", as_index=False)["환자수"]
            .sum()
            .rename(columns={"환자수": "2시간이상_소요환자수"})
        )

        TIME_DIR.mkdir(parents=True, exist_ok=True)
        output_file = TIME_DIR / f"time{year}.csv"
        new_df.to_csv(output_file, index=False)
        print(f'time{year}.csv creation success')

    except Exception as e:
        print(f'[error] {e}')
        return