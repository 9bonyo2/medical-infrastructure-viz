# app/emergency/emergency_jh/src/config.py
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data" / "emergency"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

POPULATION_DIR = PROCESSED_DIR / "population"
EMERGENCY_DIR = PROCESSED_DIR / "emergency"
DOCTOR_DIR = PROCESSED_DIR / "doctor"
TIME_DIR = PROCESSED_DIR / "time"

MAP_DIR = PROCESSED_DIR / "maps"
EMERGENCY_MAP_DIR = MAP_DIR / "emergency_maps"
DOCTOR_MAP_DIR = MAP_DIR / "doctor_maps"
TIME_MAP_DIR = MAP_DIR / "time_maps"
GEOJSON_PATH = MAP_DIR / "skorea_provinces_geo_simple.json"

# ================================================================
# 필요한 디렉토리 자동 생성
# ================================================================
REQUIRED_DIRS = [
    RAW_DIR,
    PROCESSED_DIR,
    POPULATION_DIR,
    EMERGENCY_DIR,
    DOCTOR_DIR,
    TIME_DIR,
    MAP_DIR,
    EMERGENCY_MAP_DIR,
    DOCTOR_MAP_DIR,
    TIME_MAP_DIR,
]

for d in REQUIRED_DIRS:
    d.mkdir(parents=True, exist_ok=True)