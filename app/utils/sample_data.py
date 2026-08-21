"""
샘플(더미) 데이터
------------------
실제 데이터가 붙기 전까지 UI 레이아웃 확인용으로 쓰는 예시 데이터입니다.
각 함수의 반환 형태(DataFrame 컬럼명)만 유지한 채, 팀원들이 실제 수집/전처리한
데이터로 내부 로직만 교체하면 됩니다. (data/ 폴더에 원본 CSV를 두고 여기서 읽어오는 식 추천)

예) def get_region_vulnerability_df():
        df = pd.read_csv("data/processed/region_vulnerability.csv")
        return df
"""

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)

# 디자인 시안의 버블맵 레이아웃을 흉내낸 17개 시도의 임의 좌표
# ⚠️ 실제 지도(위경도/GeoJSON) 라이브러리로 교체 예정 지점 — 팀 논의된 라이브러리로 교체하세요.
REGION_LAYOUT = {
    "서울":   (2, 8),
    "강원":   (4, 8),
    "경기":   (2, 7),
    "충북":   (3, 6),
    "충남":   (1, 6),
    "경북":   (4, 6),
    "전북":   (2, 5),
    "경남":   (4, 5),
    "전남":   (2, 4),
    "제주":   (2, 3),
    "인천":   (1, 8),
    "대전":   (1.6, 6.3),
    "세종":   (1.8, 6.6),
    "광주":   (1.6, 4.6),
    "대구":   (3.6, 6.3),
    "울산":   (4.2, 5.6),
    "부산":   (4, 5.2),
}


def get_region_vulnerability_df() -> pd.DataFrame:
    """메인 대시보드 '전국 의료 취약도 현황' 버블차트용 데이터."""
    rows = []
    for name, (x, y) in REGION_LAYOUT.items():
        score = int(RNG.integers(20, 95))
        rows.append(
            {
                "region": name,
                "x": x,
                "y": y,
                "vulnerability_score": score,
                "population": int(RNG.integers(200_000, 9_000_000)),
            }
        )
    return pd.DataFrame(rows)


def get_top5_vulnerable_df() -> pd.DataFrame:
    """우측 'TOP 5' 랭킹 리스트용 데이터."""
    data = [
        {"rank": 1, "region": "전라남도 보성군", "score": 89},
        {"rank": 2, "region": "경상북도 영양군", "score": 84},
        {"rank": 3, "region": "강원특별자치도 삼척시", "score": 78},
        {"rank": 4, "region": "경상남도 산청군", "score": 75},
        {"rank": 5, "region": "전라북도 장수군", "score": 72},
    ]
    return pd.DataFrame(data)


def get_overview_kpis() -> dict:
    return {
        "analysis_target": "17개 시도",
        "analysis_period": "2015~2024",
        "analysis_fields": "4개 영역",
        "vulnerable_top": "TOP 5",
    }


def get_aging_kpis() -> dict:
    return {
        "facility_per_100k": {"value": 2.48, "unit": "개", "delta": "0.15 (6.4%)", "trend": "up"},
        "specialist_per_100k": {"value": 4.63, "unit": "명", "delta": "0.32 (7.4%)", "trend": "up"},
        "transfer_rate": {"value": 18.7, "unit": "%", "delta": "1.2%p", "trend": "up"},
        "emergency_cases": {"value": 7_842_123, "unit": "건", "delta": "5.6%", "trend": "up"},
    }


def get_emergency_kpis() -> dict:
    return {
        "facility_per_100k": {"value": 2.12, "unit": "개", "delta": "0.05 (2.4%)", "trend": "up"},
        "bed_capacity": {"value": 6.8, "unit": "병상", "delta": "0.3 (4.6%)", "trend": "up"},
        "response_time": {"value": 9.4, "unit": "분", "delta": "0.4분", "trend": "down"},
        "transfer_success": {"value": 91.2, "unit": "%", "delta": "0.8%p", "trend": "up"},
    }


def get_birth_kpis() -> dict:
    return {
        "birth_rate": {"value": 0.72, "unit": "명", "delta": "0.02", "trend": "down"},
        "pediatric_per_100k": {"value": 3.1, "unit": "개", "delta": "0.2 (6.1%)", "trend": "down"},
        "delivery_hospitals": {"value": 452, "unit": "개소", "delta": "12개소", "trend": "down"},
        "newborns": {"value": 230_014, "unit": "명", "delta": "3.4%", "trend": "down"},
    }


def get_correlation_trend_df() -> pd.DataFrame:
    """'고령인구비율 vs 시설 공급 — 연도별 상관계수 추이' 라인차트용 데이터."""
    years = list(range(2015, 2025))
    welfare_r = [0.64, 0.61, 0.59, 0.56, 0.73, 0.55, 0.53, 0.53, 0.54, 0.51]
    hospital_r = [-0.38, -0.37, -0.28, -0.17, -0.08, -0.02, 0.03, 0.07, 0.10, 0.19]
    return pd.DataFrame({"year": years, "노인복지시설": welfare_r, "요양병원": hospital_r})


def get_small_multiples_df(metric: str) -> pd.DataFrame:
    """연도별 소규모 산점도(고령인구비율 vs 시설 수) 그리드용 더미 데이터."""
    frames = []
    for year in range(2015, 2025):
        n = 40
        x = RNG.uniform(5, 30, n)  # 고령인구비율(%)
        if metric == "노인복지시설":
            y = 30 * x + RNG.normal(0, 300, n) + 200
        else:  # 요양병원
            y = -0.3 * x + RNG.normal(0, 8, n) + 20
        frames.append(pd.DataFrame({"year": year, "고령인구비율": x, "value": y}))
    return pd.concat(frames, ignore_index=True)
