"""Generate a simplified Hangul-compatible TrueType font for the reporter."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import base64
import gzip
from pathlib import Path
from typing import Iterable, Sequence

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

BASE_FONT_PATH = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
PACKAGE_DIR = Path(__file__).resolve().parents[1] / "github_feedback" / "fonts"
OUTPUT_TTF_PATH = PACKAGE_DIR / "HangulSimplified-Regular.ttf"
OUTPUT_DATA_PATH = PACKAGE_DIR / "hangul_font_data.py"

CHO_LIST = [
    "ㄱ",
    "ㄲ",
    "ㄴ",
    "ㄷ",
    "ㄸ",
    "ㄹ",
    "ㅁ",
    "ㅂ",
    "ㅃ",
    "ㅅ",
    "ㅆ",
    "ㅇ",
    "ㅈ",
    "ㅉ",
    "ㅊ",
    "ㅋ",
    "ㅌ",
    "ㅍ",
    "ㅎ",
]

JUNG_LIST = [
    "ㅏ",
    "ㅐ",
    "ㅑ",
    "ㅒ",
    "ㅓ",
    "ㅔ",
    "ㅕ",
    "ㅖ",
    "ㅗ",
    "ㅘ",
    "ㅙ",
    "ㅚ",
    "ㅛ",
    "ㅜ",
    "ㅝ",
    "ㅞ",
    "ㅟ",
    "ㅠ",
    "ㅡ",
    "ㅢ",
    "ㅣ",
]

JONG_LIST = [
    "",
    "ㄱ",
    "ㄲ",
    "ㄳ",
    "ㄴ",
    "ㄵ",
    "ㄶ",
    "ㄷ",
    "ㄹ",
    "ㄺ",
    "ㄻ",
    "ㄼ",
    "ㄽ",
    "ㄾ",
    "ㄿ",
    "ㅀ",
    "ㅁ",
    "ㅂ",
    "ㅄ",
    "ㅅ",
    "ㅆ",
    "ㅇ",
    "ㅈ",
    "ㅊ",
    "ㅋ",
    "ㅌ",
    "ㅍ",
    "ㅎ",
]


@dataclass(frozen=True)
class Pattern:
    rows: Sequence[str]

    def merge(self, other: "Pattern") -> "Pattern":
        merged_rows: list[str] = []
        for a, b in zip(self.rows, other.rows):
            merged_rows.append("".join("1" if (ca == "1" or cb == "1") else "0" for ca, cb in zip(a, b)))
        return Pattern(tuple(merged_rows))


def _pattern(rows: Iterable[str]) -> Pattern:
    normalized = tuple(row.strip() for row in rows)
    if not normalized:
        raise ValueError("Pattern must contain at least one row")
    width = {len(row) for row in normalized}
    if len(width) != 1:
        raise ValueError("All rows must be the same length")
    return Pattern(normalized)


CHO_PATTERNS = {
    "ㄱ": _pattern([
        "1111111",
        "1000000",
        "1000000",
        "1000000",
        "1000000",
        "1000000",
        "1000000",
    ]),
    "ㄲ": _pattern([
        "1110111",
        "1100011",
        "1100011",
        "1100011",
        "1100011",
        "1100011",
        "1100011",
    ]),
    "ㄴ": _pattern([
        "1000000",
        "1000000",
        "1000000",
        "1000000",
        "1000000",
        "1000000",
        "1111111",
    ]),
    "ㄷ": _pattern([
        "1111111",
        "1000000",
        "1000000",
        "1111111",
        "1000000",
        "1000000",
        "1111111",
    ]),
    "ㄸ": _pattern([
        "1111111",
        "1100011",
        "1100011",
        "1111111",
        "1100011",
        "1100011",
        "1111111",
    ]),
    "ㄹ": _pattern([
        "1111111",
        "1000000",
        "1111111",
        "1000000",
        "1111111",
        "0000001",
        "1111111",
    ]),
    "ㅁ": _pattern([
        "1111111",
        "1000001",
        "1000001",
        "1000001",
        "1000001",
        "1000001",
        "1111111",
    ]),
    "ㅂ": _pattern([
        "1111111",
        "1000001",
        "1000001",
        "1111111",
        "1000001",
        "1000001",
        "1000001",
    ]),
    "ㅃ": _pattern([
        "1111111",
        "1100011",
        "1100011",
        "1111111",
        "1100011",
        "1100011",
        "1100011",
    ]),
    "ㅅ": _pattern([
        "0011100",
        "0110110",
        "1100011",
        "1000001",
        "1000001",
        "1000001",
        "1000001",
    ]),
    "ㅆ": _pattern([
        "0011100",
        "0110110",
        "1111111",
        "1000001",
        "1000001",
        "1000001",
        "1000001",
    ]),
    "ㅇ": _pattern([
        "0011100",
        "0110110",
        "1100011",
        "1100011",
        "1100011",
        "0110110",
        "0011100",
    ]),
    "ㅈ": _pattern([
        "0011100",
        "0110110",
        "1100011",
        "0011100",
        "0011100",
        "0011100",
        "0011100",
    ]),
    "ㅉ": _pattern([
        "0011100",
        "0110110",
        "1111111",
        "0011100",
        "0011100",
        "0011100",
        "0011100",
    ]),
    "ㅊ": _pattern([
        "0011100",
        "0110110",
        "1111111",
        "0011100",
        "0011100",
        "1100011",
        "1100011",
    ]),
    "ㅋ": _pattern([
        "1111111",
        "1000000",
        "1011100",
        "1010110",
        "1010011",
        "1000001",
        "1000001",
    ]),
    "ㅌ": _pattern([
        "1111111",
        "0011100",
        "0011100",
        "0011100",
        "0011100",
        "0011100",
        "1111111",
    ]),
    "ㅍ": _pattern([
        "1111111",
        "1000001",
        "1111111",
        "1000001",
        "1111111",
        "1000001",
        "1000001",
    ]),
    "ㅎ": _pattern([
        "1111111",
        "1000001",
        "1111111",
        "0011100",
        "0011100",
        "0011100",
        "1111111",
    ]),
}


JUNG_PATTERNS = {
    "ㅏ": _pattern([
        "0000100",
        "0000100",
        "0000100",
        "1111111",
        "0000100",
        "0000100",
        "0000100",
    ]),
    "ㅐ": _pattern([
        "0001100",
        "0001100",
        "0001100",
        "1111111",
        "0001100",
        "0001100",
        "0001100",
    ]),
    "ㅑ": _pattern([
        "0000100",
        "0000100",
        "1111111",
        "0000100",
        "1111111",
        "0000100",
        "0000100",
    ]),
    "ㅒ": _pattern([
        "0001100",
        "0001100",
        "1111111",
        "0001100",
        "1111111",
        "0001100",
        "0001100",
    ]),
    "ㅓ": _pattern([
        "0010000",
        "0010000",
        "0010000",
        "1111111",
        "0010000",
        "0010000",
        "0010000",
    ]),
    "ㅔ": _pattern([
        "0011000",
        "0011000",
        "0011000",
        "1111111",
        "0011000",
        "0011000",
        "0011000",
    ]),
    "ㅕ": _pattern([
        "0010000",
        "0010000",
        "1111111",
        "0010000",
        "1111111",
        "0010000",
        "0010000",
    ]),
    "ㅖ": _pattern([
        "0011000",
        "0011000",
        "1111111",
        "0011000",
        "1111111",
        "0011000",
        "0011000",
    ]),
    "ㅗ": _pattern([
        "0000000",
        "1111111",
        "0000000",
        "0000000",
        "0000000",
        "0000000",
        "1111111",
    ]),
    "ㅘ": _pattern([
        "0000000",
        "1111111",
        "0000100",
        "1111111",
        "0000100",
        "0000100",
        "1111111",
    ]),
    "ㅙ": _pattern([
        "0000000",
        "1111111",
        "0001100",
        "1111111",
        "0001100",
        "0001100",
        "1111111",
    ]),
    "ㅚ": _pattern([
        "0000000",
        "1111111",
        "0000100",
        "0000100",
        "0000100",
        "0000100",
        "1111111",
    ]),
    "ㅛ": _pattern([
        "0000000",
        "1111111",
        "0000000",
        "1111111",
        "0000000",
        "1111111",
        "0000000",
    ]),
    "ㅜ": _pattern([
        "1111111",
        "0000000",
        "0000000",
        "0000000",
        "0000000",
        "1111111",
        "0000000",
    ]),
    "ㅝ": _pattern([
        "1111111",
        "0000000",
        "0010000",
        "1111111",
        "0010000",
        "0010000",
        "1111111",
    ]),
    "ㅞ": _pattern([
        "1111111",
        "0000000",
        "0011000",
        "1111111",
        "0011000",
        "0011000",
        "1111111",
    ]),
    "ㅟ": _pattern([
        "1111111",
        "0000000",
        "0011000",
        "0011000",
        "0011000",
        "0011000",
        "1111111",
    ]),
    "ㅠ": _pattern([
        "1111111",
        "0000000",
        "1111111",
        "0000000",
        "1111111",
        "0000000",
        "1111111",
    ]),
    "ㅡ": _pattern([
        "0000000",
        "0000000",
        "0000000",
        "1111111",
        "0000000",
        "0000000",
        "0000000",
    ]),
    "ㅢ": _pattern([
        "1111111",
        "0000000",
        "0000100",
        "1111111",
        "0000100",
        "0000100",
        "0000100",
    ]),
    "ㅣ": _pattern([
        "0000100",
        "0000100",
        "0000100",
        "0000100",
        "0000100",
        "0000100",
        "0000100",
    ]),
}

JUNG_HORIZONTAL = {"ㅗ", "ㅘ", "ㅙ", "ㅚ", "ㅛ", "ㅜ", "ㅝ", "ㅞ", "ㅟ", "ㅠ", "ㅡ"}

JONG_BASE_PATTERNS = {
    "ㄱ": _pattern([
        "1111111",
        "1000000",
        "1000000",
        "1000000",
        "1000000",
    ]),
    "ㄴ": _pattern([
        "1000000",
        "1000000",
        "1000000",
        "1000000",
        "1111111",
    ]),
    "ㄷ": _pattern([
        "1111111",
        "1000000",
        "1000000",
        "1000000",
        "1111111",
    ]),
    "ㄹ": _pattern([
        "1111111",
        "1000000",
        "1111111",
        "0000001",
        "1111111",
    ]),
    "ㅁ": _pattern([
        "1111111",
        "1000001",
        "1000001",
        "1000001",
        "1111111",
    ]),
    "ㅂ": _pattern([
        "1111111",
        "1000001",
        "1111111",
        "1000001",
        "1000001",
    ]),
    "ㅅ": _pattern([
        "0011100",
        "0110110",
        "1100011",
        "1000001",
        "1000001",
    ]),
    "ㅇ": _pattern([
        "0011100",
        "0110110",
        "1100011",
        "0110110",
        "0011100",
    ]),
    "ㅈ": _pattern([
        "0011100",
        "0110110",
        "1100011",
        "0011100",
        "0011100",
    ]),
    "ㅊ": _pattern([
        "0011100",
        "0110110",
        "1111111",
        "1100011",
        "1100011",
    ]),
    "ㅋ": _pattern([
        "1111111",
        "1000000",
        "1011100",
        "1000011",
        "1000001",
    ]),
    "ㅌ": _pattern([
        "1111111",
        "0011100",
        "0011100",
        "0011100",
        "1111111",
    ]),
    "ㅍ": _pattern([
        "1111111",
        "1000001",
        "1111111",
        "1000001",
        "1000001",
    ]),
    "ㅎ": _pattern([
        "1111111",
        "1000001",
        "1111111",
        "0011100",
        "1111111",
    ]),
}

JONG_PATTERN_CACHE: dict[str, Pattern] = {}


def get_jong_pattern(symbol: str) -> Pattern:
    if symbol in JONG_PATTERN_CACHE:
        return JONG_PATTERN_CACHE[symbol]
    if symbol in JONG_BASE_PATTERNS:
        pattern = JONG_BASE_PATTERNS[symbol]
    elif symbol == "ㄲ":
        base = JONG_BASE_PATTERNS["ㄱ"]
        pattern = base.merge(base)
    elif symbol == "ㅆ":
        base = JONG_BASE_PATTERNS["ㅅ"]
        pattern = base.merge(base)
    elif symbol == "ㄳ":
        pattern = JONG_BASE_PATTERNS["ㄱ"].merge(JONG_BASE_PATTERNS["ㅅ"])
    elif symbol == "ㄵ":
        pattern = JONG_BASE_PATTERNS["ㄴ"].merge(JONG_BASE_PATTERNS["ㅈ"])
    elif symbol == "ㄶ":
        pattern = JONG_BASE_PATTERNS["ㄴ"].merge(JONG_BASE_PATTERNS["ㅎ"])
    elif symbol == "ㄺ":
        pattern = JONG_BASE_PATTERNS["ㄹ"].merge(JONG_BASE_PATTERNS["ㄱ"])
    elif symbol == "ㄻ":
        pattern = JONG_BASE_PATTERNS["ㄹ"].merge(JONG_BASE_PATTERNS["ㅁ"])
    elif symbol == "ㄼ":
        pattern = JONG_BASE_PATTERNS["ㄹ"].merge(JONG_BASE_PATTERNS["ㅂ"])
    elif symbol == "ㄽ":
        pattern = JONG_BASE_PATTERNS["ㄹ"].merge(JONG_BASE_PATTERNS["ㅅ"])
    elif symbol == "ㄾ":
        pattern = JONG_BASE_PATTERNS["ㄹ"].merge(JONG_BASE_PATTERNS["ㅌ"])
    elif symbol == "ㄿ":
        pattern = JONG_BASE_PATTERNS["ㄹ"].merge(JONG_BASE_PATTERNS["ㅍ"])
    elif symbol == "ㅀ":
        pattern = JONG_BASE_PATTERNS["ㄹ"].merge(JONG_BASE_PATTERNS["ㅎ"])
    elif symbol == "ㅄ":
        pattern = JONG_BASE_PATTERNS["ㅂ"].merge(JONG_BASE_PATTERNS["ㅅ"])
    else:
        raise KeyError(f"Unsupported final jamo: {symbol}")
    JONG_PATTERN_CACHE[symbol] = pattern
    return pattern


CELL_PADDING = 0.08
UNITS_PER_EM = 1000


def draw_rect(pen: TTGlyphPen, x0: float, y0: float, x1: float, y1: float) -> None:
    pen.moveTo((x0, y0))
    pen.lineTo((x1, y0))
    pen.lineTo((x1, y1))
    pen.lineTo((x0, y1))
    pen.closePath()


def render_pattern(pen: TTGlyphPen, pattern: Pattern, box: tuple[float, float, float, float]) -> None:
    rows = len(pattern.rows)
    cols = len(pattern.rows[0])
    x0, y0, x1, y1 = box
    cell_w = (x1 - x0) / cols
    cell_h = (y1 - y0) / rows
    pad_w = cell_w * CELL_PADDING
    pad_h = cell_h * CELL_PADDING

    for row_index, row in enumerate(pattern.rows):
        for col_index, value in enumerate(row):
            if value != "1":
                continue
            cell_x0 = x0 + col_index * cell_w + pad_w
            cell_y0 = y0 + (rows - row_index - 1) * cell_h + pad_h
            cell_x1 = x0 + (col_index + 1) * cell_w - pad_w
            cell_y1 = y0 + (rows - row_index) * cell_h - pad_h
            draw_rect(pen, cell_x0, cell_y0, cell_x1, cell_y1)


def syllable_glyph(char: str) -> tuple[object, tuple[int, int]]:
    code = ord(char) - 0xAC00
    cho_index = code // 588
    jung_index = (code % 588) // 28
    jong_index = code % 28

    initial = CHO_PATTERNS[CHO_LIST[cho_index]]
    vowel = JUNG_PATTERNS[JUNG_LIST[jung_index]]

    pen = TTGlyphPen(None)

    has_final = jong_index != 0
    top_body = 950 if has_final else 980

    if JUNG_LIST[jung_index] in JUNG_HORIZONTAL:
        initial_box = (60, top_body - 250, UNITS_PER_EM - 60, top_body)
        vowel_box = (60, 250 if has_final else 80, UNITS_PER_EM - 60, top_body - 280)
    else:
        initial_box = (60, top_body - 300, 500, top_body)
        vowel_box = (500, 250 if has_final else 80, UNITS_PER_EM - 60, top_body)

    render_pattern(pen, initial, initial_box)
    render_pattern(pen, vowel, vowel_box)

    if has_final:
        final_symbol = JONG_LIST[jong_index]
        final_pattern = get_jong_pattern(final_symbol)
        final_box = (60, 40, UNITS_PER_EM - 60, 220)
        render_pattern(pen, final_pattern, final_box)

    glyph = pen.glyph()
    glyph.xMin = 0
    glyph.yMin = 0
    glyph.xMax = UNITS_PER_EM
    glyph.yMax = UNITS_PER_EM
    return glyph, (UNITS_PER_EM, 0)


def build_font() -> None:
    base_font = TTFont(str(BASE_FONT_PATH))
    base_cmap = base_font.getBestCmap()
    glyph_order: list[str] = [".notdef"]
    cmap: dict[int, str] = {}
    glyf_table = {".notdef": deepcopy(base_font["glyf"][".notdef"])}
    metrics = {".notdef": base_font["hmtx"][".notdef"]}

    ascii_codes = list(range(32, 127))
    used_glyphs: set[str] = set(glyph_order)

    for codepoint in ascii_codes:
        glyph_name = base_cmap.get(codepoint)
        if not glyph_name or glyph_name in used_glyphs:
            cmap[codepoint] = glyph_name or ".notdef"
            continue
        glyph_order.append(glyph_name)
        used_glyphs.add(glyph_name)
        glyf_table[glyph_name] = deepcopy(base_font["glyf"][glyph_name])
        metrics[glyph_name] = base_font["hmtx"][glyph_name]
        cmap[codepoint] = glyph_name

    for codepoint in range(0xAC00, 0xD7A4):
        char = chr(codepoint)
        glyph_name = f"uni{codepoint:04X}"
        glyph, metric = syllable_glyph(char)
        glyph_order.append(glyph_name)
        glyf_table[glyph_name] = glyph
        metrics[glyph_name] = metric
        cmap[codepoint] = glyph_name

    fb = FontBuilder(UNITS_PER_EM, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyf_table)
    fb.setupHorizontalMetrics(metrics)

    hhea = base_font["hhea"]
    advance_width_max = max(width for width, _ in metrics.values())
    min_left_side_bearing = min(lsb for _, lsb in metrics.values())
    min_right_side_bearing = min(
        width - glyf_table[name].xMax if hasattr(glyf_table[name], "xMax") else width
        for name, (width, _) in metrics.items()
    )
    x_max_extent = max(
        glyf_table[name].xMax if hasattr(glyf_table[name], "xMax") else 0
        for name in glyph_order
    )

    fb.setupHorizontalHeader(
        ascent=hhea.ascent,
        descent=hhea.descent,
        lineGap=hhea.lineGap,
        advanceWidthMax=advance_width_max,
        minLeftSideBearing=min_left_side_bearing,
        minRightSideBearing=min_right_side_bearing,
        xMaxExtent=x_max_extent,
        caretSlopeRise=hhea.caretSlopeRise,
        caretSlopeRun=hhea.caretSlopeRun,
        caretOffset=hhea.caretOffset,
        reserved0=hhea.reserved0,
        reserved1=hhea.reserved1,
        reserved2=hhea.reserved2,
        reserved3=hhea.reserved3,
        metricDataFormat=hhea.metricDataFormat,
        numberOfHMetrics=len(metrics),
    )

    os2 = base_font["OS/2"]
    fb.setupOS2(
        version=os2.version,
        xAvgCharWidth=os2.xAvgCharWidth,
        usWeightClass=os2.usWeightClass,
        usWidthClass=os2.usWidthClass,
        fsType=os2.fsType,
        ySubscriptXSize=os2.ySubscriptXSize,
        ySubscriptYSize=os2.ySubscriptYSize,
        ySubscriptXOffset=os2.ySubscriptXOffset,
        ySubscriptYOffset=os2.ySubscriptYOffset,
        ySuperscriptXSize=os2.ySuperscriptXSize,
        ySuperscriptYSize=os2.ySuperscriptYSize,
        ySuperscriptXOffset=os2.ySuperscriptXOffset,
        ySuperscriptYOffset=os2.ySuperscriptYOffset,
        yStrikeoutSize=os2.yStrikeoutSize,
        yStrikeoutPosition=os2.yStrikeoutPosition,
        sFamilyClass=os2.sFamilyClass,
        panose=os2.panose,
        ulUnicodeRange1=os2.ulUnicodeRange1,
        ulUnicodeRange2=os2.ulUnicodeRange2,
        ulUnicodeRange3=os2.ulUnicodeRange3,
        ulUnicodeRange4=os2.ulUnicodeRange4,
        achVendID=os2.achVendID,
        fsSelection=os2.fsSelection,
        usFirstCharIndex=min(cmap.keys()),
        usLastCharIndex=max(cmap.keys()),
        sTypoAscender=os2.sTypoAscender,
        sTypoDescender=os2.sTypoDescender,
        sTypoLineGap=os2.sTypoLineGap,
        usWinAscent=os2.usWinAscent,
        usWinDescent=os2.usWinDescent,
        ulCodePageRange1=os2.ulCodePageRange1,
        ulCodePageRange2=os2.ulCodePageRange2,
    )

    fb.setupNameTable(
        {
            "familyName": "Hangul Simplified",
            "styleName": "Regular",
            "uniqueFontIdentifier": "HangulSimplified Regular",
            "fullName": "Hangul Simplified Regular",
            "psName": "HangulSimplified-Regular",
            "manufacturer": "GitHub Feedback",
            "designer": "GitHub Feedback",
        }
    )

    fb.setupPost()
    fb.setupMaxp()

    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
    fb.save(str(OUTPUT_TTF_PATH))
    print(f"Saved font to {OUTPUT_TTF_PATH}")

    compressed = gzip.compress(OUTPUT_TTF_PATH.read_bytes(), compresslevel=9)
    encoded = base64.b64encode(compressed).decode("ascii")
    lines = "\n".join(
        encoded[index : index + 80] for index in range(0, len(encoded), 80)
    )
    OUTPUT_DATA_PATH.write_text(
        "# Auto-generated font payload\n"
        "FONT_BASE64 = '''\n"
        f"{lines}\n"
        "'''\n",
        encoding="utf-8",
    )
    print(f"Updated compressed font payload at {OUTPUT_DATA_PATH}")


if __name__ == "__main__":
    build_font()
