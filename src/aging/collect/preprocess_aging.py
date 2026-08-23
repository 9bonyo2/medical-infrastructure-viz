"""
[Step 1] 데이터 전처리 스크립트
-------------------------------
원본 데이터(@data/aging/raw/aging_raw_2015-2024.csv)를 로드하고
결측치/이상치 처리, 시도 명칭 통일 정제를 수행한 뒤
'data/aging/processed/aging_processed_2015-2024.csv'로 저장합니다.
"""

import sys
import io
import os
from pathlib import Path
import pandas as pd

# 한글 출력 환경 지원
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except Exception:
        pass

# 프로젝트 경로 설정
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parents[2]
RAW_DATA_PATH = PROJECT_ROOT / "data" / "aging" / "raw" / "aging_raw_2015-2024.csv"
PROCESSED_DIR = PROJECT_ROOT / "data" / "aging" / "processed"

# 사용자 지정 absolute path 지원
ALT_PROCESSED_DIR = Path(r"C:\rookies6\medical-infrastructure-viz\data\aging\processed")

# SIDO 표준화 매핑
SIDO_MAP = {
    "서울": "서울특별시", "서울특별시": "서울특별시", "서울 Seoul": "서울특별시",
    "부산": "부산광역시", "부산광역시": "부산광역시", "부산 Busan": "부산광역시",
    "대구": "대구광역시", "대구광역시": "대구광역시", "대구 Daegu": "대구광역시",
    "인천": "인천광역시", "인천광역시": "인천광역시", "인천 Incheon": "인천광역시",
    "광주": "광주광역시", "광주광역시": "광주광역시", "광주 Gwangju": "광주광역시",
    "대전": "대전광역시", "대전광역시": "대전광역시", "대전 Daejeon": "대전광역시",
    "울산": "울산광역시", "울산광역시": "울산광역시", "울산 Ulsan": "울산광역시",
    "세종": "세종특별자치시", "세종특별자치시": "세종특별자치시", "세종 Sejong": "세종특별자치시",
    "경기": "경기도", "경기도": "경기도", "경기 Gyeonggi": "경기도",
    "강원": "강원특별자치도", "강원도": "강원특별자치도", "강원특별자치도": "강원특별자치도", "강원 Gangwon": "강원특별자치도",
    "충북": "충청북도", "충청북도": "충청북도", "충북 Chungbuk": "충청북도",
    "충남": "충청남도", "충청남도": "충청남도", "충남 Chungnam": "충청남도",
    "전북": "전북특별자치도", "전라북도": "전북특별자치도", "전북특별자치도": "전북특별자치도", "전북 Jeonbuk": "전북특별자치도",
    "전남": "전라남도", "전라남도": "전라남도", "전남 Jeonnam": "전라남도",
    "경북": "경상북도", "경상북도": "경상북도", "경북 Gyeongbuk": "경상북도",
    "경남": "경상남도", "경상남도": "경상남도", "경남 Gyongnam": "경상남도", "경남 Gyeongnam": "경상남도",
    "제주": "제주특별자치도", "제주도": "제주특별자치도", "제주특별자치도": "제주특별자치도", "제주 Jeju": "제주특별자치도",
    "전국": "전국"
}

def standardize_sido(name: str) -> str:
    """시도 명칭을 프로젝트 표준 규격으로 변환"""
    if not isinstance(name, str):
        return name
    return SIDO_MAP.get(name.strip(), name.strip())

def preprocess_aging_data(raw_csv_path: Path = RAW_DATA_PATH) -> pd.DataFrame:
    """
    원본 고령화 데이터를 로드하여 결측치/이상치 처리 및 시도 정제를 수행합니다.
    """
    if not raw_csv_path.exists():
        raise FileNotFoundError(f"원본 데이터 파일이 존재하지 않습니다: {raw_csv_path}")

    # 인코딩 처리 (cp949 또는 euc-kr)
    try:
        df = pd.read_csv(raw_csv_path, encoding='cp949')
    except Exception:
        df = pd.read_csv(raw_csv_path, encoding='euc-kr')

    # 1. 대상 연도 컬럼 추출 ('2015 년' ~ '2024 년')
    year_cols = [c for c in df.columns if '년' in c and any(c.startswith(str(y)) for y in range(2015, 2025))]

    # 2. 65세 이상 연령대 정의
    ages = df['연령별'].unique().tolist()
    senior_ages = [
        a for a in ages 
        if a == '100세 이상' or (a.endswith('세') and a.replace('세', '').isdigit() and int(a.replace('세', '')) >= 65)
    ]

    # 3. 시도 명칭 통일 정제
    df['시도_std'] = df['행정구역(시군구)별'].apply(standardize_sido)

    # 4. 항목별 데이터 분리
    total_df = df[(df['항목'] == '총인구수[명]') & (df['연령별'] == '계')].copy()
    senior_df = df[(df['항목'] == '총인구수[명]') & (df['연령별'].isin(senior_ages))].copy()

    records = []
    sidos = total_df['시도_std'].unique()

    for sido in sidos:
        sido_tot = total_df[total_df['시도_std'] == sido]
        sido_sen = senior_df[senior_df['시도_std'] == sido]
        
        for col in year_cols:
            y_int = int(col.split()[0])
            tot_val = sido_tot[col].values[0] if len(sido_tot) > 0 else None
            
            # 결측치/이상치 확인 (전남광주통합특별시 등 NaN 행 제외)
            if pd.isna(tot_val) or tot_val <= 0:
                continue
                
            sen_val = sido_sen[col].sum()
            aging_ratio = round((sen_val / tot_val) * 100, 2)
            
            # 고령화 단계 판정 (UN 기준)
            if aging_ratio >= 20.0:
                stage = '초고령사회'
            elif aging_ratio >= 14.0:
                stage = '고령사회'
            elif aging_ratio >= 7.0:
                stage = '고령화사회'
            else:
                stage = '일반'
                
            records.append({
                '연도': y_int,
                '시도': sido,
                '총인구 (명)': int(tot_val),
                '65세이상 인구 (명)': int(sen_val),
                '고령화율 (%)': aging_ratio,
                '고령화 단계': stage
            })

    processed_df = pd.DataFrame(records)
    # 연도 및 시도순 정렬
    processed_df.sort_values(by=['연도', '시도'], inplace=True)
    processed_df.reset_index(drop=True, inplace=True)

    return processed_df

def main():
    print("[Step 1] 고령화 raw 데이터 전처리 시작...")
    df = preprocess_aging_data()
    
    # 저장 디렉토리 생성
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    save_path = PROCESSED_DIR / "aging_processed_2015-2024.csv"
    df.to_csv(save_path, index=False, encoding='utf-8-sig')
    print(f"-> 기본 저장 완료: {save_path} ({len(df)}건)")

    # 사용자가 명시한 보조 디렉토리도 준비 및 저장 시도
    try:
        ALT_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        alt_save_path = ALT_PROCESSED_DIR / "aging_processed_2015-2024.csv"
        df.to_csv(alt_save_path, index=False, encoding='utf-8-sig')
        print(f"-> 보조 저장 완료: {alt_save_path}")
    except Exception as e:
        print(f"-> 보조 저장 참고: {e}")

    print("[Step 1] 데이터 전처리 완료!")

if __name__ == "__main__":
    main()
