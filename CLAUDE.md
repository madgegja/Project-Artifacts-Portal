# CLAUDE.md — BizOps Global Platform Operations

## 프로젝트 개요
- 소속: Toomics Global / 글로벌 플랫폼 운영팀 (BizOps)
- 담당: 결제(PG), 고객지원(CS), 저작권 보호(IP) — 10개 언어 마켓
- 팀: 유종선(팀장), 김지호, 이동원, 박선주, 왕시베이
- 주요 도구: Zendesk, Confluence, Slack, Google Sheets, GitHub

---

## 핵심 행동 규칙

### 1. 진단 먼저, 수정은 승인 후
- 모든 작업은 읽기 → 진단 → 보고 → (승인) → 수정 순서를 따른다
- "수정해", "실행해", "업데이트해"라는 명시적 지시가 없으면 분석/보고까지만 한다
- 진단서 없는 수정은 없다

### 2. 최소 변경 원칙
- 가장 작은 범위의 변경으로 목표를 달성한다
- 인접 코드나 문서를 김에 리팩터링하지 않는다
- 기존 패턴과 컨벤션을 따른다

### 3. 검증 없이 완료 없다
- "될 것 같다"는 완료가 아니다
- 테스트, 빌드, 린트, 또는 수동 확인 중 하나 이상의 증거가 있어야 한다
- 검증을 못 했으면 왜 못 했는지 + 어떻게 검증할 수 있는지 명시한다

### 4. 불확실하면 말한다
- 확인할 수 없는 것은 추측하지 않고 "확인 필요"라고 표시한다
- 질문할 때는 1개만, 추천 기본값과 함께

---

## 작업 흐름

### Plan Mode (기본값)
3단계 이상, 멀티파일 변경, 아키텍처 결정이 있으면 반드시 계획부터:
1. 목표 + 완료 조건 정리
2. 기존 구현/패턴 파악
3. 최소 접근법 설계
4. 가장 작은 단위로 구현
5. 테스트/검증
6. 변경 요약 + 검증 결과 보고

### 점진적 실행
- 한 번에 다 하지 않는다. 작은 단위로: 구현 → 테스트 → 확인 → 확장
- 위험한 변경은 롤백 가능한 형태로

### 자기 교정
- 실수하거나 사용자 교정을 받으면 tasks/lessons.md에 기록
- 세션 시작 시 tasks/lessons.md 확인

---

## 데이터 소스 및 외부 연동

### Confluence
- Cloud ID: 545a7a53-51cd-4bd5-82cd-b47956669400
- 주요 스페이스: 프로덕트실 (Tlos64YMyGN2, spaceId: 559392)
- API Base: https://toomics.atlassian.net/wiki
- 페이지 수정 시 반드시 사전 승인 필요

### Zendesk
- CS 티켓 분석, 주간/월간 리포트 자동화
- 10개 언어: EN, FR, ES, DE, PT, JP, CN, IT, TH, KR
- 7개 카테고리, 8개 PG사

### GitHub
- 리포지토리: bizops-weekly-report (private)
- 구조: scripts/, Weekly CS log/, history/, reports/charts/
- **BizOPS 리포**: `git@github-bizops:TG-BizOps/BizOPS.git` (branch: main)
- **toomics-ai-agent 리포**: `github-personal:madgegja/toomics-ai-agent.git` (branch: main)

### HTML 파일 자동 커밋 & 푸시 규칙
HTML 리포트 파일(`.html`)을 생성·수정·삭제한 작업이 완료되면, 별도 지시 없이 자동으로:
1. 해당 리포지토리에서 변경된 `.html` 파일을 `git add`
2. 변경 내용을 요약한 커밋 메시지 작성 (영어)
3. `git push origin main` 실행
4. push 결과를 한 줄로 보고

적용 대상 디렉토리:
- `/root/Claude/BizOPS/` → `TG-BizOps/BizOPS` 리포
- `/root/Claude/toomics-ai-agent/` → `madgegja/toomics-ai-agent` 리포

예외: 사용자가 "푸시하지 마", "커밋만" 등 명시적으로 제외 지시한 경우

