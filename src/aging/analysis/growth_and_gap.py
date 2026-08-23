"""
[고령화 파트] 지역별 증가속도 비교 + 의료 취약지역 격차점수 산출 (2015~2024)

기존 상관분석(같은 시점 내 지역 간 비교)과 달리, "10년간 각 지역이 얼마나 빠르게
변했는지"를 계산한다 — 대시보드 "의료 취약지역 TOP 5"에 쓰이는 격차점수도 여기서 나온다.

산출 지표 (시도별 1행):
  - 고령화_증가폭: 2024년 고령인구비율 - 2015년 고령인구비율 (%p)
  - 시설_증가율 / 요양병원_증가율: (2024값 - 2015값) / 2015값 * 100 (%)
  - 격차점수: z(고령화_증가폭) - z(공급_증가율)
      -> 클수록 "고령화는 빨리 진행됐는데 공급 증가는 못 따라간" 지역

실행: python -m src.aging.analysis.growth_and_gap
"""
import pandas as pd

from src.aging.collect.common import PROCESSED_DIR, get_logger

logger = get_logger(__name__)

PANEL_PATH = PROCESSED_DIR / "aging_panel_2015_2024.csv"
OUT_PATH = PROCESSED_DIR / "growth_gap_2015_2024_sy.csv"


def _zscore(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / s.std(ddof=0)


def compute_growth_gap(panel: pd.DataFrame) -> pd.DataFrame:
    start_year, end_year = panel["연도"].min(), panel["연도"].max()
    start = panel[panel["연도"] == start_year].set_index("시도")
    end = panel[panel["연도"] == end_year].set_index("시도")

    out = pd.DataFrame(index=start.index)
    out["고령인구비율_시작"] = start["고령인구비율"]
    out["고령인구비율_종료"] = end["고령인구비율"]
    out["고령화_증가폭"] = round(end["고령인구비율"] - start["고령인구비율"], 2)

    for col, label in [
        ("고령인구10만명당_노인복지시설수", "시설"),
        ("고령인구10만명당_요양병원수", "요양병원"),
    ]:
        out[f"{label}_시작"] = round(start[col], 2)
        out[f"{label}_종료"] = round(end[col], 2)
        out[f"{label}_증가율"] = round((end[col] - start[col]) / start[col] * 100, 1)

    # 격차점수: 고령화는 빨리 늘었는데 공급(노인복지시설·요양병원 평균 증가율)은 못 따라간 정도
    out["공급_증가율_평균"] = out[["시설_증가율", "요양병원_증가율"]].mean(axis=1)
    out["격차점수"] = round(_zscore(out["고령화_증가폭"]) - _zscore(out["공급_증가율_평균"]), 3)

    out = out.reset_index().rename(columns={"index": "시도"})
    out.insert(1, "기간", f"{start_year}~{end_year}")
    return out.sort_values("격차점수", ascending=False).reset_index(drop=True)


def main() -> None:
    panel = pd.read_csv(PANEL_PATH)
    result = compute_growth_gap(panel)
    result.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
    logger.info(f"저장 완료: {OUT_PATH} ({len(result)}행)")

    logger.info("=== 격차점수 상위 5개 지역(취약) ===")
    for _, r in result.head(5).iterrows():
        logger.info(
            f"{r['시도']}: 격차점수={r['격차점수']}, 고령화 +{r['고령화_증가폭']}%p, "
            f"시설 {r['시설_증가율']}%, 요양병원 {r['요양병원_증가율']}%"
        )


if __name__ == "__main__":
    main()
