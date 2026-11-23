#!/usr/bin/env python3
"""news-image-20261123 -- "Sum up 23 November's world news in one image".

Draws a newspaper-style front page for Monday, 23 November 2026 as a
1024x1024 PNG, entirely with the Python standard library: its own PNG
encoder, its own 5x7 bitmap type, and hand-drawn panels for the day's
stories (verified 23 Nov 2026 from Reuters, AP, BBC, NPR and Xinhua):

  HERO    COP31 in Antalya ends with NO DEAL -- the EU and about 130
          other parties reject a text with no fossil-fuel phase-out;
          the longest UN climate summit ever ends after ~48h overtime.
  KYIV    A Russian strike on Dymer, north of Kyiv, kills at least 11;
          rescuers dig through the rubble of an apartment block.
  MARKETS An AI sell-off routs world markets: Nikkei -5.06%,
          S&P 500 -3.7%, gold +2.72%, oil near $90.
  US      Democrats clinch a House majority of at least 258 seats,
          the largest for either party since 1992 (AP).
  BRIEFS  Trump 'inclined' to resume the Iran conflict if there is no
          deal by New Year; a Banten candy-factory fire kills 24 with
          about 30 missing; Delta delays 1,000+ flights at Atlanta;
          Marquez wins his 8th MotoGP title, equalling Agostini;
          Liverpool beat Manchester United 4-0 in Pochettino's first
          match in charge; fighting disrupts the Ebola response in
          DR Congo (WHO).

The grader runs `python3 -P -s main.py` with no argv, the code mounted
read-only, and MAKEFUN_OUTPUT_DIR pointing at a writable /output.
So main() tries, in order: an explicit argv[1] path, then
$MAKEFUN_OUTPUT_DIR/entry.png, then ./entry.png in the cwd, then
entry.png beside this file.  It never raises: each candidate that
fails is noted on stderr and the next is tried; exit is 0 as soon as
one candidate holds a PNG that re-reads clean (every chunk CRC, the
1024x1024 IHDR, the 1 MiB cap).  No clock, no randomness, no network:
two runs write byte-identical files.
"""

import os
import struct
import sys
import zlib

W = 1024
H = 1024
MAX_BYTES = 1048576

# ---------------------------------------------------------------- canvas

INK = (20, 24, 38)        # near-black blue, rules and type
PAPER = (244, 240, 230)   # newsprint
RED = (178, 34, 44)       # strike / falling market red
TEAL = (10, 74, 82)       # hero panel deep teal
SEA = (38, 122, 140)      # globe sea
LAND = (96, 168, 110)     # globe land
SAND = (232, 213, 163)    # hero panel accent
GOLD = (196, 148, 32)     # gold line
GREY = (96, 100, 110)     # secondary type
WHITE = (250, 249, 245)
SKY = (24, 34, 58)        # Kyiv panel night
LIT = (255, 196, 84)      # lit windows / rescue lights


