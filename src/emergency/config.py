from pathlib import Path 

# 루트 디렉토리
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# 데이터 공통 및 응급의료 데이터 루트
DATA_DIR = ROOT_DIR / "data"
DATA_EMERGENCY_DIR = DATA_DIR / "emergency"

# GeoJSON 파일 경로
GEOJSON_PATH = DATA_EMERGENCY_DIR / "skorea_provinces_geo_simple.json"

POPULATION_DIR = DATA_EMERGENCY_DIR / "population"
EMERGENCY_DIR = DATA_EMERGENCY_DIR / "emergency"
DOCTOR_DIR = DATA_EMERGENCY_DIR / "doctor"
TIME_DIR = DATA_EMERGENCY_DIR / "time"
MAP_DIR = DATA_EMERGENCY_DIR / "map"

# 맵 세부 저장 폴더
EMERGENCY_MAP_DIR = MAP_DIR / "emergency_map"
DOCTOR_MAP_DIR = MAP_DIR / "doctor_map"
TIME_MAP_DIR = MAP_DIR / "time_map"