# app/emergency/emergency_jh/src/config.py
from pathlib import Path

# 1. 디렉토리 계층 계산
SRC_DIR = Path(__file__).resolve().parent            
JH_DIR = SRC_DIR.parent                              
APP_DIR = JH_DIR.parent.parent                       
ROOT_DIR = APP_DIR.parent                            

# 2. 데이터 저장 폴더
DATA_DIR = JH_DIR / "data"

GEOJSON_PATH = DATA_DIR / "skorea_provinces_geo_simple.json"

POPULATION_DIR = DATA_DIR / "population"
DOCTOR_DIR = DATA_DIR / "doctor"
EMERGENCY_DIR = DATA_DIR / "emergency_center"
TIME_DIR = DATA_DIR / "time_delay"

# 3. 지도 HTML 저장 폴더
MAP_DIR = DATA_DIR / "maps"
DOCTOR_MAP_DIR = MAP_DIR / "doctor_maps"
EMERGENCY_MAP_DIR = MAP_DIR / "emergency_maps"
TIME_MAP_DIR = MAP_DIR / "time_maps"

# 4. 필수 디렉토리 일괄 자동 생성
ALL_DIRS = [
    POPULATION_DIR,
    DOCTOR_DIR,
    EMERGENCY_DIR,
    TIME_DIR,
    MAP_DIR,
    DOCTOR_MAP_DIR,
    EMERGENCY_MAP_DIR,
    TIME_MAP_DIR,
]

for directory in ALL_DIRS:
    directory.mkdir(parents=True, exist_ok=True)