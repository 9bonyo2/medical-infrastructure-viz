import json
from urllib.error import URLError
from urllib.request import Request, urlopen

import pandas as pd
import streamlit as st

try:
    import plotly.graph_objects as go
except ModuleNotFoundError:
    go = None

from pediatric.config import (
    KOREA_MAP_PATH,
    KOREA_MAP_URL,
    MAP_REGION_ALIASES,
)


@st.cache_data(show_spinner=False)
def load_korea_province_geojson() -> dict:
    """로컬 지도 파일을 우선 사용하고, 없으면 공개 GeoJSON을 읽는다."""
    if KOREA_MAP_PATH.is_file():
        return json.loads(KOREA_MAP_PATH.read_text(encoding="utf-8"))

    request = Request(
        KOREA_MAP_URL,
        headers={"User-Agent": "pediatric-supply-dashboard/1.0"},
    )
    with urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def plot_supply_capacity_map(data: pd.DataFrame, selected_year: int) -> None:
    """중앙값 대비 공급 수준을 지도에 표시하고 클릭한 지역 값만 보여준다."""
    if go is None:
        st.error("대화형 지도를 사용하려면 Plotly 설치가 필요합니다.")
        st.code("pip install plotly")
        return

    map_data = data.loc[
        data["시점"] == selected_year,
        ["지역", "의원1개당전문의수", "아동1만명당전문의수"],
    ].dropna().drop_duplicates("지역")

    if map_data.empty:
        st.warning(f"{selected_year}년에는 공급 수준 지도를 만들 수 있는 데이터가 없습니다.")
        return

    clinic_median = map_data["의원1개당전문의수"].median()
    child_median = map_data["아동1만명당전문의수"].median()
    if clinic_median <= 0 or child_median <= 0:
        st.warning("중앙값이 0 이하이므로 공급 수준 지도를 계산할 수 없습니다.")
        return

    map_data = map_data.assign(
        의원당중앙값대비=lambda frame: (
            frame["의원1개당전문의수"] / clinic_median * 100
        ),
        아동대비중앙값대비=lambda frame: (
            frame["아동1만명당전문의수"] / child_median * 100
        ),
    )
    map_data["공급수준지수"] = (
        map_data["의원당중앙값대비"] + map_data["아동대비중앙값대비"]
    ) / 2
    map_data["지도지역"] = map_data["지역"].replace(MAP_REGION_ALIASES)

    try:
        geojson = load_korea_province_geojson()
    except (OSError, URLError, json.JSONDecodeError) as error:
        st.error(f"대한민국 시도 경계 데이터를 읽을 수 없습니다. {error}")
        st.caption(
            "오프라인 실행 시 app/data/skorea_provinces_geo_simple.json "
            "파일을 추가해 주세요."
        )
        return

    score_values = map_data["공급수준지수"]
    minimum_score = min(float(score_values.min()), 99.0)
    maximum_score = max(float(score_values.max()), 101.0)
    median_position = (100 - minimum_score) / (maximum_score - minimum_score)
    color_scale = [
        [0.0, "#eff6ff"],
        [median_position, "#93c5fd"],
        [1.0, "#1e3a8a"],
    ]

    custom_data = map_data[
        [
            "지역",
            "의원1개당전문의수",
            "아동1만명당전문의수",
            "의원당중앙값대비",
            "아동대비중앙값대비",
            "공급수준지수",
        ]
    ].to_numpy()

    figure = go.Figure(
        go.Choropleth(
            geojson=geojson,
            locations=map_data["지도지역"],
            z=map_data["공급수준지수"],
            featureidkey="properties.name",
            customdata=custom_data,
            colorscale=color_scale,
            zmin=minimum_score,
            zmax=maximum_score,
            hoverinfo="none",
            marker_line_color="#ffffff",
            marker_line_width=0.8,
            colorbar={
                "title": {"text": "공급 수준<br>(100=기준)"},
                "tickvals": [minimum_score, 100, maximum_score],
                "ticktext": [
                    f"{minimum_score:.0f}",
                    "100 기준",
                    f"{maximum_score:.0f}",
                ],
                "thickness": 14,
                "len": 0.72,
            },
        )
    )
    figure.update_geos(
        fitbounds="locations",
        visible=False,
        projection_type="mercator",
    )
    figure.update_layout(
        clickmode="event+select",
        dragmode=False,
        height=540,
        margin={"l": 0, "r": 0, "t": 10, "b": 0},
    )

    chart_state = st.plotly_chart(
        figure,
        width="stretch",
        key=f"supply_capacity_map_{selected_year}",
        on_select="rerun",
        selection_mode="points",
        config={
            "displayModeBar": False,
            "scrollZoom": False,
        },
    )

    selected_points = chart_state.selection.points
    if not selected_points:
        st.info("지도에서 지역을 클릭하면 해당 지역의 값이 표시됩니다.")
    else:
        selected_point = selected_points[-1]
        selected_map_region = selected_point.get("location")
        selected_rows = map_data[map_data["지도지역"] == selected_map_region]

        if selected_rows.empty:
            point_custom_data = selected_point.get("customdata", [])
            if point_custom_data:
                selected_rows = map_data[map_data["지역"] == point_custom_data[0]]

        if not selected_rows.empty:
            selected_row = selected_rows.iloc[0]
            st.markdown(f"##### {selected_row['지역']} 선택 결과")
            clinic_column, child_column, index_column = st.columns(3)

            with clinic_column:
                st.metric(
                    "의원 1개당 전문의 수",
                    f"{selected_row['의원1개당전문의수']:.2f}명",
                    f"중앙값 대비 {selected_row['의원당중앙값대비']:.1f}%",
                )

            with child_column:
                st.metric(
                    "아동 1만 명당 전문의 수",
                    f"{selected_row['아동1만명당전문의수']:.2f}명",
                    f"중앙값 대비 {selected_row['아동대비중앙값대비']:.1f}%",
                )

            with index_column:
                st.metric(
                    "통합 공급 수준 지수",
                    f"{selected_row['공급수준지수']:.1f}",
                    f"기준 대비 {selected_row['공급수준지수'] - 100:+.1f}",
                )

    st.caption(
        f"의원 1개당 전문의 수 중앙값 {clinic_median:.2f}명과 아동 1만 명당 "
        f"전문의 수 중앙값 {child_median:.2f}명을 각각 100으로 환산해 평균한 "
        "지수입니다. 100보다 높을수록 두 지표의 종합 공급 수준이 기준보다 "
        "높고, 지도의 색이 진해집니다."
    )