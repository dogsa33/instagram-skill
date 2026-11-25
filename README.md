# Instagram Skill — Codex · Claude Code · Cursor · OpenClaw용 인스타그램 자동화

> [원본 Instagram Skill](https://github.com/social-media-skills/instagram-skill)을 Fork한 **한국어 + Seedance 영상 생성 확장판**입니다. 원본의 이미지·캐러셀·릴스·스토리 제작, 검수, 미리보기, 예약 게시 기능은 유지하면서 선택적으로 AI 영상을 생성하고 한국어 자막을 합성할 수 있게 했습니다.
>
> **개발 상태:** `feature/seedance-ko-reels` 브랜치 · 선택적 Seedance 확장 · 오프라인 테스트 10개 통과. **실제 Seedance 유료 API 호출과 Instagram 게시 통합 테스트는 아직 완료되지 않았습니다.**

**Instagram Skill**은 Claude Code, Codex, Cursor, OpenClaw 같은 AI 에이전트가 인스타그램 게시물을 **기획 → 제작 → 검수 → 미리보기 → 사용자 승인 → 게시·예약**하도록 돕는 오픈소스 Skill입니다. 한 계정 또는 여러 계정의 캐러셀, 단일 이미지, 릴스, 스토리를 지원합니다.

기존 기능:

- **캐러셀·단일 이미지:** 1080×1350 JPEG 제작, 프로필 그리드 3:4 잘림 영역 고려
- **실제 사진·스크린샷:** PNG, HEIC, 3:4 이미지, 파노라마 등의 규격 변환
- **실제 영상 릴스:** 9:16·H.264·AAC 검수, 가로 영상 프레이밍, 표지 추출 및 화면 UI 가림 영역 확인
- **스토리:** 예약된 게시물 전에 예고 스토리 배치
- **자동 검수:** 인스타그램 규격에 맞지 않는 미디어·캡션 검사 및 수정본 생성
- **미리보기:** 피드·그리드·슬라이드의 실제 표시 형태 확인
- **다중 계정:** 계정별 콘텐츠·캡션·시간대·일정 관리
- **성과 확인:** 게시 성과를 같은 계정의 유사한 게시물과 비교

이 Fork에서 추가된 기능:

- **Seedance 영상 생성:** Higgsfield CLI를 통해 사진과 프롬프트로 AI 영상 생성
- **한국어 영상 편집:** 여러 영상 결합, 시간대별 한글 자막, 실제 제품 사진 엔딩 카드
- **한글 글꼴 지원:** 환경 변수를 설정하면 한국어 글꼴로 렌더링
- **중복 생성 방지:** 작업 ID 저장과 중단된 생성 작업 재개(`--resume`)

**비용 구분:** 기본 캐러셀·이미지·기존 영상 처리에는 별도 영상 생성 API 비용이 필요하지 않습니다. **Seedance 실제 생성에는 Higgsfield 구독 크레딧이 차감될 수 있습니다.** Instagram 자동 게시에는 별도 WoopSocial 계정 연결이 필요합니다.

![Instagram Skill로 제작한 캐러셀, 릴스, 스토리 및 미리보기 예시](skills/instagram-skill/examples/showcase.png)

*위 이미지는 원본 저장소의 예시입니다. [`examples/water-week/`](skills/instagram-skill/examples/water-week/)에는 USGS 수치, NASA 사진, 영어·스페인어 슬라이드, 스토리, 릴스 표지, 검수 결과 및 미리보기가 들어 있습니다. 예제 릴스는 원본 제작자의 영상을 Remotion Shorts Skill로 처리한 것입니다. 출처는 [CREDITS](skills/instagram-skill/examples/water-week/CREDITS.md)를 참고하세요.*

## 목차

- [1. 기능과 실행 흐름](#1-기능과-실행-흐름)
- [2. 실행 환경 및 준비물](#2-실행-환경-및-준비물)
- [3. 설치](#3-설치)
- [4. Seedance AI 릴스 제작](#4-seedance-ai-릴스-제작)
- [5. 한국어 글꼴 및 자막](#5-한국어-글꼴-및-자막)
- [6. 기존 기능 사용 예시](#6-기존-기능-사용-예시)
- [7. 검수 항목](#7-검수-항목)
- [8. Instagram 게시 및 예약](#8-instagram-게시-및-예약)
- [9. 지원 범위와 제한 사항](#9-지원-범위와-제한-사항)
- [10. 자주 묻는 질문](#10-자주-묻는-질문)
- [11. 프로젝트 구조](#11-프로젝트-구조)

## 1. 기능과 실행 흐름

에이전트에게 “이번 주 인스타그램 게시물을 만들어줘”, “이 사진으로 캐러셀을 만들어줘”, “이 영상을 릴스로 올려줘”, “제품 사진으로 Seedance 광고 영상을 만들어줘”처럼 요청할 수 있습니다.

1. **계정 파악:** 브랜드, 타깃, 계정, 색상, 언어, 시간대, 기존 게시물을 확인하고 `brand.md`에 기록
2. **형식 결정:** 저장을 유도하는 캐러셀, 신규 도달용 릴스, 단일 이미지, 기존 팔로워 대상 스토리 중 목적에 맞는 형식 선택
3. **미디어 제작:** 기존 이미지·영상 도구 사용. AI 영상을 명시적으로 요청한 경우에만 Seedance 확장 사용
4. **캡션 작성:** 검색어·첫 문장 후킹·행동 요청·최대 5개 해시태그·이미지 대체 텍스트 작성
5. **규격 검사:** `ig_check.py`로 검사하고 필요한 경우 원본을 유지한 채 수정본 생성
6. **게시 계획:** 계정별 시간대와 팔로워 활동 시간에 따라 일정 수립
7. **미리보기:** 실제 그리드·피드 표현을 확인하고 수정 사항 반영
8. **사용자 승인:** 명확한 최종 승인 후에만 게시 또는 예약
9. **성과 분석:** WoopSocial 통계를 읽고 같은 계정·형식·게시 후 경과 기간의 게시물과 비교

### 영상 제작 흐름

```text
한국어 자연어 요청 + 실제 제품 사진
              ↓
      프롬프트·장면 기획
              ↓
  [신규] Seedance / Higgsfield CLI
              ↓
      원본 영상 MP4 저장
              ↓
  [신규] 영상 결합·한글 자막
              ↓
   [기존] reel.py: 표지·안전영역
              ↓
   [기존] ig_check.py: 규격 검사
              ↓
   [기존] preview.py: 미리보기
              ↓
     사용자 피드백 및 최종 승인
              ↓
  [기존] WoopSocial: 게시·예약
```

Seedance 생성 모듈과 영상 편집 모듈은 **자동 게시 기능을 포함하지 않습니다**. 기존 Skill의 사용자 승인 규칙을 따릅니다.

## 2. 실행 환경 및 준비물

| 항목 | 기본 기능 | Seedance 확장 |
|---|---|---|
| AI 에이전트 | Codex, Claude Code, Cursor, OpenClaw 등 | 동일 |
| Python | **3.9 이상** | 동일 |
| Python 라이브러리 | Pillow | 신규 실행 모듈은 표준 라이브러리 사용 |
| FFmpeg·FFprobe | 영상 작업 시 필요 | 필수 |
| 한국어 글꼴 | 한국어 슬라이드·표지 사용 시 필요 | 한국어 자막 시 필요 |
| Higgsfield CLI·로그인 | 불필요 | 실제 영상 생성 시 필요 (API 키 불필요) |
| WoopSocial 연결 | 자동 게시할 때 필요 | 자동 게시할 때 동일하게 필요 |

선택 사항: iPhone HEIC 사진을 사용한다면 `pillow-heif`를 설치할 수 있습니다. Windows에서는 시간대 관련 패키지 `tzdata`도 권장합니다.

**Windows PowerShell:**

```powershell
py -m pip install pillow tzdata
# ffmpeg / ffprobe 는 별도로 설치하고 PATH에 등록합니다.
py skills/instagram-skill/scripts/check_setup.py
```

**macOS / Linux:**

```bash
python3 -m pip install pillow
python3 skills/instagram-skill/scripts/check_setup.py
```

원본 프로젝트는 Windows, macOS, Ubuntu용 파이프라인 테스트를 포함합니다. 이번 Seedance 확장은 별도의 오프라인 단위 테스트도 제공합니다.

## 3. 설치

### Codex — 이 Fork 버전 사용

**원본 `social-media-skills/instagram-skill`을 설치하면 Seedance 확장이 포함되지 않습니다.** 확장 버전은 아래 `dogsa33` 저장소를 대상으로 설치해야 합니다.

```bash
npx skills add dogsa33/instagram-skill
```

명령 실행 후 사용할 에이전트로 **Codex**를 선택합니다. 또는 Git 저장소를 복제해 `skills/instagram-skill/` 폴더를 에이전트의 Skill 폴더에 설치할 수 있습니다.

개발 브랜치의 최신 확장 코드를 직접 확인하거나 실행하려면:

```bash
git clone -b feature/seedance-ko-reels https://github.com/dogsa33/instagram-skill.git
cd instagram-skill
```

**주의:** `npx skills add dogsa33/instagram-skill` 명령은 기본 브랜치를 기준으로 설치될 수 있습니다. 이 확장 기능이 `main`에 병합되기 전에는 **개발 브랜치를 복제하여 Skill 폴더를 사용**하세요.

### 다른 에이전트

원본 Claude Code 설치 명령은 다음과 같습니다.

```bash
npx skills add social-media-skills/instagram-skill -g -a claude-code -y
```

원본은 OpenClaw(`openclaw skills install @social-media-skills/instagram-skill`), GitHub CLI(`gh skill install social-media-skills/instagram-skill instagram-skill`), Gemini CLI(`gemini extensions install https://github.com/social-media-skills/instagram-skill`)에서도 설치할 수 있습니다. **이 원본 설치 명령은 이 Fork의 추가 기능을 설치하는 명령이 아닙니다.**

## 4. Seedance AI 릴스 제작

이 기능은 **선택적 확장**입니다. 기존 사진·캐러셀·실제 영상 릴스 기능은 Seedance 없이 그대로 사용할 수 있습니다.

### 4.1 Higgsfield CLI 설치 및 로그인

이 Fork의 영상 생성은 **Higgsfield CLI 한 가지 방식**만 사용합니다. Replicate 계정이나 별도 API 키는 필요하지 않습니다. Windows에서는 Node.js/npm을 설치한 후 아래를 실행합니다.

```powershell
npm install -g @higgsfield/cli
higgsfield auth login
higgsfield account status
higgsfield model get seedance_2_5
```

브라우저 로그인 후 Higgsfield 계정의 구독 크레딧으로 생성합니다. **Higgsfield 웹의 무료·Unlimited 혜택은 CLI 생성에는 적용되지 않습니다.** 실행 전에는 `higgsfield generate cost`로 크레딧 비용을 확인하세요. 모델 ID는 `seedance_2_5`로 고정하며, 지원 길이는 4~30초입니다.

### 4.2 생성 전에 무료 Dry Run 실행

```powershell
cd skills/instagram-skill
py scripts/seedance_video.py --prompt "따뜻한 주방에서 빵 반죽이 발효되는 장면" --image product.jpg --duration 15 --out reel/raw.mp4 --dry-run
```

`--dry-run`은 **네트워크 요청·과금 없이** Higgsfield CLI 명령 구성을 표시합니다. `product.jpg`는 실제 로컬 파일이어야 합니다.

실제 크레딧 확인 예시(생성하지 않음):

```powershell
higgsfield generate cost seedance_2_5 --mode omni_reference --start-image product.jpg --prompt "따뜻한 주방에서 빵 반죽이 발효되는 장면" --duration 5 --resolution 720p --aspect_ratio 9:16
```

### 4.3 실제 영상 생성

```powershell
py scripts/seedance_video.py --prompt-file prompt_ko.txt --image product.jpg --duration 5 --out reel/raw.mp4
```

- `--prompt` 또는 `--prompt-file`로 제작 프롬프트 지정
- `--image`는 참조 사진을 최대 4장까지 반복 지정 가능
- `--duration`으로 길이 지정(기본값 15초, Seedance 2.5 지원 범위 4~30초)
- 결과 MP4를 `--out`에 저장
- 작업 정보는 `reel/raw.job.json`에 저장
- 생성 중 연결이 끊겼다면 `--resume`으로 **기존 작업 조회**

```powershell
py scripts/seedance_video.py --resume --out reel/raw.mp4
```

동일 작업 상태 파일이 있는 상태에서 새 과금 요청을 중복 제출하지 않도록 보호합니다. **새 영상을 생성하려면 별도의 출력 경로를 선택**하세요.

## 5. 한국어 글꼴 및 자막

### 5.1 한국어 글꼴 활성화

기본 Inter/Instrument Serif 사용 방식은 유지됩니다. **한국어 사용 시에만** 글꼴을 전환합니다.

```powershell
$env:INSTAGRAM_SKILL_LANG = "ko"
# 글꼴 경로를 직접 지정하려면:
# $env:INSTAGRAM_KOREAN_FONT = "C:\Windows\Fonts\malgun.ttf"
```

Windows에서는 맑은 고딕을 자동 탐색하며, macOS/Linux에서는 지원되는 한국어 글꼴 경로를 확인합니다. 자동 탐색에 실패하면 `INSTAGRAM_KOREAN_FONT`를 설정하세요.

### 5.2 시간대별 한글 자막

UTF-8 인코딩의 `captions_ko.json`을 작성합니다.

```json
{
  "captions": [
    {"start": 0, "end": 3, "text": "집에서 만드는 빵, 발효부터"},
    {"start": 3, "end": 8, "text": "작은 차이가 만드는 베이킹의 즐거움"},
    {"start": 8, "end": 13, "text": "실제 제품 정보를 확인해 보세요"}
  ]
}
```

```powershell
py scripts/compose_reel.py --clip reel/raw.mp4 --photo product.jpg --captions captions_ko.json --out reel/final.mp4
```

`compose_reel.py`는 여러 `--clip` 영상을 순서대로 결합할 수 있고, 기존 영상 오디오를 유지하며, 자막을 합성하고, 선택적으로 **실제 제품 사진을 엔딩 카드로 추가**할 수 있습니다. 한국어 음성 자동 합성이나 자동 번역은 현재 1차 범위에 포함하지 않습니다.

### 5.3 기존 릴스 기능으로 검수

```powershell
py scripts/reel.py frames reel/final.mp4 --out reel/preview
py scripts/reel.py cover reel/final.mp4 --at 5 --title "집에서 만드는 빵" --out reel/cover.jpg
py scripts/reel.py zones reel/final.mp4 --out reel/zones.jpg
```

표지와 안전영역을 검토한 뒤 기존 `plan.json` 규격을 사용합니다.

```json
{
  "id": "product-reel",
  "format": "reel",
  "media": ["reel/final.mp4"],
  "cover": "reel/cover.jpg",
  "caption": "발효부터 시작하는 홈베이킹",
  "targets": [{"account": "main"}]
}
```

위 JSON은 **전체 `plan.json`이 아니라 `posts` 배열에 넣는 게시물 예시**입니다. 계정 설정까지 포함하는 전체 형식은 [`references/plan-json.md`](skills/instagram-skill/references/plan-json.md)를 참고하세요.

더 자세한 Windows 실행 예시와 주의 사항은 [한국어 확장 가이드](skills/instagram-skill/references/README_KO.md)에 있습니다.

## 6. 기존 기능 사용 예시

### 다중 계정의 일주일 콘텐츠 제작

아래는 원본 저장소에서 제공하는 예시를 한국어로 정리한 것입니다.

```text
사용자:
  뉴욕 @earthinnumbers와 마드리드 스페인어 계정
  @latierraennumeros에 지구의 물을 주제로 일주일 게시물을
  만들어줘. 실제 통계를 사용해. 우리가 만든 공기 관련 영상도 있어.

에이전트:
  월요일: 지구의 모든 물을 1리터 병으로 표현한 캐러셀.
          스페인어 계정에는 스페인어 슬라이드 제작.
          게시 1시간 전에 예고 스토리 배치.
  화요일: 지하수의 염분 관련 통계 이미지 1장.
  수요일: 제공한 애니메이션 영상을 릴스로 구성하고,
          표지와 화면 가림 영역을 점검.
  검수 완료. 미리보기: preview/index.html

사용자:
  확인했어. 예약해줘.

에이전트:
  계정별 시간대에 맞춰 게시물 7개 예약.
  게시 후 첫 1시간 대응과 앱에서 해야 할 항목을
  schedule.md에 정리.
```

실제 예제 결과물은 [`examples/water-week/`](skills/instagram-skill/examples/water-week/)에 있습니다.

### 기존 스크립트

```bash
# 캐러셀·이미지 제작
python3 scripts/render_slides.py slides.json --out slides/

# 기존 영상에서 릴스 표지와 안전영역 생성
python3 scripts/reel.py frames video.mp4 --out reel/
python3 scripts/reel.py cover video.mp4 --at 4.2 --out reel/cover.jpg
python3 scripts/reel.py zones video.mp4 --out reel/zones.jpg

# 게시 계획 검사 및 수정본 생성
python3 scripts/ig_check.py plan.json
python3 scripts/ig_check.py plan.json --fix

# 일정 생성
python3 scripts/schedule.py plan.json --start 2026-11-09

# 미리보기 생성
python3 scripts/preview.py plan.json --out preview/
```

위 스크립트는 Fork의 기존 기능입니다. Seedance 확장을 사용하지 않아도 계속 동작하도록 유지했습니다.

## 7. 검수 항목

| 항목 | 검사 기준 / 동작 | 목적 |
|---|---|---|
| 이미지 형식 | JPEG, sRGB, 가로 320~1440px, 최대 8MB | API에서 거부되는 형식 예방 |
| 이미지 비율 | 피드 4:5~1.91:1, 스토리 9:16 | 인스타그램 업로드 규격 확인 |
| 캐러셀 | 2~20개, 첫 이미지와 동일한 비율 | 게시 시 잘림 방지 |
| 동영상 | MP4/MOV, H.264, 8-bit, AAC, 23~60fps, 릴스 9:16 | 코덱·HDR 호환성 확인 |
| 영상 길이 | 릴스 3초~15분, 스토리 최대 60초, 캐러셀 동영상 최대 60초 | 원본 Skill에 문서화된 API 기준 |
| 프로필 그리드 | 표지의 3:4 잘림 영역 확인 | 핵심 문구 잘림 예방 |
| 릴스 안전영역 | `reel.py zones`로 캡션·버튼·상단 바 영역 표시 | 자막 가림 방지 |
| 캡션 | 최대 2,200자, 해시태그 최대 5개, 언급 최대 20개 등 | 문구 규격 확인 |
| 여러 계정 | 계정별 원본성·첫 문장·게시 빈도 확인 | 중복 게시 예방 |
| 게시물 묶음 | 같은 수치·내용 반복 경고 | 콘텐츠 중복 방지 |

위 수치는 **원본 Skill에 기록된 검수 기준**입니다. 실제 플랫폼 정책이 변경될 수 있으므로 운영 전 [Instagram 규격 문서](skills/instagram-skill/references/instagram-specs.md)와 최신 공식 안내를 확인하세요.

`ig_check.py --fix`는 가능한 경우 수정본을 생성하고 원본 파일은 보존합니다. 긴 동영상을 어디서 자를지, 가로 영상을 어떻게 프레이밍할지 등 판단이 필요한 작업은 사용자에게 확인합니다.

## 8. Instagram 게시 및 예약

기존 게시 기능은 [WoopSocial](https://woopsocial.com/) MCP/API를 사용합니다. WoopSocial은 인스타그램 게시·예약·성과 분석을 위한 외부 서비스이며, **Skill 개발사와 관련된 서비스**입니다.

- **필수 계정:** Instagram Business 또는 Creator 계정
- **지원 형식:** 이미지, 캐러셀, 릴스(지원되는 계정의 Trial Reel 포함), 스토리
- **작업 순서:** 계정 연결 → 미디어 업로드 → 요청 유효성 검사 → 미리보기 → **사용자 승인** → 게시/예약 → 게시 상태 확인
- **여러 계정:** 각 계정에 맞는 콘텐츠·캡션·시간대별 요청을 별도로 생성
- **게시하지 않고 사용:** 파일·캡션·계획만 받아 직접 업로드 가능

WoopSocial의 무료 플랜은 원본 문서 기준 소셜 계정 2개 연결을 안내하고 있습니다. 현재 요금제는 별도로 확인하세요. 협업자 태그, 위치, 음악, 대체 텍스트, 첫 댓글 등 일부 항목은 API를 통해 처리할 수 없으며 인스타그램 앱에서 직접 추가해야 할 수 있습니다.

Codex용 MCP 연결은 원본의 [`references/woopsocial.md`](skills/instagram-skill/references/woopsocial.md)를 따릅니다.

```bash
codex mcp add woopsocial --url https://api.woopsocial.com/mcp
codex mcp login woopsocial
```

MCP 연결 후 Codex 세션을 새로 열거나 재개해야 할 수 있습니다. **사용자의 명시적 승인 없이 게시하거나 예약하지 않습니다.**

## 9. 지원 범위와 제한 사항

원본과 확장판 모두 다음 원칙을 따릅니다.

- 확인되지 않은 수치, 후기, 인용문, 인증, 제품 기능 또는 성능을 만들어내지 않습니다.
- 사용자 승인 없이 게시하지 않습니다.
- 일반적인 “최적 게시 시간”을 임의로 정하지 않고 사용자 계정 Insights를 기준으로 계획합니다.
- 동일한 콘텐츠를 여러 계정에 무분별하게 반복 게시하지 않습니다.
- 가로 영상을 사전 확인 없이 무조건 자르거나 타인의 영상을 자신의 원본인 것처럼 사용하지 않습니다.

**원본과 확장판의 기능 차이:** 원본은 이미 만들어진 실사 영상을 릴스로 마무리하며 장면 편집이나 자체 AI 영상 생성을 제공하지 않습니다. 이 Fork에서는 **Seedance 영상 생성과 별도 FFmpeg 편집 모듈**을 추가하여 해당 작업을 선택적으로 지원합니다. 다만 자동 음성 합성, 전문 NLE 수준의 장면 편집, 텍스트만으로 된 모션그래픽 릴스 제작은 현재 지원 범위가 아닙니다.

**AI 제품 광고 주의:** 생성 영상은 실제 제품 외형과 다를 수 있습니다. 실제 제품 사진과 대조하고, 허위 성능 표시·권리 없는 음악·초상권 문제·AI 콘텐츠 표시 요건을 게시 전에 검토해야 합니다. 업로드 단계에서 필요한 앱 내 설정은 체크리스트에 남깁니다.

**실행 환경:** 로컬 Skill과 Python 스크립트는 기본적으로 사용자의 PC에서 실행됩니다. PC가 꺼져 있을 때 영상을 새로 생성하는 백그라운드 서버 기능은 포함하지 않습니다. 단, WoopSocial에 예약이 정상 등록된 게시물은 게시 시점에 PC가 켜져 있을 필요가 없습니다.

## 10. 자주 묻는 질문

**Q. Instagram Skill이란 무엇인가요?**  
`SKILL.md`에 정의된 에이전트용 업무 절차와 Python 실행 도구를 묶은 프로젝트입니다. 단순한 프롬프트가 아니라 실제 미디어 파일을 제작·검사합니다.

**Q. Codex에서 한국어로 제작을 요청할 수 있나요?**  
네. 한국어로 지시할 수 있고, 한글 글꼴 및 영상 자막을 지원하도록 확장했습니다. 다만 원본 내부의 모든 출력 메시지가 한국어로 번역된 것은 아닙니다.

**Q. Seedance 없이도 기존 기능을 쓸 수 있나요?**  
네. Seedance는 선택 기능이며, 사진·캐러셀·기존 영상 릴스·스토리·검수·미리보기·게시 기능은 그대로 유지됩니다.

**Q. Seedance 영상은 무료인가요?**  
아닙니다. `--dry-run`은 무료이지만 실제 모델 생성에는 Higgsfield 구독 크레딧이 사용됩니다. CLI 생성에는 웹사이트의 Unlimited 혜택이 적용되지 않습니다.

**Q. 인간의 검토와 수정 피드백을 반복할 수 있나요?**  
네. Codex와 대화하면서 자막을 수정하거나 필요한 클립만 별도로 재생성하고, 미리보기를 다시 생성하는 방식입니다. 자동 피드백 웹 UI나 자동 승인 시스템은 포함되어 있지 않습니다.

**Q. 개인 Instagram 계정에도 자동 게시할 수 있나요?**  
원본 Skill의 게시 절차는 Business 또는 Creator 계정을 요구합니다. 개인 계정은 앱에서 전문 계정으로 전환한 뒤 연결해야 합니다.

**Q. Instagram 게시가 반드시 필요한가요?**  
아닙니다. 자동 게시 없이 로컬 MP4, 이미지, 캡션, 일정표만 만들어 직접 올릴 수 있습니다.

**Q. 여러 계정에 예약 게시할 수 있나요?**  
네. 계정별 미디어, 캡션, 타임존을 설정해 게시 요청을 만듭니다. 계정마다 실제로 다른 버전을 제작해야 합니다.

**Q. 왜 피드 이미지는 3:4가 아니라 4:5인가요?**  
원본 문서 기준 프로필 그리드는 3:4로 보여주지만 게시 API가 허용하는 이미지 비율은 4:5~1.91:1이므로, 제작물은 4:5로 만들고 그리드 잘림을 고려합니다.

**Q. 해시태그는 몇 개까지인가요?**  
원본 Skill의 검수 기준은 최대 5개이며, 6개 이상이면 경고 또는 오류 처리합니다.

## 11. 프로젝트 구조

```text
instagram-skill/
├── README.md                      # 이 문서: 한국어 전체 안내
├── LICENSE                        # 원본 MIT 라이선스
├── skills/
│   └── instagram-skill/
│       ├── SKILL.md                # 원본 워크플로 + 선택적 Seedance 절차
│       ├── scripts/
│       │   ├── check_setup.py      # 환경 점검 (기존)
│       │   ├── render_slides.py    # 이미지·캐러셀 + 선택적 한글 글꼴
│       │   ├── ig_check.py         # 미디어 규격 검사 및 수정 (기존)
│       │   ├── reel.py             # 표지·안전영역 (기존)
│       │   ├── schedule.py         # 예약 계획 (기존)
│       │   ├── preview.py          # 피드·그리드 미리보기 (기존)
│       │   ├── upload_parts.py     # WoopSocial 미디어 업로드 (기존)
│       │   ├── log.py              # 게시·성과 로그 (기존)
│       │   ├── seedance_video.py   # [신규] Seedance 영상 생성
│       │   └── compose_reel.py     # [신규] 한국어 자막·영상 결합
│       ├── references/
│       │   ├── README_KO.md        # [신규] Seedance 상세 한국어 가이드
│       │   ├── instagram-specs.md  # 인스타그램 게시 규격
│       │   ├── plan-json.md        # 게시 계획 JSON 구조
│       │   ├── woopsocial.md       # 게시 API 연결 절차
│       │   └── ...                 # 기타 기존 문서
│       ├── fonts/                  # 원본 Inter·Instrument Serif (OFL)
│       ├── examples/water-week/    # 원본 종합 예시
│       └── evals/evals.json        # 원본 평가 프롬프트
└── tests/
    ├── run_pipeline.py            # 원본 파이프라인 테스트
    └── test_seedance_extension.py  # [신규] 오프라인 단위 테스트
```

### 오프라인 확장 테스트

프로젝트 루트에서 다음을 실행합니다.

```powershell
py -m unittest discover -s tests -p test_seedance_extension.py -v
```

이 테스트는 실제 Higgsfield 과금 요청이나 Instagram 게시를 수행하지 않습니다. **실제 생성·게시 성공 여부를 보증하는 통합 테스트는 아닙니다.**

### 출처 및 라이선스

- **원본 프로젝트:** [social-media-skills/instagram-skill](https://github.com/social-media-skills/instagram-skill)
- **현재 Fork:** [dogsa33/instagram-skill](https://github.com/dogsa33/instagram-skill)
- **확장 가이드:** [`README_KO.md`](skills/instagram-skill/references/README_KO.md)
- **원본 저작권·라이선스:** 프로젝트의 [MIT LICENSE](LICENSE) 유지
- 포함된 Inter 및 Instrument Serif 글꼴은 SIL Open Font License를 따릅니다. 예제 NASA 사진 및 Remotion Shorts Skill 관련 크레딧은 [원본 CREDITS](skills/instagram-skill/examples/water-week/CREDITS.md)를 참고하세요.

원본 팀의 다른 소셜 미디어 Skill은 [social-media-skills.com](https://social-media-skills.com/) 및 [Instagram Carousel Skill](https://github.com/social-media-skills/instagram-carousel-skill)에서 확인할 수 있습니다.
