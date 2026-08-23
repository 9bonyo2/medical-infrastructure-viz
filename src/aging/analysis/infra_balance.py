"""
# 노인의료 및 복지시설 수급 균형 분석 모듈 (infra_balance.py)
===========================================================
이 모듈은 고령화에 따른 노인복지시설과 요양병원의 수급 균형 상태를 데이터 기반으로 
전처리 및 분석하기 위해 작성되었습니다.

## 처리 흐름 (Process Flow)
1. **데이터 전처리 (Preprocessing)**
   - raw 데이터 로드: 
     - 노인복지시설 (`senior_welfare_facilities_raw.csv`)
     - 의료기관 현황 (`kosis_medical_hospital_raw.csv`)
   - 2015년 ~ 2024년 범위 데이터 추출 및 필터링
   - 시도 명칭 통일 (예: '서울 Seoul' -> '서울특별시')
   - 요양병원 지표만 정밀 추출 및 분기별 평균을 통해 연도별 수치 산출
   - 전처리 결과 저장:
     - `senior_welfare_processed.csv`
     - `care_hospitals_processed.csv`
2. **메인 분석 (Main Analysis)**
   - [분석 1] 전국 연도별 복지시설 vs 요양병원 공급 추이 분석 -> `1_national_yearly_supply_trend_result.csv`
   - [분석 2] 지역별 연도별 복지시설 vs 요양병원 인프라 상대적 비율 비교 (Min-Max 정규화) -> `2_regional_yearly_minmax_normalized_result.csv`
   - [분석 3] 10년간(2015~2024) 지역별 복지/의료시설 연평균 증감률 (CAGR) 분석 -> `3_regional_10yr_cagr_analysis_result.csv`
3. **일괄 실행 (Main Runner)**
   - `python -m src.aging.analysis.infra_balance` 실행 시 전체 파이프라인 자동 구동

## 제공 함수 목록 (API Functions)
- `clean_sido(sido_str)`: 시도 명칭 통일 규칙을 적용하는 헬퍼 함수
- `preprocess_data()`: raw 데이터를 정제하여 processed 폴더에 저장하는 전처리 함수
- `analyze_supply_trend(welfare_df, hospital_df)`: 전국 단위 시계열 공급량 추이 분석 함수
- `analyze_minmax_normalized(welfare_df, hospital_df)`: 지역별/연도별 Min-Max 정규화 비율 비교 함수
- `analyze_cagr(welfare_df, hospital_df)`: 10년간 연평균 증감률(CAGR) 분석 함수
"""

import os
import sys
import pandas as pd
import numpy as np

# 시도 명칭 통일 맵
SIDO_MAP = {
    "서울": "서울특별시",
    "부산": "부산광역시",
    "대구": "대구광역시",
    "인천": "인천광역시",
    "광주": "광주광역시",
    "대전": "대전광역시",
    "울산": "울산광역시",
    "세종": "세종특별자치시",
    "경기": "경기도",
    "강원": "강원특별자치도",
    "충북": "충청북도",
    "충남": "충청남도",
    "전북": "전북특별자치도",
    "전남": "전라남도",
    "경북": "경상북도",
    "경남": "경상남도",
    "제주": "제주특별자치도"
}

def clean_sido(sido_str):
    """
    시도 명칭을 표준 명칭(예: '서울특별시')으로 통일합니다.
    """
    if not isinstance(sido_str, str):
        return None
    s = sido_str.strip()
    s_base = s.split()[0]  # 영문 병기 제거 ('서울 Seoul' -> '서울')
    
    # 맵 매핑 적용
    for k, v in SIDO_MAP.items():
        if k in s_base:
            return v
    return s_base

