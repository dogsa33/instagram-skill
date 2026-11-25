"""Offline-only tests for optional Seedance/Korean extension. No API charges or posts."""
import contextlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "instagram-skill" / "scripts"


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class SeedanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seedance = load_module("seedance_video")
        cls.compose = load_module("compose_reel")

    def test_dry_run_avoids_network_and_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            photo = Path(tmp) / "제품.jpg"
            photo.write_bytes(b"test")
            out = Path(tmp) / "raw.mp4"
            args = self.seedance.parse_args(["--prompt", "주방의 빵 발효 장면", "--image", str(photo),
                                             "--out", str(out), "--dry-run"])
            with mock.patch.object(self.seedance, "_api_request", side_effect=AssertionError("API called")):
                with mock.patch.dict(os.environ, {"REPLICATE_API_TOKEN": ""}):
                    with contextlib.redirect_stdout(io.StringIO()) as buf:
                        self.seedance.run(args)
            response = json.loads(buf.getvalue())
            self.assertEqual(response["input"]["aspect_ratio"], "9:16")
            self.assertEqual(response["model"], "bytedance/seedance-2.5")
            self.assertFalse(out.exists())
            self.assertFalse(out.with_suffix(".job.json").exists())

    def test_existing_job_refuses_duplicate_paid_submission(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "raw.mp4"
            out.with_suffix(".job.json").write_text('{"id":"xyz"}', encoding="utf-8")
            args = self.seedance.parse_args(["--prompt", "hello", "--out", str(out)])
            with self.assertRaisesRegex(self.seedance.ProviderError, "Existing job"):
                self.seedance.run(args)

    def test_resume_does_not_create_prediction(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "raw.mp4"
            job = out.with_suffix(".job.json")
            job.write_text(json.dumps({"id": "pred_123", "model": "bytedance/seedance-2.5"}))
            args = self.seedance.parse_args(["--resume", "--out", str(out)])
            calls = []
            def get(url, token, *params, **kw):
                calls.append(url)
                return {"id": "pred_123", "status": "succeeded", "output": "https://example.com/result.mp4"}
            def save(url, path):
                Path(path).write_bytes(b"MP4")
                return Path(path)
            with mock.patch.dict(os.environ, {"REPLICATE_API_TOKEN": "fake-token"}):
                with mock.patch.object(self.seedance, "_api_request", side_effect=get):
                    with mock.patch.object(self.seedance, "_download_video", side_effect=save):
                        with contextlib.redirect_stdout(io.StringIO()):
                            self.seedance.run(args)
            self.assertEqual(calls, ["https://api.replicate.com/v1/predictions/pred_123"])
            self.assertTrue(out.exists())

    def test_unsafe_result_url_rejected(self):
        with self.assertRaises(self.seedance.ProviderError):
            self.seedance._video_output_url({"output": "http://example.com/unsafe.mp4"})

    def test_caption_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "captions.json"
            path.write_text('{"captions":[{"start":0,"end":3,"text":"한국어"}]}', encoding="utf-8")
            self.assertEqual(self.compose._load_captions(path), [(0., 3., "한국어")])
            path.write_text('{"captions":[{"start":3,"end":2,"text":"오류"}]}', encoding="utf-8")
            with self.assertRaises(self.compose.ComposeError):
                self.compose._load_captions(path)

    def test_caption_png_with_korean_font(self):
        candidates = [r"C:\Windows\Fonts\malgun.ttf",
                      "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
                      "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"]
        fonts = [x for x in candidates if Path(x).is_file()]
        if not fonts:
            self.skipTest("Korean font not present in test environment")
        with tempfile.TemporaryDirectory() as tmp:
            pic = Path(tmp) / "ko.png"
            self.compose._caption_png("우리집 빵 발효\n오늘도 맛있게", pic, fonts[0])
            self.assertTrue(pic.exists())
            from PIL import Image
            with Image.open(pic) as image:
                self.assertEqual(image.size, (1080, 1920))
                self.assertIsNotNone(image.getbbox())


if __name__ == "__main__":
    unittest.main()
