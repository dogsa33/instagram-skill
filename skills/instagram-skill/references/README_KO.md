# Instagram Skill + Seedance: 한국어 확장 가이드

이 확장은 기존 `instagram-skill`의 이미지·캐러셀·릴스 검수·미리보기·예약 기능을 **대체하지 않습니다**. 선택적으로 Seedance(Replicate 경유)에서 원본 영상을 만들고, 여러 클립과 한국어 자막을 합성한 후 기존 릴스 검수·게시 절차로 넘깁니다.

## 1. 준비물

- Codex 또는 Claude Code, Python 3.9+, Pillow, FFmpeg/FFprobe
- 영상 생성 시에만 `REPLICATE_API_TOKEN`과 Replicate 유료 모델 접근 권한
- 게시할 때만 WoopSocial MCP와 Instagram Business/Creator 계정
- Windows에서 시간대 처리를 한다면 `tzdata`
- 한글 글꼴: Windows에서는 맑은 고딕을 자동 검색합니다. 다른 OS는 Noto Sans CJK/NanumGothic을 검색하며, 필요하면 `INSTAGRAM_KOREAN_FONT`로 직접 지정합니다.

Windows에서 `py -m pip install pillow tzdata`로 필요한 Python 패키지를 준비하고, 기존 `scripts/check_setup.py`를 실행해 환경을 확인합니다. 신규 Seedance API 모듈은 Python 표준 라이브러리만 사용합니다.

## 2. Windows PowerShell 예시

Fork한 저장소의 `skills/instagram-skill` 디렉터리에서 실행합니다.

```powershell
$env:INSTAGRAM_SKILL_LANG = "ko"
# 선택적으로 글꼴 지정:
# $env:INSTAGRAM_KOREAN_FONT = "C:\Windows\Fonts\malgun.ttf"

# 비용 없이 API 요청 내용 확인
py scripts/seedance_video.py --prompt-file .\prompt_ko.txt --image .\product.jpg --duration 15 --out .\reel\raw.mp4 --dry-run

# 실제 영상 생성 (API 요금 발생 가능, 환경 변수 REPLICATE_API_TOKEN 필요)
py scripts/seedance_video.py --prompt-file .\prompt_ko.txt --image .\product.jpg --duration 15 --out .\reel\raw.mp4

# 중단된 작업 이어받기 (중복 과금 방지)
# py scripts/seedance_video.py --resume --out .\reel\raw.mp4

# 한국어 자막과 실제 제품 사진 결합
py scripts/compose_reel.py --clip .\reel\raw.mp4 --photo .\product.jpg --captions .\captions_ko.json --out .\reel\final.mp4

# 기존 릴스 도구 이용
py scripts/reel.py frames .\reel\final.mp4 --out .\reel\preview
py scripts/reel.py cover .\reel\final.mp4 --at 5 --title "집에서 만드는 빵" --out .\reel\cover.jpg
py scripts/reel.py zones .\reel\final.mp4 --out .\reel\zones.jpg
```

`reel.py`는 표지·안전영역을 처리하지만 영상 편집기는 아닙니다. 편집은 신규 `compose_reel.py`가 담당합니다.

## 3. 입력 예시

`prompt_ko.txt`:

```text
세로 9:16 홈베이킹 광고 영상. 따뜻한 자연광 속에 반죽이 발효되는 장면과 빵이 완성되는 과정을 보여준다. 업로드한 실제 발효기 사진의 구조·버튼·외형을 임의로 바꾸지 말 것. 확인되지 않은 성능 수치, 타사 비교, 가짜 후기, 가상의 인증 마크는 만들지 말 것. 화면 내 글자를 AI가 생성하지 말고 후처리에서 자막으로 넣는다.
```

`captions_ko.json`:

```json
{
  "captions": [
    {"start": 0, "end": 3, "text": "집에서 만드는 빵, 발효부터"},
    {"start": 3, "end": 8, "text": "작은 차이가 만드는 베이킹의 즐거움"},
    {"start": 8, "end": 13, "text": "실제 제품 정보를 확인해 보세요"}
  ]
}
```

작업을 다시 생성할 때 기존 `.job.json`을 확인합니다. 새로 과금되는 작업을 생성하려면 새 `--out` 경로를 사용하고, 중단된 작업은 `--resume`으로 재개합니다.

## 4. 검토와 게시

1. AI 영상을 실제 제품 사진과 대조하고 형태·기능·광고 문구를 검수합니다.
2. 기존 `reel.py zones`와 `ig_check.py`로 릴스 규격과 안전영역을 확인합니다.
3. 원본 `references/plan-json.md` 규격의 `plan.json`에 `"format": "reel"`, `"media": ["reel/final.mp4"]`, `"cover": "reel/cover.jpg"`를 입력합니다.
4. 기존 `preview.py`로 검토합니다. 수정할 경우 해당 장면만 재생성한 후 다시 검증합니다.
5. **사용자가 명시적으로 최종 승인한 뒤에만** 기존 WoopSocial 연동으로 업로드·예약 게시합니다. 이 확장 자체는 자동 게시하지 않습니다.

## 5. 호환성·한계

- `INSTAGRAM_SKILL_LANG=ko` 또는 `INSTAGRAM_KOREAN_FONT`가 없으면 원본 Inter/Instrument Serif 글꼴 동작은 바뀌지 않습니다.
- 현재 Seedance 입력 필드는 Replicate의 `bytedance/seedance-2.5` 워크플로를 참고했습니다. 실제 모델 API 스키마와 사용 권한은 호출 전에 다시 확인해야 합니다.
- AI가 제품 외형을 정확히 유지한다는 보장은 없습니다. 최종 카드에는 **실제 제품 사진을 원본 그대로** 첨부하는 방식이 안전합니다.
- 한국어 음성 합성·자동 번역은 1차 버전 범위에 포함하지 않습니다. 한글 텍스트·자막은 지원합니다.
- 음악·초상권·허위 광고 표현·AI 콘텐츠 표시 규칙은 게시 전에 확인합니다.
