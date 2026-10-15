# Morbit

**Reversible, layered encoding and Python runtime protection.**

Morbit is a Python package that transforms text and source code into a binary-style bitstream using a custom, reversible Morse-inspired format. It includes encoding and decoding APIs, file operations, a command-line interface, and a Python runtime loader for protected scripts.

> **Security note:** Morbit is obfuscation, not cryptographic encryption. Because the format is reversible and code must be decoded to execute, a determined analyst may recover the source or inspect runtime behavior. Do not use it to protect secrets.

## Installation

```bash
python -m pip install morbit
```

Requires Python 3.10 or newer. The package has no runtime dependencies.

## Python API

```python
from morbit import encode, decode

source = "print('Hello')"
bits = encode(source)  # Layer 1 is the default
decoded = decode(bits)  # Uses the same default layer count

assert decoded == source
```

Choose an explicit layer when needed:

```python
bits = encode("x = 1 + 2", layers=2)
original = decode(bits, layers=2)
assert original == "x = 1 + 2"
```

## Layers

Morbit supports only layers `0` through `4`:

- **Layer 0:** Base encoding pass only. Select explicitly.
- **Layer 1:** Base encoding plus one additional pass. This is the default.
- **Layer 2:** Base encoding plus two additional passes.
- **Layer 3:** Base encoding plus three additional passes.
- **Layer 4:** Base encoding plus four additional passes.

Values below `0` or above `4` are rejected. Use the same layer count for encoding and decoding. Each additional layer makes the payload grow substantially, so use modest layer counts for larger inputs.

## File operations

For UTF-8 text files:

```python
from morbit import encode_file, decode_file

encode_file("source.py", "source.py.morbit", layers=1)
decode_file("source.py.morbit", "restored.py", layers=1)
```

To preserve arbitrary binary bytes, use binary mode on both operations:

```python
encode_file("archive.bin", "archive.bin.morbit", layers=1, binary=True)
decode_file("archive.bin.morbit", "restored.bin", layers=1, binary=True)
```

Binary mode uses a byte-preserving Latin-1 bridge. It is intended for arbitrary bytes and differs from passing decoded Unicode text to the HTML workbench.

## Command line

Show available commands:

```bash
morbit --help
```

Encode or decode text through standard input/output:

```bash
printf "print('Hello')" | morbit encode --layers 1
morbit decode --layers 1 --input output.morbit
```

Encode or decode files:

```bash
morbit encode-file source.py source.py.morbit --layers 2
morbit decode-file source.py.morbit restored.py --layers 2
```

## Protect and run a Python script

Morbit includes a Python runtime-loader workflow. It replaces a `.py` script with a small loader and writes the encoded source into a companion `.lock.morbit` payload file. The loader decodes the source in memory and executes it when the script is run.

Back up important files before protecting them. The original entry-point path is retained, but applications using unusual import patterns, relative paths, `__file__`, or self-inspection should be tested carefully.

```bash
# Install Morbit in the same environment that will run the protected script
python -m pip install morbit

# Create hello.py.lock.morbit and replace hello.py with the loader
morbit protect-python hello.py --layers 1

# Run the original entry point as usual
python hello.py
```

To preserve the source before replacement:

```bash
morbit protect-python hello.py --layers 1 --backup
```

This creates `hello.py.source.bak`. Keep the `hello.py.lock.morbit` payload next to the loader. The loader imports the installed `morbit` package at runtime.

**Current runtime support:** Python scripts only. JavaScript/Electron, Java, and native executable formats require separate runtime-specific implementations; they are not automatically supported by this Python loader.

## Format overview

Morbit uses a Morse-inspired character mapping and converts the resulting ASCII token string to eight-bit binary. Spaces map to `/`; lowercase letters use a reserved escape token and their uppercase Morse patterns; other unsupported characters use framed hexadecimal escapes. Additional layers repeat the transformation on the previous layer's bit string.

See [FORMAT_SPEC.md](FORMAT_SPEC.md) for the format details.

## Development and tests

```bash
python -m unittest discover -s tests -v
python -m build
python -m twine check dist/*
```

## Publishing

See [PUBLISHING.md](PUBLISHING.md) for the package-build and PyPI upload workflow. Never commit API tokens or other credentials to the repository.

## License

Morbit is released under the MIT License. See [LICENSE](LICENSE) for details.
