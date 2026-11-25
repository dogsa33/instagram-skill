"""Offline tests: mock Higgsfield CLI, never spend credits or publish posts."""
import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "instagram-skill" / "scripts"


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class KlingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seedance = load_module("seedance_video")
        cls.compose = load_module("compose_reel")

    def test_dry_run_has_higgsfield_only_and_no_charge(self):
        with tempfile.TemporaryDirectory() as tmp:
            photo = Path(tmp) / "product.jpg"
            photo.write_bytes(b"image")
            out = Path(tmp) / "raw.mp4"
            args = self.seedance.parse_args(["--prompt", "따뜻한 베이킹", "--image", str(photo),
                                             "--out", str(out), "--dry-run"])
            with mock.patch.object(self.seedance, "_cli_json", side_effect=AssertionError("CLI called")):
                with contextlib.redirect_stdout(io.StringIO()) as buf:
                    self.seedance.run(args)
            obj = json.loads(buf.getvalue())
            self.assertEqual(obj["model"], "kling3_0")
            self.assertIn("--start-image", obj["command"])
            self.assertIn("std", obj["command"])
            self.assertNotIn("--resolution", obj["command"])
            self.assertNotIn("--image-references", obj["command"])
            self.assertIn("9:16", obj["command"])
            self.assertFalse(out.exists())
            self.assertFalse(out.with_suffix(".job.json").exists())

    def test_prompt_only_uses_std_mode(self):
        args = self.seedance.parse_args(["--prompt", "pan across kitchen", "--out", "raw.mp4", "--dry-run"])
        cmd = self.seedance._create_args(args, args.prompt)
        self.assertEqual(cmd[0:3], ["generate", "create", "kling3_0"])
        self.assertIn("std", cmd)
        self.assertNotIn("--start-image", cmd)
        self.assertNotIn("--resolution", cmd)

    def test_multiple_images_rejected_before_paid_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            images = []
            for name in ("one.png", "two.png"):
                p = Path(tmp) / name
                p.write_bytes(b"fake")
                images.append(str(p))
            args = self.seedance.parse_args(["--prompt", "ad", "--image", images[0],
                                             "--image", images[1], "--out", "raw.mp4"])
            with self.assertRaisesRegex(self.seedance.ProviderError, "at most one reference image"):
                self.seedance._create_args(args, args.prompt)

    def test_no_audio_uses_kling_sound_off(self):
        args = self.seedance.parse_args(["--prompt", "ad", "--no-audio", "--out", "raw.mp4"])
        cmd = self.seedance._create_args(args, args.prompt)
        self.assertEqual(cmd[cmd.index("--sound") + 1], "off")

    def test_duration_limit_rejects_before_paid_call(self):
        args = self.seedance.parse_args(["--prompt", "ad", "--duration", "2", "--out", "raw.mp4"])
        with self.assertRaisesRegex(self.seedance.ProviderError, "3–15"):
            self.seedance._create_args(args, args.prompt)

    def test_existing_job_prevents_duplicate_charge(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "raw.mp4"
            out.with_suffix(".job.json").write_text('{"id":"abc"}', encoding="utf-8")
            args = self.seedance.parse_args(["--prompt", "ad", "--out", str(out)])
            with mock.patch.object(self.seedance, "_cli_json", side_effect=AssertionError("CLI called")):
                with self.assertRaisesRegex(self.seedance.ProviderError, "Existing job"):
                    self.seedance.run(args)

    def test_generate_and_download_uses_cli_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "raw.mp4"
            args = self.seedance.parse_args(["--prompt", "ad", "--out", str(out)])
            calls = []
            def cli(command):
                calls.append(command)
                if command[:2] == ["generate", "create"]:
                    return ["hf-42"]
                return {"id": "hf-42", "status": "completed", "result_url": "https://cdn.example.com/ad.mp4"}
            def download(url, path):
                Path(path).write_bytes(b"mock mp4")
                return Path(path)
            with mock.patch.object(self.seedance, "_cli_json", side_effect=cli):
                with mock.patch.object(self.seedance, "_download_video", side_effect=download):
                    with contextlib.redirect_stdout(io.StringIO()):
                        self.seedance.run(args)
            self.assertEqual(calls[1], ["generate", "get", "hf-42"])
            self.assertTrue(out.exists())
            self.assertEqual(json.loads(out.with_suffix(".job.json").read_text())["id"], "hf-42")

    def test_resume_queries_existing_job_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "raw.mp4"
            out.with_suffix(".job.json").write_text('{"id":"hf-42"}', encoding="utf-8")
            args = self.seedance.parse_args(["--resume", "--out", str(out)])
            calls = []
            def cli(command):
                calls.append(command)
                return {"status": "completed", "result_url": "https://cdn.example.com/ad.mp4"}
            with mock.patch.object(self.seedance, "_cli_json", side_effect=cli):
                with mock.patch.object(self.seedance, "_download_video", return_value=out):
                    with contextlib.redirect_stdout(io.StringIO()):
                        self.seedance.run(args)
            self.assertEqual(calls, [["generate", "get", "hf-42"]])

    def test_resume_rejects_previous_model_job(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "raw.mp4"
            out.with_suffix(".job.json").write_text(
                '{"id":"old-99","model":"seedance_2_5"}', encoding="utf-8")
            args = self.seedance.parse_args(["--resume", "--out", str(out)])
            with mock.patch.object(self.seedance, "_cli_json", side_effect=AssertionError("CLI called")):
                with self.assertRaisesRegex(self.seedance.ProviderError, "another model"):
                    self.seedance.run(args)

    def test_untrusted_http_result_rejected(self):
        with self.assertRaises(self.seedance.ProviderError):
            self.seedance._result_url({"result_url": "http://example.com/ad.mp4"})

    def test_caption_validation_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "captions.json"
            path.write_text('{"captions":[{"start":0,"end":3,"text":"한국어"}]}', encoding="utf-8")
            self.assertEqual(self.compose._load_captions(path), [(0., 3., "한국어")])
            path.write_text('{"captions":[{"start":3,"end":2,"text":"오류"}]}', encoding="utf-8")
            with self.assertRaises(self.compose.ComposeError):
                self.compose._load_captions(path)

    def test_caption_render_korean_if_font_available(self):
        paths = [r"C:\Windows\Fonts\malgun.ttf", "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
                 "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"]
        fonts = [x for x in paths if Path(x).is_file()]
        if not fonts:
            self.skipTest("Korean font not installed")
        with tempfile.TemporaryDirectory() as tmp:
            png = Path(tmp) / "ko.png"
            self.compose._caption_png("우리집 빵 발효", png, fonts[0])
            self.assertTrue(png.exists())


if __name__ == "__main__":
    unittest.main()
