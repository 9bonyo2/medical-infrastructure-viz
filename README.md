# 고령화 파트 — 지역별 고령인구 · 노인복지센터 분석

> 3조 "지역별 의료 인프라 격차 분석" 프로젝트 중 **고령화 파트** (담당: 정성재·홍서연·황지영) 산출물입니다.
> 팀 공통 목표인 "고령화율 vs 병상수 상관관계"에 더해, 고령화 파트 자체 지표로
> **지역별 고령인구비율 vs 노인복지센터(노인복지관) 수 상관관계**를 분석합니다.

## 1. 데이터 출처

| 데이터 | 출처 | 수집 방법 | 기간 |
|---|---|---|---|
| 시도별 노인복지시설 현황 (노인복지관/경로당 등, 시설유형별 상세) | [공공데이터포털 - 보건복지부_노인복지 이용시설 현황](https://www.data.go.kr/data/15127876/fileData.do) | 원본 첨부 CSV 직접 다운로드 (`requests`) | 2015~2024 |
| 시도별 고령인구(65세 이상)·고령인구비율 | [행정안전부 주민등록인구통계](https://jumin.mois.go.kr/ageStatMonth.do) | 5세 단위 연령구간 조회 결과 HTML을 `requests` + `BeautifulSoup`으로 파싱 | 2024-12 스냅샷 |
| **[검증완료]** KOSIS 공식 고령인구비율 (`DT_1YL20631`) | [KOSIS 국가통계포털](https://kosis.kr) Open API | `KOSIS_API_KEY` 발급 후 `collect_kosis_api.py` 실행 | 연도별(2024 기본) |
| **[검증완료]** KOSIS 노인천명당 노인여가복지시설수 (`DT_1YL20961`) | KOSIS 국가통계포털 Open API | 상동 | 연도별(2024 기본) |

**KOSIS 접근 관련**: KOSIS 웹 통계표(`statHtml.do`)는 SSO 로그인 세션이 필요해 정적 스크래핑이
불가능합니다(비로그인 요청 시 302 로그인 리다이렉트 발생 확인). 대신 **KOSIS Open API**(인증키 발급 후 사용)로
공식 지표에 접근했고, 실제 인증키로 호출해 다음 두 테이블을 확보·검증했습니다.

**교차검증 결과**: `collect_aging_population.py`(행안부 웹 스크래핑)로 얻은 2024년 시도별
65세이상인구·전체인구·고령인구비율 수치가 KOSIS 공식 API(`DT_1YL20631`) 응답과 **완전히 일치**함을 확인했습니다
(예: 서울 65세이상인구 1,813,648명 / 전체인구 9,331,828명 / 고령인구비율 19.4% — 두 출처 동일).
즉 두 데이터가 궁극적으로 같은 원천(행정안전부 주민등록인구현황)을 가리키고 있어, 스크래핑 파이프라인의
정확성이 KOSIS 공식 API로 입증된 상태입니다.

`DT_117N_B00003`(보건복지부 노인복지시설현황, 시설유형별)은 Open API에서 시도 축(objL2) 조회 파라미터를
찾지 못해(`err:21` 응답) 이 경로로는 재수집하지 않았습니다 — 대신 `collect_senior_facilities.py`가
data.go.kr 원본 파일로 이미 더 상세한(시설유형별) 버전을 확보하고 있습니다.

## 2. 폴더 구조

```
src/collect/
  common.py                     # 로깅, 시도명 표준화, GeoJSON 로더 공통 유틸
  collect_senior_facilities.py  # 노인복지시설 현황 수집 (data.go.kr CSV)
  collect_aging_population.py   # 고령인구 웹 스크래핑 (BeautifulSoup)
  collect_kosis_api.py          # KOSIS Open API 보조 수집 (API 키 필요)
src/preprocess/
  preprocess_aging.py           # 시도명 표준화·결측치 처리·병합 -> 마스터 테이블 생성
src/analysis/
  correlation.py                # Pearson/Spearman 상관분석
app/
  streamlit_app.py              # Streamlit 대시보드 (지도/상관관계/추이/데이터)
data/raw/                       # 원본 수집 데이터 (+ 시도 경계 GeoJSON)
data/processed/                 # 전처리 결과물 (분석/시각화 입력)
```

## 3. 실행 방법

```bash
pip install -r requirements.txt

# 1) 데이터 수집
python -m src.collect.collect_senior_facilities
python -m src.collect.collect_aging_population --year 2024 --month 12
# KOSIS 공식 지표 교차검증용 수집 - 사전에 KOSIS_API_KEY 환경변수 설정 필요
python -m src.collect.collect_kosis_api --year 2024

# 2) 전처리 (시도명 표준화 + 병합 + 파생지표 생성)
python -m src.preprocess.preprocess_aging

# 3) 상관관계 분석 (콘솔 로그 + data/processed/correlation_result.csv)
python -m src.analysis.correlation

# 4) Streamlit 대시보드 실행
streamlit run app/streamlit_app.py
```

## 4. 전처리 원칙

- **시도명 표준화**: "서울 Seoul", "경남 Gyongnam" 등 원본별 표기를 표준 시도명으로 통일 (`common.SIDO_STANDARD_MAP`)
- **연도 통일**: 노인복지시설 데이터 최신연도(2024)에 맞춰 인구 데이터도 2024-12 스냅샷으로 수집
  (2025~2026년 사이 일부 시도 통합 등 행정구역 변경이 있어 동일 시점 기준 비교가 필요함)
- **결측치 처리**: 시설 수 결측은 "시설 없음(0)"으로 대체, 시도 자체가 누락된 경우는 제외 후 로그 경고
- **중복 제거**: (시도 + 연도) 조합 기준
- **규모 보정 지표**: 인구 10만명당 노인복지관 수, 고령인구 1만명당 노인복지관 수를 파생 지표로 추가
  (절대량 비교는 인구 규모가 큰 지역에 유리하게 왜곡되므로 규모 보정 지표를 함께 봐야 함)

## 5. 핵심 분석 결과 (2024년 기준, 예시)

- 고령인구비율 vs 노인복지관 수(절대량): 상관관계 약함 (r ≈ 0.10, 유의하지 않음) — 인구 규모 효과로 왜곡
- **고령인구비율 vs 인구 10만명당 노인복지관 수: r ≈ 0.68 (p < 0.01), 통계적으로 유의한 중간 강도 양의 상관관계**
- 고령인구 수(절대량) vs 노인복지관 수(절대량): r ≈ 0.93 — 둘 다 인구 규모에 비례하는 공통 요인(인구 규모)의 영향

> 실제 수치는 실행 시점 데이터로 재계산되며, 최신 실행 결과는 `data/processed/correlation_result.csv` 참고.

## 6. Streamlit 대시보드 구성

1. **지역 지도**: 시도별 고령인구비율/노인복지관 수 등을 한국 지도(Choropleth)에 표시 + 순위 막대그래프
2. **상관관계 분석**: 지표 쌍 선택 → 산점도 + 추세선 + Pearson r/p-value
3. **연도별 추이**: 2015~2024 노인복지관 수 추이 (시도 다중 선택 비교)
4. **데이터**: 마스터 테이블 및 시계열 원자료 조회/다운로드

## 7. 남은 작업 / 팀 공유 필요 사항

- [ ] 공통 파트(병상 수) 데이터와 조인하여 "고령화율 vs 병상수" 팀 공통 목표 분석에 연결
- [x] KOSIS Open API 키 발급 및 `collect_kosis_api.py` 실제 검증 완료 (2024년 기준 스크래핑 데이터와 완전 일치)
- [ ] GitHub 레포에 push 및 팀 업무보고서 산출물 링크 업데이트
- [ ] `KOSIS_API_KEY`는 절대 코드/커밋에 포함하지 말 것 — 팀원 각자 개인 환경변수로 설정
      (`.gitignore`에 `.claude/`, `.env` 등록되어 있으니 로컬 설정 파일이 실수로 올라가지 않는지 `git status`로 확인)