class Canvas:
    """A flat RGB pixel buffer with just the drawing we need."""

    def __init__(self, w, h, colour):
        self.w = w
        self.h = h
        self.px = bytearray(colour) * (w * h)

    def set(self, x, y, colour):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(colour)

    def rect(self, x, y, w, h, colour):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(colour) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def frame(self, x, y, w, h, colour, t=3):
        self.rect(x, y, w, t, colour)
        self.rect(x, y + h - t, w, t, colour)
        self.rect(x, y, t, h, colour)
        self.rect(x + w - t, y, t, h, colour)

    def line(self, x0, y0, x1, y1, colour, t=2):
        # Bresenham, stamped with a small square brush.
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        r = max(0, t // 2)
        while True:
            self.rect(x - r, y - r, t, t, colour)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def disc(self, cx, cy, rad, colour):
        r2 = rad * rad
        for yy in range(cy - rad, cy + rad + 1):
            dy = yy - cy
            span = int((r2 - dy * dy) ** 0.5)
            self.rect(cx - span, yy, 2 * span + 1, 1, colour)

    def ring(self, cx, cy, rad, colour, t=3):
        r2o = rad * rad
        r2i = (rad - t) * (rad - t)
        for yy in range(cy - rad, cy + rad + 1):
            for xx in range(cx - rad, cx + rad + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if r2i < d2 <= r2o:
                    self.set(xx, yy, colour)


# ------------------------------------------------------------------ font
# A plain 5x7 bitmap type, capitals only (lowercase folds up in text()).

FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11100", "10010", "10001", "10001", "10001", "10010", "11100"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "01010", "00100", "00100", "00100", "01010", "10001"),
    "Y": ("10001", "01010", "00100", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10001", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "=": ("00000", "00000", "01110", "00000", "01110", "00000", "00000"),
    "*": ("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
}


def text_w(s, scale):
    return len(s) * 6 * scale - scale


def text(cv, x, y, s, scale, colour, centre=False):
    s = s.upper()
    if centre:
        x = x - text_w(s, scale) // 2
    cx = x
    for ch in s:
        glyph = FONT.get(ch, FONT[" "])
        for row_i, row in enumerate(glyph):
            for col_i, bit in enumerate(row):
                if bit == "1":
                    cv.rect(cx + col_i * scale, y + row_i * scale,
                            scale, scale, colour)
        cx += 6 * scale
    return cx


# -------------------------------------------------------------- drawings

def draw_globe(cv, cx, cy, rad):
    """A sea globe with simple land blobs, split by a jagged crack."""
    cv.disc(cx, cy, rad, SEA)
    # land masses: a few deterministic ellipses clipped by the disc
    blobs = [(-0.45, -0.30, 0.34, 0.22), (0.30, -0.42, 0.30, 0.20),
             (-0.10, 0.05, 0.36, 0.26), (0.48, 0.28, 0.26, 0.20),
             (-0.52, 0.42, 0.22, 0.16), (0.05, 0.55, 0.20, 0.13)]
    for fx, fy, rx, ry in blobs:
        bx = cx + int(fx * rad)
        by = cy + int(fy * rad)
        brx = int(rx * rad)
        bry = int(ry * rad)
        for yy in range(by - bry, by + bry + 1):
            for xx in range(bx - brx, bx + brx + 1):
                if ((xx - bx) / brx) ** 2 + ((yy - by) / bry) ** 2 <= 1.0:
                    if (xx - cx) ** 2 + (yy - cy) ** 2 <= rad * rad:
                        cv.set(xx, yy, LAND)
    # meridian + equator
    for yy in range(cy - rad, cy + rad + 1):
        cv.set(cx, yy, TEAL)
    for xx in range(cx - rad, cx + rad + 1):
        cv.set(xx, cy, TEAL)
    cv.ring(cx, cy, rad, WHITE, 4)
    # the crack: a jagged white-then-red split down the middle
    pts = [(cx - 6, cy - rad + 8), (cx + 14, cy - rad // 2),
           (cx - 16, cy - 10), (cx + 10, cy + rad // 3),
           (cx - 8, cy + rad // 2), (cx + 6, cy + rad - 10)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        cv.line(ax, ay, bx, by, WHITE, 7)
        cv.line(ax, ay, bx, by, RED, 3)


def draw_building(cv, x, y, w, h):
    """An apartment block at night, one corner torn away, rubble below."""
    cv.rect(x, y, w, h, (52, 58, 74))
    # windows: a deterministic grid, some lit, some dark
    cols = w // 26
    rows = h // 30
    for r in range(rows):
        for c in range(cols):
            wx = x + 8 + c * 26
            wy = y + 10 + r * 30
            # the torn corner: skip windows near the top-right break
            if c >= cols - 2 and r <= 2:
                continue
            lit = ((r * 7 + c * 13) % 5) in (0, 3)
            cv.rect(wx, wy, 13, 17, LIT if lit else (26, 30, 42))
    # torn corner: paper-coloured notch with a jagged edge
    for i in range(6):
        cv.rect(x + w - 18 - i * 9, y + i * 11, 18 + i * 9, 11, SKY)
    cv.line(x + w - 70, y + 62, x + w - 8, y + 4, RED, 4)
    # rubble pile
    for i, (rw, rh) in enumerate(((150, 16), (110, 14), (70, 12))):
        cv.rect(x + 16 + i * 22, y + h - rh - (2 - i) * 2, rw, rh,
                (74, 78, 92))
    # rescue lights
    for dx in (30, 86, 150):
        cv.disc(x + dx, y + h + 14, 5, LIT)
        cv.disc(x + dx, y + h + 14, 2, WHITE)


def draw_chart(cv, x, y, w, h):
    """A plunging market line with one gold line climbing away."""
    cv.rect(x, y, w, h, (250, 249, 245))
    for gy in range(y + 18, y + h, 26):
        cv.line(x + 4, gy, x + w - 4, gy, (214, 212, 204), 1)
    fall = [(0.02, 0.16), (0.16, 0.10), (0.28, 0.26), (0.40, 0.20),
            (0.52, 0.44), (0.64, 0.38), (0.76, 0.62), (0.88, 0.58),
            (0.98, 0.82)]
    pts = [(x + int(fx * w), y + int(fy * h)) for fx, fy in fall]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        cv.line(ax, ay, bx, by, RED, 5)
    rise = [(0.02, 0.84), (0.30, 0.74), (0.55, 0.62), (0.80, 0.48),
            (0.98, 0.36)]
    pts = [(x + int(fx * w), y + int(fy * h)) for fx, fy in rise]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        cv.line(ax, ay, bx, by, GOLD, 4)
    # down arrow head at the end of the fall
    ex, ey = x + int(0.98 * w), y + int(0.82 * h)
    cv.line(ex, ey, ex - 18, ey - 4, RED, 5)
    cv.line(ex, ey, ex - 6, ey - 18, RED, 5)


def draw_capitol(cv, cx, base_y):
    """A simple capitol, about 84 px tall: dome, drum, columns."""
    for i in range(30):
        half = int(52 * (1 - (i / 30.0) ** 2) ** 0.5)
        cv.rect(cx - half, base_y - 76 + i, 2 * half, 1, WHITE)
    cv.rect(cx - 2, base_y - 84, 4, 9, WHITE)            # lantern
    cv.rect(cx - 66, base_y - 46, 132, 6, WHITE)         # entablature
    for i in range(6):                                   # columns
        cv.rect(cx - 60 + i * 21, base_y - 40, 8, 30, WHITE)
    cv.rect(cx - 72, base_y - 10, 144, 10, WHITE)        # steps


# ----------------------------------------------------------------- page

def build_page():
    cv = Canvas(W, H, PAPER)

    # ---- masthead
    cv.rect(0, 0, W, 148, INK)
    text(cv, W // 2, 16, "THE WORLD IN ONE IMAGE", 3, SAND, centre=True)
    text(cv, W // 2, 52, "MONDAY 23 NOVEMBER 2026", 6, WHITE, centre=True)
    text(cv, W // 2, 116,
         "ONE DAY · ONE IMAGE · THE NEWS OF 23 NOVEMBER 2026",
         2, SAND, centre=True)
    cv.rect(0, 148, W, 6, RED)

    # ---- hero: COP31 ends with no deal (y 166..478)
    hx, hy, hw, hh = 24, 166, 976, 312
    cv.rect(hx, hy, hw, hh, TEAL)
    draw_globe(cv, hx + 150, hy + 152, 112)
    tx = hx + 310
    text(cv, tx, hy + 26, "COP31 ENDS WITH", 5, WHITE)
    text(cv, tx, hy + 74, "NO DEAL", 8, SAND)
    text(cv, tx, hy + 148, "ANTALYA, TURKIYE: THE EU AND ABOUT 130", 2,
         WHITE)
    text(cv, tx, hy + 172, "NATIONS REJECT A TEXT WITH NO PLEDGE TO", 2,
         WHITE)
    text(cv, tx, hy + 196, "PHASE OUT FOSSIL FUELS", 2, WHITE)
    text(cv, tx, hy + 232, "THE LONGEST CLIMATE SUMMIT EVER ENDS", 2,
         SAND)
    text(cv, tx, hy + 256, "AFTER TWO DAYS OF OVERTIME - NO AGREEMENT", 2,
         SAND)
    text(cv, hx + 24, hy + hh - 26, "CLIMATE", 2, SAND)

    # ---- left: Kyiv / Dymer (y 490..730)
    lx, ly, lw, lh = 24, 490, 480, 240
    cv.rect(lx, ly, lw, lh, SKY)
    text(cv, lx + 16, ly + 12, "UKRAINE", 2, LIT)
    draw_building(cv, lx + 20, ly + 52, 168, 138)
    text(cv, lx + 204, ly + 22, "RUSSIAN STRIKE", 3, WHITE)
    text(cv, lx + 204, ly + 50, "ON DYMER", 3, WHITE)
    text(cv, lx + 204, ly + 84, "AT LEAST 11", 3, RED)
    text(cv, lx + 204, ly + 112, "KILLED", 3, RED)
    text(cv, lx + 204, ly + 146, "RESCUERS DIG IN THE", 2, WHITE)
    text(cv, lx + 204, ly + 168, "RUBBLE NORTH OF KYIV", 2, WHITE)

    # ---- right: markets (y 490..730)
    rx, ry, rw, rh = 520, 490, 480, 240
    cv.frame(rx, ry, rw, rh, INK, 3)
    text(cv, rx + 20, ry + 16, "AI SELL-OFF ROUTS MARKETS", 3, INK)
    draw_chart(cv, rx + 20, ry + 56, 284, 118)
    text(cv, rx + 320, ry + 60, "NIKKEI", 2, INK)
    text(cv, rx + 320, ry + 82, "-5.06%", 3, RED)
    text(cv, rx + 320, ry + 116, "S&P 500", 2, INK)
    text(cv, rx + 320, ry + 138, "-3.7%", 3, RED)
    text(cv, rx + 20, ry + 190, "GOLD +2.72% · OIL HOLDS NEAR $90", 2, GOLD)
    text(cv, rx + 20, ry + 214, "AI SHARES FEARED OVERPRICED", 2, GREY)

    # ---- US strip (y 742..834)
    ux, uy, uw, uh = 24, 742, 976, 92
    cv.rect(ux, uy, uw, uh, INK)
    draw_capitol(cv, ux + 104, uy + uh - 4)
    text(cv, ux + 216, uy + 16, "DEMOCRATS CLINCH THE HOUSE: 258 SEATS", 3,
         WHITE)
    text(cv, ux + 216, uy + 50,
         "THE LARGEST MAJORITY FOR EITHER PARTY SINCE 1992 - AP", 2, SAND)

    # ---- briefs (y 848..976)
    bx, by = 24, 848
    text(cv, bx, by, "IN BRIEF", 2, RED)
    briefs_l = [
        "IRAN: TRUMP 'INCLINED' TO RESUME",
        "CONFLICT IF NO DEAL BY NEW YEAR",
        "BANTEN: FACTORY FIRE KILLS 24,",
        "ABOUT 30 STILL MISSING (XINHUA)",
        "ATLANTA: DELTA DELAYS 1,000+",
        "FLIGHTS AFTER A SYSTEMS FAILURE",
    ]
    briefs_r = [
        "MOTOGP: MARQUEZ WINS 8TH TITLE,",
        "EQUALLING AGOSTINI AT PORTIMAO",
        "LIVERPOOL 4-0 MAN UTD: POCHETTINO",
        "FIRST MATCH ENDS IN DEFEAT",
        "DR CONGO: FIGHTING DISRUPTS THE",
        "EBOLA RESPONSE NEAR OUTBREAK - WHO",
    ]
    for i, line in enumerate(briefs_l):
        text(cv, bx, by + 24 + i * 18, line, 2,
             INK if i % 2 == 0 else GREY)
    for i, line in enumerate(briefs_r):
        text(cv, bx + 512, by + 24 + i * 18, line, 2,
             INK if i % 2 == 0 else GREY)

    # ---- ticker footer
    cv.rect(0, 984, W, 40, INK)
    text(cv, W // 2, 995,
         "BELGIUM AIRPORTS SHUT · LEBANON VILLAGERS GO HOME · "
         "TRUMP, PUTIN, XI AT APEC",
         2, WHITE, centre=True)
    return cv


# ------------------------------------------------------------- PNG write

def encode_png(cv):
    def chunk(tag, data):
        body = tag + data
        return (struct.pack(">I", len(data)) + body
                + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = cv.w * 3
    for yy in range(cv.h):
        raw.append(0)
        raw += cv.px[yy * stride:(yy + 1) * stride]
    idat = zlib.compress(bytes(raw), 9)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", idat) + chunk(b"IEND", b""))


def validate_png(data):
    """Re-read a PNG: signature, every chunk CRC, IHDR size, cap."""
    if len(data) > MAX_BYTES or not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return False
    pos = 8
    dims = None
    while pos + 8 <= len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        tag = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        (crc,) = struct.unpack(">I",
                               data[pos + 8 + length:pos + 12 + length])
        if zlib.crc32(tag + body) & 0xFFFFFFFF != crc:
            return False
        if tag == b"IHDR":
            dims = struct.unpack(">II", body[:8])
        pos += 12 + length
        if tag == b"IEND":
            break
    return dims == (W, H)


def candidate_paths(argv):
    paths = []
    if len(argv) > 1 and argv[1]:
        p = argv[1]
        paths.append(os.path.join(p, "entry.png")
                     if os.path.isdir(p) else p)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if out_dir:
        paths.append(os.path.join(out_dir, "entry.png"))
    paths.append(os.path.join(os.getcwd(), "entry.png"))
    paths.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "entry.png"))
    seen = []
    for p in paths:
        if p not in seen:
            seen.append(p)
    return seen


def main(argv):
    data = encode_png(build_page())
    if not validate_png(data):
        print("error: generated PNG failed self-validation",
              file=sys.stderr)
        return 1
    for path in candidate_paths(argv):
        try:
            parent = os.path.dirname(path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(path, "wb") as fh:
                fh.write(data)
            with open(path, "rb") as fh:
                if validate_png(fh.read()):
                    print("wrote %s (%d bytes)" % (path, len(data)))
                    return 0
            print("note: %s did not re-read clean" % path,
                  file=sys.stderr)
        except OSError as exc:
            print("note: cannot write %s: %s" % (path, exc),
                  file=sys.stderr)
    print("error: no writable output location", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