### BizOPS 인덱스 자동 동기화 규칙
`/root/Claude/toomics-ai-agent/`에서 HTML 리포트를 생성·수정·삭제한 경우, toomics-ai-agent 커밋·푸시 후 추가로:
1. 해당 HTML 파일을 `/root/Claude/BizOPS/`로 복사 (파일명 유지, 플랫하게)
2. `cd /root/Claude/BizOPS && python3 scripts/generate_index.py` 실행하여 인덱스 재생성
3. 변경된 HTML + index.html을 커밋·푸시 (`TG-BizOps/BizOPS` 리포)
4. 신규 파일의 prefix가 `generate_index.py`의 PREFIX_RULES에 없으면 규칙 추가 후 재생성

### Google Sheets
- 차지백 데이터, CS 처리 현황 시트

---

## 커뮤니케이션 규칙

### 간결하고 핵심만
- 결과와 영향부터 말한다. 과정 나열 금지
- 구체적 근거: 파일 경로, 명령어, 에러 메시지, 변경 내역
- 큰 로그 덤프 대신 요약 + 원본 위치 안내

### 보고 타이밍
- 매 단계가 아니라 이럴 때만: 범위 변경, 리스크 발견, 검증 실패, 의사결정 필요

### 언어
- 설명과 보고는 한국어
- 코드, 변수명, 커밋 메시지, 파일명은 영어

---

## 에러 대응

### Stop-the-Line 규칙
예상치 못한 일이 생기면:
1. 기능 추가 중단
2. 증거 보존
3. 진단으로 돌아가서 재계획

### 버그 수정 순서
재현 → 근본 원인 격리 → 수정 → 회귀 테스트 → 검증

### 안전 폴백
- 불완전한 동작보다 안전한 기본값 + 경고
- 조용한 실패 금지
- 프로덕션 영향 불확실하면 비활성 상태로 배포

---

## HTML 리포트 디자인 시스템

모든 하위 프로젝트(toomics-ai-agent, Ai-Chat-bot-project 등)에서 HTML 리포트 생성 시 이 규칙을 따른다.

### 기본 원칙
- **싱글 파일**: 외부 CSS/JS/CDN 없이 `<style>` 태그에 모든 스타일 포함
- **차트**: CSS-only 바차트 사용 (Chart.js 등 외부 라이브러리 금지)
- **다크모드**: `prefers-color-scheme`으로 라이트/다크 자동 대응
- **인쇄**: `@media print` + `-webkit-print-color-adjust: exact` 포함
- **한국어**: `word-break: keep-all; overflow-wrap: break-word` 필수

### 디자인 토큰

모든 리포트는 `:root`에 아래 CSS 변수를 선언하고, 하드코딩 색상 대신 변수를 사용한다:

```css
:root {
  /* 레이아웃 */
  --max-w: 960px;
  --max-w-wide: 1280px;
  --radius: 12px;
  --gap: 16px;

  /* 색상 — 라이트 */
  --bg-base: #F8FAFC;
  --bg-card: #FFFFFF;
  --bg-muted: #F1F5F9;
  --text-primary: #1E293B;
  --text-secondary: #475569;
  --text-muted: #94A3B8;
  --border: #E2E8F0;
  --accent-brand: #2563EB;
  --accent-info: #0EA5E9;
  --accent-success: #10B981;
  --accent-warn: #F59E0B;
  --accent-danger: #EF4444;
  --accent-purple: #7C3AED;

  /* 타이포 */
  --font-base: 14px;
  --font-sm: 12px;
  --font-lg: 18px;
  --font-xl: 28px;
  --line-height: 1.7;
  --font-family: 'Malgun Gothic','Apple SD Gothic Neo','Noto Sans KR',-apple-system,sans-serif;
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg-base: #0F172A;
    --bg-card: #1E293B;
    --bg-muted: #334155;
    --text-primary: #F1F5F9;
    --text-secondary: #CBD5E1;
    --text-muted: #64748B;
    --border: #334155;
  }
}
```

### 문서 유형별 레이아웃

