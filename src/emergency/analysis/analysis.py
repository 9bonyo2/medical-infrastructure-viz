# map_visualize.py
import os
import requests
import json
import pandas as pd
import folium
import streamlit as st
from scipy import stats
from src.emergency.collect import collect as dc
from src.emergency.config import (
    DOCTOR_DIR,
    DOCTOR_MAP_DIR,
    EMERGENCY_DIR,
    EMERGENCY_MAP_DIR,
    GEOJSON_PATH,
    POPULATION_DIR,
    TIME_DIR,
    TIME_MAP_DIR
)

REGION_DICT = {
    '서울특별시': '서울', '부산광역시': '부산', '대구광역시': '대구',
    '인천광역시': '인천', '광주광역시': '광주', '대전광역시': '대전',
    '울산광역시': '울산', '세종특별자치시': '세종', '경기도': '경기',
    '강원도': '강원', '강원특별자치도': '강원', '충청북도': '충북',
    '충청남도': '충남', '전라북도': '전북', '전북특별자치도': '전북',
    '전라남도': '전남', '경상북도': '경북', '경상남도': '경남',
    '제주특별자치도': '제주', '제주도': '제주'
}

REGION_COORDS = {
    '서울': [37.5665, 126.9780],
    '부산': [35.1796, 129.0756],
    '대구': [35.8714, 128.6014],
    '인천': [37.4563, 126.7052],
    '광주': [35.1595, 126.8526],
    '대전': [36.3504, 127.3845],
    '울산': [35.5384, 129.3114],
    '세종': [36.5300, 127.2890],
    '경기': [37.5000, 127.3000],
    '강원': [37.8228, 128.1555],
    '충북': [36.8000, 127.7500],
    '충남': [36.5184, 126.8000],
    '전북': [35.7175, 127.1530],
    '전남': [34.8161, 126.8500],
    '경북': [36.4919, 128.8889],
    '경남': [35.4606, 128.2132],
    '제주': [33.3800, 126.5312]
}

def get_geojson_data():
    geojson_url = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2013/json/skorea_provinces_geo_simple.json"

    if not GEOJSON_PATH.exists():
        res = requests.get(geojson_url)
        if not res.ok:
            print(f"[error] GeoJSON을 다운로드할 수 없습니다.")
            return None

        with open(GEOJSON_PATH, 'w', encoding='utf-8') as f:
            f.write(res.text)

    with open(GEOJSON_PATH, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)

    for feature in geojson_data["features"]:
        full_name = feature["properties"]["name"]
        feature["properties"]["name_short"] = REGION_DICT.get(full_name, full_name)

    return geojson_data

