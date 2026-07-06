# geo-wiki 이식 패턴 (설계만)

> HANDOVER §1(자산 재사용 맵) 기준. geo-wiki는 **패턴 공급원**으로 강등됨 — 코드 복붙이
> 아니라 아래 3개 설계를 Neon + Drizzle + Claude 스택으로 **재구현**한다.
> Supabase / Railway / GitHub Models 결합부는 전량 폐기.
>
> 원본 참조: `~/github/Obsidian/geo-wiki` (scripts/, app/api/chat/route.ts, KNOWLEDGE_MODEL.md)

---

## 1. Ingest 단계 구조

### geo-wiki 원본 흐름
```
raw/geo-archive/*.md, incoming/files/*, URL, PDF
   ↓  incoming/manifest.yaml (무엇을 ingest할지 선언)
   ↓  scripts/ingest_manifest.py   (openkb add 래핑, content-hash 기반 skip)
kb/wiki/sources/  ·  summaries/  ·  concepts/     (사람이 검토 가능한 md 원본)
   ↓  scripts/summarize_sources.py (LLM 요약 생성)
   ↓  scripts/embed_knowledge.py   (concept/page/summary 임베딩)
   ↓  scripts/export_openkb_index.py
public/data/*.json  ·  markdown/*.md            (앱이 소비하는 정적 export)
   ↓  Next.js UI
```

핵심 관찰:
- **선언적 manifest → 처리 → 검토 가능한 중간 산출물 → export** 의 단방향 파이프라인
- 각 단계가 독립 스크립트(argparse, `--dry-run`/`--force`/`--file` 옵션) → 재실행·부분실행 용이
- **content hash 로 재처리 skip** (`kb/.openkb/hashes.json`) — LLM 비용 가드
- 중간 산출물이 md 파일이라 사람이 git diff 로 검토 가능

### research-wiki 재구현 방침 (HANDOVER §2)
- 중간 산출물을 **md 파일이 아니라 Neon 테이블**로: `raw_sources → sources → summaries → knowledge_items → knowledge_embeddings` 5단.
- `incoming/manifest.yaml` 역할을 **`ingestion/sources.yaml` + `router.py`** 가 대체 (tier 라우팅).
- content-hash skip 패턴은 **유지** → `ingestion/dedupe.py` (URL 정규화 + SHA256, 동일 hash skip). Hard Rule "LLM 파싱은 content hash 변경 시에만".
- 단계별 독립 스크립트 + `--dry-run` 관례 **유지**.
- 실행처는 로컬이 아니라 **GitHub Actions** (D7). Neon 접근은 Python raw SQL(psycopg), 스키마 진실은 Drizzle.
- geo-wiki의 GitHub Models(gpt-4o-mini) 요약 → **Claude Sonnet 한국어 6섹션**으로 교체.

---

## 2. RSS 발굴 + 스코어링 + 승인 워크플로우

### geo-wiki 원본 (`scripts/discover_sources.py`)
1. **RSS 피드 목록 하드코딩** (Search Engine Journal, Moz, Ahrefs 등) — 표준 라이브러리만으로 RSS 2.0 + Atom 파싱.
2. **키워드 1차 필터** — 제목/설명에 도메인 키워드(정규식) 매칭되는 항목만 통과 → LLM 호출 절감.
3. 기존 소스 URL/title 조회로 **중복 제거** (Supabase → JSON 폴백).
4. **LLM 품질 스코어링** — 통과 후보를 LLM으로 평가, `SCORE_THRESHOLD = 6.0` 이상만 후보 채택.
5. 결과를 `source_candidates` 테이블(또는 JSON 폴백)에 적재 → 사람이 승인.

핵심 관찰:
- **키워드 프리필터 → LLM 스코어 → 후보 큐 → 사람 승인** 의 깔때기.
- 모든 외부 저장(Supabase)에 **JSON 파일 폴백** 이 있어 로컬/CI 어디서든 동작.

### research-wiki 재구현 방침
- 피드 목록을 하드코딩이 아니라 **`sources.yaml` 의 sector_tags 기반**으로 확장 가능하게.
- 키워드 프리필터 **유지**하되 섹터 키워드(power_equipment, ai_semis)로 교체.
- **스코어링 모델을 Haiku로 교체** (HANDOVER: "스코어링 모델을 Haiku로") — 단, 이 발굴 스코어링은
  §2.5 품질 게이트(수집된 문서 판정)와는 **별개 층**. 발굴은 "소스를 등록할지", 게이트는 "수집분을 승격할지".
