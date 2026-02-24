# CLAUDE.md — BizOPS 산출물 배포 폴더

## 폴더 역할

GitHub Pages 배포 대상 (`tg-bizops.github.io/BizOPS/`)으로, 모든 프로젝트의 HTML 리포트 최종본이 모이는 곳입니다.

- 소스: `toomics-ai-agent/reports/`, `Ai-Chat-bot-project/docs/`
- 이 폴더의 파일은 **배포용 복사본** — 원본 수정은 소스 프로젝트에서 진행
- 직접 편집하는 경우에도 아래 규칙을 따른다

## HTML 리포트 규칙

**상위 `../CLAUDE.md` §HTML 리포트 디자인 시스템**을 따른다.

핵심 요약:
- CSS 변수(`:root` 디자인 토큰) 사용, 하드코딩 색상 금지
- `prefers-color-scheme` 다크모드 자동 대응
- 외부 CDN/JS 금지 (싱글 파일 원칙)
- 기본 폰트 14px, 한국어 `word-break: keep-all`
- `@media print` 인쇄 대응 필수

## 파일 분류

| 접두사 | 유형 | max-width | 소스 프로젝트 |
|--------|------|-----------|--------------|
| `cs_manual_*` | 매뉴얼 | 960px | toomics-ai-agent |
| `cs_weekly_*` | 주간분석 | 1280px | toomics-ai-agent |
| `cs_infographic_*` | 인포그래픽 | 1280px | toomics-ai-agent |
| `cs_flow_*` | 플로우 | 1280px | toomics-ai-agent |
| `chargeback_*` | 차지백 | 960px | toomics-ai-agent |
| `chatbot_*` | 챗봇 문서 | 960px | Ai-Chat-bot-project |
| `ticket_dashboard_*` | 대시보드 | 1280px | toomics-ai-agent |

## 작성자

모든 문서의 작성자: **유종선**