def preprocess_data(raw_dir="data/aging/raw", processed_dir="data/aging/processed"):
    """
    Raw 데이터를 로드하여 결측치 검사, 연도 필터링, 시도명 정제 등을 완료한 후 
    Processed 디렉토리에 저장합니다.
    """
    print("[1] 데이터 전처리 시작...")
    os.makedirs(processed_dir, exist_ok=True)
    
    welfare_raw_path = os.path.join(raw_dir, "senior_welfare_facilities_raw.csv")
    hospital_raw_path = os.path.join(raw_dir, "kosis_medical_hospital_raw.csv")
    
    if not os.path.exists(welfare_raw_path) or not os.path.exists(hospital_raw_path):
        raise FileNotFoundError(f"필수 Raw 파일이 누락되었습니다: {welfare_raw_path} 또는 {hospital_raw_path}")

    # ──── 1. 노인복지시설 데이터 전처리 ────
    print("  - 노인복지시설 데이터 처리 중...")
    df_welfare = pd.read_csv(welfare_raw_path, encoding="utf-8-sig")
    
    # 결측치 체크
    null_count_welfare = df_welfare.isnull().sum().sum()
    print(f"    * 노인복지시설 데이터 결측치 개수: {null_count_welfare}")
    
    # 연도 범위 필터링 (2015 ~ 2024)
    df_welfare = df_welfare[(df_welfare["연도"] >= 2015) & (df_welfare["연도"] <= 2024)]
    
    # 시도명 통일
    df_welfare["시도"] = df_welfare["시도"].apply(clean_sido)
    
    # 복지시설 합계 연산 (경로당, 복지관, 재가서비스 등 시설수 컬럼 합산)
    facility_cols = [
        "노인여가복지시설_경로당", "노인여가복지시설_복지관",
        "재가노인복지시설_방문요양서비스_시설수", "재가노인복지시설_주야간보호서비스_시설수",
        "재가노인복지시설_단기보호서비스_시설수", "재가노인복지시설_방문목욕서비스_시설수",
        "재가노인복지시설_방문간호서비스_시설수", "재가노인복지시설_재가노인지원서비스_시설수",
        "노인보호전문기관_시설수", "노인일자리지원기관_시설수"
    ]
    # 실제 존재하는 컬럼들만 합산
    actual_facility_cols = [col for col in facility_cols if col in df_welfare.columns]
    df_welfare["복지시설_합계"] = df_welfare[actual_facility_cols].sum(axis=1).astype(int)
    
    # 정제 완료 데이터 저장
    welfare_processed_path = os.path.join(processed_dir, "senior_welfare_processed.csv")
    df_welfare.to_csv(welfare_processed_path, index=False, encoding="utf-8-sig")
    print(f"    * 복지시설 정제 데이터 저장 완료: {welfare_processed_path}")

    # ──── 2. 의료기관(요양병원) 데이터 전처리 ────
    print("  - 의료기관(요양병원) 데이터 처리 중...")
    df_hospital_raw = pd.read_csv(hospital_raw_path, encoding="utf-8-sig")
    
    # 멀티헤더 파악 및 '요양병원' 종별 컬럼 인덱스 추출
    # index 1 행(실제 2번째 줄)에 요양병원 정보가 있음
    hosp_cols = []
    for col in df_hospital_raw.columns:
        if col == "시도별(1)":
            continue
        val = str(df_hospital_raw.loc[1, col]).strip()
        if val == "요양병원":
            hosp_cols.append(col)
            
    print(f"    * 요양병원 데이터 컬럼 개수: {len(hosp_cols)}")
    
    # 시도별 요양병원 수 시계열 데이터 가공
    hospital_records = []
    # index 2부터 실제 시도별 데이터
    for idx, row in df_hospital_raw.iloc[2:].iterrows():
        sido_raw = row["시도별(1)"]
        if sido_raw in ["계", "시도별(1)"]:
            continue
        sido_clean = clean_sido(sido_raw)
        
        for col in hosp_cols:
            # 컬럼명에서 연도 추출 (예: '2015.1/4.4' -> 2015)
            try:
                year = int(col.split(".")[0])
            except ValueError:
                continue
                
            if year < 2015 or year > 2024:
                continue
                
            val_str = str(row[col]).replace(",", "").strip()
            # 결측치나 이상값 처리
            try:
                val = float(val_str) if val_str not in ["-", "", "nan"] else 0.0
            except ValueError:
                val = 0.0
                
            hospital_records.append({
                "시도": sido_clean,
                "연도": year,
                "요양병원수": val
            })
            
    df_hosp_parsed = pd.DataFrame(hospital_records)
    
    # 결측치 체크
    null_count_hosp = df_hosp_parsed.isnull().sum().sum()
    print(f"    * 요양병원 가공 데이터 결측치 개수: {null_count_hosp}")
    
    # 연도별/시도별 분기 평균 요양병원 수 계산
    df_hosp_yearly = df_hosp_parsed.groupby(["시도", "연도"])["요양병원수"].mean().reset_index()
    df_hosp_yearly["요양병원수"] = df_hosp_yearly["요양병원수"].round(0).astype(int)
    
    # 정제 완료 데이터 저장
    hosp_processed_path = os.path.join(processed_dir, "care_hospitals_processed.csv")
    df_hosp_yearly.to_csv(hosp_processed_path, index=False, encoding="utf-8-sig")
    print(f"    * 요양병원 정제 데이터 저장 완료: {hosp_processed_path}")
    print("[1] 데이터 전처리 완료!")
    
    return df_welfare, df_hosp_yearly