| 유형 | max-width | 용도 |
|------|-----------|------|
| 매뉴얼/가이드 | `var(--max-w)` 960px | 읽기 중심 문서 |
| 대시보드/인포그래픽 | `var(--max-w-wide)` 1280px | 데이터 시각화 |
| 원페이저/요약 | `var(--max-w)` 960px | 보고용 |

### Hero 헤더

- 기본 그라디언트: `linear-gradient(135deg, #1E3A5F 0%, #2563EB 50%, #0EA5E9 100%)`
- 차지백/위험 문서만 `--accent-danger` 포인트 허용
- 필수 요소: 뱃지(문서유형) + 제목 + 부제 + 메타(작성자/날짜/버전)

### 공통 컴포넌트

| 컴포넌트 | 규칙 |
|----------|------|
| **KPI 카드** | 상단 3px 컬러보더 + 큰 숫자(`var(--font-xl)`) + 라벨 |
| **테이블** | `border-collapse:separate` + 헤더 둥근모서리 + hover 배경 |
| **뱃지** | `padding:2px 8px` + `border-radius:6px` + 의미별 색상 |
| **카드** | `border-radius:var(--radius)` + 좌측 4px 컬러보더 |
| **알림** | info/warn/danger/success 4종 |
| **숫자** | `font-variant-numeric: tabular-nums` (열 정렬) |

### 도넛 차트 레이아웃 (필수 패턴)

파이/도넛 차트가 필요한 경우 반드시 **좌측 도넛 + 우측 테이블** 가로 배치 구조를 사용한다.
차트 아래 범례(legend) 나열 금지.

```
┌──────────────────────────────────────────┐
│  섹션 제목                                │
├─────────────────┬────────────────────────┤
│   도넛 차트      │  테이블 (범례 역할)     │
│   (canvas)      │  컬러닷 + 항목명       │
│   max-w: 360px  │  비중(%) | 건수 | 설명  │
│   중앙 정렬      │  hover 배경 효과       │
└─────────────────┴────────────────────────┘
```

**CSS 구조:**
```css
/* 레이아웃: grid 2열, 반응형 1열 전환 */
.category-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}
@media (max-width: 900px) {
  .category-layout { grid-template-columns: 1fr; }
}

/* 차트 컨테이너 */
.chart-container {
  position: relative;
  width: 100%;
  max-width: 360px;
  margin: 0 auto;
}

/* 테이블 */
.category-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.category-table th {
  text-align: left; padding: 10px 12px;
  border-bottom: 2px solid var(--border);
  color: var(--text-muted); font-weight: 600;
  font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;
}
.category-table td { padding: 10px 12px; border-bottom: 1px solid var(--border); }
.category-table tr:hover td { background: var(--bg-muted); }

/* 컬러 닷 (차트 색상과 매칭) */
.cat-dot {
  display: inline-block; width: 10px; height: 10px;
  border-radius: 50%; margin-right: 8px; vertical-align: middle;
}

/* 처리방식 배지 */
.cat-badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 12px; font-weight: 600; }
.cat-badge.auto    { background: rgba(5,150,105,0.12);  color: #047857; }
.cat-badge.partial { background: rgba(180,83,9,0.10);   color: #b45309; }
.cat-badge.manual  { background: rgba(185,28,28,0.10);  color: #b91c1c; }
```

**Chart.js 사용 시:** `plugins: { legend: { display: false } }` — 내장 범례 반드시 비활성화
**테이블 필수 컬럼:** 항목명 (cat-dot 포함) | 비중(%) | 건수 | 처리방식 또는 핵심 설명

---

## 코드 품질
- 영리함보다 명확함. 읽기 쉬운 코드가 좋은 코드
- 새 라이브러리는 기존 스택으로 해결 불가할 때만
- 코드/로그/대화에 시크릿 노출 금지
- 커밋은 원자적으로. 포맷팅과 동작 변경 분리

---

## 완료 기준
- [ ] 동작이 완료 조건과 일치
- [ ] 테스트/린트/빌드 통과
- [ ] 위험한 변경에 롤백 전략 있음
- [ ] 기존 컨벤션 준수
- [ ] 검증 요약: "뭘 바꿨고 + 어떻게 확인했다"
