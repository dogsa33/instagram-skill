# Instagram Skill + Higgsfield: 한국어 Seedance 사용 가이드

현재 Fork의 영상 생성 도구는 **Higgsfield CLI 하나만** 사용합니다. Replicate 계정이나 API 키는 필요하지 않습니다.
원본 캐러셀·이미지·릴스 검수·미리보기·WoopSocial 게시 기능과 기존 `compose_reel.py` 한국어 자막 기능은 유지됩니다.

## 1. 준비

- Windows PowerShell, Python 3.9+, Pillow, FFmpeg/FFprobe
- Node.js/npm, Higgsfield 계정(영상 생성에 필요한 구독 크레딧)
- 실제 제품 JPG/PNG/WebP 사진 1장부터 테스트
- Instagram 게시 시에만 WoopSocial 및 Instagram Business/Creator 계정 연결

Windows에서 저장소의 `skills/instagram-skill` 폴더로 이동한 뒤:

```powershell
py -m pip install pillow tzdata
npm install -g @higgsfield/cli
higgsfield auth login
higgsfield account status
higgsfield model get seedance_2_5
```

Higgsfield CLI는 **구독 크레딧을 사용**합니다. 웹사이트의 무료·Unlimited 생성 혜택은 CLI에 적용되지 않습니다. API 토큰을 별도로 만들거나 코드에 저장하지 않습니다.

## 2. 무료 테스트 → 실제 영상 생성

```powershell
$env:INSTAGRAM_SKILL_LANG = "ko"
# 필요하면 글꼴을 직접 지정:
# $env:INSTAGRAM_KOREAN_FONT = "C:\Windows\Fonts\malgun.ttf"

# 비용 없이 명령 구성 확인 (CLI 로그인 없이도 가능)
py scripts/seedance_video.py --prompt "따뜻한 홈베이킹 광고" --image product.jpg --duration 5 --out reel/raw.mp4 --dry-run

# Higgsfield에서 실제 차감될 크레딧을 먼저 조회 (생성은 하지 않음)
higgsfield generate cost seedance_2_5 --mode omni_reference --start-image product.jpg --prompt "따뜻한 홈베이킹 광고" --duration 5 --resolution 720p --aspect_ratio 9:16

# 실제 영상 생성 (크레딧 차감 가능)
py scripts/seedance_video.py --prompt "따뜻한 홈베이킹 광고" --image product.jpg --duration 5 --out reel/raw.mp4

# 실행 중 중단됐을 때: 새 과금 요청을 만들지 않고 동일 작업 조회
py scripts/seedance_video.py --resume --out reel/raw.mp4
```

- 모델은 Higgsfield Seedance 2.5(내부 CLI ID: `seedance_2_5`)로 고정됩니다.
- 사진 1장이면 첫 프레임(`--start-image`), 사진 여러 장이면 참조 이미지(`--image-references`)로 전달합니다.
- 길이 4~30초, 기본 해상도 720p, 화면 비율 9:16입니다.
- 작업 정보는 `reel/raw.job.json`, 완료 영상은 `reel/raw.mp4`에 저장합니다.
- 중복 과금 위험을 줄이려면 작업 파일이 있는 경우 새 실행 대신 `--resume`을 사용하세요.
- 모델 규격과 크레딧 정책은 업데이트될 수 있으므로 최초 실제 실행 전에 `higgsfield model get seedance_2_5`와 비용 조회를 확인하세요.

## 3. 한국어 자막 합성

`captions_ko.json`:

```json
{
  "captions": [
    {"start": 0, "end": 3, "text": "집에서 만드는 빵, 발효부터"},
    {"start": 3, "end": 5, "text": "홈베이킹의 즐거움을 더하다"}
  ]
}
```

```powershell
py scripts/compose_reel.py --clip reel/raw.mp4 --photo product.jpg --captions captions_ko.json --out reel/final.mp4
py scripts/reel.py frames reel/final.mp4 --out reel/preview
py scripts/reel.py zones reel/final.mp4 --out reel/zones.jpg
```

선택적으로 실제 제품 사진을 엔딩 카드로 붙일 수 있습니다. AI가 제품의 구조·버튼·외형을 잘못 생성했는지 반드시 확인하세요.

## 4. 게시 및 테스트

1. 원본 `ig_check.py`로 MP4·캡션 검수
2. 원본 `preview.py`에서 최종 결과 확인
3. 사용자 승인 후 기존 WoopSocial 게시 흐름 진행 (자동 게시 없음)

프로젝트 루트의 오프라인 테스트:

```powershell
py -m unittest discover -s tests -p test_seedance_extension.py -v
```

이 테스트는 Higgsfield 호출을 모의 처리하며 비용이 발생하지 않습니다. 실제 유료 생성 및 Instagram 게시 통합 테스트는 별도 진행이 필요합니다.
