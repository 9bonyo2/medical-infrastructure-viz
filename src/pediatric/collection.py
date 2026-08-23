import json
import os
import urllib.request
import pandas as pd

# 현재 파일(collection.py)의 위치 기준으로 프로젝트 최상위 루트 디렉토리(medical-infrastructure-viz) 탐색
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))

# 루트 디렉토리 기준 절대 경로로 데이터 디렉토리 설정
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "pediatric")
LOCAL_GEOJSON_PATH = os.path.join(DATA_DIR, "skorea_sido_boundary.geojson")
REMOTE_GEOJSON_URL = "https://raw.githubusercontent.com/southkorea/southkorea-maps/master/kostat/2013/json/skorea_provinces_2013_geo.json"


def collect_birth_data(
    input_path: str = "data/pediatric/시군구_출생아수_합계출산율.csv",
    output_path: str = os.path.join(DATA_DIR, "연도별_출생아수_합계출산율.csv"),
) -> pd.DataFrame:

    df = pd.read_csv(input_path, header=[0, 1])

    columns = list(df.columns)
    columns[0] = ("연도별", "시도별")
    df.columns = pd.MultiIndex.from_tuples(columns)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return df


def collect_pediatric_data(
    input_path: str = "data/pediatric/시도별_표시과목별_기관수.csv",
    output_path: str = os.path.join(DATA_DIR, "연도별_소아청소년과_기관수_평균.csv"),
) -> pd.DataFrame:
   
    if not os.path.exists(input_path) and os.path.exists(
        "시도별_표시과목별_기관수.csv"
    ):
        input_path = "시도별_표시과목별_기관수.csv"

    df = pd.read_csv(input_path)

    df["연도별"] = df["시점"].astype(str).str.split(".").str[0]
    df["시도별"] = df["시도별"].astype(str).str.strip().replace({"계": "전국"})

    result = (
        df.groupby(["연도별", "시도별"])["소아청소년과"].mean().reset_index()
    )
    result["소아청소년과"] = result["소아청소년과"].round(2)
    result = result.sort_values(
        by=["연도별", "소아청소년과"], ascending=[True, False]
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    result.to_csv(output_path, index=False, encoding="utf-8-sig")
    return result


def get_geojson(
    local_path: str = LOCAL_GEOJSON_PATH, url: str = REMOTE_GEOJSON_URL
) -> dict | None:
   
    geo_data = None

    if os.path.exists(local_path):
        with open(local_path, "r", encoding="utf-8") as f:
            geo_data = json.load(f)
    else:
        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                geo_data = json.loads(response.read().decode("utf-8"))

            with open(local_path, "w", encoding="utf-8") as f:
                json.dump(geo_data, f, ensure_ascii=False)
        except Exception:
            return None

    name_map = {"강원도": "강원특별자치도", "전라북도": "전북특별자치도"}

    for feature in geo_data.get("features", []):
        name = feature["properties"].get("name", "")
        if name in name_map:
            feature["properties"]["name"] = name_map[name]

    return geo_data


def run_data_collection():
    print("데이터 수집 및 정제 시작 (저장 위치: ./data)...")
    collect_birth_data()
    collect_pediatric_data()
    get_geojson()
    print("데이터 수집 완료!")


if __name__ == "__main__":
    run_data_collection()