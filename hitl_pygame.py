"""Rank axisymmetric shapes (adaptive merge-sort GUI).

← / A  pick left   → / D  pick right   Esc abort
"""
from __future__ import annotations
import math, colorsys, numpy as np, pygame
import pygame.gfxdraw as gfx
from typing import List, Dict
from shape import Shape

# ── config ────────────────────────────────────────────────────────────
W, H          = 1500, 640
BG, FG        = (30, 30, 30), (230, 230, 230)
FONT_NAME     = "consolas"
FPS, SLICE    = 60, 6
STRETCH       = 2.5
CX_L, CX_R    = W // 4, 3 * W // 4
LIGHT         = tuple(c / math.hypot(-0.6, -0.8) for c in (-0.6, -0.8))

# ── helpers ───────────────────────────────────────────────────────────
def scale(rad, mx: int = 300) -> list[int]:
    """Return radii scaled so the largest fits into *mx* pixels."""
    rad = np.asarray(rad, dtype=float)        # works for list/tuple too
    if rad.size == 0:                         # empty → nothing to draw
        return []
    k = mx / rad.max()                        # avoid /0: rad.max() ≥ 0 here
    return (rad * k).astype(int).tolist()


def grad(i: int, n: int) -> tuple[int, int, int]:
    hue = 220 / 360 * (1 - i / (n - 1 or 1))
    r, g, b = colorsys.hsv_to_rgb(hue, .8, .95)
    return int(r * 255), int(g * 255), int(b * 255)

# ── drawing ───────────────────────────────────────────────────────────
def draw_3d(dst: pygame.Surface, shp: Shape, cx: int, cy: int) -> None:
    radii = scale(shp.radii)
    if not radii: return
    n, h, r_max = len(radii), len(radii) * SLICE, max(radii)
    cols = np.array([grad(i, n) for i in range(n)], float)
    buf  = np.zeros((h, 2 * r_max + 1, 4), np.uint8)
    Lx, Ly = LIGHT

    for y in range(h):
        i0, t = divmod(y, SLICE); t /= SLICE
        i0 = min(i0, n - 2)
        r   = int((1 - t) * radii[i0] + t * radii[i0 + 1])
        col = (1 - t) * cols[i0] + t * cols[i0 + 1]
        if not r: continue
        xs  = np.arange(-r, r + 1)
        nx  = xs / r
        nz  = np.sqrt(1 - nx ** 2)
        lam = np.clip(-(nx * Lx + nz * Ly), 0, 1)
        shade = (.25 + .75 * lam)[:, None]
        rgb   = (col * shade).astype(np.uint8)
        cov   = np.clip(r - np.abs(xs) + .5, 0, 1)
        alpha = (cov * 255).astype(np.uint8)
        rgb   = (rgb * cov[:, None]).astype(np.uint8)
        x0    = r_max - r
        buf[y, x0:x0 + 2 * r + 1, :3], buf[y, x0:x0 + 2 * r + 1, 3] = rgb, alpha

    surf = pygame.image.frombuffer(buf.tobytes(), (2 * r_max + 1, h), "RGBA")
    if STRETCH != 1:
        surf = pygame.transform.smoothscale(surf, (surf.get_width(), int(h * STRETCH)))
    dst.blit(surf, (cx - surf.get_width() // 2, cy - surf.get_height() // 2))

def draw_section(dst: pygame.Surface, shp: Shape, x: int, y: int) -> None:
    radii = np.asarray(scale(shp.radii, 120))
    if radii.size == 0: return
    n, h, y_top = len(radii), len(radii) * SLICE, y - (len(radii) * SLICE) // 2
    ys = np.arange(h)
    idx = np.clip(ys // SLICE, 0, n - 2)
    t   = (ys % SLICE) / SLICE
    r_y = (1 - t) * radii[idx] + t * radii[idx + 1]
    pts = [(x, y_top)] + [(x + int(r), y_top + i) for i, r in enumerate(r_y)] + [(x, y_top + h)]
    pygame.draw.line(dst, (120, 120, 120), (x, y_top), (x, y_top + h), 1)
    gfx.filled_polygon(dst, pts, (60, 200, 80, 150))
    gfx.aapolygon(dst, pts, (200, 240, 100))

def blit(dst, font, txt, x, y):
    dst.blit(font.render(txt, True, FG), (x, y))

# ── public API ────────────────────────────────────────────────────────
def ask_scores_pygame(ids, pop):
    ids = list(ids)
    if not ids: return {}
    pygame.init()
    try:
        scr = pygame.display.set_mode((W, H))
        pygame.display.set_caption("Rate shapes  |  ← / → choose")
        clk  = pygame.time.Clock()
        font = pygame.font.SysFont(FONT_NAME, 20)

        def choose(a, b, done, total):
            while True:
                for e in pygame.event.get():
                    if e.type == pygame.QUIT: return None
                    if e.type == pygame.KEYDOWN:
                        if e.key == pygame.K_ESCAPE:           return None
                        if e.key in (pygame.K_LEFT, pygame.K_a): return a
                        if e.key in (pygame.K_RIGHT, pygame.K_d): return b
                scr.fill(BG)
                cy = H // 2 + 40
                draw_3d(scr, pop.shapes[a], CX_L, cy)
                draw_section(scr, pop.shapes[a], CX_L, cy - 200)
                draw_3d(scr, pop.shapes[b], CX_R, cy)
                draw_section(scr, pop.shapes[b], CX_R, cy - 200)
                blit(scr, font, f"Generation: {getattr(pop, 'generation', '?')}", 20, 10)
                blit(scr, font, f"Pair {done}/{total}", 20, 35)
                blit(scr, font, "← / A : left    → / D : right", 20, H - 30)
                pygame.display.flip(); clk.tick(FPS)

        def merge(L, R, done, total):
            out = []; i = j = 0
            while i < len(L) and j < len(R):
                pick = choose(L[i], R[j], len(done) + 1, total)
                if pick is None: return None
                out.append(pick); done.append(pick)
                if pick == L[i]: i += 1
                else:            j += 1
            return out + L[i:] + R[j:]

        q     = [[i] for i in ids]
        total = math.ceil(len(ids) * math.log2(max(len(ids), 1)))
        prog  = []
        while len(q) > 1:
            nxt = []
            for k in range(0, len(q), 2):
                if k + 1 == len(q): nxt.append(q[k]); continue
                m = merge(q[k], q[k + 1], prog, total)
                if m is None: return {}
                nxt.append(m)
            q = nxt

        ranks: Dict[int, int] = {cid: r for r, cid in enumerate(q[0], 1)}
        for cid, r in ranks.items():
            s: Shape = pop.shapes[cid]
            s.h_anchor = float(r); s.anchor_r = s.radii.copy(); s.update_guard()
        return ranks
    finally:
        pygame.quit()
