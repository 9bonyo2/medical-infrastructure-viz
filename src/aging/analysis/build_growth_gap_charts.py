"""
[고령화 파트] 지역별 증가속도 산점도 / 시도×연도 히트맵 / 취약지역 TOP5 차트 생성

growth_and_gap.py, build_panel.py 의 산출물을 읽어 app/assets/aging/ 에 PNG로 저장한다.

실행: python -m src.aging.analysis.build_growth_gap_charts
"""
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pandas as pd

from src.aging.collect.common import PROCESSED_DIR, ROOT_DIR, get_logger

logger = get_logger(__name__)

for _c in ["Malgun Gothic", "AppleGothic", "NanumGothic"]:
    if any(_c == f.name for f in fm.fontManager.ttflist):
        plt.rcParams["font.family"] = _c
        break
plt.rcParams["axes.unicode_minus"] = False

OUT = ROOT_DIR / "app" / "assets" / "aging"
OUT.mkdir(parents=True, exist_ok=True)

GAP_COLOR = "#e35652"
GRID_COLOR = "#e2e8f0"
TREND_COLOR = "#94a3b8"


def build_growth_scatter(panel: pd.DataFrame, gap: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9, 7), dpi=110)
    x = gap["고령화_증가폭"].to_numpy(float)
    y = gap["공급_증가율_평균"].to_numpy(float)
    score = gap["격차점수"].to_numpy(float)

    sizes = 90 + (score - score.min()) / (score.max() - score.min()) * 220
    colors = plt.cm.Reds(0.35 + 0.55 * (score - score.min()) / (score.max() - score.min()))

    ax.axhline(y.mean(), color=TREND_COLOR, linewidth=1, linestyle="--", zorder=1)
    ax.axvline(x.mean(), color=TREND_COLOR, linewidth=1, linestyle="--", zorder=1)
    ax.scatter(x, y, s=sizes, color=colors, edgecolor="white", linewidth=1.2, zorder=2)

    for xi, yi, name in zip(x, y, gap["시도"]):
        ax.annotate(name, (xi, yi), textcoords="offset points", xytext=(6, 5), fontsize=8.5, color="#334155")

    ax.set_xlabel("고령화 증가폭 (2015→2024, %p)", fontsize=11)
    ax.set_ylabel("고령인구 10만명당 공급 증가율 (2015→2024, 시설·요양병원 평균, %)", fontsize=11)
    ax.set_title("지역별 고령화 속도 vs 의료·복지 공급 증가 속도 (2015~2024)", fontsize=13, fontweight="bold", pad=14)
    ax.grid(True, color=GRID_COLOR, linewidth=0.8, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.text(
        0.015, 0.02,
        "※ 점이 클수록/붉을수록 격차점수(취약도) 높음. 모든 지역이 y<0 — 고령인구 1인당 공급은 전국에서 감소.",
        transform=ax.transAxes, fontsize=8.5, color="#64748b",
    )
    plt.tight_layout()
    out_path = OUT / "growth_vs_supply_scatter.png"
    plt.savefig(out_path)
    plt.close()
    logger.info(f"저장: {out_path}")


def _heatmap(panel: pd.DataFrame, order: list, col: str, title: str, cmap: str, fname: str) -> None:
    piv = panel.pivot(index="시도", columns="연도", values=col).reindex(order)
    fig, ax = plt.subplots(figsize=(10, 7), dpi=110)
    im = ax.imshow(piv.values, aspect="auto", cmap=cmap)
    ax.set_xticks(range(len(piv.columns)))
    ax.set_xticklabels(piv.columns, fontsize=9)
    ax.set_yticks(range(len(piv.index)))
    ax.set_yticklabels(piv.index, fontsize=9)
    ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
    cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cbar.ax.tick_params(labelsize=8)
    for spine in ax.spines.values():
        spine.set_visible(False)
    plt.tight_layout()
    out_path = OUT / fname
    plt.savefig(out_path)
    plt.close()
    logger.info(f"저장: {out_path}")


def build_heatmaps(panel: pd.DataFrame, gap: pd.DataFrame) -> None:
    order = gap.sort_values("고령인구비율_종료", ascending=False)["시도"].tolist()
    _heatmap(
        panel, order, "고령인구10만명당_노인복지시설수",
        "시도×연도 히트맵 — 고령인구 10만명당 노인복지시설 수 (2015~2024)",
        "Blues", "heatmap_facility.png",
    )
    _heatmap(
        panel, order, "고령인구10만명당_요양병원수",
        "시도×연도 히트맵 — 고령인구 10만명당 요양병원 수 (2015~2024)",
        "Oranges", "heatmap_hospital.png",
    )


def build_top5_chart(gap: pd.DataFrame) -> None:
    top5 = gap.sort_values("격차점수", ascending=False).head(5).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8.5, 5), dpi=110)
    bars = ax.barh(top5["시도"], top5["격차점수"], color=GAP_COLOR, height=0.55)
    for bar, v in zip(bars, top5["격차점수"]):
        ax.text(bar.get_width() + 0.03, bar.get_y() + bar.get_height() / 2, f"{v:.2f}",
                va="center", fontsize=10, fontweight="bold", color="#334155")
    ax.set_xlabel("격차점수 (고령화 속도 대비 공급 증가 부족 정도)", fontsize=11)
    ax.set_title("의료 취약지역 TOP 5 (2015~2024 격차 심화 속도 기준)", fontsize=13, fontweight="bold", pad=12)
    ax.grid(True, axis="x", color=GRID_COLOR, linewidth=0.8, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    plt.tight_layout()
    out_path = OUT / "vulnerable_top5.png"
    plt.savefig(out_path)
    plt.close()
    logger.info(f"저장: {out_path}")


def main() -> None:
    panel = pd.read_csv(PROCESSED_DIR / "aging_panel_2015_2024.csv")
    gap = pd.read_csv(PROCESSED_DIR / "growth_gap_2015_2024_sy.csv")
    build_growth_scatter(panel, gap)
    build_heatmaps(panel, gap)
    build_top5_chart(gap)


if __name__ == "__main__":
    main()
