import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

from pediatric.config import METRIC_LABELS


def plot_region_trends(
    data: pd.DataFrame,
    selected_regions: list[str],
    selected_metric: str,
) -> None:
    """선택 지역의 연도별 공급 지표 변화를 표시한다."""
    filtered = data[data["지역"].isin(selected_regions)].copy()
    colors = sns.color_palette("husl", n_colors=len(selected_regions))
    color_map = dict(zip(selected_regions, colors))
    metric_label = METRIC_LABELS[selected_metric]
    fig, axis = plt.subplots(figsize=(8.4, 5.2))

    for region in selected_regions:
        region_df = filtered[filtered["지역"] == region].sort_values("시점")
        axis.plot(
            region_df["시점"], region_df[selected_metric], marker="o",
            markersize=4, linewidth=1.7, color=color_map[region], label=region,
        )

    axis.set_xlabel("연도")
    axis.set_ylabel(metric_label)
    axis.grid(alpha=0.3)
    axis.legend(bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=7)
    fig.subplots_adjust(right=0.76, bottom=0.12)
    st.pyplot(fig, width="stretch")
    plt.close(fig)


def plot_year_comparison(
    data: pd.DataFrame,
    selected_year: int,
    selected_metric: str,
) -> None:
    """선택 연도의 지역별 공급 지표를 내림차순으로 비교한다."""
    year_df = data[data["시점"] == selected_year].drop_duplicates("지역").copy()
    regions = sorted(year_df["지역"].dropna().unique())
    colors = sns.color_palette("husl", n_colors=len(regions))
    color_map = dict(zip(regions, colors))
    metric_label = METRIC_LABELS[selected_metric]
    fig, axis = plt.subplots(figsize=(8.4, 5.2))

    order = year_df.sort_values(selected_metric, ascending=False)["지역"].tolist()
    sns.barplot(
        data=year_df, x="지역", y=selected_metric, hue="지역", order=order,
        palette=color_map, legend=False, ax=axis,
    )
    axis.set_xlabel("지역")
    axis.set_ylabel(metric_label)
    axis.tick_params(axis="x", rotation=55, labelsize=8)
    axis.grid(axis="y", alpha=0.3)
    fig.subplots_adjust(bottom=0.27, left=0.11, right=0.98)
    st.pyplot(fig, width="stretch")
    plt.close(fig)