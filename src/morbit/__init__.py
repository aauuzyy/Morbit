"""Morbit: HTML-compatible, reversible Morbit Morse encoding."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Union

__version__ = "1.1.1"

MORSE = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".", "F": "..-.",
    "G": "--.", "H": "....", "I": "..", "J": ".---", "K": "-.-", "L": ".-..",
    "M": "--", "N": "-.", "O": "---", "P": ".--.", "Q": "--.-", "R": ".-.",
    "S": "...", "T": "-", "U": "..-", "V": "...-", "W": ".--", "X": "-..-",
    "Y": "-.--", "Z": "--..",
    "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-",
    "5": ".....", "6": "-....", "7": "--...", "8": "---..", "9": "----.",
    ".": ".-.-.-", ",": "--..--", "?": "..--..", "'": ".----.", "!": "-.-.--",
    "/": "-..-.", "(": "-.--.", ")": "-.--.-", "&": ".-...", ":": "---...",
    ";": "-.-.-.", "=": "-...-", "+": ".-.-.", "-": "-....-", "_": "..--.-",
    '"': ".-..-.", "$": "...-..-", "@": ".--.-.",
}
MORSE_REVERSE = {value: key for key, value in MORSE.items()}
ESCAPE_TOKEN = "...---..."
# The HTML builds the 128-entry table from this exact character rule.
def morse_tokens_for_char(char: str) -> list[str]:
    if char == " ":
        return ["/"]
    if len(char) == 1 and "a" <= char <= "z":
        return [ESCAPE_TOKEN, MORSE[char.upper()], "/"]
    if len(char) == 1 and char == char.upper() and char in MORSE:
        return [MORSE[char]]
    hex_code = format(ord(char), "X")
    return [ESCAPE_TOKEN, *(MORSE[digit] for digit in hex_code), ESCAPE_TOKEN]


MORBIT_MORSE = {
    chr(code): " ".join(morse_tokens_for_char(chr(code)))
    for code in range(128)
}


def tokens_for_text(text: str) -> list[str]:
    tokens: list[str] = []
    for char in text:
        tokens.extend(MORBIT_MORSE[char].split(" ") if char in MORBIT_MORSE
                      else morse_tokens_for_char(char))
    return tokens


def ascii_to_bits(text: str) -> str:
    """Encode each ASCII character as its eight-bit binary representation."""
    try:
        raw = text.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("Morbit's Morse layer must contain ASCII characters.") from exc
    return "".join(f"{byte:08b}" for byte in raw)


def bits_to_ascii(bits: str) -> str:
    if not bits or re.search(r"[^01]", bits):
        raise ValueError("Morbit input must contain only 0s and 1s.")
    if len(bits) % 8:
        raise ValueError(
            f"Bit count ({len(bits)}) is not divisible by 8. Check the pasted output."
        )
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8)).decode("ascii")


def encode_one_layer(text: str) -> str:
    """Apply exactly one HTML-compatible source-to-Morbit-Morse-to-binary pass."""
    morse_text = " ".join(tokens_for_text(text))
    return ascii_to_bits(morse_text)


def decode_one_layer(bits: str) -> str:
    """Reverse exactly one HTML-compatible binary/Morbit-Morse pass."""
    morse_text = bits_to_ascii(bits)
    tokens = [token for token in morse_text.split(" ") if token]
    decoded: list[str] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token == ESCAPE_TOKEN:
            next_token = tokens[i + 1] if i + 1 < len(tokens) else None
            next_next = tokens[i + 2] if i + 2 < len(tokens) else None
            if (
                next_token in MORSE_REVERSE
                and next_next == "/"
                and len(MORSE_REVERSE[next_token]) == 1
                and "A" <= MORSE_REVERSE[next_token] <= "Z"
            ):
                decoded.append(MORSE_REVERSE[next_token].lower())
                i += 3
                continue
            decoded.append("~")
        elif token == "/":
            decoded.append(" ")
        elif token in MORSE_REVERSE:
            decoded.append(MORSE_REVERSE[token])
        else:
            raise ValueError(
                f"Unknown Morse token {token!r}. Check the layer count and input."
            )
        i += 1

    intermediate = "".join(decoded)

    def replace_escape(match: re.Match[str]) -> str:
        try:
            point = int(match.group(1), 16)
            if not 0 <= point <= 0x10FFFF:
                raise ValueError
            return chr(point)
        except ValueError as exc:
            raise ValueError("The Morbit escape contains an invalid code point.") from exc

    return re.sub(r"~([0-9A-F]+)~", replace_escape, intermediate)


def encode(text: str, layers: int = 1, *, grouped: bool = False) -> str:
    """Encode text exactly like the Morbit HTML.

    Layer 0 is source text -> Morbit Morse tokens -> ASCII binary.
    Each additional layer repeats that same transformation on the previous
    layer's binary string. Thus ``layers=0`` returns Layer 0 and ``layers=1``
    returns Layer 1, matching the website's layer selector.
    """
    _validate_layers(layers)
    if not isinstance(text, str):
        raise TypeError("text must be str")
    if not text:
        raise ValueError("Paste some code or text first.")
    result = encode_one_layer(text)
    for _ in range(layers):
        result = encode_one_layer(result)
    return format_bits(result) if grouped else result


def decode(value: str, layers: int = 1) -> str:
    """Decode compact or whitespace-grouped Morbit bits to the original text."""
    _validate_layers(layers)
    if not isinstance(value, str):
        raise TypeError("value must be str")
    bits = "".join(value.split())
    if not bits:
        raise ValueError("Paste a Morbit bit string first.")
    if re.search(r"[^01]", bits):
        raise ValueError("Morbit output should contain only 0s and 1s (spaces are allowed between bytes).")
    if len(bits) % 8:
        raise ValueError(
            f"Bit count ({len(bits)}) is not divisible by 8. Remove any non-binary characters and check the output."
        )
    result = bits
    for _ in range(layers + 1):
        result = decode_one_layer(result)
    return result


def format_bits(bits: str) -> str:
    """Group a bit string into eight-bit bytes, like the HTML readable format."""
    if re.search(r"[^01]", bits):
        raise ValueError("bits must contain only 0s and 1s")
    return " ".join(bits[i:i + 8] for i in range(0, len(bits), 8))


def encode_bytes(data: bytes, layers: int = 1, *, grouped: bool = False) -> str:
    """Encode arbitrary bytes reversibly using a byte-preserving Latin-1 bridge.

    This is for binary files. Text passed to ``encode`` uses Unicode code points
    and is exactly compatible with the website; this helper instead maps each
    byte 0..255 to the same-valued Unicode code point before encoding.
    """
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("data must be bytes-like")
    return encode(bytes(data).decode("latin-1"), layers, grouped=grouped)


def decode_bytes(value: str, layers: int = 1) -> bytes:
    """Reverse ``encode_bytes`` and return the original arbitrary bytes."""
    return decode(value, layers).encode("latin-1")


def encode_file(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    layers: int = 1,
    *,
    grouped: bool = False,
    binary: bool = False,
) -> str:
    """Encode a file. Text mode matches the website; binary mode preserves bytes.

    Returns the encoded bit string (also written to output_path).
    """
    source = Path(input_path)
    destination = Path(output_path)
    if binary:
        result = encode_bytes(source.read_bytes(), layers, grouped=grouped)
    else:
        # Decode bytes directly to avoid universal-newline conversion (CRLF must survive).
        result = encode(source.read_bytes().decode("utf-8"), layers, grouped=grouped)
    destination.write_bytes(result.encode("ascii"))
    return result


def decode_file(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    layers: int = 1,
    *,
    binary: bool = False,
) -> str:
    """Decode a Morbit file. Set binary=True for data encoded with encode_bytes."""
    source = Path(input_path)
    destination = Path(output_path)
    encoded = source.read_bytes().decode("ascii")
    if binary:
        destination.write_bytes(decode_bytes(encoded, layers))
        return str(destination)
    result = decode(encoded, layers)
    destination.write_bytes(result.encode("utf-8"))
    return result



def protect_python(
    script_path: Union[str, Path],
    layers: int = 1,
    *,
    backup: bool = False,
) -> tuple[Path, Path]:
    """Replace a Python script with a runtime loader and a Morbit payload.

    The original filename remains executable; its encoded source is stored as
    ``<script>.lock.morbit``. The generated loader requires this package in the
    Python environment used to run the script. ``backup=True`` preserves the
    original source as ``<script>.source.bak``. This is obfuscation, not encryption.
    """
    import os

    _validate_layers(layers)
    script = Path(script_path).resolve()
    if not script.is_file():
        raise FileNotFoundError(f"Python script not found: {script}")
    if script.suffix.lower() != ".py":
        raise ValueError("protect-python expects a .py source file")

    original = script.read_bytes()
    source_text = original.decode("utf-8-sig")
    payload = script.with_name(script.name + ".lock.morbit")
    backup_path = script.with_name(script.name + ".source.bak")
    if payload.exists():
        raise FileExistsError(f"Morbit payload already exists: {payload}")
    if backup and backup_path.exists():
        raise FileExistsError(f"Source backup already exists: {backup_path}")

    encoded = encode(source_text, layers=layers)
    shebang = source_text.splitlines()[0] if source_text.startswith("#!") and source_text.splitlines() else None
    loader_lines = ([shebang] if shebang else []) + [
        f"# Generated by Morbit {__version__}.",
        "from pathlib import Path as _MorbitPath",
        "from morbit import decode as _morbit_decode",
        "_MORBIT_SCRIPT = _MorbitPath(__file__).resolve()",
        '_MORBIT_PAYLOAD = _MORBIT_SCRIPT.with_name(_MORBIT_SCRIPT.name + ".lock.morbit")',
        f"_MORBIT_LAYERS = {layers}",
        '_MORBIT_BITS = _MORBIT_PAYLOAD.read_text(encoding="ascii")',
        "_MORBIT_SOURCE = _morbit_decode(_MORBIT_BITS, layers=_MORBIT_LAYERS)",
        "# Execute in this module's globals to preserve normal script semantics.",
        'exec(compile(_MORBIT_SOURCE, str(_MORBIT_SCRIPT), "exec"), globals(), globals())',
        "",
    ]
    loader = "\n".join(loader_lines)
    payload_tmp = payload.with_name(payload.name + ".tmp")
    loader_tmp = script.with_name(script.name + ".morbit-tmp")
    try:
        with open(payload_tmp, "w", encoding="ascii", newline="") as fh:
            fh.write(encoded)
        with open(loader_tmp, "w", encoding="utf-8", newline="") as fh:
            fh.write(loader)
        os.chmod(loader_tmp, script.stat().st_mode)
        if backup:
            backup_path.write_bytes(original)
        os.replace(payload_tmp, payload)
        try:
            os.replace(loader_tmp, script)
        except Exception:
            payload.unlink(missing_ok=True)
            raise
    finally:
        payload_tmp.unlink(missing_ok=True)
        loader_tmp.unlink(missing_ok=True)
    return script, payload

def _validate_layers(layers: int) -> None:
    if isinstance(layers, bool) or not isinstance(layers, int) or not 0 <= layers <= 4:
        raise ValueError("layers must be an integer from 0 to 4 (Layer 1 is the default)")


__all__ = [
    "ESCAPE_TOKEN", "MORSE", "MORSE_REVERSE", "MORBIT_MORSE", "__version__",
    "ascii_to_bits", "bits_to_ascii", "decode", "decode_bytes", "decode_file",
    "decode_one_layer", "encode", "encode_bytes", "encode_file",
    "encode_one_layer", "format_bits", "morse_tokens_for_char", "tokens_for_text",
    "protect_python",
]
