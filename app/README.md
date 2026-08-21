# 지역 의료 인프라 균형 대시보드 — 베이스라인

디자인 시안(메인 대시보드 + 파트별 상세 페이지)을 그대로 반영한 Streamlit 멀티페이지 앱 뼈대입니다.
지금은 전부 예시(더미) 데이터로 채워져 있으니, 팀원들이 각자 파트 데이터를 붙이면서 고도화하면 됩니다.

## 폴더 구조

```
medical-infra-dashboard/
├── app.py                             # 메인 대시보드 (첫 화면)
├── pages/
│   ├── 1_응급의료_균형_분석.py
│   ├── 2_고령화와_노인의료_분석.py       # 상세 페이지 레이아웃 기준 템플릿
│   ├── 3_출산율과_소아과_분석.py
│   └── 4_의료_취약지역_TOP5.py
├── utils/
│   ├── style.py         # 공통 CSS (색상/카드 스타일은 여기서만 수정)
│   ├── nav.py            # 사이드바 메뉴 (새 페이지 추가 시 PAGES 리스트만 수정)
│   ├── components.py    # 재사용 UI 컴포넌트 (KPI 카드, 버블맵, 랭킹리스트 등)
│   └── sample_data.py   # 예시 데이터 → 실데이터로 교체할 지점
├── data/                  # 파트별 원본/가공 데이터 (README 참고)
└── requirements.txt
```

## 실행 방법

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 실데이터로 교체하는 방법 (팀원 공통 작업 순서)

1. `data/<파트명>/` 폴더에 본인 파트 원본·가공 CSV를 넣습니다.
2. `utils/sample_data.py` 에서 본인 파트가 쓰는 `get_*` 함수 내부를
   `pd.read_csv(...)` 기반 실데이터 로딩으로 교체합니다. (함수 시그니처·반환 컬럼명은 유지)
3. 필요하면 `utils/components.py` 에 새 차트 컴포넌트를 추가합니다 (다른 페이지에서도 재사용 가능).
4. `pages/*.py` 는 레이아웃 골격만 있는 상태이므로, 본인 파트에 맞게 문구/차트를 자유롭게 채워주세요.

## 지도(버블맵) 관련

`utils/components.py` 의 `region_bubble_chart()` 는 지금 임의 좌표 기반 산점도로
디자인 시안의 버블맵을 흉내낸 상태입니다. 팀에서 논의한 지도 라이브러리
(folium / pydeck / plotly choropleth + GeoJSON 등)로 이 함수 내부만 교체하면,
이 함수를 호출하는 모든 페이지(홈, 각 상세 페이지)에 자동으로 반영됩니다.

## 브랜치 / 커밋 컨벤션 (참고)

- 브랜치: `feature/<파트명>-<작업내용>` (예: `feature/aging-panel-data`)
- 커밋: `feat:`, `fix:`, `refactor:`, `chore:` 등 Conventional Commits 스타일 권장
