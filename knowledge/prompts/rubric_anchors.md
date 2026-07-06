# Gate 2 — 루브릭 앵커 예시

> 이 파일은 R2 루틴이 실제 반려 사례로 교체한다. 하드코딩 금지.
> Sonnet 루브릭 프롬프트에 그대로 삽입된다 — 포맷 변경 주의.

## 합격 앵커

### [PASS-1] IMF WEO 섹터별 성장 전망 (권위 기관, 수치 밀도 높음)
- relevance: 5 — 전력기기·AI 반도체 수요에 직결되는 글로벌 투자 전망
- density: 4 — 국가·섹터별 구체 수치 다수, 시나리오 분기 포함
- authority: 5 — IMF 공식 발행물, 저자 명기
- novelty: 4 — 직전 WEO 대비 전망치 업데이트, 신규 리스크 항목 추가

### [PASS-2] Goldman Sachs AI 인프라 capex 전망 보고서
- relevance: 5 — AI 반도체·데이터센터 직접 섹터
- density: 5 — 기업별 capex, CAGR, 점유율 수치 빽빽함
- authority: 4 — 글로벌 IB 리서치, 애널리스트 명기
- novelty: 4 — 신규 전망치, 기존 시장 컨센서스 대비 상향 이유 제시

## 불합격 앵커

### [FAIL-1] 기업 IR 보도자료 — 신제품 출시 공지
- relevance: 2 — 섹터 관련 기업이나 분석 없는 홍보 문구
- density: 1 — 구체 수치 없음, '업계 선도' 등 수사만
- authority: 2 — 기업 자체 발행, 이해관계 충돌
- novelty: 1 — 분석 없음, 신규 인사이트 없음

### [FAIL-2] 금융 포털 요약 기사 — 원출처 재인용
- relevance: 3 — 섹터 관련 내용 있으나 애그리게이터
- density: 2 — 수치는 원출처 재인용만, 고유 분석 없음
- authority: 1 — 금융 포털, 저자 미명기
- novelty: 1 — 기존 시장 보도 재패키징
