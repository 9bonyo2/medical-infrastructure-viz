# data 폴더 안내

실제 수집/전처리 데이터를 이 폴더 아래에 파트별로 정리해주세요.

```
data/
├── aging/          # 고령화와 노인의료
├── emergency/       # 응급의료 균형
├── birth/            # 출산율과 소아과
└── vulnerability/    # 종합 취약지역 TOP5
```

`utils/sample_data.py` 의 각 `get_*` 함수 내부를
`pd.read_csv("data/aging/xxx.csv")` 형태로 교체하면
UI/차트 코드는 수정 없이 그대로 실데이터로 전환됩니다.
