"""Command-line interface for Morbit."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, decode, decode_file, encode, encode_file, protect_python


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="morbit",
        description="HTML-compatible Morbit Morse encoder and decoder.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    enc = sub.add_parser("encode", help="encode text from stdin or --input")
    enc.add_argument("--layers", type=int, default=1, help="layer selection 0-4 (default: 1; maximum: 4)")
    enc.add_argument("--grouped", action="store_true", help="separate output into 8-bit groups")
    enc.add_argument("--input", help="UTF-8 text file; otherwise read stdin")

    dec = sub.add_parser("decode", help="decode Morbit bits from stdin or --input")
    dec.add_argument("--layers", type=int, default=1, help="same layer selection used to encode (0-4)")
    dec.add_argument("--input", help="encoded text file; otherwise read stdin")

    ef = sub.add_parser("encode-file", help="encode a file to a Morbit bitstream")
    ef.add_argument("input")
    ef.add_argument("output")
    ef.add_argument("--layers", type=int, default=1)
    ef.add_argument("--grouped", action="store_true")
    ef.add_argument("--binary", action="store_true", help="preserve arbitrary bytes; not Unicode-text mode")

    df = sub.add_parser("decode-file", help="decode a Morbit bitstream to a file")
    df.add_argument("input")
    df.add_argument("output")
    df.add_argument("--layers", type=int, default=1)
    df.add_argument("--binary", action="store_true", help="restore arbitrary bytes encoded with --binary")

    pp = sub.add_parser(
        "protect-python",
        help="replace a .py script with a runtime loader and create a .lock.morbit payload",
    )
    pp.add_argument("script", help="Python source script to protect in place")
    pp.add_argument("--layers", type=int, default=1, help="layer selection 0-4 (default: 1; maximum: 4)")
    pp.add_argument("--backup", action="store_true", help="preserve original source as .source.bak")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "encode":
            text = Path(args.input).read_bytes().decode("utf-8") if args.input else sys.stdin.read()
            print(encode(text, args.layers, grouped=args.grouped), end="")
        elif args.command == "decode":
            value = Path(args.input).read_bytes().decode("ascii") if args.input else sys.stdin.read()
            print(decode(value, args.layers), end="")
        elif args.command == "encode-file":
            encode_file(args.input, args.output, args.layers, grouped=args.grouped, binary=args.binary)
        elif args.command == "decode-file":
            decode_file(args.input, args.output, args.layers, binary=args.binary)
        elif args.command == "protect-python":
            script, payload = protect_python(args.script, args.layers, backup=args.backup)
            print(f"Protected script: {script}")
            print(f"Morbit payload:   {payload}")
            print("Run the original script path normally with Python.")
            print("Note: install morbit in the runtime environment first.")
        return 0
    except (ValueError, TypeError, OSError) as exc:
        print(f"morbit: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
