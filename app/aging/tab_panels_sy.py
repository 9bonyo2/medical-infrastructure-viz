"""
[고령화 파트 · 서연] KPI 박스 아래 탭바(4개) — 좌측 지도뷰 / 우측 분석뷰

탭 4개 모두 같은 구조로 통일했다:
  [메인 패널] 좌측 지도 카드(2/3, 하단에 인사이트 카드 별도) + 우측 TOP5/인사이트 카드(1/3)
  [경계선]
  [하단 상세 시각화] 좌측 그래프(2/3) + 우측 수치 데이터표(1/3)
  [핵심 인사이트] 2열×2행 카드 그리드 (항목당 1~2줄, 관련 항목끼리 묶음)

  1) 취약지역 Top5 분석      — 메인: 격차점수 지도(+인사이트 카드) / TOP5 카드
                              하단: 고령화속도 vs 공급증가속도 산점도 / 전체 순위표
                              인사이트: 최다취약·최다안정·취약비중·최대감소폭
  2) 지역별 증가 속도        — 메인: 증가율 지도 / 감소 TOP5(가장 뒤처진 지역)
                              하단: 시도별 증가율 막대그래프 / 수치표
                              인사이트: 노인복지시설 2종 + 요양병원 2종(관련 항목끼리 묶음)
  3) 노인복지시설 상관관계    — 메인: 연도별 수준 지도 / 상관계수 인사이트 + 상위 TOP5
                              하단: 산점도 / 연도 데이터표
                              인사이트: 상관계수·추이·최고지역·최저지역
  4) 요양병원 상관관계        — 3)과 동일 구성, 요양병원 지표로

기존 utils/components.py, utils/sample_data.py 는 수정하지 않고 공개 함수만 재사용한다.
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy import stats

from utils.components import region_panel, top5_ranking_panel

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "aging" / "processed"

GROWTH_METRIC_OPTIONS = {
    "노인복지시설": {"level": "고령인구10만명당_노인복지시설수", "growth": "시설_증가율"},
    "요양병원": {"level": "고령인구10만명당_요양병원수", "growth": "요양병원_증가율"},
}


# ── 공용 데이터 로더 ────────────────────────────────────────────────────
@st.cache_data
def load_panel_df() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "aging_panel_2015_2024.csv")


@st.cache_data
def load_growth_gap_df() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "growth_gap_2015_2024_sy.csv")


@st.cache_data
def load_correlation_by_year_df() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "correlation_by_year.csv")


def _size_col_from_panel(df: pd.DataFrame, year: int = 2024) -> pd.DataFrame:
    """지도 버블 크기용 고령인구수_65세이상 컬럼을 연도 기준으로 병합."""
    panel_year = load_panel_df()
    panel_year = panel_year[panel_year["연도"] == year][["시도", "고령인구수_65세이상"]]
    return df.merge(panel_year, on="시도", how="left")


def _insight_box(html_body: str, icon: str = "") -> None:
    """짧은 인사이트 요약 카드. 본문 안의 <b>강조어</b>는 CSS(.sy-insight b)로 자동 파란색 처리된다."""
    prefix = f'<span class="sy-insight-icon">{icon}</span> ' if icon else ""
    st.markdown(f'<div class="sy-insight">{prefix}{html_body}</div>', unsafe_allow_html=True)


def _section_title(text: str) -> None:
    st.markdown(
        f'<div class="panel-title sy-section-title" style="margin-bottom:10px;">'
        f'<span class="sy-title-bar"></span>{text}</div>',
        unsafe_allow_html=True,
    )


def _inject_page_theme() -> None:
    """이 페이지(고령화 파트) 전용 톤 다듬기 — 공유 파일(utils/*)은 건드리지 않고
    이 스코프에서만 CSS를 덮어쓴다(다른 페이지엔 영향 없음).

      - TOP5 랭킹 강조색: 빨강 → 파랑 통일
      - 인사이트 카드: 좌측 파란 포인트바 + <b>강조어</b> 자동 파란색·굵게 처리
      - 섹션 제목: 앞에 작은 파란 바 추가로 가독성 강화
    """
    st.markdown(
        """
        <style>
        /* TOP5 랭킹 패널 강조색 통일 */
        .rank-badge { background: #2F6FED !important; }
        .rank-score { color: #2F6FED !important; }
        .rank-bar-fill { background: #2F6FED !important; }

        /* 인사이트 카드 */
        .sy-insight {
            background: linear-gradient(135deg, #F5F8FF 0%, #F8F9FB 100%);
            border: 1px solid #E1E9FB;
            border-left: 4px solid #2F6FED;
            border-radius: 10px;
            padding: 14px 14px;
            font-size: 13px;
            line-height: 1.8;
            color: #1A1F2B;
            margin-bottom: 10px;
        }
        .sy-insight b { color: #2F6FED; font-weight: 700; }
        .sy-insight-icon { margin-right: 2px; }

        /* 섹션 제목 앞 포인트 바 */
        .sy-section-title { display: flex; align-items: center; gap: 8px; }
        .sy-title-bar { width: 4px; height: 15px; background: #2F6FED; border-radius: 2px; display: inline-block; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _insight_grid(items: list[str]) -> None:
    """하단 상세뷰 아래에 붙는 핵심 인사이트 — 2열×2행 카드, 항목당 1~2줄."""
    st.write("")
    _section_title("핵심 인사이트")
    row1 = st.columns(2, gap="small")
    row2 = st.columns(2, gap="small")
    for col, text in zip(row1 + row2, items[:4]):
        with col:
            _insight_box(text, icon="💡")


# ══════════════════════════════════════════════════════════════════════
# 탭 1) 취약지역 Top5 분석
# ══════════════════════════════════════════════════════════════════════
def render_top5_tab() -> None:
    _inject_page_theme()
    gap_df = load_growth_gap_df()
    map_df = _size_col_from_panel(gap_df)

    worst = gap_df.sort_values("격차점수", ascending=False).iloc[0]
    best = gap_df.sort_values("격차점수", ascending=True).iloc[0]
    n_positive = int((gap_df["격차점수"] > 0).sum())
    max_drop_row = gap_df.loc[gap_df["요양병원_증가율"].idxmin()]

    # ── 메인 패널 ──
    left, right = st.columns([2, 1], gap="medium")
    with left:
        # 지도 카드 (인사이트는 아래에 별도 카드로 분리 — 컨테이너 경계 밖으로 밀려나오는 문제 방지)
        with st.container(border=True):
            region_panel(
                map_df,
                title="전국 의료 취약도 현황",
                tag="격차점수 · 2015~2024",
                color_col="격차점수",
                size_col="고령인구수_65세이상",
                color_label="격차점수",
                legend_low="안전(공급이 고령화 속도를 따라감)",
                legend_high="취약(공급이 고령화 속도를 못 따라감)",
            )
        st.write("")
        with st.container(border=True):
            _insight_box(
                f"<b>{worst['시도']}</b>이 격차점수 <b>{worst['격차점수']:.2f}</b>로 가장 취약합니다 — "
                f"10년간 고령화율은 <b>+{worst['고령화_증가폭']:.1f}%p</b> 늘었지만 "
                f"고령인구 1인당 공급은 오히려 <b>{worst['공급_증가율_평균']:.1f}%</b> 줄었습니다.<br/>"
                f"반대로 <b>{best['시도']}</b>은 격차점수 {best['격차점수']:.2f}로 가장 안정적입니다. "
                f"전체 17개 시도 중 <b>{n_positive}곳</b>이 격차점수 양(+)수, 즉 고령화 속도 대비 "
                f"공급이 뒤처지고 있습니다.",
                icon="📌",
            )

    with right:
        top5 = gap_df.sort_values("격차점수", ascending=False).head(5).reset_index(drop=True)
        top5["rank"] = top5.index + 1
        top5["region"] = top5["시도"]
        top5["score"] = top5["격차점수"].round(2)
        with st.container(border=True):
            top5_ranking_panel(
                top5[["rank", "region", "score"]],
                title="의료 취약지역 TOP 5",
                tag="격차점수 · 2015~2024",
                unit_label="격차점수",
            )

    st.write("")
    st.divider()

    # ── 하단 상세 시각화: 좌 산점도 / 우 전체 순위표 ──
    with st.container(border=True):
        chart_col, table_col = st.columns([2, 1], gap="medium")
        with chart_col:
            _section_title("지역별 고령화 속도 vs 공급 증가 속도 (상세)")
            x = gap_df["고령화_증가폭"].to_numpy(float)
            y = gap_df["공급_증가율_평균"].to_numpy(float)
            score = gap_df["격차점수"].to_numpy(float)
            size_vals = score - score.min() + 0.5

            fig = go.Figure()
            fig.add_hline(y=y.mean(), line_dash="dash", line_color="#C9CDD6", line_width=1)
            fig.add_vline(x=x.mean(), line_dash="dash", line_color="#C9CDD6", line_width=1)
            fig.add_trace(
                go.Scatter(
                    x=x, y=y, mode="markers+text", text=gap_df["시도"], textposition="top center",
                    textfont=dict(size=9),
                    marker=dict(
                        size=size_vals, sizemode="area", sizeref=2.0 * size_vals.max() / (34 ** 2), sizemin=6,
                        color=score, colorscale="RdBu_r", cmid=0, showscale=True,
                        colorbar=dict(title="격차점수", thickness=12), line=dict(width=1, color="white"),
                    ),
                )
            )
            fig.update_layout(
                height=420, margin=dict(l=10, r=10, t=10, b=10),
                plot_bgcolor="white", paper_bgcolor="white",
                xaxis=dict(title="고령화 증가폭(%p)", gridcolor="#F0F1F5"),
                yaxis=dict(title="공급 증가율(%)", gridcolor="#F0F1F5", zeroline=True, zerolinecolor="#D8DAE3"),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.caption("점이 클수록/붉을수록 격차점수(취약도)가 높습니다.")
        with table_col:
            _section_title("시도별 전체 순위")
            ranking_all = gap_df.sort_values("격차점수", ascending=False).reset_index(drop=True)
            ranking_all.index = ranking_all.index + 1
            st.dataframe(
                ranking_all[["시도", "격차점수", "고령화_증가폭", "공급_증가율_평균"]]
                .rename(columns={"고령화_증가폭": "고령화 증가폭(%p)", "공급_증가율_평균": "공급 증가율(%)"}),
                use_container_width=True, height=440,
            )

    # ── 핵심 인사이트 (2열×2행) ──
    _insight_grid([
        f"<b>가장 취약한 지역</b>: {worst['시도']} (격차점수 {worst['격차점수']:.2f}) — 고령화는 빨랐지만 공급이 못 따라갔습니다.",
        f"<b>가장 안정적인 지역</b>: {best['시도']} (격차점수 {best['격차점수']:.2f}) — 공급 증가가 고령화 속도를 상회했습니다.",
        f"<b>취약지역 비중</b>: 17개 시도 중 {n_positive}곳이 격차점수 양(+)수로, 절반 가까이가 공급 부족 상태입니다.",
        f"<b>최대 공급 감소</b>: {max_drop_row['시도']}의 요양병원 수가 10년간 {max_drop_row['요양병원_증가율']:.1f}%로 가장 크게 줄었습니다.",
    ])


# ══════════════════════════════════════════════════════════════════════
# 탭 2) 지역별 증가 속도
# ══════════════════════════════════════════════════════════════════════
def render_growth_rate_tab() -> None:
    _inject_page_theme()
    gap_df = load_growth_gap_df()

    metric_label = st.radio(
        "지표 선택", list(GROWTH_METRIC_OPTIONS.keys()), horizontal=True, key="growth_rate_metric_sy",
    )
    growth_col = GROWTH_METRIC_OPTIONS[metric_label]["growth"]

    # ── 메인 패널 ──
    left, right = st.columns([2, 1], gap="medium")
    with left:
        with st.container(border=True):
            map_df = _size_col_from_panel(gap_df)
            region_panel(
                map_df,
                title=f"전국 {metric_label} 증가율 현황 (2015→2024)",
                tag="고령인구10만명당 기준",
                color_col=growth_col,
                size_col="고령인구수_65세이상",
                color_label=f"{metric_label} 증가율(%)",
                legend_low="감소",
                legend_high="증가",
            )

    with right:
        with st.container(border=True):
            # 특성: "증가 속도"가 핵심이므로 가장 많이 감소한(=가장 뒤처진) TOP5를 보여준다
            worst5 = gap_df.sort_values(growth_col).head(5).reset_index(drop=True)
            worst5["rank"] = worst5.index + 1
            worst5["region"] = worst5["시도"] + worst5[growth_col].apply(lambda v: f" ({v:+.1f}%)")
            worst5["score"] = worst5[growth_col].abs().round(1)
            top5_ranking_panel(
                worst5[["rank", "region", "score"]],
                title=f"{metric_label} 감소 TOP 5",
                tag="2015→2024",
                unit_label="% 감소폭",
            )

    st.write("")
    st.divider()

    # ── 하단 상세 시각화: 좌 막대그래프 / 우 수치표 ──
    with st.container(border=True):
        chart_col, table_col = st.columns([2, 1], gap="medium")
        with chart_col:
            _section_title(f"시도별 {metric_label} 증가율 (상세)")
            bar_df = gap_df[["시도", growth_col]].sort_values(growth_col, ascending=True)
            colors = ["#E5484D" if v >= 0 else "#2F6FED" for v in bar_df[growth_col]]
            fig = go.Figure(
                go.Bar(
                    x=bar_df[growth_col], y=bar_df["시도"], orientation="h", marker_color=colors,
                    text=[f"{v:.1f}%" for v in bar_df[growth_col]], textposition="outside",
                )
            )
            fig.update_layout(
                height=480, margin=dict(l=10, r=30, t=10, b=10),
                plot_bgcolor="white", paper_bgcolor="white",
                xaxis=dict(title="증가율(%)", gridcolor="#F0F1F5", zeroline=True, zerolinecolor="#D8DAE3"),
                yaxis=dict(title=None),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.caption("모든 지역이 음수(-)라는 것은, 고령인구 1인당 공급이 10년간 전국에서 줄었다는 뜻입니다.")
        with table_col:
            _section_title("수치 표 데이터")
            table_df = gap_df[["시도", "시설_증가율", "요양병원_증가율"]].sort_values(growth_col)
            st.dataframe(table_df, use_container_width=True, hide_index=True, height=440)

    # ── 핵심 인사이트 (2열×2행, 노인복지시설/요양병원 관련 항목끼리 묶음) ──
    facility_up = gap_df[gap_df["시설_증가율"] > 0]
    facility_worst = gap_df.loc[gap_df["시설_증가율"].idxmin()]
    hospital_worst = gap_df.loc[gap_df["요양병원_증가율"].idxmin()]
    hospital_all_negative = (gap_df["요양병원_증가율"] < 0).all()
    _insight_grid([
        f"<b>[노인복지시설] 증가 지역</b>: {len(facility_up)}개 시도만 증가"
        + (f"({', '.join(facility_up['시도'])})" if len(facility_up) else "") + ", 나머지는 모두 감소했습니다.",
        f"<b>[노인복지시설] 최대 감소</b>: {facility_worst['시도']}가 {facility_worst['시설_증가율']:.1f}%로 가장 크게 줄었습니다.",
        f"<b>[요양병원] 전국 패턴</b>: "
        + ("17개 시도 전체가 감소 — 예외 없이 고령인구 1인당 공급이 줄었습니다." if hospital_all_negative
           else "일부 지역은 증가했지만 대부분 감소했습니다."),
        f"<b>[요양병원] 최대 감소</b>: {hospital_worst['시도']}가 {hospital_worst['요양병원_증가율']:.1f}%로 전국에서 가장 크게 줄었습니다.",
    ])


# ══════════════════════════════════════════════════════════════════════
# 탭 3·4 공용: 상관관계 탭
# ══════════════════════════════════════════════════════════════════════
def _render_corr_tab(metric_label: str, metric_col: str, unit: str, key_prefix: str) -> None:
    _inject_page_theme()
    panel = load_panel_df()
    corr_year_df = load_correlation_by_year_df()

    # 서연 수정분: 단일 연도 대신 연도 범위(시작~끝) 슬라이더 — 시작=끝이면 그 해 수준(level)을,
    # 시작≠끝이면 두 시점 사이의 변화량 기준 상관관계를 지도·산점도·TOP5·인사이트에 반영한다.
    start_year, end_year = st.slider(
        "연도 범위", min_value=2015, max_value=2024, value=(2015, 2024), step=1,
        key=f"{key_prefix}_year_range_sy",
    )
    is_range = start_year != end_year
    start_df = panel[panel["연도"] == start_year].set_index("시도")
    end_df = panel[panel["연도"] == end_year].set_index("시도")

    if not is_range:
        view_df = end_df.reset_index()
        map_col, x_col, y_col = metric_col, "고령인구비율", metric_col
        period_label = f"{end_year}년"
        map_tag = period_label
        color_label = f"{metric_label}({unit})"
        legend_low, legend_high = "낮음", "높음"
        x_label, y_label = "고령인구비율(%)", f"{metric_label}({unit})"
    else:
        # 서연 주의: pd.DataFrame({"시도": Index, "col": Series, ...})처럼 Index와 Series를
        # 섞어서 dict로 넘기면 정렬이 꼬여 값이 엉뚱한 시도에 매칭되는 pandas 버그가 있어서,
        # 반드시 두 데이터프레임을 같은 순서(common_sido)로 맞춘 뒤 .to_numpy()로 값만 꺼내 쓴다.
        common_sido = sorted(set(start_df.index) & set(end_df.index))
        start_df = start_df.loc[common_sido]
        end_df = end_df.loc[common_sido]

        change_col = f"{metric_col}_변화"
        view_df = pd.DataFrame({
            "시도": common_sido,
            "고령인구수_65세이상": end_df["고령인구수_65세이상"].to_numpy(),
            "고령인구비율_변화": (end_df["고령인구비율"] - start_df["고령인구비율"]).to_numpy(),
            change_col: (end_df[metric_col] - start_df[metric_col]).to_numpy(),
        })
        map_col, x_col, y_col = change_col, "고령인구비율_변화", change_col
        period_label = f"{start_year}→{end_year}"
        map_tag = f"{period_label} 변화량"
        color_label = f"{metric_label} 변화량({unit})"
        legend_low, legend_high = "감소", "증가"
        x_label, y_label = "고령인구비율 변화(%p)", f"{metric_label} 변화량({unit})"

    x = view_df[x_col].to_numpy(float)
    y = view_df[y_col].to_numpy(float)
    r, p = stats.pearsonr(x, y)
    strength = "강한" if abs(r) >= 0.7 else "중간" if abs(r) >= 0.4 else "약한" if abs(r) >= 0.2 else "거의 없는"
    direction = "양(+)의" if r > 0 else "음(-)의"

    # ── 메인 패널 ──
    left, right = st.columns([2, 1], gap="medium")
    with left:
        with st.container(border=True):
            region_panel(
                view_df,
                title=f"전국 {metric_label} {'변화' if is_range else '현황'}",
                tag=map_tag,
                color_col=map_col,
                size_col="고령인구수_65세이상",
                color_label=color_label,
                legend_low=legend_low,
                legend_high=legend_high,
            )

    with right:
        with st.container(border=True):
            _section_title(f"{period_label} 상관관계 인사이트")
            rel = "변화량" if is_range else "수준"
            _insight_box(
                f"고령인구비율{'변화' if is_range else ''}과 {metric_label} {rel} 간 상관계수는 "
                f"<b>r = {r:.2f}</b>({'유의함' if p < 0.05 else '유의하지 않음'}, p={p:.3f})으로 "
                f"<b>{strength} {direction} 상관관계</b>입니다.",
                icon="📊",
            )
            st.write("")
            top5 = view_df.sort_values(map_col, ascending=False).head(5).reset_index(drop=True)
            top5["rank"] = top5.index + 1
            top5["region"] = top5["시도"]
            top5["score"] = top5[map_col].round(1)
            top5_ranking_panel(
                top5[["rank", "region", "score"]],
                title=f"{metric_label} {'증가' if is_range else '상위'} TOP 5",
                tag=period_label, unit_label=unit,
            )

    st.write("")
    st.divider()

    # ── 하단 상세 시각화: 좌 산점도 / 우 데이터표 ──
    with st.container(border=True):
        chart_col, table_col = st.columns([2, 1], gap="medium")
        with chart_col:
            _section_title(f"고령인구비율 vs {metric_label} 산점도 (상세, {period_label})")
            fig = px.scatter(
                view_df, x=x_col, y=y_col, text="시도", trendline="ols",
                color_discrete_sequence=["#2F6FED"],
            )
            fig.update_traces(textposition="top center", marker=dict(size=9))
            fig.update_layout(
                height=420, margin=dict(l=10, r=10, t=10, b=10),
                plot_bgcolor="white", paper_bgcolor="white",
                xaxis=dict(title=x_label, gridcolor="#F0F1F5"),
                yaxis=dict(title=y_label, gridcolor="#F0F1F5"),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            trend = corr_year_df[corr_year_df["y"] == metric_col].sort_values("연도")
            if not trend.empty:
                st.caption(
                    f"(참고) 2015~2024 전체 연도별 추이: {trend.iloc[0]['연도']}년 r={trend.iloc[0]['pearson_r']:.2f} "
                    f"→ {trend.iloc[-1]['연도']}년 r={trend.iloc[-1]['pearson_r']:.2f}"
                )
        with table_col:
            _section_title("수치 표 데이터")
            st.dataframe(
                view_df[["시도", x_col, y_col]].sort_values(y_col, ascending=False),
                use_container_width=True, hide_index=True, height=400,
            )

    # ── 핵심 인사이트 (2열×2행) ──
    top_region = view_df.loc[view_df[map_col].idxmax()]
    bottom_region = view_df.loc[view_df[map_col].idxmin()]
    trend_full = corr_year_df[corr_year_df["y"] == metric_col].sort_values("연도")
    r_first, r_last = trend_full.iloc[0], trend_full.iloc[-1]
    _insight_grid([
        f"<b>{period_label} 상관계수</b>: r = {r:.2f} ({'유의' if p < 0.05 else '유의하지 않음'}, p={p:.3f}) — {strength} {direction} 관계입니다.",
        f"<b>2015~2024 전체 추이(참고)</b>: {int(r_first['연도'])}년 r={r_first['pearson_r']:.2f} → {int(r_last['연도'])}년 r={r_last['pearson_r']:.2f}로 변화했습니다.",
        f"<b>{'가장 많이 증가' if is_range else '최고 지역'}</b>: {top_region['시도']} ({top_region[map_col]:.1f}{unit}) — "
        + ("고령인구 대비 공급이 가장 빠르게 늘었습니다." if is_range else "고령인구 대비 공급이 가장 넉넉합니다."),
        f"<b>{'가장 많이 감소' if is_range else '최저 지역'}</b>: {bottom_region['시도']} ({bottom_region[map_col]:.1f}{unit}) — "
        + ("고령인구 대비 공급이 가장 빠르게 줄었습니다." if is_range else "고령인구 대비 공급이 가장 부족합니다."),
    ])


def render_facility_corr_tab() -> None:
    _render_corr_tab("노인복지시설", "고령인구10만명당_노인복지시설수", "개", "facility_corr")


def render_hospital_corr_tab() -> None:
    _render_corr_tab("요양병원", "고령인구10만명당_요양병원수", "개", "hospital_corr")
