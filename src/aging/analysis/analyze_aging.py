"""
[Step 2] 데이터 분석 스크립트
-------------------------------
전처리된 고령화 데이터(aging_processed_2015-2024.csv)를 기반으로
아래 3가지 세부 분석 항목을 수행하고 결과를 CSV로 보관합니다:
  (1) 지역별 고령화율 추이 (aging_trend.csv)
  (2) 고령화율 연평균 증감률 CAGR (aging_cagr.csv)
  (3) 지역별 고령화 위험/취약 순위 (aging_risk_rank.csv)
"""

import sys
import io
from pathlib import Path
import pandas as pd

# 한글 출력 설정
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except Exception:
        pass

# 경로 설정
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "aging" / "processed"
INPUT_CSV = PROCESSED_DIR / "aging_processed_2015-2024.csv"

# 보조 저장 경로
ALT_PROCESSED_DIR = Path(r"C:\rookies6\medical-infrastructure-viz\data\aging\processed")


def analyze_aging_trend(df: pd.DataFrame) -> pd.DataFrame:
    """(1) 지역별 고령화율 추이 데이터프레임 생성"""
    trend_df = df.copy()
    trend_df.sort_values(by=['연도', '시도'], inplace=True)
    return trend_df


def analyze_aging_cagr(df: pd.DataFrame) -> pd.DataFrame:
    """(2) 고령화율 연평균 증감률 (CAGR: 2015년~2024년, 9개년 기준) 데이터프레임 생성"""
    df_2015 = df[df['연도'] == 2015].set_index('시도')['고령화율 (%)']
    df_2024 = df[df['연도'] == 2024].set_index('시도')['고령화율 (%)']

    cagr_list = []
    sidos = df['시도'].unique()

    for sido in sidos:
        r2015 = df_2015.get(sido)
        r2024 = df_2024.get(sido)
        
        if r2015 is not None and r2024 is not None and r2015 > 0:
            diff_p = round(r2024 - r2015, 2)
            # CAGR 공식: (r2024 / r2015)^(1/9) - 1
            cagr_val = round((pow(r2024 / r2015, 1 / 9) - 1) * 100, 2)
            
            cagr_list.append({
                '시도': sido,
                '2015_고령화율(%)': r2015,
                '2024_고령화율(%)': r2024,
                '변화폭(%p)': diff_p,
                'CAGR(%)': cagr_val
            })

    cagr_df = pd.DataFrame(cagr_list)

    # 전국과 17개 시도 각각 순위 부여
    sido_cagr = cagr_df[cagr_df['시도'] != '전국'].copy()
    sido_cagr.sort_values(by='CAGR(%)', ascending=False, inplace=True)
    sido_cagr['CAGR_순위'] = range(1, len(sido_cagr) + 1)

    nat_cagr = cagr_df[cagr_df['시도'] == '전국'].copy()
    if not nat_cagr.empty:
        nat_cagr['CAGR_순위'] = 0
        final_cagr = pd.concat([nat_cagr, sido_cagr], ignore_index=True)
    else:
        final_cagr = sido_cagr

    return final_cagr


def analyze_aging_risk_rank(df: pd.DataFrame) -> pd.DataFrame:
    """(3) 지역별 고령화 위험/취약 순위 데이터프레임 생성 (고령화율 높은 순 = 1위)"""
    # 17개 시도 대상 (전국 제외)
    sido_df = df[df['시도'] != '전국'].copy()
    
    # 연도별 위험 순위 (고령화율 내림차순)
    sido_df['위험순위'] = sido_df.groupby('연도')['고령화율 (%)'].rank(ascending=False, method='min').astype(int)

    # 시도별 연도순 정렬 후 전년대비 변화 계산
    sido_df.sort_values(by=['시도', '연도'], inplace=True)
    sido_df['전년대비_증감(%p)'] = round(sido_df.groupby('시도')['고령화율 (%)'].diff(), 2)
    # 순위 변화 (이전 연도 순위 - 현재 연도 순위 : 양수면 위험 순위 상승/취약 심화)
    sido_df['전년대비_순위변화'] = sido_df.groupby('시도')['위험순위'].shift(1) - sido_df['위험순위']
    sido_df['전년대비_순위변화'] = sido_df['전년대비_순위변화'].fillna(0).astype(int)

    # 연도 및 위험순위 순으로 재정렬
    sido_df.sort_values(by=['연도', '위험순위'], inplace=True)
    sido_df.reset_index(drop=True, inplace=True)

    return sido_df


def main():
    print("[Step 2] 데이터 분석 스크립트 실행 시작...")
    
    if not INPUT_CSV.exists():
        print(f"Error: 입력 데이터 파일이 없습니다. ({INPUT_CSV})")
        print("먼저 Step 1 전처리 스크립트(preprocess_aging.py)를 실행하세요.")
        return

    df = pd.read_csv(INPUT_CSV, encoding='utf-8-sig')

    # 1. 추이 분석
    trend_df = analyze_aging_trend(df)
    # 2. CAGR 분석
    cagr_df = analyze_aging_cagr(df)
    # 3. 위험/취약 순위 분석
    risk_rank_df = analyze_aging_risk_rank(df)

    # CSV 저장
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    trend_path = PROCESSED_DIR / "aging_trend.csv"
    cagr_path = PROCESSED_DIR / "aging_cagr.csv"
    risk_path = PROCESSED_DIR / "aging_risk_rank.csv"

    trend_df.to_csv(trend_path, index=False, encoding='utf-8-sig')
    cagr_df.to_csv(cagr_path, index=False, encoding='utf-8-sig')
    risk_rank_df.to_csv(risk_path, index=False, encoding='utf-8-sig')

    print(f"-> 저장 완료: {trend_path.name} ({len(trend_df)}건)")
    print(f"-> 저장 완료: {cagr_path.name} ({len(cagr_df)}건)")
    print(f"-> 저장 완료: {risk_path.name} ({len(risk_rank_df)}건)")

    # 보조 경로에도 저장 시도
    try:
        ALT_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        trend_df.to_csv(ALT_PROCESSED_DIR / "aging_trend.csv", index=False, encoding='utf-8-sig')
        cagr_df.to_csv(ALT_PROCESSED_DIR / "aging_cagr.csv", index=False, encoding='utf-8-sig')
        risk_rank_df.to_csv(ALT_PROCESSED_DIR / "aging_risk_rank.csv", index=False, encoding='utf-8-sig')
        print(f"-> 보조 저장 완료: {ALT_PROCESSED_DIR}")
    except Exception as e:
        print(f"-> 보조 저장 참고: {e}")

    print("[Step 2] 데이터 분석 완료!")


if __name__ == "__main__":
    main()
