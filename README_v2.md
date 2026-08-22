# 👵🏥👶 지역별 의료 인프라 격차 현황 분석 웹 대시보드
> **Regional Healthcare Infrastructure Disparity Analysis Dashboard**

2015년부터 2024년까지 약 10개년의 공공데이터를 기반으로 대한민국 시도 단위의 **응급의료**, **고령복지**, **소아의료** 인프라 현황을 다차원 분석하고 격차를 시각화하여, 최우선 인프라 확충이 필요한 의료 취약지 및 정책 지원 대상을 도출하는 의사결정 지원 대시보드 프로젝트입니다.

---

## 📌 Badges
![Python Version](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Build](https://img.shields.io/badge/Build-Passing-brightgreen)
![Data Source](https://img.shields.io/badge/Data%20Source-KOSIS%20%2F%20공공데이터포털-orange)

---

## 1. 프로젝트 소개 & 핵심 가치 (Overview & Key Features)

본 프로젝트는 지역 간 의료 인프라 양극화 문제를 데이터 기반으로 규명합니다. 지자체 보건 정책 담당자와 보건의료 데이터 분석가가 정책 수립 시 직관적이고 과학적인 근거로 활용할 수 있도록 다차원 인터랙티브 시각화를 제공합니다.

### 🌟 핵심 가치 (Core Values)
* **다차원 보건의료 데이터 통합**: 응급의료 접근성, 고령층 요양·복지 자원 수급 균형, 출산율 변화에 따른 소아청소년과 인프라 추이를 하나의 시스템에서 유기적으로 조회합니다.
* **인프라 치우침 지수(Imbalance Index)**: 단순 시설 수 비교를 넘어, Min-Max 정규화를 적용한 상대 비교 지수를 자체 산출하여 어느 지역이 요양병원이나 노인복지시설에 치우쳐 있는지(공급 불균형) 한눈에 진단합니다.
* **공간적 지리 시각화 (Choropleth Map)**: 대한민국 시도 경계 GeoJSON 데이터와 정밀 매핑하여 인프라 분포 및 불균형 정도를 시각적·지리적으로 직관화합니다.
* **연평균 증감률(CAGR) 동적 분석**: 연도 구간을 슬라이더로 조절함에 따라 해당 기간 동안의 인프라 성장/감소/정체 패턴을 실시간 연산하여 트렌드를 분석합니다.

---

## 2. 디렉터리 구조 (Directory Structure)

프로젝트 코드는 데이터 수집/전처리를 담당하는 **Backend Module (`src`)**과 대시보드 화면을 렌더링하는 **Frontend Dashboard (`app`)**가 엄격히 격리·모듈화되어 운영됩니다.

```ascii
medical-infrastructure-viz/
├── .env                                        # 환경 변수 설정 파일
├── .gitignore                                  # Git 제외 파일 목록
├── README.md                                   # 구버전 README
├── README_v2.md                                # 고도화된 메인 README (본 파일)
├── requirements.txt                            # 의존성 패키지 목록
├── 1차프로젝트_3조업무보고서 - 기본 정보.pdf    # 분석 결과 업무 보고서
├── 1. 파이썬활용미니프로젝트 개요.md          # 프로젝트 수행 개요
├── app/                                        # [Frontend] Streamlit 대시보드 소스
│   ├── home.py                                 # 대시보드 메인 홈 화면
│   ├── README.md                               
│   ├── pages/                                  # 상세 분석 서브 페이지 폴더
│   │   ├── 1_응급의료_균형_JH.py                # 응급의료 인프라 분석 (JH 담당)
│   │   ├── 2_응급의료_균형_BY.py                # 응급의료 인프라 고도화 (BY 담당)
│   │   ├── 3_고령화_의료시설_SJ.py              # 고령인구 인프라 기본 (SJ 담당)
│   │   ├── 4_고령화_의료시설_SY.py              # 고령화 복지시설 시계열 (SY 담당)
│   │   ├── 5_고령화_의료시설_JY.py              # [핵심] 고령화 인프라 수급 균형 분석 (JY 담당)
│   │   ├── 6_출산율_소아과_JH.py                # 소아청소년과 인프라 (JH 담당)
│   │   └── 7_출산율_소아과_DY.py                # 출산율 대비 소아과 현황 (DY 담당)
│   └── utils/                                  # 프론트엔드 공통 컴포넌트 및 유틸
│       ├── __init__.py
│       ├── components.py                       # 재사용 가능한 차트, KPI 카드 컴포넌트
│       ├── nav.py                              # 사이드바 네비게이션 모듈
│       ├── sample_data.py                      # 샘플/초기 테스트 데이터셋
│       └── style.py                            # CSS 인젝션 등 공통 스타일 유틸
├── data/                                       # [Data Store] 데이터 레이어
│   └── aging/                                  
│       ├── raw/                                # 1차 원본 공공 데이터 & 경계 GeoJSON
│       │   ├── TL_SCCO_CTPRVN.json             # 대한민국 행정구역 경계 GeoJSON
│       │   ├── aging_population_raw.csv        
│       │   ├── kosis_medical_hospital_raw.csv  
│       │   └── senior_welfare_facilities_raw.csv
│       ├── processed/                          # 2차 정제 및 결측치 처리 완료 데이터
│       │   ├── care_hospitals_processed.csv    
│       │   └── senior_welfare_processed.csv    
│       └── result/                             # 3차 통계/지표 분석 결과 데이터 (백엔드 아웃풋)
│           ├── 1_national_yearly_supply_trend_result.csv
│           ├── 2_regional_yearly_minmax_normalized_result.csv
│           └── 3_regional_10yr_cagr_analysis_result.csv
├── notebooks/                                  # [Research] 탐색적 데이터 분석(EDA) 공간
│   └── aging/
│       └── scatter_correlation.ipynb           # 상관관계 분석 프로토타입 노트북
└── src/                                        # [Backend] 데이터 수집, 가공 및 연산 엔진
    ├── __init__.py
    ├── logs/                                   # 수집/가공 로그 저장소
    └── aging/                                  
        ├── __init__.py
        ├── analysis/                           # 핵심 통계 지표 연산 모듈
        │   ├── __init__.py
        │   ├── correlation.py                  # 상관관계 계수 연산
        │   └── infra_balance.py                # [핵심] 정규화 비율 연산 및 CAGR 파이프라인
        ├── collect/                            # 공공 API 및 크롤링 데이터 수집 모듈
        │   ├── __init__.py
        │   ├── collect_kosis_api.py            
        │   └── collect_senior_facilities.py    
        └── preprocess/                         # 로우 데이터 클렌징 및 시도명 정제 모듈
            ├── __init__.py
            └── preprocess_aging.py             
```

---

## 3. 주요 기능 및 대시보드 화면 안내 (Features)

### 📊 1. 종합 실시간 의사결정 KPI 카드
* **의료/복지 치우침 지역 자동 연산**: 매년 분석 연도 변경에 맞춰, 인프라 치우침(Imbalance Index)이 가장 극단적인 지역을 백엔드 지표에서 연산하여 타 지역 평균 대비 수치(%)와 함께 동적 노출합니다.
* **10개년 장기 CAGR 추이**: 10년간 가장 가파르게 성장한 지역과 감소/정체한 지역을 추적하여 표시합니다.

### 🗺️ 2. 공간 분포 시각화 및 탭별 랭킹 보드
* **의료현황 탭**: 요양병원 공급을 파란색 계열(`Blues`)의 단계구분도로 투영하고 우측에 TOP 3 지역을 표기합니다.
* **복지현황 탭**: 경로당 등 복지 인프라 공급을 주황색 계열(`Oranges`)로 투영합니다.
* **균형현황 탭**: 인프라 불균형이 심할수록 **빨간색/주황색**, 균형 잡힌 상태일수록 **초록색**으로 표현하는 신호등 컬러 맵을 통해 지리적 취약 요소를 즉각 판별할 수 있게 돕습니다.

### 📈 3. 심층 분석 섹션 (독립 카드형 UI)
* **인프라 상대적 비율 비교 (Min-Max 정규화)**: 서로 단위가 다른 두 인프라를 0~1 사이 값으로 정규화하여 나란히 바 차트로 비교 진단합니다.
* **공급 추이 산점도**: 2차원 공간 상에 시도를 버블로 플로팅하여 복지-의료 간의 클러스터 분화 상태를 확인합니다.
* **구간별 CAGR 분석**: 연도 범위 슬라이더를 통해 임의의 특정 시기(예: `2017~2022`) 동안 발생한 시도별 연평균 증감률 변화 패턴을 실시간 연산하여 차트와 상세 수치 테이블로 제공합니다.

---

## 4. 기술 스택 (Tech Stack)

| 구분 | 기술 / 라이브러리 | 사용 목적 |
| :--- | :--- | :--- |
| **언어 (Language)** | `Python 3.12` | 전체 분석 시스템 구축 및 파이프라인 개발 |
| **프레임워크 (Web)** | `Streamlit` | 대시보드 레이아웃, 대화형 UI 설계 |
| **데이터 처리 (Analytics)**| `Pandas`, `NumPy` | 데이터 정제(Data Cleansing), CAGR 및 정규화(Min-Max) 지수 연산 |
| **시각화 (Visualization)** | `Plotly Express`, `Plotly Graph Objects` | 단계구분도 지도(Choropleth), 인터랙티브 차트(산점도, 막대그래프) 설계 |
| **버전 관리 (VC)** | `Git`, `GitHub` | 분업 개발 및 소스코드 버전 이력 관리 |

---

## 5. 시작 가이드 (Quick Start)

로컬 개발 환경에서 대시보드를 빠르고 간편하게 구동할 수 있습니다.

### 1) 가상환경 구성 및 활성화 (Windows 기준)
터미널을 열고 아래 명령어를 순서대로 실행합니다.

```bash
# 가상환경 생성 (.venv)
python -m venv .venv

# 가상환경 활성화 (Powershell 기준)
.venv\Scripts\Activate.ps1
```

### 2) 필수 의존성 패키지 설치
`requirements.txt`에 명시된 필수 외부 모듈들을 일괄 설치합니다.

```bash
pip install -r requirements.txt
```

### 3) 백엔드 데이터 파이프라인 구동 (선택 사항)
만약 `data/aging/result` 디렉토리 내에 분석 파일들이 비어있거나 데이터를 최신화하고 싶다면 아래 백엔드 모듈을 가동합니다. (페이지 실행 시 자동으로 탐색하여 자동 기동되도록 내장되어 있습니다.)

```bash
python -m src.aging.analysis.infra_balance
```

### 4) Streamlit 대시보드 서버 가동
대시보드 메인 서버를 구동하고 웹 브라우저를 엽니다.

```bash
streamlit run app/home.py
```
> 브라우저 창에 자동으로 `http://localhost:8501` 주소로 접속되어 화면이 표출됩니다.

---

## 6. 팀원 역할 분담 (Team Members & Roles)

3조 개발팀은 의료 인프라 현황을 분야별로 세분화하여, 프론트엔드 시각화부터 백엔드 데이터 전처리 파이프라인까지 주도적으로 분업 협업을 완수했습니다.

* **김지현 (JH)**
  * **담당**: 응급의료 인프라 분포 및 출산율 추이 분석
  * **구현**: 인구 10만 명당 응급의료 자원 불균형 지수 시각화 및 상관계수 연산, 소아청소년과 공급 추이 페이지 설계
* **박보영 (BY)**
  * **담당**: 응급의료 분포 및 접근성 정밀 분석
  * **구현**: 응급환자 전원율 및 대도시 쏠림 현상 상관성 분석 대시보드 고도화
* **이성재 (SJ)**
  * **담당**: 고령화 인프라 시계열 원천 분석
  * **구현**: KOSIS 통계 기반 시도별 노인 인프라 시계열 데이터 기초 EDA 및 탐색적 분석 페이지 구축
* **김서연 (SY)**
  * **담당**: 고령화 복지시설 시계열 추이 분석
  * **구현**: 요양시설 공급 추세선 및 상관관계 추이 시각화 차트 구축
* **정지영 (JY)**
  * **담당**: 고령화 노인복지/의료시설 수급 균형 분석 총괄
  * **구현**: Min-Max 정규화 기반 인프라 치우침 지수 연산 모듈화, 공간 분포 단계구분도 지도(Choropleth Map) 매핑, 동적 CAGR 연산 차트 및 UI 리팩토링 개발
* **이도영 (DY)**
  * **담당**: 출산율과 소아과 상관 관계 분석
  * **구현**: 가임인구/출산율 대비 소아청소년과 폐업/신설 추이 산점도 매핑 및 공급 취약도 판별 페이지 구축
