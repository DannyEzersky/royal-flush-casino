"""
Builds the Royal Spin A/B Test findings PowerPoint presentation.
Output: exports/royal_spin_ab_test.pptx
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import copy

# ---------------------------------------------------------------------------
# Brand colours
# ---------------------------------------------------------------------------
NAVY        = RGBColor(0x0D, 0x1B, 0x3E)   # slide backgrounds
GOLD        = RGBColor(0xD4, 0xAF, 0x37)   # accent / headlines
WHITE       = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GREY  = RGBColor(0xF2, 0xF2, 0xF2)
MID_GREY    = RGBColor(0xCC, 0xCC, 0xCC)
GREEN       = RGBColor(0x2E, 0xCC, 0x71)
RED         = RGBColor(0xE7, 0x4C, 0x3C)
AMBER       = RGBColor(0xF3, 0x9C, 0x12)

W = Inches(13.33)   # widescreen width
H = Inches(7.5)     # widescreen height


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def blank_slide(prs: Presentation) -> object:
    layout = prs.slide_layouts[6]   # completely blank
    return prs.slides.add_slide(layout)


def fill_bg(slide, colour: RGBColor) -> None:
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = colour


def box(slide, x, y, w, h,
        bg: RGBColor = None, border: RGBColor = None, border_pt: float = 0):
    """Add a plain rectangle shape."""
    from pptx.util import Pt as Pt_
    shape = slide.shapes.add_shape(
        1,   # MSO_SHAPE_TYPE.RECTANGLE
        x, y, w, h
    )
    shape.line.fill.background()
    if bg:
        shape.fill.solid()
        shape.fill.fore_color.rgb = bg
    else:
        shape.fill.background()
    if border and border_pt:
        shape.line.color.rgb = border
        shape.line.width = Pt_(border_pt)
    else:
        shape.line.fill.background()
    return shape


def txbox(slide, x, y, w, h,
          text: str = "",
          size: int = 18,
          bold: bool = False,
          colour: RGBColor = WHITE,
          align=PP_ALIGN.LEFT,
          wrap: bool = True) -> object:
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = colour
    run.font.name = "Calibri"
    return tb


def metric_card(slide, x, y, w, h,
                label: str, value: str, delta: str = "",
                delta_colour: RGBColor = GREEN,
                bg: RGBColor = None):
    """Stat card: label on top, big value, optional delta below."""
    card_bg = bg or RGBColor(0x1A, 0x2D, 0x5A)
    box(slide, x, y, w, h, bg=card_bg, border=GOLD, border_pt=1.5)
    pad = Inches(0.15)
    txbox(slide, x + pad, y + pad, w - pad*2, Inches(0.4),
          label, size=11, colour=MID_GREY, align=PP_ALIGN.CENTER)
    txbox(slide, x + pad, y + Inches(0.45), w - pad*2, Inches(0.65),
          value, size=26, bold=True, colour=GOLD, align=PP_ALIGN.CENTER)
    if delta:
        txbox(slide, x + pad, y + Inches(1.05), w - pad*2, Inches(0.35),
              delta, size=13, bold=True, colour=delta_colour,
              align=PP_ALIGN.CENTER)


def divider(slide, y, colour: RGBColor = GOLD, thickness_pt: float = 1.5):
    line = slide.shapes.add_shape(1, Inches(0.5), y, W - Inches(1), Pt(thickness_pt))
    line.fill.solid()
    line.fill.fore_color.rgb = colour
    line.line.fill.background()


def slide_header(slide, title: str, subtitle: str = ""):
    """Gold bar at top with title."""
    box(slide, 0, 0, W, Inches(0.85), bg=GOLD)
    txbox(slide, Inches(0.4), Inches(0.1), W - Inches(0.8), Inches(0.65),
          title, size=22, bold=True, colour=NAVY, align=PP_ALIGN.LEFT)
    if subtitle:
        txbox(slide, Inches(0.4), Inches(0.82), W - Inches(0.8), Inches(0.35),
              subtitle, size=12, colour=MID_GREY, align=PP_ALIGN.LEFT)


def tag(slide, x, y, text, bg, fg=WHITE):
    w, h = Inches(1.5), Inches(0.32)
    box(slide, x, y, w, h, bg=bg)
    txbox(slide, x, y, w, h, text, size=11, bold=True,
          colour=fg, align=PP_ALIGN.CENTER)


# ---------------------------------------------------------------------------
# Slides
# ---------------------------------------------------------------------------

def slide_title(prs):
    sl = blank_slide(prs)
    fill_bg(sl, NAVY)

    # Gold accent bar left edge
    box(sl, 0, 0, Inches(0.18), H, bg=GOLD)

    # Casino chip watermark (large faded circle)
    chip = sl.shapes.add_shape(9, Inches(8.5), Inches(0.5), Inches(6.2), Inches(6.2))
    chip.fill.solid()
    chip.fill.fore_color.rgb = RGBColor(0x14, 0x26, 0x52)
    chip.line.fill.background()

    txbox(sl, Inches(0.6), Inches(1.5), Inches(8), Inches(0.7),
          "ROYAL FLUSH CASINO", size=14, bold=True, colour=GOLD)
    txbox(sl, Inches(0.6), Inches(2.1), Inches(9), Inches(1.6),
          "Royal Spin Feature\nA/B Test Results", size=40, bold=True, colour=WHITE)

    divider(sl, Inches(3.75), GOLD, 2)

    txbox(sl, Inches(0.6), Inches(3.95), Inches(7), Inches(0.4),
          "Experiment period: July 1 – September 28, 2024", size=14, colour=MID_GREY)
    txbox(sl, Inches(0.6), Inches(4.35), Inches(7), Inches(0.4),
          "SpinCrown Studios  |  Data & Analytics", size=14, colour=MID_GREY)

    # Stat teaser bottom-right
    box(sl, Inches(9.8), Inches(5.2), Inches(3.1), Inches(1.8),
        bg=RGBColor(0x1A, 0x2D, 0x5A), border=GOLD, border_pt=1.5)
    txbox(sl, Inches(9.9), Inches(5.3), Inches(2.9), Inches(0.4),
          "ARPU LIFT", size=11, colour=MID_GREY, align=PP_ALIGN.CENTER)
    txbox(sl, Inches(9.9), Inches(5.65), Inches(2.9), Inches(0.7),
          "+40%", size=36, bold=True, colour=GOLD, align=PP_ALIGN.CENTER)
    txbox(sl, Inches(9.9), Inches(6.3), Inches(2.9), Inches(0.35),
          "$16.56  →  $23.17", size=12, colour=WHITE, align=PP_ALIGN.CENTER)


def slide_agenda(prs):
    sl = blank_slide(prs)
    fill_bg(sl, NAVY)
    slide_header(sl, "Agenda")

    items = [
        ("01", "Test Setup & Methodology"),
        ("02", "Headline Result — ARPU +40%"),
        ("03", "Royal Token Revenue Impact"),
        ("04", "Segment Deep-Dive"),
        ("05", "Platform Breakdown"),
        ("06", "Guardrail Metrics"),
        ("07", "Recommendation"),
    ]

    col_x = [Inches(0.6), Inches(6.9)]
    for i, (num, label) in enumerate(items):
        col = i % 2
        row = i // 2
        x = col_x[col]
        y = Inches(1.3) + row * Inches(1.35)
        box(sl, x, y, Inches(5.9), Inches(1.1),
            bg=RGBColor(0x1A, 0x2D, 0x5A), border=GOLD, border_pt=1)
        txbox(sl, x + Inches(0.15), y + Inches(0.08), Inches(0.7), Inches(0.5),
              num, size=22, bold=True, colour=GOLD)
        txbox(sl, x + Inches(0.85), y + Inches(0.25), Inches(4.8), Inches(0.5),
              label, size=15, bold=True, colour=WHITE)


def slide_methodology(prs):
    sl = blank_slide(prs)
    fill_bg(sl, NAVY)
    slide_header(sl, "Test Setup & Methodology",
                 "Royal Spin — a new premium spin mechanic funded by Royal Tokens (in-app currency)")

    # Two columns: Control / Treatment
    for i, (title, lines) in enumerate([
        ("CONTROL", [
            "Standard coin-based spins only",
            "No Royal Token currency",
            "~12,500 players",
            "Baseline period: Apr – Jun 2024",
        ]),
        ("TREATMENT", [
            "Royal Spin mechanic unlocked",
            "Royal Tokens purchasable via IAP",
            "~12,500 players",
            "Experiment: Jul – Sep 2024",
        ]),
    ]):
        x = Inches(0.5) + i * Inches(6.3)
        bg = RGBColor(0x1A, 0x2D, 0x5A)
        box(sl, x, Inches(1.2), Inches(5.9), Inches(3.8), bg=bg, border=GOLD, border_pt=1.5)
        label_bg = GOLD if i == 1 else MID_GREY
        label_fg = NAVY if i == 1 else NAVY
        box(sl, x, Inches(1.2), Inches(5.9), Inches(0.45), bg=label_bg)
        txbox(sl, x, Inches(1.22), Inches(5.9), Inches(0.4),
              title, size=14, bold=True, colour=label_fg, align=PP_ALIGN.CENTER)
        for j, line in enumerate(lines):
            txbox(sl, x + Inches(0.3), Inches(1.85) + j * Inches(0.65),
                  Inches(5.3), Inches(0.55),
                  "•  " + line, size=14, colour=WHITE)

    # Key parameters bottom bar
    box(sl, Inches(0.5), Inches(5.2), W - Inches(1), Inches(1.9),
        bg=RGBColor(0x0A, 0x14, 0x30))
    params = [
        ("Players", "50,000 total"),
        ("Simulation Period", "181 days"),
        ("Segments", "Minnow · Dolphin · Whale"),
        ("Platforms", "iOS · Android"),
        ("Markets", "US · UK · DE · CA · AU · Other"),
    ]
    for i, (k, v) in enumerate(params):
        x = Inches(0.8) + i * Inches(2.5)
        txbox(sl, x, Inches(5.3), Inches(2.3), Inches(0.35),
              k, size=10, colour=GOLD, align=PP_ALIGN.CENTER)
        txbox(sl, x, Inches(5.65), Inches(2.3), Inches(0.35),
              v, size=12, bold=True, colour=WHITE, align=PP_ALIGN.CENTER)


def slide_headline(prs):
    sl = blank_slide(prs)
    fill_bg(sl, NAVY)
    slide_header(sl, "Headline Result — ARPU +40%",
                 "Treatment group generated significantly more revenue per user with no engagement cost")

    cw = Inches(2.9)
    ch = Inches(1.55)
    gap = Inches(0.22)
    start_x = Inches(0.5)
    y = Inches(1.15)

    metrics = [
        ("ARPU", "$23.17", "▲ +40%  vs $16.56", GREEN),
        ("Conversion Rate", "19.23%", "▲ +0.91pp  vs 18.32%", GREEN),
        ("FTD 30-Day Rate", "16.66%", "▲ +0.82pp  vs 15.84%", GREEN),
        ("Avg Spins / Session", "70.77", "▲ +1.32  vs 69.45", GREEN),
    ]
    for i, (label, val, delta, dc) in enumerate(metrics):
        metric_card(sl, start_x + i * (cw + gap), y, cw, ch, label, val, delta, dc)

    # Retention table
    box(sl, Inches(0.5), Inches(2.95), W - Inches(1), Inches(0.38),
        bg=GOLD)
    for i, txt in enumerate(["", "D1 Retention", "D7 Retention", "D30 Retention"]):
        txbox(sl, Inches(0.6) + i * Inches(3.0), Inches(2.97), Inches(2.8), Inches(0.34),
              txt, size=13, bold=True, colour=NAVY, align=PP_ALIGN.CENTER)

    rows = [
        ("Control",   "25.97%", "20.89%", "7.23%"),
        ("Treatment", "25.53%", "21.16%", "7.82%"),
    ]
    for r, (grp, d1, d7, d30) in enumerate(rows):
        row_bg = RGBColor(0x1A, 0x2D, 0x5A) if r == 1 else RGBColor(0x12, 0x22, 0x48)
        y_row = Inches(3.33) + r * Inches(0.6)
        box(sl, Inches(0.5), y_row, W - Inches(1), Inches(0.58), bg=row_bg)
        for i, val in enumerate([grp, d1, d7, d30]):
            bold = (i == 0)
            colour = GOLD if i == 0 else WHITE
            txbox(sl, Inches(0.6) + i * Inches(3.0), y_row + Inches(0.1),
                  Inches(2.8), Inches(0.38),
                  val, size=14, bold=bold, colour=colour, align=PP_ALIGN.CENTER)

    txbox(sl, Inches(0.5), Inches(4.65), W - Inches(1), Inches(0.4),
          "Retention is statistically flat between groups — the Royal Spin feature did not harm engagement.",
          size=13, colour=MID_GREY, align=PP_ALIGN.CENTER)

    # Big callout
    box(sl, Inches(0.5), Inches(5.15), W - Inches(1), Inches(1.95),
        bg=RGBColor(0x0A, 0x14, 0x30), border=GOLD, border_pt=2)
    txbox(sl, Inches(0.7), Inches(5.25), W - Inches(1.4), Inches(0.45),
          "KEY TAKEAWAY", size=11, bold=True, colour=GOLD)
    txbox(sl, Inches(0.7), Inches(5.65), W - Inches(1.4), Inches(1.2),
          "Treatment players spent 40% more on average than Control, while session engagement "
          "remained identical. The ARPU lift is driven purely by monetisation, not playtime inflation.",
          size=14, colour=WHITE, wrap=True)


def slide_royal_token(prs):
    sl = blank_slide(prs)
    fill_bg(sl, NAVY)
    slide_header(sl, "Royal Token Revenue Impact",
                 "8.39% of Treatment players adopted Royal Tokens — and contributed 23% of all Treatment revenue")

    # Big stat left
    box(sl, Inches(0.5), Inches(1.1), Inches(5.8), Inches(4.5),
        bg=RGBColor(0x1A, 0x2D, 0x5A), border=GOLD, border_pt=2)
    txbox(sl, Inches(0.7), Inches(1.3), Inches(5.4), Inches(0.4),
          "ROYAL TOKEN ADOPTERS", size=12, colour=GOLD, align=PP_ALIGN.CENTER)
    txbox(sl, Inches(0.7), Inches(1.7), Inches(5.4), Inches(1.1),
          "8.39%", size=60, bold=True, colour=WHITE, align=PP_ALIGN.CENTER)
    txbox(sl, Inches(0.7), Inches(2.75), Inches(5.4), Inches(0.4),
          "of Treatment players", size=14, colour=MID_GREY, align=PP_ALIGN.CENTER)

    divider(sl, Inches(3.3), MID_GREY, 1)

    txbox(sl, Inches(0.7), Inches(3.45), Inches(5.4), Inches(0.4),
          "REVENUE GENERATED", size=12, colour=GOLD, align=PP_ALIGN.CENTER)
    txbox(sl, Inches(0.7), Inches(3.8), Inches(5.4), Inches(0.7),
          "$55,419", size=36, bold=True, colour=WHITE, align=PP_ALIGN.CENTER)
    txbox(sl, Inches(0.7), Inches(4.45), Inches(5.4), Inches(0.4),
          "in Royal Token transactions", size=13, colour=MID_GREY, align=PP_ALIGN.CENTER)

    # Revenue split right
    box(sl, Inches(6.7), Inches(1.1), Inches(6.2), Inches(4.5),
        bg=RGBColor(0x1A, 0x2D, 0x5A), border=GOLD, border_pt=2)
    txbox(sl, Inches(6.9), Inches(1.3), Inches(5.8), Inches(0.4),
          "TREATMENT REVENUE BREAKDOWN", size=12, colour=GOLD, align=PP_ALIGN.CENTER)

    # Simple bar chart (manual shapes)
    bars = [
        ("Coin Purchases",  76.76, RGBColor(0x41, 0x8C, 0xF0), "$183,089"),
        ("Royal Tokens",    23.24, GOLD,                         "$55,419"),
    ]
    for i, (label, pct, colour, amt) in enumerate(bars):
        by = Inches(2.0) + i * Inches(1.8)
        bar_w = Inches(5.4) * pct / 100
        txbox(sl, Inches(6.9), by, Inches(5.8), Inches(0.35),
              label, size=12, colour=WHITE)
        box(sl, Inches(6.9), by + Inches(0.38), bar_w, Inches(0.55), bg=colour)
        txbox(sl, Inches(6.9) + bar_w + Inches(0.1), by + Inches(0.38),
              Inches(1.5), Inches(0.55),
              f"{pct}%  {amt}", size=12, bold=True, colour=colour)

    txbox(sl, Inches(6.9), Inches(5.65), Inches(5.8), Inches(0.35),
          f"Total Treatment Revenue: $238,508", size=13,
          bold=True, colour=WHITE, align=PP_ALIGN.CENTER)

    # Callout
    box(sl, Inches(0.5), Inches(5.75), W - Inches(1), Inches(1.4),
        bg=RGBColor(0x0A, 0x14, 0x30), border=GOLD, border_pt=2)
    txbox(sl, Inches(0.7), Inches(5.85), W - Inches(1.4), Inches(0.35),
          "KEY TAKEAWAY", size=11, bold=True, colour=GOLD)
    txbox(sl, Inches(0.7), Inches(6.2), W - Inches(1.4), Inches(0.8),
          "A small fraction of players drove an outsized share of revenue — "
          "a classic high-value cohort effect amplified by the Royal Spin mechanic.",
          size=14, colour=WHITE, wrap=True)


def slide_segments(prs):
    sl = blank_slide(prs)
    fill_bg(sl, NAVY)
    slide_header(sl, "Segment Deep-Dive",
                 "Whales drove the lift — but Dolphin cannibalization is a concern")

    # ARPU table
    headers = ["Segment", "Control ARPU", "Treatment ARPU", "Delta", "Signal"]
    col_w   = [Inches(2.0), Inches(2.2), Inches(2.5), Inches(1.8), Inches(4.3)]
    col_x   = [Inches(0.5)]
    for w in col_w[:-1]:
        col_x.append(col_x[-1] + w)

    box(sl, Inches(0.5), Inches(1.05), W - Inches(1), Inches(0.42), bg=GOLD)
    for i, (h, x, w) in enumerate(zip(headers, col_x, col_w)):
        txbox(sl, x + Inches(0.05), Inches(1.07), w, Inches(0.38),
              h, size=12, bold=True, colour=NAVY, align=PP_ALIGN.CENTER)

    rows = [
        ("Whale",   "$414.30",  "$557.38",  "+34.5%", GREEN,  "Strong lift — additive token model working"),
        ("Dolphin", "$18.56",   "$15.02",   "-19.1%", RED,    "Cannibalization: Royal Tokens replaced coin spend"),
        ("Minnow",  "$0.38",    "$0.34",    "-10.5%", AMBER,  "Negligible impact either way"),
    ]
    for r, (seg, ctrl, trt, delta, dc, signal) in enumerate(rows):
        row_bg = RGBColor(0x1A, 0x2D, 0x5A) if r % 2 == 0 else RGBColor(0x12, 0x22, 0x48)
        y_row = Inches(1.47) + r * Inches(0.72)
        box(sl, Inches(0.5), y_row, W - Inches(1), Inches(0.7), bg=row_bg)
        for i, (val, colour, align) in enumerate([
            (seg,   GOLD,  PP_ALIGN.CENTER),
            (ctrl,  WHITE, PP_ALIGN.CENTER),
            (trt,   WHITE, PP_ALIGN.CENTER),
            (delta, dc,    PP_ALIGN.CENTER),
            (signal, MID_GREY, PP_ALIGN.LEFT),
        ]):
            txbox(sl, col_x[i] + Inches(0.05), y_row + Inches(0.18),
                  col_w[i] - Inches(0.1), Inches(0.4),
                  val, size=13, bold=(i == 0), colour=colour, align=align)

    # Dolphin detail box
    box(sl, Inches(0.5), Inches(3.7), Inches(6.0), Inches(2.5),
        bg=RGBColor(0x2C, 0x10, 0x10), border=RED, border_pt=1.5)
    txbox(sl, Inches(0.7), Inches(3.8), Inches(5.6), Inches(0.38),
          "DOLPHIN CANNIBALIZATION DETAIL", size=12, bold=True, colour=RED)
    dolphin_rows = [
        ("",            "Coin Revenue", "Royal Token Revenue"),
        ("Control",     "$15,512",      "—"),
        ("Treatment",   "$9,704",       "$3,905"),
        ("Net change",  "-$5,808",      "+$3,905  =  -$1,903 net loss"),
    ]
    for r, row_vals in enumerate(dolphin_rows):
        y_r = Inches(4.25) + r * Inches(0.44)
        for c, val in enumerate(row_vals):
            colour = GOLD if r == 0 else (RED if (r == 3 and c == 1) else WHITE)
            txbox(sl, Inches(0.65) + c * Inches(1.75), y_r,
                  Inches(1.8), Inches(0.4),
                  val, size=12, bold=(r == 0 or r == 3), colour=colour)

    # Whale box
    box(sl, Inches(6.9), Inches(3.7), Inches(6.0), Inches(2.5),
        bg=RGBColor(0x0D, 0x2A, 0x1A), border=GREEN, border_pt=1.5)
    txbox(sl, Inches(7.1), Inches(3.8), Inches(5.6), Inches(0.38),
          "WHALE REVENUE SHARE", size=12, bold=True, colour=GREEN)
    txbox(sl, Inches(7.1), Inches(4.2), Inches(5.6), Inches(0.4),
          "Control:    88.8% of group revenue from Whales", size=13, colour=WHITE)
    txbox(sl, Inches(7.1), Inches(4.65), Inches(5.6), Inches(0.4),
          "Treatment:  93.0% of group revenue from Whales", size=13, colour=WHITE)
    txbox(sl, Inches(7.1), Inches(5.1), Inches(5.6), Inches(0.7),
          "Treatment is more Whale-dependent — revenue base\nis more sensitive to Whale churn.",
          size=12, colour=AMBER, wrap=True)

    # Callout
    box(sl, Inches(0.5), Inches(6.35), W - Inches(1), Inches(0.85),
        bg=RGBColor(0x0A, 0x14, 0x30), border=GOLD, border_pt=2)
    txbox(sl, Inches(0.7), Inches(6.45), W - Inches(1.4), Inches(0.65),
          "RISK: Before full rollout, address Dolphin cannibalization — "
          "the substitutive token model cost more in lost coin revenue than it earned in token revenue.",
          size=13, colour=WHITE, wrap=True)


def slide_platform(prs):
    sl = blank_slide(prs)
    fill_bg(sl, NAVY)
    slide_header(sl, "Platform Breakdown",
                 "The Royal Spin lift is an iOS story — Android saw minimal impact")

    platforms = [
        ("iOS",     "$17.65", "$28.08", "+59.1%", GREEN),
        ("Android", "$15.09", "$16.46", "+9.1%",  AMBER),
    ]

    for i, (plat, ctrl, trt, delta, dc) in enumerate(platforms):
        x = Inches(0.5) + i * Inches(6.5)
        box(sl, x, Inches(1.1), Inches(6.0), Inches(5.2),
            bg=RGBColor(0x1A, 0x2D, 0x5A), border=GOLD, border_pt=1.5)
        box(sl, x, Inches(1.1), Inches(6.0), Inches(0.45),
            bg=GOLD if i == 0 else MID_GREY)
        txbox(sl, x, Inches(1.13), Inches(6.0), Inches(0.4),
              plat, size=15, bold=True, colour=NAVY, align=PP_ALIGN.CENTER)

        txbox(sl, x + Inches(0.2), Inches(1.7), Inches(5.6), Inches(0.38),
              "Control ARPU", size=12, colour=MID_GREY, align=PP_ALIGN.CENTER)
        txbox(sl, x + Inches(0.2), Inches(2.05), Inches(5.6), Inches(0.6),
              ctrl, size=30, bold=True, colour=WHITE, align=PP_ALIGN.CENTER)

        txbox(sl, x + Inches(0.2), Inches(2.75), Inches(5.6), Inches(0.38),
              "Treatment ARPU", size=12, colour=MID_GREY, align=PP_ALIGN.CENTER)
        txbox(sl, x + Inches(0.2), Inches(3.1), Inches(5.6), Inches(0.6),
              trt, size=30, bold=True, colour=GOLD, align=PP_ALIGN.CENTER)

        box(sl, x + Inches(1.5), Inches(3.85), Inches(3.0), Inches(0.6), bg=dc)
        txbox(sl, x + Inches(1.5), Inches(3.88), Inches(3.0), Inches(0.55),
              delta, size=22, bold=True, colour=WHITE, align=PP_ALIGN.CENTER)

    # Insight
    box(sl, Inches(0.5), Inches(6.45), W - Inches(1), Inches(0.75),
        bg=RGBColor(0x0A, 0x14, 0x30), border=GOLD, border_pt=2)
    txbox(sl, Inches(0.7), Inches(6.52), W - Inches(1.4), Inches(0.6),
          "iOS players responded 6.5× more strongly to the Royal Spin feature than Android players. "
          "Prioritise iOS in rollout targeting and marketing spend.",
          size=13, colour=WHITE, wrap=True)


def slide_guardrails(prs):
    sl = blank_slide(prs)
    fill_bg(sl, NAVY)
    slide_header(sl, "Guardrail Metrics",
                 "Engagement held firm — revenue concentration is the only structural risk")

    guardrails = [
        ("D1 Retention",         "25.53% T  vs  25.97% C",  "PASS", GREEN,  "No meaningful change"),
        ("D7 Retention",         "21.16% T  vs  20.89% C",  "PASS", GREEN,  "Slight positive trend"),
        ("D30 Retention",        "7.82% T  vs  7.23% C",    "PASS", GREEN,  "Slight positive trend"),
        ("Avg Active Days",      "5.4 T  vs  5.2 C",        "PASS", GREEN,  "No churn signal"),
        ("Spins / Session",      "70.77 T  vs  69.45 C",    "PASS", GREEN,  "Engagement unchanged"),
        ("Dolphin Revenue",      "$15.02 T  vs  $18.56 C",  "WATCH", AMBER, "Cannibalization confirmed"),
        ("Whale Revenue Share",  "93.0% T  vs  88.8% C",    "WATCH", AMBER, "Increased concentration risk"),
    ]

    for i, (metric, values, status, sc, note) in enumerate(guardrails):
        row_bg = RGBColor(0x1A, 0x2D, 0x5A) if i % 2 == 0 else RGBColor(0x12, 0x22, 0x48)
        y_r = Inches(1.1) + i * Inches(0.71)
        box(sl, Inches(0.5), y_r, W - Inches(1), Inches(0.69), bg=row_bg)

        # Status badge
        box(sl, Inches(0.55), y_r + Inches(0.12), Inches(0.85), Inches(0.45), bg=sc)
        txbox(sl, Inches(0.55), y_r + Inches(0.14), Inches(0.85), Inches(0.4),
              status, size=10, bold=True, colour=WHITE, align=PP_ALIGN.CENTER)

        txbox(sl, Inches(1.5), y_r + Inches(0.14), Inches(3.2), Inches(0.42),
              metric, size=13, bold=True, colour=WHITE)
        txbox(sl, Inches(4.7), y_r + Inches(0.14), Inches(4.0), Inches(0.42),
              values, size=12, colour=MID_GREY)
        txbox(sl, Inches(8.7), y_r + Inches(0.14), Inches(4.3), Inches(0.42),
              note, size=12, colour=sc)

    box(sl, Inches(0.5), Inches(6.2), W - Inches(1), Inches(1.0),
        bg=RGBColor(0x0A, 0x14, 0x30), border=GOLD, border_pt=2)
    txbox(sl, Inches(0.7), Inches(6.3), W - Inches(1.4), Inches(0.35),
          "SUMMARY", size=11, bold=True, colour=GOLD)
    txbox(sl, Inches(0.7), Inches(6.62), W - Inches(1.4), Inches(0.5),
          "No engagement or churn guardrails were triggered. The two WATCH items are known model "
          "effects (substitutive pricing for Dolphins; Whale concentration) — not surprises.",
          size=13, colour=WHITE, wrap=True)


def slide_recommendation(prs):
    sl = blank_slide(prs)
    fill_bg(sl, NAVY)
    slide_header(sl, "Recommendation",
                 "Ship Royal Spin — with one fix before broad rollout")

    # Verdict banner
    box(sl, Inches(0.5), Inches(1.05), W - Inches(1), Inches(0.75), bg=GREEN)
    txbox(sl, Inches(0.5), Inches(1.08), W - Inches(1), Inches(0.68),
          "VERDICT:  SHIP  —  Royal Spin delivers a statistically meaningful +40% ARPU lift with no engagement cost",
          size=16, bold=True, colour=WHITE, align=PP_ALIGN.CENTER)

    actions = [
        (GREEN, "SHIP NOW",
         "Roll out Royal Spin to all Whale players on iOS",
         [
             "Strongest signal group: iOS Whales saw +59% ARPU and +34% segment ARPU",
             "Additive token model means no cannibalization risk for this segment",
             "8.39% Royal Token adoption rate driving 23% of Treatment revenue",
         ]),
        (AMBER, "FIX FIRST",
         "Redesign Dolphin token pricing before broad rollout",
         [
             "Substitutive model cost Dolphins more in lost coin revenue than token revenue gained",
             "Net Dolphin loss: -$1,903 across the experiment cohort",
             "Consider additive-only token model for Dolphins, or tiered pricing",
         ]),
        (RGBColor(0x41, 0x8C, 0xF0), "MONITOR",
         "Track Whale retention and revenue concentration post-launch",
         [
             "Treatment revenue is 93% Whale-dependent vs 88.8% in Control",
             "Set up weekly Whale churn alert (>2pp above baseline)",
             "Review Android performance separately — only +9% ARPU lift",
         ]),
    ]

    for i, (colour, badge, title, bullets) in enumerate(actions):
        x = Inches(0.5) + i * Inches(4.25)
        box(sl, x, Inches(2.0), Inches(4.0), Inches(4.8),
            bg=RGBColor(0x1A, 0x2D, 0x5A), border=colour, border_pt=2)
        box(sl, x, Inches(2.0), Inches(4.0), Inches(0.42), bg=colour)
        txbox(sl, x, Inches(2.02), Inches(4.0), Inches(0.38),
              badge, size=13, bold=True, colour=WHITE, align=PP_ALIGN.CENTER)
        txbox(sl, x + Inches(0.15), Inches(2.52), Inches(3.7), Inches(0.55),
              title, size=13, bold=True, colour=WHITE, wrap=True)
        for j, b in enumerate(bullets):
            txbox(sl, x + Inches(0.15), Inches(3.15) + j * Inches(0.68),
                  Inches(3.7), Inches(0.65),
                  "•  " + b, size=11, colour=MID_GREY, wrap=True)

    # Footer
    txbox(sl, Inches(0.5), Inches(7.1), W - Inches(1), Inches(0.3),
          "Royal Flush Casino  |  SpinCrown Studios  |  Data & Analytics  |  2024",
          size=10, colour=RGBColor(0x55, 0x55, 0x55), align=PP_ALIGN.CENTER)


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def main():
    prs = Presentation()
    prs.slide_width  = W
    prs.slide_height = H

    slide_title(prs)
    slide_agenda(prs)
    slide_methodology(prs)
    slide_headline(prs)
    slide_royal_token(prs)
    slide_segments(prs)
    slide_platform(prs)
    slide_guardrails(prs)
    slide_recommendation(prs)

    out = "exports/royal_spin_ab_test.pptx"
    prs.save(out)
    print(f"Saved: {out}  ({len(prs.slides)} slides)")


if __name__ == "__main__":
    main()
