from pathlib import Path


APP_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = APP_DIR / "data" / "ped_stats.csv"
KOREA_MAP_PATH = APP_DIR / "data" / "skorea_provinces_geo_simple.json"
KOREA_MAP_URL = (
    "https://raw.githubusercontent.com/southkorea/southkorea-maps/"
    "master/kostat/2013/json/skorea_provinces_geo_simple.json"
)

MAP_REGION_ALIASES = {
    "강원특별자치도": "강원도",
    "전북특별자치도": "전라북도",
}

REQUIRED_COLUMNS = {
    "시점",
    "지역",
    "의원1개당전문의수",
    "아동1만명당전문의수",
}

METRIC_OPTIONS = [
    ("의원1개당전문의수", "의원 1개당 전문의 수"),
    ("아동1만명당전문의수", "아동 1만 명당 전문의 수"),
]
METRIC_LABELS = dict(METRIC_OPTIONS)

ANALYSIS_START_YEAR = 2015
ANALYSIS_END_YEAR = 2024
