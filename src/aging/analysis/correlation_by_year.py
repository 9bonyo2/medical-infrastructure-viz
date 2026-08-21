"""
[고령화 파트] 연도별(2015~2024) 패널 상관계수 산출

기존 correlation.py(2024년 단일연도 상관계수 1개)와 달리, aging_panel_2015_2024.csv를 이용해
연도마다 Pearson/Spearman r을 각각 계산한다 — "고령화율과 시설 공급 간 관계가 시간이 갈수록
강해지는가/약해지는가"라는 추세를 보기 위함. (각 연도는 n=17짜리 독립된 횡단면 상관계수이며,
패널회귀/고정효과 모델이 아니다.)

실행: python -m src.aging.analysis.correlation_by_year
"""
import pandas as pd
from scipy import stats

from src.aging.collect.common import PROCESSED_DIR, get_logger

logger = get_logger(__name__)

PANEL_PATH = PROCESSED_DIR / "aging_panel_2015_2024.csv"
OUT_PATH = PROCESSED_DIR / "correlation_by_year.csv"

# (x, y, 설명) — correlation.py의 CORR_PAIRS와 동일한 규모보정 지표 쌍을 연도별로 반복 계산
YEARLY_PAIRS = [
    ("고령인구비율", "고령인구10만명당_노인복지시설수", "고령인구비율 vs 고령인구 10만명당 노인복지시설 수"),
    ("고령인구비율", "고령인구10만명당_요양병원수", "고령인구비율 vs 고령인구 10만명당 요양병원 수"),
]


def compute_by_year(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for year, group in panel.groupby("연도"):
        for x, y, desc in YEARLY_PAIRS:
            pearson_r, pearson_p = stats.pearsonr(group[x], group[y])
            spearman_r, spearman_p = stats.spearmanr(group[x], group[y])
            rows.append(
                {
                    "연도": year, "x": x, "y": y, "설명": desc,
                    "pearson_r": round(pearson_r, 3), "pearson_p": round(pearson_p, 4),
                    "spearman_r": round(spearman_r, 3), "spearman_p": round(spearman_p, 4),
                    "n": len(group),
                }
            )
    return pd.DataFrame(rows).sort_values(["y", "연도"]).reset_index(drop=True)


def main() -> None:
    panel = pd.read_csv(PANEL_PATH)
    result = compute_by_year(panel)
    result.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
    logger.info(f"연도별 상관분석 결과 저장: {OUT_PATH} ({len(result)}행)")

    for y in result["y"].unique():
        sub = result[result["y"] == y]
        trend = " -> ".join(f"{int(r.연도)}:{r.pearson_r}" for r in sub.itertuples())
        logger.info(f"[{y}] 연도별 Pearson r 추이: {trend}")


if __name__ == "__main__":
    main()