def analyze_supply_trend(welfare_df, hospital_df, result_dir="data/aging/result"):
    """
    [분석 1] 전국 연도별 복지시설 vs 요양병원 공급 추이 분석
    """
    print("[2-1] 분석 1 진행 중 (전국 연도별 공급 추이)...")
    os.makedirs(result_dir, exist_ok=True)
    
    # 전국 합계 연산
    df_nat_welfare = welfare_df.groupby("연도")["복지시설_합계"].sum().reset_index()
    df_nat_hosp = hospital_df.groupby("연도")["요양병원수"].sum().reset_index()
    
    df_trend = pd.merge(df_nat_welfare, df_nat_hosp, on="연도")
    df_trend.columns = ["연도", "전국_복지시설_합계", "전국_요양병원_수"]
    
    # 결과 저장
    out_path = os.path.join(result_dir, "1_national_yearly_supply_trend_result.csv")
    df_trend.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"  - 결과 저장 완료: {out_path}")
    return df_trend

def analyze_minmax_normalized(welfare_df, hospital_df, result_dir="data/aging/result"):
    """
    [분석 2] 지역별 연도별 복지시설 vs 요양병원 인프라 상대적 비율 비교 (Min-Max 정규화)
    """
    print("[2-2] 분석 2 진행 중 (지역별/연도별 Min-Max 정규화)...")
    os.makedirs(result_dir, exist_ok=True)
    
    # 시도별/연도별 복지시설 합계 및 요양병원수 병합
    df_w_sub = welfare_df.groupby(["시도", "연도"])["복지시설_합계"].sum().reset_index()
    df_merged = pd.merge(df_w_sub, hospital_df, on=["시도", "연도"])
    df_merged.columns = ["시도", "연도", "복지시설_합계", "요양병원_수"]
    
    # 연도별로 Min-Max 정규화 적용
    normalized_dfs = []
    for year, group in df_merged.groupby("연도"):
        grp = group.copy()
        
        w_min = grp["복지시설_합계"].min()
        w_max = grp["복지시설_합계"].max()
        h_min = grp["요양병원_수"].min()
        h_max = grp["요양병원_수"].max()
        
        # Min-Max 정규화 연산 (분모가 0일 경우 예외처리)
        grp["복지시설_정규화"] = grp["복지시설_합계"].apply(lambda x: (x - w_min) / (w_max - w_min) if w_max > w_min else 0.0)
        grp["요양병원_정규화"] = grp["요양병원_수"].apply(lambda x: (x - h_min) / (h_max - h_min) if h_max > h_min else 0.0)
        grp["인프라_치우침_지수"] = grp["복지시설_정규화"] - grp["요양병원_정규화"]
        
        normalized_dfs.append(grp)
        
    df_normalized = pd.concat(normalized_dfs, ignore_index=True)
    df_normalized = df_normalized.round(4)
    
    # 결과 저장
    out_path = os.path.join(result_dir, "2_regional_yearly_minmax_normalized_result.csv")
    df_normalized.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"  - 결과 저장 완료: {out_path}")
    return df_normalized

