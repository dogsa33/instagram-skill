# Instagram Skill + Higgsfield Kling 3.0 사용 가이드

이 Fork는 **Higgsfield CLI의 Kling 3.0 한 가지 영상 생성 모델**만 사용합니다. 기존 캐러셀·사진·영상 검수·미리보기·게시 및 한국어 자막 기능은 그대로 유지됩니다.

> 기존 실행 명령과 호환되도록 Python 파일명은 `seedance_video.py`로 유지하지만, **실제 생성 모델은 `kling3_0`**입니다.

## 1. 준비

- Windows PowerShell, Python 3.9+, Pillow, FFmpeg/FFprobe
- Node.js/npm 및 Higgsfield 계정(영상 생성 시 구독 크레딧 사용)
- JPG/PNG/WebP 제품 사진 **1장** (사진 없이 텍스트만으로도 생성 가능)
- Instagram에 실제 게시할 때만 WoopSocial + Instagram 전문 계정

```powershell
py -m pip install pillow tzdata
npm install -g @higgsfield/cli
higgsfield auth login
higgsfield account status
higgsfield model get kling3_0
```

별도 API 키는 필요하지 않습니다. **CLI 생성은 Higgsfield 구독 크레딧을 사용**하며, 웹사이트의 무료/Unlimited 혜택과 별도입니다.

## 2. 첫 테스트 (5초, 9:16)

저장소의 `skills/instagram-skill` 폴더에서 실행합니다.

```powershell
$env:INSTAGRAM_SKILL_LANG = "ko"
# 필요한 경우:
# $env:INSTAGRAM_KOREAN_FONT = "C:\Windows\Fonts\malgun.ttf"

# 무료: 생성 요청 명령만 출력
py scripts/seedance_video.py --prompt "따뜻한 홈베이킹 광고" --image product.jpg --duration 5 --out reel/raw.mp4 --dry-run

# 비용 조회: 실제 생성은 하지 않음
higgsfield generate cost kling3_0 --mode std --start-image product.jpg --prompt "따뜻한 홈베이킹 광고" --duration 5 --aspect_ratio 9:16 --sound off

# 실제 생성: 크레딧 차감 가능
py scripts/seedance_video.py --prompt "따뜻한 홈베이킹 광고" --image product.jpg --duration 5 --no-audio --out reel/raw.mp4

# 도중에 중단된 작업 확인 (새 생성 요청 없음)
py scripts/seedance_video.py --resume --out reel/raw.mp4
```

- 모델 `kling3_0`만 사용하며, 비용을 줄이기 위한 기본 `std` 모드입니다.
- 길이 **3~15초**, 세로 **9:16**. CLI의 Kling 3.0에는 별도 `--resolution` 인자가 없습니다.
- `--image`는 **최대 1장**으로 `--start-image`에 전달됩니다. 여러 사진을 한 번에 넣는 방식은 지원하지 않습니다.
- `--no-audio`로 원본 사운드를 생성하지 않도록 지정할 수 있습니다.
- 생성 상태는 `reel/raw.job.json`, 결과 영상은 `reel/raw.mp4`에 저장됩니다.
- 기존 파일이 있으면 `--resume`을 사용하고, 새 버전 생성에는 다른 `--out` 경로를 사용하세요.
- 예전에 Seedance 모델로 생성했던 상태 파일을 Kling 작업으로 이어받지는 않습니다.

## 3. 한국어 자막과 릴스 검수

`captions_ko.json` 예시:

```json
{"captions":[
  {"start":0,"end":3,"text":"집에서 만드는 빵, 발효부터"},
  {"start":3,"end":5,"text":"홈베이킹의 즐거움을 더하다"}
]}
```

```powershell
py scripts/compose_reel.py --clip reel/raw.mp4 --photo product.jpg --captions captions_ko.json --out reel/final.mp4
py scripts/reel.py frames reel/final.mp4 --out reel/preview
py scripts/reel.py zones reel/final.mp4 --out reel/zones.jpg
```

실제 제품 사진을 엔딩 카드로 붙일 수 있습니다. 생성된 제품의 구조·버튼·외형 및 광고 문구를 검증하세요.

## 4. 게시와 검증

원본 `ig_check.py`와 `preview.py`로 검수·미리보기를 진행한 뒤, **명시적인 사용자 승인 후에만** WoopSocial을 통해 게시·예약합니다.

프로젝트 루트에서 무료 오프라인 테스트:

```powershell
py -m unittest discover -s tests -p test_seedance_extension.py -v
```

오프라인 테스트는 CLI를 모의 실행하며 **실제 영상 생성 비용은 발생하지 않습니다**. 최초 유료 생성은 별도 통합 검증이 필요합니다.
