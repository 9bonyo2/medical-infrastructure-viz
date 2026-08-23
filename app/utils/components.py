"""
재사용 가능한 UI 컴포넌트 모음
------------------------------
각 페이지에서 반복적으로 쓰이는 카드/차트 블록을 함수로 분리했습니다.
새 페이지를 만들 때는 이 함수들을 조합해서 쓰면 디자인이 자동으로 통일됩니다.
"""

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.sample_data import REGION_LAYOUT


REGION_NAME_ALIASES = {
    "서울": "서울특별시",
    "부산": "부산광역시",
    "대구": "대구광역시",
    "인천": "인천광역시",
    "광주": "광주광역시",
    "대전": "대전광역시",
    "울산": "울산광역시",
    "세종": "세종특별자치시",
    "경기": "경기도",
    "강원": "강원도",
    "강원특별자치도": "강원도",
    "충북": "충청북도",
    "충남": "충청남도",
    "전북": "전라북도",
    "전북특별자치도": "전라북도",
    "전남": "전라남도",
    "경북": "경상북도",
    "경남": "경상남도",
    "제주": "제주특별자치도",
}


# 시도 경계 GeoJSON 파일을 읽어서 반환 (캐시됨)
@st.cache_data
def _load_sido_geojson():
    geojson_path = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "aging"
        / "raw"
        / "skorea_sido_boundary.geojson"
    )
    with geojson_path.open(encoding="utf-8") as f:
        return json.load(f)


# 지역명을 별칭 매핑을 통해 GeoJSON 표기(정식 명칭)로 통일
def _normalize_region_name(region_name):
    if pd.isna(region_name):
        return None
    name = str(region_name).strip()
    return REGION_NAME_ALIASES.get(name, name)


# 다각형 하나(ring)의 면적과 무게중심 좌표를 계산
def _ring_centroid(ring):
    points = ring[:-1] if ring and ring[0] == ring[-1] else ring
    if len(points) < 3:
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        return 0, (sum(xs) / len(xs), sum(ys) / len(ys))

    area2 = 0
    cx = 0
    cy = 0
    for i, point in enumerate(points):
        next_point = points[(i + 1) % len(points)]
        cross = point[0] * next_point[1] - next_point[0] * point[1]
        area2 += cross
        cx += (point[0] + next_point[0]) * cross
        cy += (point[1] + next_point[1]) * cross

    if area2 == 0:
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        return 0, (sum(xs) / len(xs), sum(ys) / len(ys))

    return area2 / 2, (cx / (3 * area2), cy / (3 * area2))


# GeoJSON feature(다중 폴리곤 포함)의 대표 중심 좌표를 면적 가중 평균으로 계산
def _feature_centroid(feature):
    geometry = feature["geometry"]
    polygons = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
    total_weight = 0
    lon_sum = 0
    lat_sum = 0

    for polygon in polygons:
        if not polygon:
            continue
        area, centroid = _ring_centroid(polygon[0])
        weight = abs(area)
        total_weight += weight
        lon_sum += centroid[0] * weight
        lat_sum += centroid[1] * weight

    if total_weight == 0:
        return None, None
    return lon_sum / total_weight, lat_sum / total_weight


# 모든 시도별 중심 좌표를 {지역명: (lon, lat)} 딕셔너리로 반환 (캐시됨)
@st.cache_data
def _get_sido_centers():
    geojson = _load_sido_geojson()
    centers = {}
    for feature in geojson["features"]:
        name = feature["properties"]["name"]
        centers[name] = _feature_centroid(feature)
    return centers


# ==========================================================================================================


# 페이지 상단 4가지 핵심데이터 컴포넌트 (KPI 카드)
def kpi_card(icon: str, label: str, value, unit: str = "", delta_text: str | None = None,
            trend: str = "up"):
    delta_html = ""
    if delta_text:
        color = "#22A06B" if trend == "up" else "#E5484D" if trend == "down" else "#6B7280"
        arrow = "▲" if trend == "up" else "▼" if trend == "down" else "•"
        delta_html = (
            f'<div class="kpi-delta" style="color:{color}">'
            f'전년 대비 {arrow} {delta_text}</div>'
        )
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-card-header">
                <span class="kpi-label">{label}</span>
                <span class="kpi-icon">{icon}</span>
            </div>
            <div class="kpi-value">{value}<span class="kpi-unit">{unit}</span></div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# KPI 데이터 딕셔너리와 아이콘/라벨 매핑을 받아 kpi_card를 가로로 나열
