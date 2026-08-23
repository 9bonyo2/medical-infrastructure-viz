import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def calculate_correlation(
    df: pd.DataFrame, variables: list[str]
) -> pd.DataFrame:
    """지정된 변수들 간의 상관계수 행렬을 계산합니다."""
    return df[variables].corr()


def create_heatmap_figure(
    corr_matrix: pd.DataFrame, figsize: tuple[int, int] = (7, 4)
) -> plt.Figure:
    """상관계수 행렬을 시각화한 Seaborn 히트맵 Figure 객체를 생성합니다."""
    fig, ax = plt.subplots(figsize=figsize)
    sns.heatmap(
        corr_matrix,
        annot=True,
        fmt=".3f",
        cmap="coolwarm",
        vmin=-1,
        vmax=1,
        ax=ax,
    )

    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    ax.set_title("상관계수 히트맵")
    plt.tight_layout()

    return fig