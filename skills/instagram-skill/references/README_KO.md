# Instagram Skill + Seedance: 한국어 확장 가이드

이 확장은 기존 `instagram-skill`의 이미지/캐러셀/릴스 검수/미리보기/예약 기능을 **대체하지 않습니다**. 선택적으로 Seedance(Replicate 경유)에서 원본 영상을 만들고, 필요하면 여러 클립과 한국어 자막을 합성한 후 **기존** 릴스 검수·게시 절차로 넘깁니다.

## 1. 준비물

- Codex 또는 Claude Code, Python 3.9+, Pillow, FFmpeg/FFprobe
- 영상 생성 시에만 `REPLICATE_API_TOKEN`과 Replicate 유료 모델 접근 권한
- 게시할 때만 WoopSocial MCP와 Instagram Business/Creator 계정
- Windows에서 시간대 처리를 한다면 `tzdata`
- 한글 글꼴: Windows에서는 맑은 고딕을 자동 검색합니다. 다른 OS는 Noto Sans CJK/NanumGothic을 검색하며, 필요하면 `INSTAGRAM_KOREAN_FONT`로 직접 지정합니다.

필요 라이브러리: `py -m pip install pillow tzdata` (Windows). 기존 리포지토리의 `scripts/check_setup.py`를 실행해 확인합니다. 신규 영상 생성 API 모듈은 Python 표준 라이브러리만 사용합니다.

## 2. Windows PowerShell 예시

원본 저장소를 Fork한 복제본에서, `skills/instagram-skill` 디렉터리로 이동한 뒤:

```powershell
$env:INSTAGRAM_SKILL_LANG = "ko"
# 글꼴을 직접 지정하려면 (선택)
# $env:INSTAGRAM_KOREAN_FONT = "C:\Windows\Fonts\malgun.ttf"

# 먼저 비용 없이 API 요청 내용을 확인합니다.
py scripts/seedance_video.py --prompt-file .\prompt_ko.txt --image .\product.jpg --duration 15 --out .\reel\raw.mp4 --dry-run

# 실제 영상 생성(외부 API 과금 발생 가능). 환경 변수에 API 키 설정 필요.
py scripts/seedance_video.py --prompt-file .\prompt_ko.txt --image .\product.jpg --duration 15 --out .\reel\raw.mp4

# 작업 중단 후 이어받기: 중복 결제 요청 방지
# py scripts/seedance_video.py --resume --out .\reel\raw.mp4

# 필요하면 여러 클립, 한국어 타임코드 자막과 원본 제품 사진을 결합합니다.
py scripts/compose_reel.py --clip .\reel\raw.mp4 --photo .\product.jpg --captions .\captions_ko.json --out .\reel\final.mp4

# 기존 원본 스크립트(수정하지 않음)
py scripts/reel.py frames .\reel\final.mp4 --out .\reel\preview
py scripts/reel.py cover .\reel\final.mp4 --at 5 --title "집에서 만드는 빵" --out .\reel\cover.jpg
```

`reel.py`는 안전영역을 확인하고 커버를 만들지만 영상 내부를 편집하지는 않습니다. 편집은 신규 `compose_reel.py`가 담당합니다.

## 3. 입력 파일

`prompt_ko.txt` 예시:

```text
세로 9:16 홈베이킹 광고 영상. 따뜻한 자연광 속에 반죽이 발효되는 장면과 빵이 완성되는 과정을 보여준다. 업로드한 실제 발효기 사진의 구조/버튼/외형을 임의로 바꾸지 말 것. 확인되지 않은 성능 수치, 타사 비교, 가짜 후기, 가상의 인증 마크는 만들지 말 것. 화면 내 글자를 AI가 생성하지 말고 후처리에서 자막으로 넣는다.
```

`captions_ko.json` 예시:

```json
{
  "captions": [
    {"start": 0, "end": 3, "text": "집에서 만드는 빵, 발효부터"},
    {"start": 3, "end": 8, "text": "작은 차이가 만드는 베이킹의 즐거움"},
    {"start": 8, "end": 13, "text": "실제 제품 정보를 확인해 보세요"}
  ]
}
```

장면을 다시 생성할 때는 기존 `.job.json` 작업을 확인하세요. **새로운 비용을 발생시키려면** 별도의 `--out` 경로로 새 작업을 만듭니다. 중단된 동일 작업을 조회할 때는 `--resume`을 사용합니다.

## 4. 게시와 사람 승인

1. 영상 생성 후 실제 제품 사진과 대조해 외형·기능·광고 문구를 검수합니다.
2. 원본 `reel.py zones`와 `ig_check.py`로 인스타그램 릴스 규격과 안전영역을 확인합니다.
3. 원본 `references/plan-json.md` 형식의 `plan.json`에 `"format": "reel"`, `"media": ["reel/final.mp4"]`, `"cover": "reel/cover.jpg"`를 입력합니다.
4. 원본 `preview.py`로 결과를 검토합니다. 피드백이 있으면 필요한 장면만 다시 만들고 동일 절차로 검증합니다.
5. **명시적 최종 승인 후에만** 기존 WoopSocial 연동으로 업로드·예약 게시합니다. 자동 게시를 위한 코드는 이 확장에 포함하지 않습니다.

## 5. 호환성·한계

- `INSTAGRAM_SKILL_LANG=ko` 설정이 없으면 원본 Inter/Instrument Serif 글꼴 동작은 바뀌지 않습니다.
- 글꼴이 설치되지 않았다면 `INSTAGRAM_KOREAN_FONT`를 지정해야 합니다. 영상 자막은 `--font`로도 지정할 수 있습니다.
- 현재 Seedance 요청 필드는 Replicate의 `bytedance/seedance-2.5` 워크플로를 참고합니다. 제공사 API 및 모델 지원 여부가 바뀌면 `--model`과 해당 모델의 입력 스키마를 확인해야 합니다.
- 영상 생성 API로부터 받은 MP4는 실제 제품과 다를 수 있습니다. 제품 자체는 최종 카드에 **실제 제품 사진**을 붙이는 편이 안전합니다.
- 커버/자막 텍스트가 한글로 표시되는지는 사용 시스템 글꼴에서 검증해야 합니다. 자동 번역이나 한국어 음성 생성은 1차 범위에서 제외합니다.
- 음악·초상권·제품 표현·AI 콘텐츠 표시는 게시 전에 별도로 확인합니다.
