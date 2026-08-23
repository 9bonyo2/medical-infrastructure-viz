import pandas as pd
import plotly.graph_objects as go
from plotly.colors import qualitative
import streamlit as st

from pediatric.config import METRIC_LABELS
import matplotlib.font_manager as fm

for font_path in fm.findSystemFonts():
    if "Nanum" in font_path:
        fm.fontManager.addfont(font_path)

plt.rcParams["font.family"] = "NanumGothic"
plt.rcParams["axes.unicode_minus"] = False

PLOTLY_FONT_FAMILY = (
    "Pretendard, Noto Sans KR, NanumGothic, Malgun Gothic, "
    "Apple SD Gothic Neo, sans-serif"
)
PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True}


def _apply_common_layout(
    figure: go.Figure,
    *,
    x_title: str,
    y_title: str,
    right_margin: int = 20,
) -> None:
    """브라우저가 한글을 렌더링하도록 공통 Plotly 스타일을 적용한다."""
    figure.update_layout(
        height=440,
        margin=dict(l=55, r=right_margin, t=15, b=70),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family=PLOTLY_FONT_FAMILY,
            size=12,
            color="#1F2937",
        ),
        hoverlabel=dict(
            font=dict(family=PLOTLY_FONT_FAMILY, size=12),
        ),
        xaxis=dict(
            title=x_title,
            showgrid=True,
            gridcolor="#E5E7EB",
            zeroline=False,
        ),
        yaxis=dict(
            title=y_title,
            showgrid=True,
            gridcolor="#E5E7EB",
            zeroline=False,
        ),
    )


def plot_region_trends(
    data: pd.DataFrame,
    selected_regions: list[str],
    selected_metric: str,
) -> None:
    """선택 지역의 연도별 공급 지표 변화를 Plotly로 표시한다."""
    filtered = data[data["지역"].isin(selected_regions)].copy()
    if filtered.empty:
        st.warning("선택한 지역의 연도별 데이터가 없습니다.")
        return

    metric_label = METRIC_LABELS[selected_metric]
    colors = qualitative.Alphabet
    figure = go.Figure()

    for index, region in enumerate(selected_regions):
        region_data = (
            filtered[filtered["지역"] == region]
            .dropna(subset=["시점", selected_metric])
            .sort_values("시점")
        )
        if region_data.empty:
            continue

        figure.add_trace(
            go.Scatter(
                x=region_data["시점"],
                y=region_data[selected_metric],
                mode="lines+markers",
                name=region,
                line=dict(color=colors[index % len(colors)], width=2),
                marker=dict(size=6),
                hovertemplate=(
                    "<b>%{fullData.name}</b><br>"
                    "연도: %{x}<br>"
                    f"{metric_label}: %{{y:.2f}}명"
                    "<extra></extra>"
                ),
            )
        )

    _apply_common_layout(
        figure,
        x_title="연도",
        y_title=metric_label,
        right_margin=145,
    )
    figure.update_layout(
        legend=dict(
            x=1.01,
            y=1,
            xanchor="left",
            yanchor="top",
            font=dict(family=PLOTLY_FONT_FAMILY, size=10),
        ),
        xaxis=dict(dtick=1),
    )
    st.plotly_chart(
        figure,
        use_container_width=True,
        config=PLOTLY_CONFIG,
        key=f"region-trend-{selected_metric}",
    )


def plot_year_comparison(
    data: pd.DataFrame,
    selected_year: int,
    selected_metric: str,
) -> None:
    """선택 연도의 지역별 공급 지표를 Plotly 막대그래프로 비교한다."""
    year_data = (
        data[data["시점"] == selected_year]
        .drop_duplicates("지역")
        .dropna(subset=["지역", selected_metric])
        .sort_values(selected_metric, ascending=False)
        .copy()
    )
    if year_data.empty:
        st.warning(f"{selected_year}년 지역별 데이터가 없습니다.")
        return

    metric_label = METRIC_LABELS[selected_metric]
    colors = qualitative.Alphabet
    bar_colors = [colors[index % len(colors)] for index in range(len(year_data))]

    figure = go.Figure(
        go.Bar(
            x=year_data["지역"],
            y=year_data[selected_metric],
            marker_color=bar_colors,
            customdata=year_data[["지역"]],
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                f"{metric_label}: %{{y:.2f}}명"
                "<extra></extra>"
            ),
        )
    )
    _apply_common_layout(
        figure,
        x_title="지역",
        y_title=metric_label,
    )
    figure.update_xaxes(
        categoryorder="array",
        categoryarray=year_data["지역"].tolist(),
        tickangle=-50,
        tickfont=dict(family=PLOTLY_FONT_FAMILY, size=10),
    )
    st.plotly_chart(
        figure,
        use_container_width=True,
        config=PLOTLY_CONFIG,
        key=f"year-comparison-{selected_year}-{selected_metric}",
    )