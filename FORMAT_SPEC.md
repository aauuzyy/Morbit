# Morbit encoding format reference

This specification mirrors the implementation in the site's `index.html`.

## Character-to-token conversion

Tokens are joined by a single ASCII space before the resulting Morse text is converted to ASCII bytes and then to eight-bit binary.

- ` ` (space) becomes `/`.
- `a` through `z` become `...---...`, the Morse token for the corresponding uppercase letter, then `/`.
- Uppercase A–Z, digits, and the explicitly mapped punctuation use their direct Morse token.
- Any other character becomes `...---...`, each hexadecimal digit of its Unicode code point encoded with the digit's Morse token, then `...---...`.
- The hexadecimal representation uses uppercase digits and no leading zeroes.

The reserved escape token is `...---...`. The digit tokens are `0` → `-----`, `1` → `.----`, `2` → `..---`, `3` → `...--`, `4` → `....-`, `5` → `.....`, `6` → `-....`, `7` → `--...`, `8` → `---..`, and `9` → `----.`.

## Binary representation and layers

Each character of the joined Morse-token text is ASCII-encoded as exactly eight bits.

- Layer 0: source text → Morbit Morse tokens → ASCII binary.
- Layer N (N = 1–4): apply the same complete conversion to the preceding layer's bit string N additional times. Layer 1 is the default; Layer 0 must be selected explicitly.
- Decode reverses N additional layers and then the base Layer 0 conversion.
- Optional spaces/newlines between bits are ignored by the decoder. Bits themselves must form complete eight-bit bytes.

Only layers 0 through 4 are valid. The default is Layer 1. This is obfuscation, not cryptographic encryption.
