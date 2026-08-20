# map_visualize.py
import os
import requests
import json
import pandas as pd
import folium
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

    # data/emergency가 없으면 생성
    GEOJSON_PATH.parent.mkdir(parents=True, exist_ok=True)
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

    m = folium.Map(location=[36.3, 127.8], zoom_start=7, tiles=None)

    folium.Choropleth(
        geo_data=geojson_data,
        name="Choropleth",
        data=df,
        columns=["지역", columns],
        key_on="feature.properties.name_short",
        fill_color=fill_color,
        fill_opacity=0.7,
        line_opacity=0.3,
        legend_name=label,
        highlight=True,
    ).add_to(m)

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