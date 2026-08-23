import matplotlib.pyplot as plt
from matplotlib import font_manager
import streamlit as st


def configure_matplotlib_font() -> None:
    """실행 환경에 설치된 한글 글꼴을 우선 적용한다."""
    installed_fonts = {font.name for font in font_manager.fontManager.ttflist}
    for font_name in ("Malgun Gothic", "AppleGothic", "NanumGothic"):
        if font_name in installed_fonts:
            plt.rcParams["font.family"] = font_name
            break
    plt.rcParams["axes.unicode_minus"] = False


def inject_pediatric_page_style() -> None:
    """분석 요약 카드의 글자 크기와 줄바꿈 스타일을 적용한다."""
    st.markdown(
        """
        <style>
        :is(
            .st-key-global-kpi-year-card,
            .st-key-global-kpi-region-card,
            .st-key-global-kpi-clinic-card,
            .st-key-global-kpi-child-card
        ),
        :is(
            .st-key-global-kpi-year-card,
            .st-key-global-kpi-region-card,
            .st-key-global-kpi-clinic-card,
            .st-key-global-kpi-child-card
        ) [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #ffffff !important;
            border-color: #e5e7eb !important;
            border-radius: 0.9rem !important;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06) !important;
        }

        :is(.st-key-trend-summary-card, .st-key-year-comparison-summary-card) {
            --summary-font-size: clamp(0.72rem, 0.78vw, 0.9rem);
        }

        :is(.st-key-trend-summary-card, .st-key-year-comparison-summary-card)
        [data-testid="stMarkdownContainer"] :is(h1, h2, h3, h4, h5, h6, p, span),
        :is(.st-key-trend-summary-card, .st-key-year-comparison-summary-card)
        [data-testid="stCaptionContainer"] :is(p, span),
        :is(.st-key-trend-summary-card, .st-key-year-comparison-summary-card)
        [data-testid="stMetricLabel"] p,
        :is(.st-key-trend-summary-card, .st-key-year-comparison-summary-card)
        [data-testid="stMetricValue"],
        :is(.st-key-trend-summary-card, .st-key-year-comparison-summary-card)
        [data-testid="stMetricValue"] > div,
        :is(.st-key-trend-summary-card, .st-key-year-comparison-summary-card)
        [data-testid="stMetricDelta"],
        :is(.st-key-trend-summary-card, .st-key-year-comparison-summary-card)
        [data-testid="stMetricDelta"] * {
            font-size: var(--summary-font-size) !important;
            line-height: 1.35 !important;
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: clip !important;
            overflow-wrap: anywhere !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )