#!/usr/bin/env python3
"""
GTA 6: How a Fire TV Stick Hacked a Billion-Dollar Secret
PaperBillionsTV-Style 2D Animated Documentary Engine (1080x1920, 30 fps)
Features:
  - Shaded pill-body + stick-limb character rigs with thick dark ink outlines
  - Localized radial lighting, heavy cinematic vignettes, and animated rain
  - Black-screen typewriter dramatic beats
  - Smooth camera push-ins, pans, under-desk POV, corkboard + red string,
    overhead conference table, magnifying glass, and golden-hour Vice City finale
  - Procedural rain + typewriter + sub-bass SFX mixed automatically with voiceover.wav
"""
import os
import math
import wave
import subprocess
import numpy as np
import cairo

W, H, FPS = 1080, 1920, 30
DEFAULT_DURATION = 78.0
OUT_MP4 = "output.mp4"
SFX_WAV = "_sfx_tmp.wav"


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def ease_out(x):
    x = clamp(x)
    return 1.0 - (1.0 - x) ** 3


def ease_in_out(x):
    x = clamp(x)
    return 3 * x * x - 2 * x * x * x


def find_voiceover():
    for name in ("voiceover.wav", "voiceover.mp3", "voiceover.m4a"):
        if os.path.exists(name):
            return name
    for fn in os.listdir("."):
        if fn.lower().endswith((".wav", ".mp3", ".m4a")) and not fn.startswith("_"):
            return fn
    return None


def get_audio_duration(path):
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", path
    ]
    return float(subprocess.check_output(cmd).decode().strip())


# --- Core Drawing Primitives ---

def rounded_rect(ctx, x, y, w, h, r):
    r = min(r, abs(w) / 2.0, abs(h) / 2.0)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def draw_text(ctx, text, x, y, size=42, rgb=(1, 1, 1), bold=True, italic=False,
              align="left", font="Noto Sans", alpha=1.0):
    ctx.select_font_face(
        font,
        cairo.FONT_SLANT_ITALIC if italic else cairo.FONT_SLANT_NORMAL,
        cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL,
    )
    ctx.set_font_size(size)
    ext = ctx.text_extents(text)
    if align == "center":
        x = x - (ext.width / 2.0 + ext.x_bearing)
    elif align == "right":
        x = x - (ext.width + ext.x_bearing)
    ctx.move_to(x, y)
    ctx.set_source_rgba(rgb[0], rgb[1], rgb[2], alpha)
    ctx.show_text(text)


def draw_radial_glow(ctx, cx, cy, r_in, r_out, rgb, alpha=0.55):
    g = cairo.RadialGradient(cx, cy, r_in, cx, cy, r_out)
    g.add_color_stop_rgba(0.0, rgb[0], rgb[1], rgb[2], alpha)
    g.add_color_stop_rgba(0.5, rgb[0], rgb[1], rgb[2], alpha * 0.35)
    g.add_color_stop_rgba(1.0, rgb[0], rgb[1], rgb[2], 0.0)
    ctx.set_source(g)
    ctx.arc(cx, cy, r_out, 0, 2 * math.pi)
    ctx.fill()


def draw_vignette(ctx, strength=0.78):
    g = cairo.RadialGradient(W / 2, H * 0.46, W * 0.25, W / 2, H * 0.48, H * 0.68)
    g.add_color_stop_rgba(0.0, 0.0, 0.0, 0.0, 0.0)
    g.add_color_stop_rgba(0.65, 0.0, 0.0, 0.0, strength * 0.38)
    g.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, strength)
    ctx.set_source(g)
    ctx.rectangle(0, 0, W, H)
    ctx.fill()


def draw_rain(ctx, t, alpha=0.22, count=55):
    ctx.set_source_rgba(0.75, 0.88, 1.0, alpha)
    ctx.set_line_width(2.0)
    for i in range(count):
        rx = ((i * 97.3 + t * 140) % (W + 200)) - 100
        ry = ((i * 173.7 + t * 1450) % (H + 200)) - 100
        ctx.move_to(rx, ry)
        ctx.line_to(rx - 14, ry + 54)
    ctx.stroke()


def draw_lower_third(ctx, title, subtitle, accent_rgb, prog, y=1440):
    """PaperBillionsTV signature dark translucent lower-third with thin colored left bar."""
    p = ease_out(prog)
    if p <= 0.01:
        return
    x0 = 90 - int(40 * (1.0 - p))
    bw, bh = 740, 118
    ctx.save()
    ctx.set_source_rgba(0.04, 0.06, 0.09, 0.82 * p)
    rounded_rect(ctx, x0, y, bw, bh, 8)
    ctx.fill()
    # Colored left accent bar
    ctx.set_source_rgba(accent_rgb[0], accent_rgb[1], accent_rgb[2], p)
    ctx.rectangle(x0, y + 10, 9, bh - 20)
    ctx.fill()
    draw_text(ctx, title, x0 + 30, y + 54, size=38, rgb=(0.96, 0.98, 1.0), bold=True, alpha=p)
    draw_text(ctx, subtitle, x0 + 30, y + 96, size=26, rgb=(0.68, 0.76, 0.84), bold=False, alpha=p)
    ctx.restore()


def draw_character(ctx, cx, cy, scale=1.0, skin=(0.94, 0.82, 0.74),
                   outfit=(0.14, 0.17, 0.22), hair=(0.12, 0.10, 0.09),
                   light_side="left", mood="focused", t=0.0,
                   arm_l_angle=25, arm_r_angle=-25, has_cap=False,
                   has_glasses=False, has_hoodie=False, facing=1):
    """PaperBillionsTV pill-body + stick-limbs rig with directional shading and thick ink outlines."""
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(scale * facing, scale)

    ink = (0.06, 0.07, 0.09)
    bob = 3.0 * math.sin(t * 2.4)

    # Stick legs
    ctx.set_source_rgb(*ink)
    ctx.set_line_width(9.0)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(-22, 130)
    ctx.line_to(-28, 225)
    ctx.move_to(22, 130)
    ctx.line_to(28, 225)
    ctx.stroke()

    # Stick arms (behind/front of torso)
    def draw_arm(sx, sy, deg):
        rad = math.radians(deg)
        ex = sx + math.cos(rad) * 85
        ey = sy + math.sin(rad) * 85
        ctx.set_source_rgb(*ink)
        ctx.set_line_width(8.5)
        ctx.move_to(sx, sy)
        ctx.line_to(ex, ey)
        ctx.stroke()
        # Small hand dot
        ctx.set_source_rgb(*skin)
        ctx.arc(ex, ey, 11, 0, 2 * math.pi)
        ctx.fill_preserve()
        ctx.set_source_rgb(*ink)
        ctx.set_line_width(4.0)
        ctx.stroke()

    draw_arm(-46, 20 + bob, 180 - arm_l_angle)
    draw_arm(46, 20 + bob, arm_r_angle)

    # Pill torso with directional shading
    rounded_rect(ctx, -56, -8 + bob, 112, 148, 46)
    gx0, gx1 = (-56, 56) if light_side == "left" else (56, -56)
    tg = cairo.LinearGradient(gx0, 0, gx1, 0)
    tg.add_color_stop_rgb(0.0, min(1.0, outfit[0] + 0.14), min(1.0, outfit[1] + 0.14), min(1.0, outfit[2] + 0.16))
    tg.add_color_stop_rgb(0.65, *outfit)
    tg.add_color_stop_rgb(1.0, outfit[0] * 0.45, outfit[1] * 0.45, outfit[2] * 0.5)
    ctx.set_source(tg)
    ctx.fill_preserve()
    ctx.set_source_rgb(*ink)
    ctx.set_line_width(6.0)
    ctx.stroke()

    # Hoodie strings or tie detail
    if has_hoodie:
        ctx.set_source_rgba(0.85, 0.88, 0.92, 0.85)
        ctx.set_line_width(3.5)
        ctx.move_to(-14, 10 + bob)
        ctx.line_to(-16, 56 + bob)
        ctx.move_to(14, 10 + bob)
        ctx.line_to(16, 56 + bob)
        ctx.stroke()
    else:
        # Crisp white collar + dark tie
        ctx.set_source_rgb(0.92, 0.94, 0.96)
        ctx.move_to(-18, -4 + bob)
        ctx.line_to(0, 24 + bob)
        ctx.line_to(18, -4 + bob)
        ctx.close_path()
        ctx.fill()
        ctx.set_source_rgb(0.72, 0.18, 0.16)
        ctx.move_to(0, 12 + bob)
        ctx.line_to(-7, 68 + bob)
        ctx.line_to(0, 82 + bob)
        ctx.line_to(7, 68 + bob)
        ctx.close_path()
        ctx.fill()

    # Large round head with directional shading
    hy = -68 + bob
    ctx.arc(0, hy, 64, 0, 2 * math.pi)
    hg = cairo.RadialGradient(-24 if light_side == "left" else 24, hy - 18, 8, 0, hy, 72)
    hg.add_color_stop_rgb(0.0, min(1.0, skin[0] + 0.08), min(1.0, skin[1] + 0.08), min(1.0, skin[2] + 0.08))
    hg.add_color_stop_rgb(0.68, *skin)
    hg.add_color_stop_rgb(1.0, skin[0] * 0.62, skin[1] * 0.58, skin[2] * 0.58)
    ctx.set_source(hg)
    ctx.fill_preserve()
    ctx.set_source_rgb(*ink)
    ctx.set_line_width(6.0)
    ctx.stroke()

    # Hair or Police Cap
    if has_cap:
        ctx.set_source_rgb(0.09, 0.13, 0.22)
        ctx.arc(0, hy - 12, 65, math.pi, 2 * math.pi)
        ctx.close_path()
        ctx.fill_preserve()
        ctx.set_source_rgb(*ink)
        ctx.set_line_width(5.0)
        ctx.stroke()
        # Cap visor
        ctx.set_source_rgb(0.05, 0.07, 0.11)
        rounded_rect(ctx, -20, hy - 22, 92, 16, 8)
        ctx.fill()
        # Gold badge on cap
        ctx.set_source_rgb(0.95, 0.78, 0.25)
        ctx.arc(14, hy - 42, 9, 0, 2 * math.pi)
        ctx.fill()
    else:
        ctx.set_source_rgb(*hair)
        ctx.arc(0, hy - 14, 65, math.pi * 0.92, math.pi * 2.08)
        ctx.curve_to(48, hy - 40, -15, hy - 32, -62, hy - 18)
        ctx.close_path()
        ctx.fill_preserve()
        ctx.set_source_rgb(*ink)
        ctx.set_line_width(4.5)
        ctx.stroke()

    # Eyes (periodic blink)
    blink = (t % 4.2) > 4.08
    ctx.set_source_rgb(*ink)
    if blink:
        ctx.set_line_width(4.0)
        ctx.move_to(2, hy - 4)
        ctx.line_to(18, hy - 4)
        ctx.move_to(28, hy - 4)
        ctx.line_to(44, hy - 4)
        ctx.stroke()
    else:
        ctx.arc(12, hy - 4, 6.2, 0, 2 * math.pi)
        ctx.arc(36, hy - 4, 6.2, 0, 2 * math.pi)
        ctx.fill()
        # Tiny eye catchlights
        ctx.set_source_rgb(1, 1, 1)
        ctx.arc(10, hy - 6, 2.0, 0, 2 * math.pi)
        ctx.arc(34, hy - 6, 2.0, 0, 2 * math.pi)
        ctx.fill()

    if has_glasses:
        ctx.set_source_rgb(*ink)
        ctx.set_line_width(3.5)
        ctx.arc(12, hy - 4, 13, 0, 2 * math.pi)
        ctx.stroke()
        ctx.arc(36, hy - 4, 13, 0, 2 * math.pi)
        ctx.stroke()
        ctx.move_to(25, hy - 4)
        ctx.line_to(23, hy - 4)
        ctx.stroke()

    # Mouth expression
    ctx.set_source_rgb(*ink)
    ctx.set_line_width(4.5)
    if mood == "shocked":
        ctx.arc(24, hy + 24, 10, 0, 2 * math.pi)
        ctx.stroke()
    elif mood == "smirk":
        ctx.move_to(12, hy + 24)
        ctx.curve_to(22, hy + 32, 34, hy + 28, 40, hy + 19)
        ctx.stroke()
    else:
        ctx.move_to(14, hy + 24)
        ctx.line_to(34, hy + 24)
        ctx.stroke()

    ctx.restore()


def draw_typewriter_beat(ctx, line1, line2, prog, accent=(0.96, 0.76, 0.26)):
    """PaperBillionsTV pure-black dramatic typewriter reveal."""
    ctx.set_source_rgb(0.0, 0.0, 0.0)
    ctx.rectangle(0, 0, W, H)
    ctx.fill()

    full = line1 + ("\n" + line2 if line2 else "")
    n_chars = int(len(full) * clamp(prog * 1.45))
    shown = full[:n_chars]
    parts = shown.split("\n")

    y_mid = H * 0.48
    if parts:
        draw_text(ctx, parts[0], W / 2, y_mid - (34 if line2 else 0),
                  size=58, rgb=(0.95, 0.96, 0.98), bold=False, italic=True, align="center", font="DejaVu Serif")
    if len(parts) > 1:
        draw_text(ctx, parts[1], W / 2, y_mid + 52,
                  size=62, rgb=accent, bold=True, italic=True, align="center", font="DejaVu Serif")

    # Subtle glowing horizontal rule
    rw = 280 * ease_out(prog)
    ctx.set_source_rgba(accent[0], accent[1], accent[2], 0.7)
    ctx.set_line_width(3.0)
    ctx.move_to(W / 2 - rw / 2, y_mid + 108)
    ctx.line_to(W / 2 + rw / 2, y_mid + 108)
    ctx.stroke()


def draw_viewfinder(ctx, lens_label="600mm  f/4  ISO 3200", rec=True, t=0.0):
    ctx.set_source_rgba(1, 1, 1, 0.55)
    ctx.set_line_width(3.5)
    m, t_y, b_y, bl = 64, 180, 1580, 48
    for p1, p2, p3 in [
        ((m, t_y + bl), (m, t_y), (m + bl, t_y)),
        ((W - m - bl, t_y), (W - m, t_y), (W - m, t_y + bl)),
        ((m, b_y - bl), (m, b_y), (m + bl, b_y)),
        ((W - m - bl, b_y), (W - m, b_y), (W - m, b_y - bl)),
    ]:
        ctx.move_to(*p1)
        ctx.line_to(*p2)
        ctx.line_to(*p3)
        ctx.stroke()
    if rec and int(t * 2) % 2 == 0:
        ctx.set_source_rgb(0.92, 0.20, 0.18)
        ctx.arc(105, 226, 10, 0, 2 * math.pi)
        ctx.fill()
    draw_text(ctx, "REC", 128, 236, size=28, rgb=(0.95, 0.95, 0.95), bold=True)
    draw_text(ctx, lens_label, W - 95, 236, size=24, rgb=(0.80, 0.85, 0.90), bold=False, align="right")


# --- 12 Cinematic Scenes (PaperBillionsTV DNA) ---

def render_frame(ctx, t, duration):
    u = t / max(1.0, duration)

    # 1. SHOT 1 (0.00 - 0.11): Rainy Travelodge Hotel Room + Smooth Camera Push-In
    if u < 0.11:
        lt = u / 0.11
        zoom = 1.0 + 0.14 * ease_in_out(lt)
        ctx.save()
        ctx.translate(W / 2, H * 0.48)
        ctx.scale(zoom, zoom)
        ctx.translate(-W / 2, -H * 0.48)

        # Dark night bedroom wall gradient
        bg = cairo.LinearGradient(0, 0, 0, H)
        bg.add_color_stop_rgb(0.0, *hex_rgb("#0B131E"))
        bg.add_color_stop_rgb(0.6, *hex_rgb("#131F2E"))
        bg.add_color_stop_rgb(1.0, *hex_rgb("#080D14"))
        ctx.set_source(bg)
        ctx.rectangle(0, 0, W, H)
        ctx.fill()

        # Rainy window on left with streetlamp glow
        rounded_rect(ctx, 90, 340, 360, 480, 12)
        ctx.set_source_rgb(*hex_rgb("#16283B"))
        ctx.fill_preserve()
        ctx.set_source_rgb(0.05, 0.07, 0.10)
        ctx.set_line_width(12.0)
        ctx.stroke()
        draw_radial_glow(ctx, 210, 520, 15, 240, hex_rgb("#F5B841"), 0.35)
        # Window rain streaks clipped-feel
        ctx.set_source_rgba(0.65, 0.82, 0.95, 0.28)
        ctx.set_line_width(2.0)
        for i in range(18):
            rx = 110 + (i * 19) % 320
            ry = 360 + ((i * 71 + t * 520) % 440)
            ctx.move_to(rx, ry)
            ctx.line_to(rx - 8, min(815, ry + 32))
        ctx.stroke()

        # Bedside warm lamp cone (right)
        draw_radial_glow(ctx, 840, 680, 20, 420, hex_rgb("#FFAE38"), 0.42)
        # Lamp shade
        ctx.set_source_rgb(*hex_rgb("#F7C86A"))
        ctx.move_to(790, 620)
        ctx.line_to(890, 620)
        ctx.line_to(915, 705)
        ctx.line_to(765, 705)
        ctx.close_path()
        ctx.fill_preserve()
        ctx.set_source_rgb(0.08, 0.08, 0.10)
        ctx.set_line_width(5.0)
        ctx.stroke()

        # Hotel bed + desk
        rounded_rect(ctx, 110, 1020, 860, 220, 24)
        ctx.set_source_rgb(*hex_rgb("#1D2A3A"))
        ctx.fill_preserve()
        ctx.set_source_rgb(0.05, 0.07, 0.09)
        ctx.set_line_width(6.0)
        ctx.stroke()

        # Flickering cyan hotel TV glow from left-foreground
        flicker = 0.42 + 0.07 * math.sin(t * 14.0)
        draw_radial_glow(ctx, 220, 960, 30, 520, hex_rgb("#2EC4FF"), flicker)

        # Arion Kurtaj sitting on bed in dark hoodie
        draw_character(ctx, 560, 930, scale=1.55, outfit=hex_rgb("#1B2430"),
                       hair=hex_rgb("#1B1410"), light_side="left", mood="focused",
                       t=t, arm_l_angle=-10, arm_r_angle=35, has_hoodie=True, facing=-1)
        ctx.restore()

        draw_vignette(ctx, 0.80)
        draw_lower_third(ctx, "18 SEPTEMBER 2022", "TRAVELODGE HOTEL  •  BICESTER, UK",
                         hex_rgb("#F5B841"), lt * 2.5)

    # 2. SHOT 2 (0.11 - 0.19): Laptop Confiscated + Nightstand TV / Phone / Fire TV Stick
    elif u < 0.19:
        lt = (u - 0.11) / 0.08
        ctx.set_source_rgb(*hex_rgb("#0B1018"))
        ctx.rectangle(0, 0, W, H)
        ctx.fill()

        # Split dramatic composition: Top = Police officer leaving with evidence bag
        draw_radial_glow(ctx, 280, 490, 20, 380, hex_rgb("#D93829"), 0.30)
        draw_character(ctx, 270, 520, scale=1.18, outfit=hex_rgb("#142238"),
                       light_side="right", t=t, arm_l_angle=25, arm_r_angle=15, has_cap=True, facing=1)

        # Evidence bag with laptop outline
        rounded_rect(ctx, 430, 440, 250, 170, 14)
        ctx.set_source_rgba(0.85, 0.92, 0.98, 0.15)
        ctx.fill_preserve()
        ctx.set_source_rgb(*hex_rgb("#D93829"))
        ctx.set_line_width(4.5)
        ctx.stroke()
        draw_text(ctx, "LAPTOP", 555, 515, size=36, rgb=(0.95, 0.96, 0.98), align="center")
        draw_text(ctx, "CONFISCATED", 555, 565, size=28, rgb=hex_rgb("#FF4D42"), align="center")

        # Bottom = Glowing wooden nightstand with TV, Phone, and Amazon Fire TV Stick
        ctx.set_source_rgb(*hex_rgb("#1B1411"))
        ctx.rectangle(0, 900, W, 1020)
        ctx.fill()
        ctx.set_source_rgb(0.05, 0.05, 0.07)
        ctx.set_line_width(6.0)
        ctx.move_to(0, 900)
        ctx.line_to(W, 900)
        ctx.stroke()

        # Glowing Hotel TV
        draw_radial_glow(ctx, 540, 1060, 30, 480, hex_rgb("#35C7FF"), 0.38)
        rounded_rect(ctx, 240, 930, 600, 290, 16)
        ctx.set_source_rgb(*hex_rgb("#10293B"))
        ctx.fill_preserve()
        ctx.set_source_rgb(0.04, 0.05, 0.07)
        ctx.set_line_width(10.0)
        ctx.stroke()
        draw_text(ctx, "HOTEL TV  •  HDMI 1", 540, 1090, size=34, rgb=hex_rgb("#6FE3FF"), align="center")

        # Glowing Amazon Fire TV Stick plugged into the side
        if lt > 0.30:
            p = ease_out((lt - 0.30) / 0.35)
            draw_radial_glow(ctx, 855, 1100, 15, 220 * p, hex_rgb("#FF9D2E"), 0.72)
            rounded_rect(ctx, 795, 1065, 165, 68, 12)
            ctx.set_source_rgb(0.10, 0.11, 0.14)
            ctx.fill_preserve()
            ctx.set_source_rgb(*hex_rgb("#FF9D2E"))
            ctx.set_line_width(5.0)
            ctx.stroke()
            draw_text(ctx, "FIRE STICK", 877, 1109, size=22, rgb=hex_rgb("#FFD27D"), align="center")

        # Smartphone on table
        if lt > 0.15:
            rounded_rect(ctx, 180, 1290, 140, 220, 18)
            ctx.set_source_rgb(*hex_rgb("#183247"))
            ctx.fill_preserve()
            ctx.set_source_rgb(*hex_rgb("#38D6FF"))
            ctx.set_line_width(4.5)
            ctx.stroke()
            draw_text(ctx, "PHONE", 250, 1412, size=24, rgb=(1, 1, 1), align="center")

        draw_vignette(ctx, 0.75)

    # 3. SHOT 3 (0.19 - 0.23): BLACK-SCREEN TYPEWRITER BEAT #1
    elif u < 0.23:
        lt = (u - 0.19) / 0.04
        draw_typewriter_beat(ctx, "All he had was a hotel TV,", "and an Amazon Fire TV Stick.", lt, hex_rgb("#FF9D2E"))

    # 4. SHOT 4 (0.23 - 0.30): Under-Desk Cable POV → Glowing Data Beam Into Rockstar Tower
    elif u < 0.30:
        lt = (u - 0.23) / 0.07
        p = ease_out(lt / 0.7)
        ctx.set_source_rgb(*hex_rgb("#070B12"))
        ctx.rectangle(0, 0, W, H)
        ctx.fill()

        # Distant stormy sky + Rockstar Fortress silhouette at top
        draw_radial_glow(ctx, W / 2, 460, 20, 440, hex_rgb("#D93829"), 0.35 + 0.2 * p)
        rounded_rect(ctx, 250, 290, 580, 340, 12)
        ctx.set_source_rgb(*hex_rgb("#131924"))
        ctx.fill_preserve()
        ctx.set_source_rgb(*hex_rgb("#D93829"))
        ctx.set_line_width(5.0)
        ctx.stroke()
        # Lit office windows grid
        for r in range(4):
            for c in range(7):
                ctx.set_source_rgba(1.0, 0.85, 0.45, 0.35 if (r + c) % 3 else 0.75)
                ctx.rectangle(300 + c * 70, 340 + r * 52, 40, 24)
                ctx.fill()
        draw_text(ctx, "ROCKSTAR GAMES", W / 2, 600, size=48, rgb=(1, 1, 1), align="center")

        # Fiber beam shooting upward from glowing Fire Stick at bottom
        beam_top = 1350 - (1350 - 630) * p
        ctx.set_source_rgba(0.18, 0.85, 1.0, 0.22)
        ctx.set_line_width(36.0)
        ctx.move_to(W / 2, 1350)
        ctx.line_to(W / 2, beam_top)
        ctx.stroke()
        ctx.set_source_rgb(*hex_rgb("#38D6FF"))
        ctx.set_line_width(10.0)
        ctx.move_to(W / 2, 1350)
        ctx.line_to(W / 2, beam_top)
        ctx.stroke()

        for i in range(7):
            py = 1350 - ((t * 580 + i * 110) % 720)
            if py > beam_top:
                draw_radial_glow(ctx, W / 2, py, 4, 42, hex_rgb("#FFAE38"), 0.85)
                ctx.set_source_rgb(1, 1, 1)
                ctx.arc(W / 2, py, 8, 0, 2 * math.pi)
                ctx.fill()

        # Fire Stick source at bottom
        draw_radial_glow(ctx, W / 2, 1380, 15, 220, hex_rgb("#FF9D2E"), 0.65)
        rounded_rect(ctx, 350, 1330, 380, 96, 16)
        ctx.set_source_rgb(0.08, 0.10, 0.14)
        ctx.fill_preserve()
        ctx.set_source_rgb(*hex_rgb("#FF9D2E"))
        ctx.set_line_width(5.0)
        ctx.stroke()
        draw_text(ctx, "FIRE TV STICK", W / 2, 1392, size=38, rgb=hex_rgb("#FFD27D"), align="center")

        draw_rain(ctx, t, alpha=0.16, count=35)
        draw_viewfinder(ctx, "BREACH  •  600mm f/4", rec=True, t=t)
        draw_vignette(ctx, 0.72)

    # 5. SHOT 5 (0.30 - 0.39): Corkboard + Red Pushpins & String (90 Clips Stolen)
    elif u < 0.39:
        lt = (u - 0.30) / 0.09
        p = ease_out(lt / 0.65)
        # Warm dark corkboard texture feel
        bg = cairo.LinearGradient(0, 0, W, H)
        bg.add_color_stop_rgb(0.0, *hex_rgb("#3C281B"))
        bg.add_color_stop_rgb(1.0, *hex_rgb("#24170F"))
        ctx.set_source(bg)
        ctx.rectangle(0, 0, W, H)
        ctx.fill()
        draw_radial_glow(ctx, W / 2, H * 0.44, 40, 620, hex_rgb("#F5B841"), 0.28)

        # Red string connecting evidence cards
        ctx.set_source_rgb(*hex_rgb("#D93829"))
        ctx.set_line_width(6.0)
        ctx.move_to(320, 420)
        ctx.line_to(750, 640)
        ctx.line_to(540, 1080)
        ctx.stroke()

        # Polaroid Card 1: Suspect Arion Kurtaj
        ctx.save()
        ctx.translate(310, 520)
        ctx.rotate(math.radians(-5.0))
        rounded_rect(ctx, -180, -160, 360, 390, 10)
        ctx.set_source_rgb(*hex_rgb("#F2EAD3"))
        ctx.fill_preserve()
        ctx.set_source_rgb(0.10, 0.08, 0.07)
        ctx.set_line_width(5.0)
        ctx.stroke()
        ctx.set_source_rgb(*hex_rgb("#162330"))
        ctx.rectangle(-155, -135, 310, 265)
        ctx.fill()
        draw_character(ctx, 0, 50, scale=0.85, outfit=hex_rgb("#1F2A36"), has_hoodie=True, t=t)
        draw_text(ctx, "ARION KURTAJ", 0, 185, size=32, rgb=(0.12, 0.12, 0.14), align="center")
        # Red pushpin
        ctx.set_source_rgb(*hex_rgb("#E32D22"))
        ctx.arc(0, -142, 16, 0, 2 * math.pi)
        ctx.fill()
        ctx.restore()

        # Evidence Card 2: 90 Unfinished Clips Counter
        ctx.save()
        ctx.translate(740, 720)
        ctx.rotate(math.radians(4.5))
        rounded_rect(ctx, -210, -140, 420, 310, 10)
        ctx.set_source_rgb(*hex_rgb("#F2EAD3"))
        ctx.fill_preserve()
        ctx.set_source_rgb(0.10, 0.08, 0.07)
        ctx.set_line_width(5.0)
        ctx.stroke()
        draw_text(ctx, f"{int(90 * p)}", 0, 10, size=118, rgb=hex_rgb("#C93B2B"), align="center")
        draw_text(ctx, "GTA 6 CLIPS STOLEN", 0, 75, size=30, rgb=(0.12, 0.12, 0.14), align="center")
        draw_text(ctx, "~1 HOUR GAMEPLAY", 0, 120, size=24, rgb=(0.35, 0.35, 0.38), bold=False, align="center")
        ctx.set_source_rgb(*hex_rgb("#E32D22"))
        ctx.arc(0, -122, 16, 0, 2 * math.pi)
        ctx.fill()
        ctx.restore()

        # Evidence Card 3: LAPSUS$ Tag
        ctx.save()
        ctx.translate(540, 1180)
        ctx.rotate(math.radians(-2.5))
        rounded_rect(ctx, -280, -110, 560, 220, 10)
        ctx.set_source_rgb(*hex_rgb("#F2EAD3"))
        ctx.fill_preserve()
        ctx.set_source_rgb(0.10, 0.08, 0.07)
        ctx.set_line_width(5.0)
        ctx.stroke()
        draw_text(ctx, "HANDLE: teapotuberhacker", 0, -20, size=32, rgb=(0.12, 0.12, 0.14), align="center")
        draw_text(ctx, "GROUP: LAPSUS$", 0, 45, size=36, rgb=hex_rgb("#C93B2B"), align="center")
        ctx.set_source_rgb(*hex_rgb("#E32D22"))
        ctx.arc(0, -92, 16, 0, 2 * math.pi)
        ctx.fill()
        ctx.restore()

        draw_vignette(ctx, 0.78)

    # 6. SHOT 6 (0.39 - 0.48): Dark Rockstar Office + Green Desk Lamp + Slack Ransom
    elif u < 0.48:
        lt = (u - 0.39) / 0.09
        ctx.set_source_rgb(*hex_rgb("#080E14"))
        ctx.rectangle(0, 0, W, H)
        ctx.fill()

        # Classic PaperBillionsTV green banker's desk lamp glow
        draw_radial_glow(ctx, 820, 520, 20, 480, hex_rgb("#2ECC71"), 0.42)
        ctx.set_source_rgb(*hex_rgb("#1E9E54"))
        rounded_rect(ctx, 730, 460, 180, 62, 26)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.05, 0.07, 0.08)
        ctx.set_line_width(5.0)
        ctx.stroke()

        # Shocked Rockstar Exec at desk
        draw_character(ctx, 270, 960, scale=1.45, outfit=hex_rgb("#1C2530"),
                       hair=hex_rgb("#2A2420"), light_side="right", mood="shocked",
                       t=t, arm_l_angle=-35, arm_r_angle=-40, has_glasses=True, facing=1)

        # Glowing Slack Ransom Card floating in dark room
        draw_radial_glow(ctx, 640, 780, 30, 380, hex_rgb("#E33B2E"), 0.25)
        rounded_rect(ctx, 130, 270, 820, 410, 18)
        ctx.set_source_rgba(0.08, 0.11, 0.16, 0.94)
        ctx.fill_preserve()
        ctx.set_source_rgb(*hex_rgb("#E33B2E"))
        ctx.set_line_width(5.0)
        ctx.stroke()
        draw_text(ctx, "# rockstar-internal-slack", 175, 340, size=34, rgb=hex_rgb("#FF5A4E"))
        draw_text(ctx, '"I have the GTA 6 source code.', 175, 425, size=38, rgb=(0.96, 0.97, 0.99))
        draw_text(ctx, " Negotiate in 24 HOURS", 175, 482, size=38, rgb=(0.96, 0.97, 0.99))
        draw_text(ctx, ' or I leak everything."', 175, 539, size=38, rgb=hex_rgb("#FFAE38"))
        draw_text(ctx, "DEADLINE:  24:00:00", 175, 628, size=42, rgb=hex_rgb("#FF4D42"))

        draw_vignette(ctx, 0.76)
        draw_lower_third(ctx, "INTERNAL SLACK BREACH", "24-HOUR RANSOM ULTIMATUM",
                         hex_rgb("#E33B2E"), lt * 2.5)

    # 7. SHOT 7 (0.48 - 0.56): Overhead Conference Table + Red Marker Circle ($5M vs $1B+) + REFUSED
    elif u < 0.56:
        lt = (u - 0.48) / 0.08
        ctx.set_source_rgb(*hex_rgb("#0E141C"))
        ctx.rectangle(0, 0, W, H)
        ctx.fill()
        draw_radial_glow(ctx, W / 2, H * 0.46, 40, 560, hex_rgb("#F5C242"), 0.26)

        # Top-down wooden boardroom table
        rounded_rect(ctx, 130, 300, W - 260, 1080, 90)
        ctx.set_source_rgb(*hex_rgb("#2C1E16"))
        ctx.fill_preserve()
        ctx.set_source_rgb(0.06, 0.04, 0.03)
        ctx.set_line_width(8.0)
        ctx.stroke()

        # Paper dossier on table
        rounded_rect(ctx, 210, 430, W - 420, 760, 10)
        ctx.set_source_rgb(*hex_rgb("#F2EAD3"))
        ctx.fill_preserve()
        ctx.set_source_rgb(0.15, 0.14, 0.12)
        ctx.set_line_width(4.0)
        ctx.stroke()

        draw_text(ctx, "DAMAGE REPORT", W / 2, 520, size=44, rgb=(0.12, 0.14, 0.18), align="center")
        draw_text(ctx, "$5,000,000", W / 2, 665, size=82, rgb=hex_rgb("#C93B2B"), align="center")
        draw_text(ctx, "RECOVERY & SECURITY COST", W / 2, 725, size=28, rgb=(0.30, 0.32, 0.36), align="center")

        # Animated hand-drawn red marker circle around $5,000,000
        ang = 2 * math.pi * ease_out(lt / 0.45)
        if ang > 0.05:
            ctx.save()
            ctx.translate(W / 2, 640)
            ctx.scale(1.0, 0.38)
            ctx.set_source_rgb(*hex_rgb("#D93829"))
            ctx.set_line_width(14.0)
            ctx.arc(0, 0, 290, -math.pi / 2, -math.pi / 2 + ang)
            ctx.stroke()
            ctx.restore()

        draw_text(ctx, "EST. BUDGET: $1 BILLION+", W / 2, 875, size=34, rgb=(0.16, 0.18, 0.22), align="center")

        # Slammed REFUSED stamp
        if lt > 0.40:
            pop = ease_out((lt - 0.40) / 0.25)
            s = max(0.05, 1.4 - 0.4 * pop)
            ctx.save()
            ctx.translate(W / 2, 1040)
            ctx.rotate(math.radians(-9.0))
            ctx.scale(s, s)
            rounded_rect(ctx, -250, -58, 500, 116, 12)
            ctx.set_source_rgba(0.85, 0.18, 0.15, 0.12)
            ctx.fill_preserve()
            ctx.set_source_rgb(*hex_rgb("#C93B2B"))
            ctx.set_line_width(8.0)
            ctx.stroke()
            draw_text(ctx, "RANSOM REFUSED", 0, 18, size=48, rgb=hex_rgb("#C93B2B"), align="center")
            ctx.restore()

        draw_vignette(ctx, 0.78)

    # 8. SHOT 8 (0.56 - 0.60): BLACK-SCREEN TYPEWRITER BEAT #2
    elif u < 0.60:
        lt = (u - 0.56) / 0.04
        draw_typewriter_beat(ctx, "Instead,", "the opposite happened.", lt, hex_rgb("#38D6FF"))

    # 9. SHOT 9 (0.60 - 0.68): Silence → Golden Obsession Ripples Over Crowds
    elif u < 0.68:
        lt = (u - 0.60) / 0.08
        ctx.set_source_rgb(*hex_rgb("#070D14"))
        ctx.rectangle(0, 0, W, H)
        ctx.fill()

        cx, cy = W / 2, 760
        draw_radial_glow(ctx, cx, cy, 30, 520, hex_rgb("#F5B841"), 0.42)
        for ri in range(5):
            rad = ((t * 170 + ri * 95) % 440) + 40
            ctx.set_source_rgba(0.96, 0.74, 0.26, max(0.06, 0.75 * (1.0 - rad / 480.0)))
            ctx.set_line_width(5.0)
            ctx.arc(cx, cy, rad, 0, 2 * math.pi)
            ctx.stroke()

        draw_text(ctx, "ROCKSTAR STAYED SILENT", cx, cy - 10, size=50, rgb=(1, 1, 1), align="center")
        draw_text(ctx, "CURIOSITY  ->  OBSESSION", cx, cy + 58, size=38, rgb=hex_rgb("#F5C242"), align="center")

        # Crowd of pill-silhouettes watching glowing phones below
        for idx, px in enumerate([190, 365, 540, 715, 890]):
            draw_character(ctx, px, 1280 + (idx % 2) * 35, scale=0.88,
                           outfit=hex_rgb("#15212E"), light_side="left" if idx < 2 else "right",
                           mood="focused", t=t + idx * 0.4, has_hoodie=(idx % 2 == 0))
        draw_vignette(ctx, 0.78)

    # 10. SHOT 10 (0.68 - 0.79): Glowing Viral Surge Bar Race (90.4M vs 475M)
    elif u < 0.79:
        lt = (u - 0.68) / 0.11
        p1 = ease_out(lt / 0.35)
        p2 = ease_out((lt - 0.32) / 0.45)
        ctx.set_source_rgb(*hex_rgb("#08121C"))
        ctx.rectangle(0, 0, W, H)
        ctx.fill()

        # Subtle glowing grid
        ctx.set_source_rgba(0.20, 0.45, 0.62, 0.22)
        ctx.set_line_width(1.5)
        for x in range(0, W + 1, 60):
            ctx.move_to(x, 0)
            ctx.line_to(x, H)
        for y in range(0, H + 1, 60):
            ctx.move_to(0, y)
            ctx.line_to(W, y)
        ctx.stroke()

        base_y = 1280
        # Bar 1: Trailer 1
        h1 = 190 * p1
        draw_radial_glow(ctx, 325, base_y - h1, 15, 240, hex_rgb("#38D6FF"), 0.35)
        rounded_rect(ctx, 200, base_y - h1, 250, h1, 12)
        ctx.set_source_rgb(*hex_rgb("#38D6FF"))
        ctx.fill()
        draw_text(ctx, f"{90.4 * p1:.1f}M", 325, base_y - h1 - 32, size=62, rgb=hex_rgb("#38D6FF"), align="center")
        draw_text(ctx, "TRAILER 1", 325, base_y + 56, size=36, rgb=(1, 1, 1), align="center")
        draw_text(ctx, "24 HOURS", 325, base_y + 98, size=26, rgb=(0.65, 0.75, 0.85), bold=False, align="center")

        # Bar 2: Trailer 2
        if lt > 0.30:
            h2 = 760 * p2
            draw_radial_glow(ctx, 755, base_y - h2, 20, 360, hex_rgb("#F5B841"), 0.50)
            rounded_rect(ctx, 630, base_y - h2, 250, h2, 12)
            ctx.set_source_rgb(*hex_rgb("#F5B841"))
            ctx.fill()
            draw_text(ctx, f"{int(475 * p2)}M", 755, base_y - h2 - 32, size=66, rgb=hex_rgb("#F5B841"), align="center")
            draw_text(ctx, "TRAILER 2", 755, base_y + 56, size=36, rgb=(1, 1, 1), align="center")
            draw_text(ctx, "5.2X SURGE", 755, base_y + 98, size=26, rgb=hex_rgb("#F5B841"), align="center")

        ctx.set_source_rgba(1, 1, 1, 0.7)
        ctx.set_line_width(4.0)
        ctx.move_to(110, base_y)
        ctx.line_to(W - 110, base_y)
        ctx.stroke()
        draw_vignette(ctx, 0.72)
        draw_lower_third(ctx, "UNPRECEDENTED HYPE", "90.4M  ->  475 MILLION VIEWS",
                         hex_rgb("#F5B841"), lt * 2.5, y=1450)

    # 11. SHOT 11 (0.79 - 0.88): PaperBillionsTV Ticking Billion-Dollar Counter ($2.3B)
    elif u < 0.88:
        lt = (u - 0.79) / 0.09
        p = ease_out(lt / 0.65)
        ctx.set_source_rgb(0.03, 0.05, 0.07)
        ctx.rectangle(0, 0, W, H)
        ctx.fill()

        draw_radial_glow(ctx, W / 2, H * 0.46, 30, 560, hex_rgb("#2ECC71"), 0.42)
        val_int = int(2_300_000_000 * p)
        draw_text(ctx, "PRE-LAUNCH REVENUE", W / 2, 710, size=38, rgb=(0.72, 0.84, 0.78), align="center")
        draw_text(ctx, f"${val_int:,}", W / 2, 855, size=86, rgb=hex_rgb("#2ECC71"), align="center")
        draw_text(ctx, "$2.3 BILLION BEFORE DAY ONE", W / 2, 955, size=40, rgb=(1, 1, 1), align="center")
        draw_text(ctx, "24M+ DIGITAL PRE-ORDERS", W / 2, 1020, size=30, rgb=hex_rgb("#F5C242"), bold=False, align="center")
        draw_vignette(ctx, 0.78)

    # 12. SHOT 12 (0.88 - 1.00): Court Verdict + Golden-Hour Vice City Finale
    else:
        lt = (u - 0.88) / 0.12
        if lt < 0.42:
            # Magnifying glass over Woolwich Crown Court paper
            p = ease_out(lt / 0.35)
            ctx.set_source_rgb(0.06, 0.07, 0.09)
            ctx.rectangle(0, 0, W, H)
            ctx.fill()

            rounded_rect(ctx, 110, 340, W - 220, 960, 14)
            ctx.set_source_rgb(*hex_rgb("#F2EAD3"))
            ctx.fill()
            draw_text(ctx, "16 NOVEMBER 2026", W / 2, 540, size=60, rgb=hex_rgb("#161C22"), italic=True, align="center")
            # Crimson underline
            ctx.set_source_rgb(*hex_rgb("#C93B2B"))
            ctx.set_line_width(8.0)
            ctx.move_to(240, 565)
            ctx.line_to(240 + 600 * p, 565)
            ctx.stroke()
            draw_text(ctx, "ARION KURTAJ", W / 2, 700, size=48, rgb=(0.14, 0.16, 0.20), align="center")
            draw_text(ctx, "PLEADED GUILTY", W / 2, 785, size=62, rgb=hex_rgb("#C93B2B"), align="center")
            draw_text(ctx, "LONDON  •  3 DAYS BEFORE LAUNCH", W / 2, 890, size=30, rgb=(0.35, 0.37, 0.40), align="center")
            draw_vignette(ctx, 0.78)
        else:
            # Golden-Hour Vice City Sunset Skyline (PaperBillionsTV golden finale)
            ft = (lt - 0.42) / 0.58
            zoom = 1.12 - 0.10 * ease_out(ft)
            ctx.save()
            ctx.translate(W / 2, H * 0.5)
            ctx.scale(zoom, zoom)
            ctx.translate(-W / 2, -H * 0.5)

            sky = cairo.LinearGradient(0, 0, 0, H)
            sky.add_color_stop_rgb(0.0, *hex_rgb("#1B102E"))
            sky.add_color_stop_rgb(0.45, *hex_rgb("#9B3359"))
            sky.add_color_stop_rgb(0.72, *hex_rgb("#F48C3B"))
            sky.add_color_stop_rgb(1.0, *hex_rgb("#0C0A14"))
            ctx.set_source(sky)
            ctx.rectangle(0, 0, W, H)
            ctx.fill()

            # Giant glowing sunset sun
            draw_radial_glow(ctx, W / 2, 980, 80, 480, hex_rgb("#FFD166"), 0.85)
            ctx.set_source_rgb(*hex_rgb("#FFE184"))
            ctx.arc(W / 2, 980, 210, 0, 2 * math.pi)
            ctx.fill()

            # Vice City skyline silhouettes
            ctx.set_source_rgb(0.06, 0.05, 0.11)
            buildings = [
                (0, 1080, 160, 840), (150, 960, 140, 960), (280, 1040, 130, 880),
                (400, 920, 150, 1000), (540, 1010, 140, 910), (670, 940, 160, 980),
                (820, 1050, 130, 870), (940, 980, 150, 940),
            ]
            for bx, by, bw, bh in buildings:
                ctx.rectangle(bx, by, bw, bh)
            ctx.fill()
            ctx.restore()

            draw_text(ctx, "19 NOVEMBER 2026", W / 2, 470, size=62, rgb=(1, 1, 1), align="center")
            draw_text(ctx, "HISTORY'S BIGGEST LAUNCH", W / 2, 555, size=50, rgb=hex_rgb("#FFE184"), align="center")
            draw_text(ctx, "GRAND THEFT AUTO VI", W / 2, 630, size=38, rgb=hex_rgb("#FF70A6"), align="center")
            draw_vignette(ctx, 0.62)


def generate_sfx_track(duration, path):
    """Synthesize subtle rain ambience, typewriter ticks, and cinematic sub-bass hits."""
    sr = 44100
    n = int(sr * duration)
    rng = np.random.default_rng(42)
    buf = np.zeros(n, dtype=np.float32)

    # Gentle rain noise in opening hotel scene (0% - 19%)
    rain_end = int(n * 0.19)
    noise = rng.normal(0, 1, rain_end).astype(np.float32)
    # Simple low-pass smoothing
    noise = np.convolve(noise, np.ones(12, dtype=np.float32) / 12.0, mode="same")
    buf[:rain_end] += noise * 0.045

    def add_tone(t0, dur, freq, amp=0.22, decay=5.5):
        i0 = int(t0 * sr)
        i1 = min(n, int((t0 + dur) * sr))
        if i0 >= n or i1 <= i0:
            return
        ts = np.arange(i1 - i0) / sr
        env = np.exp(-decay * ts)
        buf[i0:i1] += (amp * env * np.sin(2 * np.pi * freq * ts)).astype(np.float32)

    # Cinematic sub-bass drops & UI cues
    for frac, freq, amp in [
        (0.00, 62, 0.25), (0.11, 85, 0.18), (0.19, 58, 0.28), (0.23, 140, 0.20),
        (0.30, 72, 0.22), (0.39, 95, 0.20), (0.48, 65, 0.26), (0.56, 55, 0.28),
        (0.60, 110, 0.18), (0.68, 220, 0.16), (0.79, 68, 0.26), (0.88, 60, 0.26), (0.93, 110, 0.22),
    ]:
        add_tone(frac * duration, 0.55, freq, amp=amp, decay=5.0)

    # Typewriter clicks during black-screen beats (0.19-0.225 and 0.56-0.595)
    for start_f, end_f in ((0.192, 0.222), (0.562, 0.592)):
        t_cur = start_f * duration
        while t_cur < end_f * duration:
            add_tone(t_cur, 0.03, 1450, amp=0.09, decay=90.0)
            t_cur += 0.085

    pcm = np.clip(buf * 32767, -32768, 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


def main():
    vo = find_voiceover()
    duration = get_audio_duration(vo) if vo else DEFAULT_DURATION
    total_frames = int(math.ceil(duration * FPS))
    print(f"Rendering PaperBillionsTV-style {total_frames} frames ({duration:.2f}s) | VO={vo}")

    generate_sfx_track(duration, SFX_WAV)

    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS),
        "-i", "-",
        "-i", SFX_WAV,
    ]
    if vo:
        cmd += [
            "-i", vo,
            "-filter_complex", "[1:a]volume=0.40[sfx];[2:a]volume=1.0[vo];[sfx][vo]amix=inputs=2:duration=longest[a]",
            "-map", "0:v", "-map", "[a]",
        ]
    else:
        cmd += ["-map", "0:v", "-map", "1:a"]

    cmd += [
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "19",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", OUT_MP4
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)

    for fi in range(total_frames):
        render_frame(ctx, fi / FPS, duration)
        surf.flush()
        buf = np.frombuffer(surf.get_data(), dtype=np.uint8).reshape((H, W, 4))
        proc.stdin.write(buf[:, :, :3].tobytes())

    proc.stdin.close()
    ret = proc.wait()
    if os.path.exists(SFX_WAV):
        os.remove(SFX_WAV)
    if ret != 0:
        raise RuntimeError(f"FFmpeg exited with code {ret}")
    print(f"Done! Saved {OUT_MP4} ({os.path.getsize(OUT_MP4) / (1024*1024):.2f} MB)")


if __name__ == "__main__":
    main()
