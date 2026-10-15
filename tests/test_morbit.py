import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Make the src-layout package importable when tests run from a fresh checkout.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from morbit import (
    MORBIT_MORSE, ascii_to_bits, bits_to_ascii, decode, decode_bytes,
    decode_file, decode_one_layer, encode, encode_bytes, encode_file,
    encode_one_layer, format_bits, protect_python,
)


class MorbitCompatibilityTests(unittest.TestCase):
    def test_html_layer_zero_vector(self):
        self.assertEqual(encode_one_layer("A"), "0010111000101101")
        self.assertEqual(encode("A", layers=0), "0010111000101101")

    def test_html_layer_one_vector(self):
        expected = "----- ----- .---- ----- .---- .---- .---- ----- ----- ----- .---- ----- .---- .---- ----- .----"
        self.assertEqual(bits_to_ascii(encode("A", layers=1)), expected)

    def test_uploaded_html_vector_case(self):
        uploaded = (Path(__file__).parent / "fixtures" / "layer0_sample.bits").read_text(encoding="ascii").strip()
        self.assertEqual(decode(uploaded, layers=0), "print('Morbit is Cool')")

    def test_exact_case_preservation(self):
        samples = [
            "print('Morbit is cool')",
            "PRINT('MORBIT IS COOL')",
            "Print('Morbit Is Cool')",
            "aBc XYZ",
            "tabs\\tand\\nnewlines",
            "café — 雪 😀",
            "tilde ~ and hex-like ~41~",
        ]
        for sample in samples:
            for depth in range(3):
                with self.subTest(sample=sample, depth=depth):
                    self.assertEqual(decode(encode(sample, depth), depth), sample)

    def test_all_ascii_round_trip(self):
        sample = "".join(chr(code) for code in range(128))
        self.assertEqual(decode_one_layer(encode_one_layer(sample)), sample)
        self.assertEqual(len(MORBIT_MORSE), 128)

    def test_grouped_and_compact_decode_match(self):
        compact = encode("print('Morbit is cool')", 0)
        self.assertEqual(decode(format_bits(compact), 0), "print('Morbit is cool')")

    def test_bytes_round_trip(self):
        data = bytes(range(256))
        for depth in range(2):
            encoded = encode_bytes(data, depth)
            self.assertEqual(decode_bytes(encoded, depth), data)

    def test_text_file_round_trip(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, encoded, restored = root / "source.py", root / "source.morbit", root / "restored.py"
            original = "print('Morbit is cool')\r\n# café\n"
            source.write_bytes(original.encode("utf-8"))
            encode_file(source, encoded, layers=1)
            decode_file(encoded, restored, layers=1)
            self.assertEqual(restored.read_bytes().decode("utf-8"), original)

    def test_binary_file_round_trip(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, encoded, restored = root / "source.bin", root / "source.morbit", root / "restored.bin"
            data = bytes(range(256))
            source.write_bytes(data)
            encode_file(source, encoded, layers=0, binary=True)
            decode_file(encoded, restored, layers=0, binary=True)
            self.assertEqual(restored.read_bytes(), data)


    def test_protect_python_runtime_loader(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            script = root / "hello.py"
            script.write_text("print('Hello')\n", encoding="utf-8")
            protected_script, payload = protect_python(script, layers=1)
            self.assertEqual(protected_script, script.resolve())
            self.assertEqual(payload.name, "hello.py.lock.morbit")
            self.assertTrue(set(payload.read_text(encoding="ascii")) <= set("01"))
            env = os.environ.copy()
            source_root = str(Path(__file__).resolve().parents[1] / "src")
            env["PYTHONPATH"] = source_root + os.pathsep + env.get("PYTHONPATH", "")
            result = subprocess.run(
                [sys.executable, str(script)], capture_output=True, text=True, env=env, check=True
            )
            self.assertEqual(result.stdout, "Hello\n")

    def test_protect_python_backup(self):
        with tempfile.TemporaryDirectory() as temp:
            script = Path(temp) / "hello.py"
            original = "print('Hello')\n"
            script.write_text(original, encoding="utf-8")
            protect_python(script, layers=0, backup=True)
            self.assertEqual(script.with_name("hello.py.source.bak").read_text(encoding="utf-8"), original)

    def test_default_is_layer_one(self):
        sample = "x = 1 + 2"
        self.assertEqual(encode(sample), encode(sample, layers=1))
        self.assertEqual(decode(encode(sample)), sample)

    def test_rejects_invalid_layer_count(self):
        for invalid in (-1, 5, 99, 1.5, True):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    encode("A", invalid)
                with self.assertRaises(ValueError):
                    decode("0010111000101101", invalid)


if __name__ == "__main__":
    unittest.main()