- `SCORE_THRESHOLD=6.0` 단일 임계치 방식은 **품질 게이트에는 쓰지 말 것** — §2.5가 명시적으로 폐기한 실패 패턴.
  (발굴 후보 1차 선별에는 단순 임계치 허용, 최종 등록은 사람/§8 R3 루틴 승인)
- 승인 UI: geo-wiki `source-review` API 패턴 → research-wiki `/review` + Drizzle.
- **§8 R3 주간 소스 발굴 루틴**이 이 워크플로우의 자동화 주체 (금요일 18:00, PR 제안까지만).

---

## 3. /api/chat RAG 패턴

### geo-wiki 원본 (`app/api/chat/route.ts`, `runtime = "nodejs"`)
1. **모듈 레벨 사전 로드** — concept summary 맵을 `public/data/knowledge-index.json`에서 1회 로드.
2. **인증** — 요청 유저 확인, 없으면 401.
3. **세션 관리** — sessionId 없으면 chat_sessions insert, 유저 메시지 저장.
4. **쿼리 재작성** (`rewriteQueryForSearch`) — 약어·구어체를 검색 최적화 문장으로 LLM 1발 변환(temperature 0, 실패 시 원본).
5. **컨텍스트 빌드** (`buildContext`):
   - 1순위: 쿼리 임베딩 → `supabase.rpc("match_knowledge", { threshold: 0.32, count: 10 })` 벡터 검색.
   - 유사도 최상위 concept(≥0.36)를 primaryConcept로 승격, 나머지는 소스 칩.
   - 컨텍스트 텍스트 = `[type] title\ncontent` 를 `---` 로 결합.
   - 2순위(폴백): 임베딩 실패 시 **FTS**(`textSearch`) 폴백.
6. **대화 히스토리** 최근 20개 조회 → 시스템 프롬프트에 `[지식 베이스]` 컨텍스트 주입.
7. **SSE 스트리밍** — LLM `stream:true` 응답을 ReadableStream으로 파싱, 완료 후 assistant 메시지 DB 저장.
8. sources / primaryConcept 를 응답 헤더(`X-Sources`, `X-Primary-Concept`)로 전달.

핵심 관찰:
- **벡터 검색 → FTS 폴백** 2단 안정성.
- **쿼리 재작성**으로 구어체 질의 recall 향상.
- 스트리밍 파싱 시 버퍼 경계 처리(`lines.pop()`), 완료 시 저장 — 견고한 SSE 처리.

### research-wiki 재구현 방침 (Phase 4)
- `supabase.rpc("match_knowledge")` → **Neon pgvector 검색 + Drizzle** 로 재작성.
- 인증: Supabase auth → **Auth.js v5 (auth.ts, 본인 전용)**.
- chat_sessions/chat_messages: Supabase 테이블 → **Drizzle 스키마**로 재정의(homestyle에 chat_sessions 존재).
- **시점 인지 추가 (핵심 차별점, HANDOVER §Phase 4)**:
  - pgvector 유사도 × **시점 가중**(published_at 지수 감쇠, 반감기 180일). '과거 뷰 조회' 모드는 감쇠 off.
  - 비교형 질의("하우스별", "누가 맞았", "뷰 변화") 감지 시 **claims 구조화 조회(Drizzle)** 를 컨텍스트에 추가 주입.
  - 답변 프롬프트: 시점 명시 강제("GS는 2026-01 기준 ~로 전망"), 현재형 단정 금지.
- 생성 모델: GitHub Models gpt-4o-mini → **Claude Sonnet**. 임베딩은 OpenAI 3-small 유지(D1).
- 쿼리 재작성·SSE 스트리밍·FTS 폴백 패턴은 **유지**.

---

## 이식 시 폐기 목록 (혼입 금지)
- Supabase 클라이언트(`lib/supabase/*`), `match_knowledge` RPC, RLS 전제
- Railway 배포(`railway.toml`), GitHub Models 엔드포인트/`GITHUB_TOKEN` 인증
- openkb CLI 의존(`ingest_manifest.py`의 `openkb add`)
- GEO 도메인 콘텐츠(kb/wiki concepts, knowledge-graph.json) 및 GEO 특화 키워드
