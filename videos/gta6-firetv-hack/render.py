#!/usr/bin/env python3
"""
GTA 6: How a Fire TV Stick Hacked a Billion-Dollar Secret
1080x1920 (9:16 Vertical), 30 fps — Procedural PyCairo 2D Vector + SFX Renderer.
Automatically syncs to voiceover.wav / voiceover.mp3 if present in the same directory.
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


def ease_out(x):
    x = max(0.0, min(1.0, x))
    return 1.0 - (1.0 - x) ** 3


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
    out = subprocess.check_output(cmd).decode().strip()
    return float(out)


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


NAVY = hex_rgb("#081B29")
GRID = hex_rgb("#133247")
CARD = hex_rgb("#0E2638")
CYAN = hex_rgb("#38D6FF")
AMBER = hex_rgb("#F5C242")
CRIMSON = hex_rgb("#C93B2B")
GREEN = hex_rgb("#2ECC71")
PAPER = hex_rgb("#F2EAD3")
INK = hex_rgb("#1C242B")
WHITE = hex_rgb("#F4F8FB")
MUTED = hex_rgb("#89A7BC")


def draw_blueprint_bg(ctx, tag, t, duration):
    ctx.set_source_rgb(*NAVY)
    ctx.rectangle(0, 0, W, H)
    ctx.fill()

    ctx.set_source_rgba(*GRID, 0.7)
    ctx.set_line_width(1.5)
    for x in range(0, W + 1, 60):
        ctx.move_to(x, 0)
        ctx.line_to(x, H)
    for y in range(0, H + 1, 60):
        ctx.move_to(0, y)
        ctx.line_to(W, y)
    ctx.stroke()

    ctx.set_source_rgba(1, 1, 1, 0.75)
    ctx.set_line_width(4.0)
    m_x, top_y, bot_y, bl = 64, 175, 1565, 42
    corners = [
        ((m_x, top_y + bl), (m_x, top_y), (m_x + bl, top_y)),
        ((W - m_x - bl, top_y), (W - m_x, top_y), (W - m_x, top_y + bl)),
        ((m_x, bot_y - bl), (m_x, bot_y), (m_x + bl, bot_y)),
        ((W - m_x - bl, bot_y), (W - m_x, bot_y), (W - m_x, bot_y - bl)),
    ]
    for p1, p2, p3 in corners:
        ctx.move_to(*p1)
        ctx.line_to(*p2)
        ctx.line_to(*p3)
        ctx.stroke()

    rounded_rect(ctx, 90, 200, 480, 56, 8)
    ctx.set_source_rgb(*CARD)
    ctx.fill_preserve()
    ctx.set_source_rgb(*CYAN)
    ctx.set_line_width(2.5)
    ctx.stroke()
    draw_text(ctx, tag, 114, 238, size=26, rgb=CYAN, bold=True)

    mins, secs = int(t // 60), int(t % 60)
    draw_text(ctx, f"REC {mins:02d}:{secs:02d}", W - 95, 238, size=26, rgb=MUTED, bold=True, align="right")

    bar_w = W - 180
    ctx.set_source_rgba(*GRID, 1.0)
    ctx.rectangle(90, 1525, bar_w, 10)
    ctx.fill()
    ctx.set_source_rgb(*CYAN)
    ctx.rectangle(90, 1525, bar_w * min(1.0, t / max(1.0, duration)), 10)
    ctx.fill()


def draw_stamp(ctx, label, cx, cy, rgb, pop, angle_deg=-8.0):
    if pop <= 0.0:
        return
    s_safe = max(0.05, 1.35 - 0.35 * ease_out(pop))
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(math.radians(angle_deg))
    ctx.scale(s_safe, s_safe)
    bw, bh = 560, 118
    rounded_rect(ctx, -bw / 2, -bh / 2, bw, bh, 12)
    ctx.set_source_rgba(0.05, 0.07, 0.11, 0.92)
    ctx.fill_preserve()
    ctx.set_source_rgb(*rgb)
    ctx.set_line_width(7.0)
    ctx.stroke()
    draw_text(ctx, label, 0, 20, size=56, rgb=rgb, bold=True, align="center")
    ctx.restore()


def draw_journal_card(ctx, date_str, location_str, headline, subline, prog):
    ctx.set_source_rgb(0.05, 0.08, 0.11)
    ctx.rectangle(0, 0, W, H)
    ctx.fill()

    x0, y0, cw, ch = 100, 360, W - 200, 960
    rounded_rect(ctx, x0, y0, cw, ch, 18)
    ctx.set_source_rgb(*PAPER)
    ctx.fill()

    ctx.set_source_rgba(0.55, 0.62, 0.68, 0.35)
    ctx.set_line_width(2.0)
    for ly in range(y0 + 120, y0 + ch - 60, 64):
        ctx.move_to(x0 + 48, ly)
        ctx.line_to(x0 + cw - 48, ly)
    ctx.stroke()

    ctx.set_source_rgba(*CRIMSON, 0.35)
    ctx.move_to(x0 + 96, y0 + 20)
    ctx.line_to(x0 + 96, y0 + ch - 20)
    ctx.stroke()

    p = ease_out(prog)
    draw_text(ctx, date_str, W / 2, y0 + 230, size=62, rgb=INK, bold=True, italic=True, align="center", alpha=p)

    ul_w = 640 * ease_out((prog - 0.15) / 0.65)
    if ul_w > 4:
        ctx.set_source_rgb(*CRIMSON)
        ctx.set_line_width(8.0)
        ctx.move_to(W / 2 - 320, y0 + 258)
        ctx.line_to(W / 2 - 320 + ul_w, y0 + 258)
        ctx.stroke()

    draw_text(ctx, location_str, W / 2, y0 + 345, size=34, rgb=CRIMSON, bold=True, align="center", alpha=p)
    draw_text(ctx, headline, W / 2, y0 + 540, size=48, rgb=INK, bold=True, align="center", alpha=ease_out((prog - 0.25) / 0.6))
    draw_text(ctx, subline, W / 2, y0 + 625, size=34, rgb=(0.28, 0.34, 0.40), bold=False, align="center", alpha=ease_out((prog - 0.35) / 0.6))


def render_frame(ctx, t, duration):
    u = t / max(1.0, duration)

    if u < 0.10:
        draw_journal_card(
            ctx,
            "18 September 2022",
            "TRAVELODGE • BICESTER, UK",
            "UNDER POLICE PROTECTION",
            "A 17-year-old suspect with no laptop.",
            u / 0.06,
        )

    elif u < 0.21:
        lt = (u - 0.10) / 0.11
        draw_blueprint_bg(ctx, "HARDWARE INVENTORY", t, duration)
        rounded_rect(ctx, 140, 340, W - 280, 230, 14)
        ctx.set_source_rgb(*CARD)
        ctx.fill_preserve()
        ctx.set_source_rgb(*CRIMSON)
        ctx.set_line_width(4.5)
        ctx.stroke()
        draw_text(ctx, "LAPTOP", W / 2, 425, size=46, rgb=MUTED, bold=True, align="center")
        draw_text(ctx, "[ X ] CONFISCATED", W / 2, 510, size=50, rgb=CRIMSON, bold=True, align="center")

        items = [
            ("01. HOTEL TV", 660, lt > 0.18, CYAN),
            ("02. SMARTPHONE", 850, lt > 0.42, CYAN),
            ("03. AMAZON FIRE TV STICK", 1040, lt > 0.65, AMBER),
        ]
        for label, y, show, clr in items:
            if show:
                rounded_rect(ctx, 110, y, W - 220, 138, 14)
                ctx.set_source_rgb(*CARD)
                ctx.fill_preserve()
                ctx.set_source_rgb(*clr)
                ctx.set_line_width(4.5)
                ctx.stroke()
                draw_text(ctx, label, W / 2, y + 86, size=44, rgb=clr, bold=True, align="center")

    elif u < 0.29:
        lt = (u - 0.21) / 0.08
        p = ease_out(lt / 0.55)
        draw_blueprint_bg(ctx, "NETWORK BREACH // LIVE", t, duration)

        rounded_rect(ctx, 150, 350, W - 300, 220, 16)
        ctx.set_source_rgb(*CARD)
        ctx.fill_preserve()
        ctx.set_source_rgb(*CRIMSON)
        ctx.set_line_width(5.5)
        ctx.stroke()
        draw_text(ctx, "ROCKSTAR GAMES", W / 2, 445, size=58, rgb=WHITE, bold=True, align="center")
        draw_text(ctx, "INTERNAL SERVERS", W / 2, 515, size=32, rgb=CRIMSON, bold=True, align="center")

        rounded_rect(ctx, 210, 1210, W - 420, 140, 14)
        ctx.set_source_rgb(*CARD)
        ctx.fill_preserve()
        ctx.set_source_rgb(*AMBER)
        ctx.set_line_width(5.0)
        ctx.stroke()
        draw_text(ctx, "FIRE TV STICK", W / 2, 1298, size=46, rgb=AMBER, bold=True, align="center")

        beam_top = 1210 - (1210 - 570) * p
        ctx.set_source_rgb(*CYAN)
        ctx.set_line_width(14.0)
        ctx.move_to(W / 2, 1210)
        ctx.line_to(W / 2, beam_top)
        ctx.stroke()
        for i in range(6):
            py = 1210 - ((t * 420 + i * 110) % 640)
            if py > beam_top:
                ctx.set_source_rgb(*AMBER)
                ctx.arc(W / 2, py, 16, 0, 2 * math.pi)
                ctx.fill()

        if lt > 0.45:
            draw_stamp(ctx, "BREACH DETECTED", W / 2, 890, CRIMSON, (lt - 0.45) / 0.25)

    elif u < 0.39:
        lt = (u - 0.29) / 0.10
        p = ease_out(lt / 0.6)
        draw_blueprint_bg(ctx, "DATA EXFILTRATION", t, duration)
        draw_text(ctx, "ARION KURTAJ", W / 2, 375, size=62, rgb=CYAN, bold=True, align="center")

        rounded_rect(ctx, 110, 440, W - 220, 390, 18)
        ctx.set_source_rgb(*CARD)
        ctx.fill_preserve()
        ctx.set_source_rgb(*AMBER)
        ctx.set_line_width(5.0)
        ctx.stroke()
        draw_text(ctx, f"{int(90 * p)}", W / 2, 620, size=140, rgb=AMBER, bold=True, align="center")
        draw_text(ctx, "UNFINISHED GTA 6 CLIPS", W / 2, 715, size=44, rgb=WHITE, bold=True, align="center")
        draw_text(ctx, "NEARLY 1 HOUR OF GAMEPLAY", W / 2, 780, size=32, rgb=MUTED, bold=False, align="center")

        for r in range(3):
            for c in range(6):
                if r * 6 + c < int(18 * p):
                    gx, gy = 140 + c * 138, 920 + r * 115
                    rounded_rect(ctx, gx, gy, 108, 78, 8)
                    ctx.set_source_rgb(*CARD)
                    ctx.fill_preserve()
                    ctx.set_source_rgb(*CYAN)
                    ctx.set_line_width(3.0)
                    ctx.stroke()

    elif u < 0.47:
        draw_blueprint_bg(ctx, "SLACK // #INTERNAL", t, duration)
        rounded_rect(ctx, 95, 390, W - 190, 760, 18)
        ctx.set_source_rgb(*CARD)
        ctx.fill_preserve()
        ctx.set_source_rgb(*CRIMSON)
        ctx.set_line_width(5.0)
        ctx.stroke()

        ctx.set_source_rgba(*CRIMSON, 0.25)
        ctx.rectangle(95, 390, W - 190, 95)
        ctx.fill()
        draw_text(ctx, "# rockstar-internal-slack", 135, 452, size=36, rgb=CRIMSON, bold=True)
        draw_text(ctx, "USER: teapotuberhacker", 135, 565, size=34, rgb=AMBER, bold=True)
        draw_text(ctx, '"I have the GTA 6 source code.', 135, 685, size=42, rgb=WHITE, bold=True)
        draw_text(ctx, " Negotiate within 24 HOURS", 135, 755, size=42, rgb=WHITE, bold=True)
        draw_text(ctx, ' or I leak everything."', 135, 825, size=42, rgb=CRIMSON, bold=True)

        rounded_rect(ctx, 210, 940, W - 420, 125, 12)
        ctx.set_source_rgba(*CRIMSON, 0.2)
        ctx.fill_preserve()
        ctx.set_source_rgb(*CRIMSON)
        ctx.set_line_width(4.0)
        ctx.stroke()
        draw_text(ctx, "DEADLINE: 24:00:00", W / 2, 1020, size=46, rgb=CRIMSON, bold=True, align="center")

    elif u < 0.57:
        lt = (u - 0.47) / 0.10
        draw_blueprint_bg(ctx, "DAMAGE ASSESSMENT", t, duration)
        draw_text(ctx, "ROCKSTAR'S RESPONSE", W / 2, 370, size=42, rgb=MUTED, bold=True, align="center")
        draw_stamp(ctx, "REFUSED", W / 2, 505, CRIMSON, lt / 0.25, angle_deg=-6.0)

        if lt > 0.25:
            rounded_rect(ctx, 110, 670, W - 220, 290, 18)
            ctx.set_source_rgb(*CARD)
            ctx.fill_preserve()
            ctx.set_source_rgb(*AMBER)
            ctx.set_line_width(5.0)
            ctx.stroke()
            draw_text(ctx, "$5 MILLION", W / 2, 810, size=92, rgb=AMBER, bold=True, align="center")
            draw_text(ctx, "RECOVERY COST VS $1B+ BUDGET", W / 2, 895, size=34, rgb=WHITE, bold=True, align="center")

        if lt > 0.55:
            draw_stamp(ctx, "RUINED?", W / 2, 1150, AMBER, (lt - 0.55) / 0.25, angle_deg=7.0)

    elif u < 0.67:
        draw_blueprint_bg(ctx, "THE PARADOX", t, duration)
        draw_text(ctx, "INSTEAD...", W / 2, 375, size=44, rgb=MUTED, bold=True, align="center")
        draw_text(ctx, "THE OPPOSITE", W / 2, 485, size=86, rgb=CYAN, bold=True, align="center")
        draw_text(ctx, "HAPPENED", W / 2, 585, size=86, rgb=CYAN, bold=True, align="center")

        cx, cy = W / 2, 990
        for ri in range(4):
            rad = ((t * 140 + ri * 95) % 340) + 40
            ctx.set_source_rgba(*AMBER, max(0.1, 1.0 - rad / 380.0))
            ctx.set_line_width(5.0)
            ctx.arc(cx, cy, rad, 0, 2 * math.pi)
            ctx.stroke()
        draw_text(ctx, "ROCKSTAR STAYED SILENT", cx, cy + 16, size=46, rgb=WHITE, bold=True, align="center")
        draw_text(ctx, "CURIOSITY  ->  OBSESSION", W / 2, 1410, size=48, rgb=AMBER, bold=True, align="center")

    elif u < 0.79:
        lt = (u - 0.67) / 0.12
        p1 = ease_out(lt / 0.35)
        p2 = ease_out((lt - 0.35) / 0.45)
        draw_blueprint_bg(ctx, "VIRAL SURGE // VIEWS", t, duration)
        draw_text(ctx, "TRAILER VIEWERSHIP", W / 2, 385, size=56, rgb=WHITE, bold=True, align="center")

        base_y = 1270
        h1 = 165 * p1
        ctx.set_source_rgb(*CYAN)
        ctx.rectangle(190, base_y - h1, 270, h1)
        ctx.fill()
        draw_text(ctx, f"{90.4 * p1:.1f}M", 325, base_y - h1 - 28, size=58, rgb=CYAN, bold=True, align="center")
        draw_text(ctx, "TRAILER 1", 325, base_y + 58, size=36, rgb=WHITE, bold=True, align="center")
        draw_text(ctx, "(24 HOURS)", 325, base_y + 104, size=28, rgb=MUTED, bold=False, align="center")

        if lt > 0.35:
            h2 = 720 * p2
            ctx.set_source_rgb(*AMBER)
            ctx.rectangle(620, base_y - h2, 270, h2)
            ctx.fill()
            draw_text(ctx, f"{int(475 * p2)}M", 755, base_y - h2 - 28, size=58, rgb=AMBER, bold=True, align="center")
            draw_text(ctx, "TRAILER 2", 755, base_y + 58, size=36, rgb=WHITE, bold=True, align="center")
            draw_text(ctx, "(5.2X SURGE)", 755, base_y + 104, size=28, rgb=AMBER, bold=True, align="center")

        ctx.set_source_rgb(*WHITE)
        ctx.set_line_width(4.0)
        ctx.move_to(110, base_y)
        ctx.line_to(W - 110, base_y)
        ctx.stroke()

    elif u < 0.88:
        lt = (u - 0.79) / 0.09
        p = ease_out(lt / 0.5)
        draw_blueprint_bg(ctx, "PRE-LAUNCH REVENUE", t, duration)
        rounded_rect(ctx, 100, 480, W - 200, 440, 20)
        ctx.set_source_rgb(*CARD)
        ctx.fill_preserve()
        ctx.set_source_rgb(*GREEN)
        ctx.set_line_width(6.0)
        ctx.stroke()
        draw_text(ctx, f"${2.3 * p:.1f} BILLION", W / 2, 665, size=104, rgb=GREEN, bold=True, align="center")
        draw_text(ctx, "EARNED BEFORE LAUNCH", W / 2, 770, size=44, rgb=WHITE, bold=True, align="center")
        draw_text(ctx, "24M+ DIGITAL PRE-ORDERS", W / 2, 845, size=34, rgb=MUTED, bold=False, align="center")

        if lt > 0.45:
            draw_stamp(ctx, "RECORD", W / 2, 1140, GREEN, (lt - 0.45) / 0.25, angle_deg=-7.0)

    else:
        lt = (u - 0.88) / 0.12
        draw_blueprint_bg(ctx, "FINAL VERDICT // NOV 2026", t, duration)

        rounded_rect(ctx, 100, 380, W - 200, 330, 18)
        ctx.set_source_rgb(*CARD)
        ctx.fill_preserve()
        ctx.set_source_rgb(*CRIMSON)
        ctx.set_line_width(5.0)
        ctx.stroke()
        draw_text(ctx, "16 NOVEMBER 2026", W / 2, 485, size=58, rgb=CRIMSON, bold=True, align="center")
        draw_text(ctx, "KURTAJ PLEADED GUILTY", W / 2, 575, size=44, rgb=WHITE, bold=True, align="center")
        draw_text(ctx, "WOOLWICH CROWN COURT, LONDON", W / 2, 645, size=30, rgb=MUTED, bold=False, align="center")

        draw_text(ctx, "JUST 3 DAYS LATER...", W / 2, 815, size=46, rgb=AMBER, bold=True, align="center")

        if lt > 0.30:
            rounded_rect(ctx, 100, 910, W - 200, 360, 18)
            ctx.set_source_rgb(*CARD)
            ctx.fill_preserve()
            ctx.set_source_rgb(*GREEN)
            ctx.set_line_width(6.0)
            ctx.stroke()
            draw_text(ctx, "19 NOVEMBER 2026", W / 2, 1020, size=58, rgb=GREEN, bold=True, align="center")
            draw_text(ctx, "HISTORY'S BIGGEST LAUNCH", W / 2, 1115, size=46, rgb=WHITE, bold=True, align="center")
            draw_text(ctx, "GRAND THEFT AUTO VI", W / 2, 1195, size=38, rgb=CYAN, bold=True, align="center")


def generate_sfx_track(duration, path):
    sr = 44100
    n = int(sr * duration)
    buf = np.zeros(n, dtype=np.float32)

    def add_tone(t0, dur, freq, amp=0.18, decay=6.0):
        i0 = int(t0 * sr)
        i1 = min(n, int((t0 + dur) * sr))
        if i0 >= n or i1 <= i0:
            return
        ts = np.arange(i1 - i0) / sr
        env = np.exp(-decay * ts)
        buf[i0:i1] += (amp * env * np.sin(2 * np.pi * freq * ts)).astype(np.float32)

    for frac, freq in [
        (0.00, 75), (0.10, 520), (0.21, 140), (0.29, 880),
        (0.39, 640), (0.47, 95), (0.57, 440), (0.67, 660),
        (0.79, 80), (0.88, 110)
    ]:
        add_tone(frac * duration, 0.35, freq, amp=0.16, decay=7.5)

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
    print(f"Rendering {total_frames} frames ({duration:.2f}s) at {W}x{H}@{FPS}fps | VO={vo}")

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
            "-filter_complex", "[1:a]volume=0.35[sfx];[2:a]volume=1.0[vo];[sfx][vo]amix=inputs=2:duration=longest[a]",
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
