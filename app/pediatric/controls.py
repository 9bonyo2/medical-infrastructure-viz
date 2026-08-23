import streamlit as st

from pediatric.config import METRIC_OPTIONS


def select_year_dropdown(
    label: str,
    years: list[int],
    key: str,
    show_label: bool = True,
) -> int:
    """텍스트 입력 없이 목록 클릭만 가능한 연도 선택 드롭다운을 만든다."""
    if not years:
        raise ValueError("연도 선택 목록이 비어 있습니다.")

    if key not in st.session_state or st.session_state[key] not in years:
        st.session_state[key] = years[-1]

    if show_label:
        st.markdown(f"**{label}**")

    selected_year = int(st.session_state[key])
    with st.popover(f"{selected_year}년", use_container_width=True):
        for year in sorted(years, reverse=True):
            is_selected = year == selected_year
            button_label = f"✓ {year}년" if is_selected else f"{year}년"

            if st.button(
                button_label,
                key=f"{key}_option_{year}",
                type="primary" if is_selected else "secondary",
                use_container_width=True,
            ):
                st.session_state[key] = year
                st.rerun()

    return selected_year


def select_regions_dropdown(
    label: str,
    regions: list[str],
    key: str,
) -> list[str]:
    """검색 입력 칸 없이 클릭으로 여러 지역을 선택하는 드롭다운을 만든다."""
    saved_regions = st.session_state.get(key)
    if not isinstance(saved_regions, list):
        saved_regions = regions.copy()

    selected_regions = [region for region in regions if region in saved_regions]
    st.session_state[key] = selected_regions

    if len(selected_regions) == len(regions):
        trigger_label = f"전체 지역 ({len(regions)}개)"
    elif not selected_regions:
        trigger_label = "지역을 선택해 주세요"
    elif len(selected_regions) == 1:
        trigger_label = selected_regions[0]
    else:
        trigger_label = f"{selected_regions[0]} 외 {len(selected_regions) - 1}개"

    st.markdown(f"**{label}**")
    with st.popover(trigger_label, use_container_width=True):
        select_all_column, clear_column = st.columns(2)

        with select_all_column:
            if st.button(
                "전체 선택",
                key=f"{key}_select_all",
                use_container_width=True,
            ):
                st.session_state[key] = regions.copy()
                st.rerun()

        with clear_column:
            if st.button(
                "선택 해제",
                key=f"{key}_clear_all",
                use_container_width=True,
            ):
                st.session_state[key] = []
                st.rerun()

        st.divider()
        for region in regions:
            is_selected = region in selected_regions
            button_label = f"✓ {region}" if is_selected else region

            if st.button(
                button_label,
                key=f"{key}_option_{region}",
                type="primary" if is_selected else "secondary",
                use_container_width=True,
            ):
                updated_regions = selected_regions.copy()
                if is_selected:
                    updated_regions.remove(region)
                else:
                    updated_regions.append(region)

                st.session_state[key] = updated_regions
                st.rerun()

    return selected_regions


def keep_only_selected_metric(selected_metric: str, key_prefix: str) -> None:
    """지표 체크박스가 항상 한 개만 선택되도록 상태를 정리한다."""
    selected_key = f"{key_prefix}_{selected_metric}"

    if not st.session_state.get(selected_key, False):
        st.session_state[selected_key] = True
        return

    for metric, _ in METRIC_OPTIONS:
        if metric != selected_metric:
            st.session_state[f"{key_prefix}_{metric}"] = False


def select_metric_with_checkboxes(label: str, key_prefix: str) -> str:
    """두 공급 지표 중 한 개만 체크박스로 선택한다."""
    st.markdown(f"**{label}**")
    columns = st.columns(2)

    for index, (metric, metric_label) in enumerate(METRIC_OPTIONS):
        state_key = f"{key_prefix}_{metric}"
        if state_key not in st.session_state:
            st.session_state[state_key] = index == 0

        with columns[index]:
            st.checkbox(
                metric_label,
                key=state_key,
                on_change=keep_only_selected_metric,
                args=(metric, key_prefix),
            )

    for metric, _ in METRIC_OPTIONS:
        if st.session_state.get(f"{key_prefix}_{metric}", False):
            return metric

    return METRIC_OPTIONS[0][0]