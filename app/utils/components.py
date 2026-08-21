"""
재사용 가능한 UI 컴포넌트 모음
------------------------------
각 페이지에서 반복적으로 쓰이는 카드/차트 블록을 함수로 분리했습니다.
새 페이지를 만들 때는 이 함수들을 조합해서 쓰면 디자인이 자동으로 통일됩니다.
"""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.sample_data import REGION_LAYOUT


# ── KPI 카드 ────────────────────────────────────────────────────────────
def kpi_card(icon: str, label: str, value, unit: str = "", delta_text: str | None = None,
             trend: str = "up"):
    """상단 4분할 KPI 카드 1개를 렌더링합니다."""
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


def kpi_row(kpi_dict: dict, icon_map: dict):
    """kpi_dict = utils.sample_data.get_*_kpis() 반환값, icon_map = {key: (icon, label)}"""
    cols = st.columns(len(icon_map))
    for col, (key, (icon, label)) in zip(cols, icon_map.items()):
        d = kpi_dict[key]
        with col:
            kpi_card(icon, label, f"{d['value']:,}" if isinstance(d["value"], int) else d["value"],
                     d.get("unit", ""), d.get("delta"), d.get("trend", "up"))


# ── 전국 의료 취약도 버블 차트 ───────────────────────────────────────────
def region_bubble_chart(df, height: int = 420):
    """
    '전국 의료 취약도 현황' 패널.
    ⚠️ 지금은 임의 좌표 기반 버블차트입니다. 팀에서 논의한 지도 라이브러리
      (예: folium / pydeck / plotly choropleth + GeoJSON)로 이 함수 내부만 교체하면
      나머지 페이지 코드는 그대로 사용할 수 있습니다.
    """
    fig = px.scatter(
        df,
        x="x",
        y="y",
        size="population",
        color="vulnerability_score",
        color_continuous_scale=["#12B886", "#F2C94C", "#E5484D"],
        text="region",
        size_max=46,
        range_color=[0, 100],
    )
    fig.update_traces(textposition="middle center", textfont=dict(color="white", size=11, family="Arial Black"))
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        coloraxis_colorbar=dict(title="취약도", thickness=12),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def region_panel(df, title="전국 의료 취약도 현황", tag="예시 데이터"):
    st.markdown(
        f"""
        <div class="panel-title" style="margin-bottom:14px;">
            {title} <span class="panel-tag">{tag}</span>
            <span style="margin-left:auto; font-size:12px; color:#6B7280;">
                낮음(안전) <span style="color:#12B886;">●●●</span>
                &nbsp;&nbsp; 높음(취약) <span style="color:#E5484D;">●●●</span>
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    region_bubble_chart(df)


# ── TOP5 랭킹 리스트 ─────────────────────────────────────────────────────
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
