"""
[고령화 파트] 고령인구 vs 노인복지센터(노인복지관) 수 상관관계 분석

data/processed/aging_master.csv 를 입력으로 Pearson/Spearman 상관계수를 계산한다.
Streamlit 앱(app/streamlit_app.py)에서도 동일 함수를 재사용한다.

실행: python -m src.analysis.correlation
"""
import pandas as pd
from scipy import stats

from src.aging.collect.common import PROCESSED_DIR, get_logger

logger = get_logger(__name__)

MASTER_PATH = PROCESSED_DIR / "aging_master.csv"

# 분석에 사용할 지표 쌍: (고령화 지표, 노인복지센터 지표, 설명)
CORR_PAIRS = [
    ("고령인구비율", "노인복지관수", "고령인구비율 vs 노인복지관 수(절대량)"),
    ("고령인구비율", "인구10만명당_노인복지관수", "고령인구비율 vs 인구 10만명당 노인복지관 수(규모보정)"),
    ("고령인구수_65세이상", "노인복지관수", "고령인구 수(절대량) vs 노인복지관 수(절대량)"),
]


def load_master() -> pd.DataFrame:
    return pd.read_csv(MASTER_PATH)


def compute_correlations(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for x, y, desc in CORR_PAIRS:
        pearson_r, pearson_p = stats.pearsonr(df[x], df[y])
        spearman_r, spearman_p = stats.spearmanr(df[x], df[y])
        rows.append(
            {
                "x": x, "y": y, "설명": desc,
                "pearson_r": round(pearson_r, 3), "pearson_p": round(pearson_p, 4),
                "spearman_r": round(spearman_r, 3), "spearman_p": round(spearman_p, 4),
                "n": len(df),
            }
        )
    return pd.DataFrame(rows)


def interpret(r: float) -> str:
    ar = abs(r)
    if ar >= 0.7:
        strength = "강한"
    elif ar >= 0.4:
        strength = "중간"
    elif ar >= 0.2:
        strength = "약한"
    else:
        strength = "거의 없는"
    direction = "양(+)의" if r > 0 else "음(-)의"
    return f"{strength} {direction} 상관관계"


def main() -> None:
    df = load_master()
    result = compute_correlations(df)
    out_path = PROCESSED_DIR / "correlation_result.csv"
    result.to_csv(out_path, index=False, encoding="utf-8-sig")
    logger.info(f"상관분석 결과 저장: {out_path}")

    for _, row in result.iterrows():
        logger.info(
            f"{row['설명']}: Pearson r={row['pearson_r']} (p={row['pearson_p']}) "
            f"-> {interpret(row['pearson_r'])}"
        )


if __name__ == "__main__":
    main()