def analyze_cagr(welfare_df, hospital_df, result_dir="data/aging/result"):
    """
    [분석 3] 10년간(2015~2024) 전국 의료시설과 복지시설의 연평균 증감률(CAGR) 변화 패턴 종합분석
    """
    print("[2-3] 분석 3 진행 중 (10년간 연평균 증감률 CAGR)...")
    os.makedirs(result_dir, exist_ok=True)
    
    # 시도별/연도별 매핑 데이터 준비
    df_w_sub = welfare_df.groupby(["시도", "연도"])["복지시설_합계"].sum().reset_index()
    df_merged = pd.merge(df_w_sub, hospital_df, on=["시도", "연도"])
    df_merged.columns = ["시도", "연도", "복지시설_합계", "요양병원_수"]
    
    # 2015년과 2024년 데이터 분리 및 추출
    df_2015 = df_merged[df_merged["연도"] == 2015][["시도", "복지시설_합계", "요양병원_수"]]
    df_2024 = df_merged[df_merged["연도"] == 2024][["시도", "복지시설_합계", "요양병원_수"]]
    
    df_cagr = pd.merge(df_2015, df_2024, on="시도", suffixes=("_2015", "_2024"))
    
    # 9년 기간 CAGR 계산
    def get_cagr(start, end, p=9):
        if start <= 0 or end <= 0:
            return 0.0
        return (((end / start) ** (1 / p)) - 1) * 100
        
    df_cagr["복지시설_CAGR(%)"] = df_cagr.apply(lambda r: get_cagr(r["복지시설_합계_2015"], r["복지시설_합계_2024"]), axis=1)
    df_cagr["요양병원_CAGR(%)"] = df_cagr.apply(lambda r: get_cagr(r["요양병원_수_2015"], r["요양병원_수_2024"]), axis=1)
    
    df_cagr = df_cagr[[
        "시도", 
        "복지시설_합계_2015", "복지시설_합계_2024", "복지시설_CAGR(%)",
        "요양병원_수_2015", "요양병원_수_2024", "요양병원_CAGR(%)"
    ]]
    df_cagr.columns = [
        "시도", 
        "복지시설_2015", "복지시설_2024", "복지시설_CAGR(%)",
        "요양병원_2015", "요양병원_2024", "요양병원_CAGR(%)"
    ]
    df_cagr = df_cagr.round(2)
    
    # 결과 저장
    out_path = os.path.join(result_dir, "3_regional_10yr_cagr_analysis_result.csv")
    df_cagr.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"  - 결과 저장 완료: {out_path}")
    return df_cagr

def run_all_pipeline(raw_dir="data/aging/raw", processed_dir="data/aging/processed", result_dir="data/aging/result"):
    """
    전처리 및 3대 분석 파이프라인을 일괄 실행합니다.
    """
    print("==================================================")
    print("  [노인 인프라 수급 균형 분석 파이프라인 일괄 기동]")
    print("==================================================")
    
    # 1. 전처리
    welfare_df, hospital_df = preprocess_data(raw_dir, processed_dir)
    
    # 2. 분석 1
    analyze_supply_trend(welfare_df, hospital_df, result_dir)
    
    # 3. 분석 2
    analyze_minmax_normalized(welfare_df, hospital_df, result_dir)
    
    # 4. 분석 3
    analyze_cagr(welfare_df, hospital_df, result_dir)
    
    print("==================================================")
    print("  [파이프라인 실행 완료 - 모든 분석이 정상 마감되었습니다]")
    print("==================================================")

if __name__ == "__main__":
    # 스크립트 단독 실행 시 구동
    run_all_pipeline()
