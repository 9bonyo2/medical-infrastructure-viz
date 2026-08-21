"""수집 모듈 공통 유틸리티 (로깅 설정 등)"""
import logging
import sys
from pathlib import Path

# 프로젝트 루트 기준 경로 (src/aging/collect/common.py -> parents[3] == 프로젝트 루트)
ROOT_DIR = Path(__file__).resolve().parents[3]
RAW_DIR = ROOT_DIR / "data" / "aging" / "raw"
PROCESSED_DIR = ROOT_DIR / "data" / "aging" / "processed"
LOG_DIR = ROOT_DIR / "logs"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


def get_logger(name: str) -> logging.Logger:
    """모듈별 로거 생성. 콘솔 + 파일(logs/collect.log) 동시 출력.

    업무보고서 수집 원칙: 성공/실패, 수집 건수, 수집 시간을 기록한다.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # 중복 핸들러 방지

    logger.setLevel(logging.INFO)
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s", "%Y-%m-%d %H:%M:%S"
    )

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt)
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(LOG_DIR / "collect.log", encoding="utf-8")
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger


# 시도명 표준화 매핑 (약칭/영문 혼용 -> 표준 시도명)
# 여러 원본 데이터(KOSIS, data.go.kr, 행안부)마다 표기가 달라 전처리 단계에서 공통으로 사용한다.
SIDO_STANDARD_MAP = {
    "서울": "서울특별시", "서울특별시": "서울특별시", "서울 Seoul": "서울특별시",
    "부산": "부산광역시", "부산광역시": "부산광역시", "부산 Busan": "부산광역시",
    "대구": "대구광역시", "대구광역시": "대구광역시", "대구 Daegu": "대구광역시",
    "인천": "인천광역시", "인천광역시": "인천광역시", "인천 Incheon": "인천광역시",
    "광주": "광주광역시", "광주광역시": "광주광역시", "광주 Gwangju": "광주광역시",
    "대전": "대전광역시", "대전광역시": "대전광역시", "대전 Daejeon": "대전광역시",
    "울산": "울산광역시", "울산광역시": "울산광역시", "울산 Ulsan": "울산광역시",
    "세종": "세종특별자치시", "세종특별자치시": "세종특별자치시", "세종 Sejong": "세종특별자치시",
    "경기": "경기도", "경기도": "경기도", "경기 Gyeonggi": "경기도",
    "강원": "강원특별자치도", "강원도": "강원특별자치도", "강원특별자치도": "강원특별자치도", "강원 Gangwon": "강원특별자치도",
    "충북": "충청북도", "충청북도": "충청북도", "충북 Chungbuk": "충청북도",
    "충남": "충청남도", "충청남도": "충청남도", "충남 Chungnam": "충청남도",
    "전북": "전북특별자치도", "전라북도": "전북특별자치도", "전북특별자치도": "전북특별자치도", "전북 Jeonbuk": "전북특별자치도",
    "전남": "전라남도", "전라남도": "전라남도", "전남 Jeonnam": "전라남도",
    "경북": "경상북도", "경상북도": "경상북도", "경북 Gyeongbuk": "경상북도",
    "경남": "경상남도", "경상남도": "경상남도", "경남 Gyongnam": "경상남도", "경남 Gyeongnam": "경상남도",
    "제주": "제주특별자치도", "제주도": "제주특별자치도", "제주특별자치도": "제주특별자치도", "제주 Jeju": "제주특별자치도",
}


def standardize_sido(name: str) -> str:
    """다양한 표기의 시도명을 표준 시도명으로 변환한다. 매핑에 없으면 원본 반환."""
    if not isinstance(name, str):
        return name
    key = name.strip()
    return SIDO_STANDARD_MAP.get(key, key)


# 지도(GeoJSON) 표준 -----------------------------------------------------
# southkorea/southkorea-maps 저장소 GeoJSON의 name_eng 값 -> 표준 시도명 매핑
GEOJSON_ENGNAME_TO_STD = {
    "Seoul": "서울특별시",
    "Busan": "부산광역시",
    "Daegu": "대구광역시",
    "Incheon": "인천광역시",
    "Gwangju": "광주광역시",
    "Daejeon": "대전광역시",
    "Ulsan": "울산광역시",
    "Sejongsi": "세종특별자치시",
    "Gyeonggi-do": "경기도",
    "Gangwon-do": "강원특별자치도",
    "Chungcheongbuk-do": "충청북도",
    "Chungcheongnam-do": "충청남도",
    "Jeollabuk-do": "전북특별자치도",
    "Jeollanam-do": "전라남도",
    "Gyeongsangbuk-do": "경상북도",
    "Gyeongsangnam-do": "경상남도",
    "Jeju-do": "제주특별자치도",
}

GEOJSON_PATH = RAW_DIR / "skorea_sido_boundary.geojson"


def load_korea_geojson() -> dict:
    """시도 경계 GeoJSON을 불러와 각 feature.properties에 표준 시도명(sido)을 추가해 반환.

    출처: https://github.com/southkorea/southkorea-maps (통계청 2013년 시도 경계 간략화본)
    """
    import json

    with open(GEOJSON_PATH, encoding="utf-8") as f:
        geo = json.load(f)

    for feature in geo["features"]:
        eng = feature["properties"].get("name_eng")
        feature["properties"]["sido"] = GEOJSON_ENGNAME_TO_STD.get(eng, eng)

    return geo