# ================================================================
def add_right_fixed_legend(m, min_val, max_val, label, fill_color="YlGnBu"):
    """지도 우측 끝에 여백 없이 딱 붙는 세로형 컬러바 렌더링"""

    # Folium fill_color에 맞춘 그라데이션 매핑 (위: 최대값 -> 아래: 최소값)
    gradients = {
        "YlGnBu": "linear-gradient(to bottom, #081d58, #225ea8, #41b6c4, #a1dab4, #ffffcc)",
        "YlOrRd": "linear-gradient(to bottom, #800026, #e31a1c, #feb24c, #ffeda0, #ffffcc)",
        "Reds": "linear-gradient(to bottom, #67000d, #cb181d, #fb6a4a, #fcae91, #fee5d9)",
    }
    gradient_css = gradients.get(fill_color, gradients["YlGnBu"])

    # 5단계 눈금 수치 계산
    step = (max_val - min_val) / 4 if max_val > min_val else 1
    t1 = max_val
    t2 = max_val - step
    t3 = max_val - step * 2
    t4 = max_val - step * 3
    t5 = min_val

    unit_str = label.split()[-1] if label else ""

    legend_html = f"""
    <style>
        /* Folium 기본 상단 가로 범례 완전 숨김 */
        .leaflet-top.leaflet-right, svg.legend {{
            display: none !important;
        }}
    </style>
    <div style="
        position: fixed; 
        top: 20px; 
        right: 12px; 
        z-index: 9999; 
        pointer-events: none;
        font-family: 'Pretendard', 'Malgun Gothic', sans-serif;
    ">
        <!-- 상단 지표 라벨 -->
        <div style="
            font-size: 11px; 
            font-weight: 700; 
            color: #1E293B; 
            margin-bottom: 6px; 
            text-align: right;
            text-shadow: 1px 1px 2px #ffffff;
        ">
            단위: {unit_str}
        </div>

        <div style="display: flex; align-items: stretch; height: 260px; gap: 6px; justify-content: flex-end;">
            <!-- 세로 컬러 바 -->
            <div style="
                width: 8px; 
                height: 100%; 
                border-radius: 4px; 
                background: {gradient_css};
                box-shadow: 0 1px 3px rgba(0,0,0,0.25);
            "></div>

            <!-- 5단계 눈금 수치 -->
            <div style="
                display: flex; 
                flex-direction: column; 
                justify-content: space-between; 
                font-size: 10px; 
                color: #334155; 
                font-weight: 700;
                line-height: 1;
                text-shadow: 1px 1px 1px #ffffff, -1px -1px 1px #ffffff;
            ">
                <span>{t1:.1f}</span>
                <span>{t2:.1f}</span>
                <span>{t3:.1f}</span>
                <span>{t4:.1f}</span>
                <span>{t5:.1f}</span>
            </div>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

def render_base_map(df, columns, label, path,
                    tooltip_fields, tooltip_aliases, fill_color="YlOrRd"):

    geojson_data = get_geojson_data()
    if geojson_data is None:
        return

    df_dict = df.set_index("지역").to_dict(orient="index")
    for feature in geojson_data["features"]:
        r_name = feature["properties"]["name_short"]
        if r_name in df_dict:
            feature["properties"].update(df_dict[r_name])

    m = folium.Map(location=[35.9, 127.4], zoom_start=6.8, tiles=None)

    choro = folium.Choropleth(
        geo_data=geojson_data,
        name="Choropleth",
        data=df,
        columns=["지역", columns],
        key_on="feature.properties.name_short",
        fill_color=fill_color,
        fill_opacity=0.7,
        line_opacity=0.3,
        legend_name="",
        highlight=True,
    ).add_to(m)

    min_val = float(df[columns].min())
    max_val = float(df[columns].max())
    add_right_fixed_legend(m, min_val, max_val, label, fill_color=fill_color)

    folium.GeoJson(
        geojson_data,
        style_function=lambda x: {
            "fillColor": "#000000",
            "color": "#444444",
            "weight": 1,
            "fillOpacity": 0.0,
        },
        highlight_function=lambda x: {
            "fillColor": "#222222",
            "color": "#111111",
            "weight": 2.5,
            "fillOpacity": 0.25,
        },
        tooltip=folium.features.GeoJsonTooltip(
            fields=tooltip_fields,
            aliases=tooltip_aliases,
            localize=True,
            sticky=True,
            labels=True,
            style="""
                background-color: #FFFFFF;
                border: 1.5px solid #333333;
                border-radius: 6px;
                box-shadow: 2px 2px 6px rgba(0,0,0,0.2);
                font-family: 'Malgun Gothic', sans-serif;
                font-size: 12px;
                line-height: 1.6;
                padding: 8px 12px;
                color: #111111;
            """,
        ),
    ).add_to(m)

    for region, coord in REGION_COORDS.items():
        label_html = f"""
        <div style="
            display: flex;
            align-items: center;
            font-family: 'Malgun Gothic', sans-serif;
            font-size: 11px;
            font-weight: bold;
            color: #111111;
            white-space: nowrap;
            pointer-events: none;
            transform: translate(-4px, -50%);
        ">
            <span style="
                display: inline-block;
                width: 7px;
                height: 7px;
                background-color: #333333;
                border: 1.5px solid #ffffff;
                border-radius: 50%;
                box-shadow: 0 0 2px rgba(0,0,0,0.5);
                margin-right: 4px;
            "></span>
            <span style="
                text-shadow: -1px -1px 0 #fff, 1px -1px 0 #fff, -1px 1px 0 #fff, 1px 1px 0 #fff;
            ">{region}</span>
        </div>
        """
    
        folium.Marker(
            location=coord, icon=folium.DivIcon(html=label_html)
        ).add_to(m)
    
    path.parent.mkdir(parents=True, exist_ok=True)
    m.save(path)
    print(f'[success] 시각화 완료: {path}')
    return m

# 1) 지역별 인구수 대비 전체 응급의료기관 수 시각화
def create_emergency_map(data_year):
    pop_file = POPULATION_DIR / f"pop{data_year}.csv"
    emer_file = EMERGENCY_DIR / f"emer{data_year}.csv"
    
    if not pop_file.exists() or not emer_file.exists():
        print(f"[error] {data_year}년 데이터가 부족하여 지도를 그릴 수 없습니다.")
        return None

    pop_df = pd.read_csv(pop_file)
    emer_df = pd.read_csv(emer_file)
    df = pd.merge(pop_df, emer_df, on='지역')
    
    # 인구 10만 명당 응급의료기관 수 계산
    df['10만명당_기관수'] = ((df['기관수'] / df['인구수']) * 100000).round(2)

    df["인구수_표시"] = df["인구수"].apply(lambda x: f"{int(x):,}명")
    df["기관수_표시"] = df["기관수"].apply(lambda x: f"{int(x):,}개")
    df["10만명당_기관수_표시"] = df["10만명당_기관수"].apply(
        lambda x: f"{x:.2f}개"
    )

    output_path = EMERGENCY_MAP_DIR / f'emer{data_year}.html'
    render_base_map(
        df, 
        "10만명당_기관수", 
        f'{data_year}년 인구 10만명당 전체 응급의료기관 수',
        output_path,
        tooltip_fields=[
            "name_short",
            "인구수_표시",
            "기관수_표시",
            "10만명당_기관수_표시",
        ],
        tooltip_aliases=[
            "지역:",
            "총 인구수:",
            "전체 기관수:",
            "10만명당 기관수:",
        ],
        fill_color="YlGnBu"
    )

    return df

# 2) 지역별 인구수 대비 응급전문의 수 시각화
def create_doctor_map(data_year):
    pop_file = POPULATION_DIR / f"pop{data_year}.csv"
    doc_file = DOCTOR_DIR / f"doc{data_year}.csv"

    if not pop_file.exists() or not doc_file.exists():
        print(f"[error] {data_year}년 데이터가 부족하여 지도를 그릴 수 없습니다.")
        return None

    pop_df = pd.read_csv(pop_file)
    doc_df = pd.read_csv(doc_file)
    df = pd.merge(pop_df, doc_df, on="지역")

    # 인구 10만 명당 응급의학 전문의 수
    df["10만명당_전문의수"] = ((df["응급의학_전문의수"] / df["인구수"]) * 100000).round(2)

    df["인구수_표시"] = df["인구수"].apply(lambda x: f"{int(x):,}명")
    df["전문의수_표시"] = df["응급의학_전문의수"].apply(
        lambda x: f"{int(x):,}명"
    )
    df["10만명당_전문의수_표시"] = df["10만명당_전문의수"].apply(
        lambda x: f"{x:.2f}명"
    )

    output_path = DOCTOR_MAP_DIR / f"doc{data_year}.html"
    render_base_map(
        df,
        "10만명당_전문의수",
        f"{data_year}년 인구 10만명당 응급의학 전문의 수",
        output_path,
        tooltip_fields=[
            "name_short",
            "인구수_표시",
            "전문의수_표시",
            "10만명당_전문의수_표시",
        ],
        tooltip_aliases=[
            "지역:",
            "총 인구수:",
            "응급전문의수:",
            "10만명당 전문의수:",
        ],
        fill_color="YlOrRd",
    )

    return df

# 3) 지역별 상위 응급기관수 대비 Delay(2시간 이상 소요) 환자수 시각화
def create_time_map(data_year):
    emer_file = EMERGENCY_DIR / f"emer{data_year}.csv"
    time_file = TIME_DIR / f"time{data_year}.csv"

    if not emer_file.exists() or not time_file.exists():
        print(f"[error] {data_year}년 데이터가 부족하여 지도를 그릴 수 없습니다.")
        return None

    emer_df = pd.read_csv(emer_file)
    delay_df = pd.read_csv(time_file)
    df = pd.merge(emer_df, delay_df, on="지역")

    df["상위기관당_지연환자수"] = df["2시간이상_소요환자수"] / df["상위2개기관수"]\
        .replace(0, pd.NA)
    df["상위기관당_지연환자수"] = df["상위기관당_지연환자수"].fillna(0).round(2)

    df["상위기관수_표시"] = df["상위2개기관수"].apply(lambda x: f"{int(x):,}개")
    df["지연환자수_표시"] = df["2시간이상_소요환자수"].apply(
        lambda x: f"{int(x):,}명"
    )
    df["상위기관당_지연환자수_표시"] = df["상위기관당_지연환자수"].apply(
        lambda x: f"{x:,.1f}명"
    )

    output_path = TIME_MAP_DIR / f"time{data_year}.html"
    render_base_map(
        df,
        "상위기관당_지연환자수",
        f"{data_year}년 상위 응급의료기관(권역, 지역의료센터) 1곳당 2시간 이상 지연 도착 환자수 (명)",
        output_path,
        tooltip_fields=[
            "name_short",
            "상위기관수_표시",
            "지연환자수_표시",
            "상위기관당_지연환자수_표시",
        ],
        tooltip_aliases=[
            "지역:",
            "상위 응급기관수:",
            "2시간이상 지연환자:",
            "기관당 지연환자:",
        ],
        fill_color="Reds",
    )

    return df

def ensure_all_years_data(api_key, years=list(range(2015, 2025))):
    """
    10개년 CSV 파일 중 누락된 파일이 있다면 수집/전처리 함수를 호출하여 
    모든 연도의 CSV를 사전에 생성해두는 워밍업 함수
    """
    for yr in years:
        pop_f = POPULATION_DIR / f"pop{yr}.csv"
        emer_f = EMERGENCY_DIR / f"emer{yr}.csv"
        doc_f = DOCTOR_DIR / f"doc{yr}.csv"
        time_f = TIME_DIR / f"time{yr}.csv"

        # 1. 인구 데이터 수집/저장
        if not pop_f.exists():
            try:
                dc.get_population(api_key, yr)
            except Exception as e:
                print(f"[{yr}년 인구 데이터 생성 실패] {e}")

        # 2. 응급의료기관 데이터 수집/저장
        if not emer_f.exists():
            try:
                dc.get_emergency(api_key, yr)
            except Exception as e:
                print(f"[{yr}년 기관 데이터 생성 실패] {e}")

        # 3. 응급의학 전문의 데이터 수집/저장
        if not doc_f.exists():
            try:
                dc.get_doctor(api_key, yr)
            except Exception as e:
                print(f"[{yr}년 전문의 데이터 생성 실패] {e}")

        # 4. 이송 소요시간 데이터 수집/저장 
        if not time_f.exists():
            try:
                dc.get_time(api_key, yr)
            except Exception as e:
                print(f"[{yr}년 이송시간 데이터 생성 실패] {e}")

    return True

def calculate_emergency_kpis(target_year: int = 2024) -> dict:
    """기본 2024년 및 전년도(2023년) 실데이터 비교 증감률 계산"""
    def get_summary(yr):
        pop_f = POPULATION_DIR / f"pop{yr}.csv"
        emer_f = EMERGENCY_DIR / f"emer{yr}.csv"
        doc_f = DOCTOR_DIR / f"doc{yr}.csv"
        time_f = TIME_DIR / f"time{yr}.csv"

        if not (pop_f.exists() and emer_f.exists() and doc_f.exists() and time_f.exists()):
            return None

        try:
            p_df = pd.read_csv(pop_f)
            e_df = pd.read_csv(emer_f)
            d_df = pd.read_csv(doc_f)
            t_df = pd.read_csv(time_f)

            total_pop = p_df["인구수"].sum()
            total_emer = e_df["기관수"].sum()
            total_upper = e_df["상위2개기관수"].sum() if "상위2개기관수" in e_df.columns else 0
            total_doc = d_df["응급의학_전문의수"].sum()
            total_delay = t_df["2시간이상_소요환자수"].sum()

            return {
                "fac_per_100k": (total_emer / total_pop) * 100000 if total_pop > 0 else 0,
                "doc_per_100k": (total_doc / total_pop) * 100000 if total_pop > 0 else 0,
                "delay_patients": total_delay,
                "delay_per_center": (total_delay / total_upper) if total_upper > 0 else 0,
            }
        except Exception:
            return None

    curr = get_summary(target_year)
    prev = get_summary(target_year - 1)

    if not curr:
        return {
            "facility_per_100k": {"value": "-", "unit": "개", "delta": None, "trend": "up"},
            "doctor_per_100k": {"value": "-", "unit": "명", "delta": None, "trend": "up"},
            "delayed_patients": {"value": "-", "unit": "명", "delta": None, "trend": "down"},
            "delayed_per_center": {"value": "-", "unit": "명/개소", "delta": None, "trend": "down"},
        }

    def calc_delta(c_val, p_val, unit_str="", is_int=False):
        if not prev or p_val == 0:
            return None, "up"
        diff = c_val - p_val
        pct = (diff / p_val) * 100
        trend = "up" if diff > 0 else "down" if diff < 0 else "same"
        
        if is_int:
            return f"{abs(int(diff)):,}{unit_str} ({abs(pct):.1f}%)", trend
        return f"{abs(diff):.2f}{unit_str} ({abs(pct):.1f}%)", trend

    d1, t1 = calc_delta(curr["fac_per_100k"], prev["fac_per_100k"] if prev else 0, "개")
    d2, t2 = calc_delta(curr["doc_per_100k"], prev["doc_per_100k"] if prev else 0, "명")
    d3, t3 = calc_delta(curr["delay_patients"], prev["delay_patients"] if prev else 0, "명", is_int=True)
    d4, t4 = calc_delta(curr["delay_per_center"], prev["delay_per_center"] if prev else 0, "명")

    return {
        "facility_per_100k": {
            "value": round(curr["fac_per_100k"], 2),
            "unit": "개",
            "delta": d1,
            "trend": t1
        },
        "doctor_per_100k": {
            "value": round(curr["doc_per_100k"], 2),
            "unit": "명",
            "delta": d2,
            "trend": t2
        },
        "delayed_patients": {
            "value": int(curr["delay_patients"]),
            "unit": "명",
            "delta": d3,
            "trend": t3
        },
        "delayed_per_center": {
            "value": round(curr["delay_per_center"], 1),
            "unit": "명/개소",
            "delta": d4,
            "trend": t4
        },
    }

def get_emergency_correlation_trend(years=list(range(2015, 2025))) -> pd.DataFrame:

    records = []

    for yr in years:
        try:
            pop_f = POPULATION_DIR / f"pop{yr}.csv"
            emer_f = EMERGENCY_DIR / f"emer{yr}.csv"
            doc_f = DOCTOR_DIR / f"doc{yr}.csv"
            time_f = TIME_DIR / f"time{yr}.csv"

            if not (pop_f.exists() and emer_f.exists() and doc_f.exists()):
                continue

            df_pop = pd.read_csv(pop_f)
            df_emer = pd.read_csv(emer_f)
            df_doc = pd.read_csv(doc_f)

            merged = df_pop.merge(df_emer, on="지역").merge(df_doc, on="지역")
            merged["10만명당_기관수"] = (merged["기관수"] / merged["인구수"]) * 100000
            merged["10만명당_전문의수"] = (merged["응급의학_전문의수"] / merged["인구수"]) * 100000

            # 1. 10만명당 기관수 vs 10만명당 전문의수
            clean_1 = merged.dropna(subset=["10만명당_기관수", "10만명당_전문의수"])
            r_fac_doc, p_fac_doc = stats.pearsonr(clean_1["10만명당_기관수"], clean_1["10만명당_전문의수"])

            # 2. 지연환자 연계 지표 (time 파일 존재 시 연산)
            r_fac_delay, p_fac_delay = None, None
            r_doc_delay, p_doc_delay = None, None

            if time_f.exists():
                df_time = pd.read_csv(time_f)
                merged_time = merged.merge(df_time, on="지역")
                merged_time["상위기관당_지연환자수"] = (
                    merged_time["2시간이상_소요환자수"] / merged_time["상위2개기관수"].replace(0, pd.NA)
                ).fillna(0)

                valid_df = merged_time.dropna(subset=["10만명당_기관수", "10만명당_전문의수", "상위기관당_지연환자수"])
                if len(valid_df) >= 5:
                    r_fac_delay, p_fac_delay = stats.pearsonr(valid_df["10만명당_기관수"], valid_df["상위기관당_지연환자수"])
                    r_doc_delay, p_doc_delay = stats.pearsonr(valid_df["10만명당_전문의수"], valid_df["상위기관당_지연환자수"])

            records.append({
                "year": yr,
                "기관수-전문의수": round(r_fac_doc, 3),
                "기관수-지연환자": round(r_fac_delay, 3) if r_fac_delay is not None else None,
                "전문의수-지연환자": round(r_doc_delay, 3) if r_doc_delay is not None else None,
                "p_fac_doc": round(p_fac_doc, 4),
                "p_fac_delay": round(p_fac_delay, 4) if p_fac_delay is not None else None,
                "p_doc_delay": round(p_doc_delay, 4) if p_doc_delay is not None else None,
            })
        except Exception as e:
            print(f"[{yr}년 연산 오류] {e}")
            continue

    return pd.DataFrame(records)