def kpi_row(kpi_dict: dict, icon_map: dict):
    """kpi_dict = utils.sample_data.get_*_kpis() 반환값, icon_map = {key: (icon, label)}"""
    cols = st.columns(len(icon_map))
    for col, (key, (icon, label)) in zip(cols, icon_map.items()):
        d = kpi_dict[key]
        with col:
            kpi_card(icon, label, f"{d['value']:,}" if isinstance(d["value"], int) else d["value"],
                     d.get("unit", ""), d.get("delta"), d.get("trend", "up"))


# ==========================================================================================================


    # 전국 의료 취약도 현황 패널.
    # 지금은 임의 좌표 기반 버블차트이지만,
    # (예: folium / pydeck / plotly choropleth + GeoJSON)로 이 함수 내부만 교체하면
    #   나머지 페이지 코드는 그대로 사용할 수 있으니 참고부탁드립니다~
    # TODO: 지도 랜더링 필요한 팀 참고사함: 현재는 실제 지도를 띄우고 있지 않고 버블차트만 랜더링하고 있습니다. 추후에 실제 한국 지도를 가져와서 지역 좌표 찍으신 후 ㅎ당 좌표ㅛ에 버블차트 랜더링하시면 될 것 같습니다!
def region_bubble_chart(
    df,
    height: int = 420,
    color_col: str | None = None,
    size_col: str | None = None,
    color_label: str = "취약도",
):
    geojson = _load_sido_geojson()
    centers = _get_sido_centers()
    plot_df = df.copy()

    region_col = "시도" if "시도" in plot_df.columns else "region"
    color_col = color_col or ("vulnerability_score" if "vulnerability_score" in plot_df.columns else "고령인구비율")
    size_col = size_col or ("population" if "population" in plot_df.columns else "고령인구수_65세이상")

    plot_df["__geo_name"] = plot_df[region_col].map(_normalize_region_name)
    plot_df["__lon"] = plot_df["__geo_name"].map(lambda name: centers.get(name, (None, None))[0])
    plot_df["__lat"] = plot_df["__geo_name"].map(lambda name: centers.get(name, (None, None))[1])
    plot_df[color_col] = pd.to_numeric(plot_df[color_col], errors="coerce")
    plot_df[size_col] = pd.to_numeric(plot_df[size_col], errors="coerce")
    plot_df = plot_df.dropna(subset=["__geo_name", "__lon", "__lat", color_col, size_col])

    fig = px.choropleth(
        plot_df,
        geojson=geojson,
        locations="__geo_name",
        featureidkey="properties.name",
        color=color_col,
        color_continuous_scale=["#12B886", "#F2C94C", "#E5484D"],
        hover_name=region_col,
        hover_data={color_col: ":,.2f", size_col: ":,.0f", "__geo_name": False},
    )
    fig.update_traces(marker_line_width=0.8, marker_line_color="white", selector=dict(type="choropleth"))

    max_size = plot_df[size_col].max()
    sizeref = 2.0 * max_size / (46 ** 2) if max_size and max_size > 0 else 1
    fig.add_trace(
        go.Scattergeo(
            lon=plot_df["__lon"],
            lat=plot_df["__lat"],
            text=plot_df[region_col],
            mode="markers+text",
            textposition="middle center",
            textfont=dict(color="white", size=10, family="Arial Black"),
            marker=dict(
                size=plot_df[size_col],
                sizemode="area",
                sizeref=sizeref,
                sizemin=8,
                color=plot_df[color_col],
                colorscale=["#12B886", "#F2C94C", "#E5484D"],
                cmin=plot_df[color_col].min(),
                cmax=plot_df[color_col].max(),
                line=dict(width=1.2, color="white"),
                opacity=0.82,
                showscale=False,
            ),
            customdata=plot_df[[color_col, size_col]].to_numpy(),
            hovertemplate=(
                "<b>%{text}</b><br>"
                + f"{color_label}: "
                + "%{customdata[0]:,.2f}<br>"
                + f"{size_col}: "
                + "%{customdata[1]:,.0f}<extra></extra>"
            ),
        )
    )

    fig.update_geos(fitbounds="locations", visible=False, projection_type="mercator")
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="white",
        coloraxis_colorbar=dict(title=color_label, thickness=12),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# 제목/범례 영역과 region_bubble_chart를 합친 지역 현황 패널 전체를 렌더링
def region_panel(
    df,
    title="전국 의료 취약도 현황",
    tag="예시 데이터",
    color_col: str | None = None,
    size_col: str | None = None,
    color_label: str = "취약도",
    legend_low: str = "낮음(안전)",
    legend_high: str = "높음(취약)",
):
    st.markdown(
        f"""
        <div class="panel-title" style="margin-bottom:14px;">
            {title} <span class="panel-tag">{tag}</span>
            <span style="margin-left:auto; font-size:12px; color:#6B7280;">
                {legend_low} <span style="color:#12B886;">●●●</span>
                &nbsp;&nbsp; {legend_high} <span style="color:#E5484D;">●●●</span>
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    region_bubble_chart(df, color_col=color_col, size_col=size_col, color_label=color_label)


# ==========================================================================================================


# ── TOP5 랭킹 리스트 (메인패널 우측영역) ──────────────────────────────────────────────────────
def top5_ranking_panel(df, title="의료 취약지역 TOP 5", tag="종합 지표", unit_label="점수"):
    st.markdown(
        f"""
        <div class="panel-title" style="margin-bottom:16px;">
            {title} <span class="panel-tag">{tag}</span>
            <span style="margin-left:auto; font-size:12px; color:#6B7280;">단위: {unit_label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    max_score = df["score"].max()
    for _, row in df.iterrows():
        badge_class = "rank-badge" if row["rank"] <= 2 else "rank-badge rank-badge-muted"
        bar_width = int(row["score"] / max_score * 100)
        st.markdown(
            f"""
            <div class="rank-item">
                <div class="rank-row">
                    <div><span class="{badge_class}">{row['rank']}</span>
                        <span class="rank-name">{row['region']}</span></div>
                    <div class="rank-score">{row['score']}</div>
                </div>
                <div class="rank-bar-bg"><div class="rank-bar-fill" style="width:{bar_width}%;"></div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ==========================================================================================================


# ── 바로가기 카드 ────────────────────────────────────────────────────────
def quicklink_card(icon, title, desc, border_color="#2F6FED"):
    st.markdown(
        f"""
        <div class="quicklink-card" style="border-left-color:{border_color};">
            <div class="quicklink-icon">{icon}</div>
            <div style="flex:1;">
                <div class="quicklink-title">{title}</div>
                <div class="quicklink-desc">{desc}</div>
            </div>
            <div style="color:#9AA0AC;">→</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── 프로세스 흐름 ────────────────────────────────────────────────────────
def process_flow(steps: list[str]):
    cols = st.columns([1] * (len(steps) * 2 - 1))
    for i, step in enumerate(steps):
        with cols[i * 2]:
            st.markdown(
                f"""
                <div class="flow-step">
                    <span class="flow-num">{i + 1}</span> {step}
                </div>
                """,
                unsafe_allow_html=True,
            )
        if i * 2 + 1 < len(cols):
            with cols[i * 2 + 1]:
                st.markdown(
                    "<div style='text-align:center; color:#9AA0AC; padding-top:10px;'>→</div>",
                    unsafe_allow_html=True,
                )


# ── 패널 카드 래퍼 (with 문으로 감싸서 쓰는 컨테이너) ──────────────────────
def panel_card():
    """
    사용 예:
        with panel_card():
            st.markdown("### 내용")
    """
    return st.container(border=False)


# 연도별 지표 추이를 보여주는 라인 차트를 렌더링
def correlation_trend_chart(df, x_col="year", series_cols=None, height=340):
    """상관계수 추이 라인차트 (예: 노인복지시설/요양병원 r값 추이)."""
    series_cols = series_cols or [c for c in df.columns if c != x_col]
    fig = go.Figure()
    colors = ["#2F6FED", "#F2994A"]
    for i, col in enumerate(series_cols):
        fig.add_trace(
            go.Scatter(
                x=df[x_col], y=df[col], mode="lines+markers", name=col,
                line=dict(color=colors[i % len(colors)], width=2.5),
                marker=dict(size=6),
            )
        )
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=30, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        yaxis=dict(title="Pearson r (상관계수)", gridcolor="#F0F1F5", zeroline=True, zerolinecolor="#D8DAE3"),
        xaxis=dict(title="연도", gridcolor="#F0F1F5"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# 연도별 산점도를 격자(facet grid) 형태로 나란히 렌더링
def small_multiples_grid(df, value_col="value", x_col="고령인구비율", year_col="year", ncols=5, height=430):
    """연도별 소규모 산점도(facet grid)를 plotly로 렌더링합니다."""
    fig = px.scatter(
        df, x=x_col, y=value_col, facet_col=year_col, facet_col_wrap=ncols,
        trendline="ols", opacity=0.6, height=height,
        color_discrete_sequence=["#2F6FED"],
    )
    fig.update_traces(marker=dict(size=4))
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1] + "년", font=dict(size=11)))
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), plot_bgcolor="white", paper_bgcolor="white")
    fig.update_xaxes(showgrid=False, title=None)
    fig.update_yaxes(showgrid=True, gridcolor="#F0F1F5", title=None)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
