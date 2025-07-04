"""
Graphical HITL rating tool (Pygame version).

UPGRADE v3
=========
* Splits human rating into an **anchor** and **guard** score per shape.
  - `h_anchor`: decaying raw rating (1–10)
  - `h_guard`: proximity bonus recalculated each rating
* On each rating key, updates both fields and calls `update_guard()`.

Key bindings
------------
    1-9,0   rate candidate 1-10  (0 == 10)
    ← / →   browse candidates   (A / D also)
    ENTER   finish & save ratings (only when all rated)
    ESC     abort without saving
"""

import math
from typing import Dict, List
import colorsys
import pygame
import config as C
from shape import Shape

# --------------------------------------------------------------------------- #
# Window / colour constants
# --------------------------------------------------------------------------- #
WIDTH, HEIGHT = 900, 640
MARGIN_TOP = 40
BG_COLOR = (30, 30, 30)
FG_COLOR = (230, 230, 230)
DISC_COLOR = (90, 180, 250)
FONT_NAME = "consolas"
FPS = 60

# Drawing layout --------------------------------------------------------------
CX_3D = WIDTH // 3              # x-centre of 3-D view
CX_2D = 2 * WIDTH // 3 + 20     # x-origin of 2-D outline
SLICE_PIX = 6                   # vertical px per slice for both views

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def scale_radii(radii: List[float], max_px: int = 300) -> List[int]:
    """Scale radii so the largest becomes *max_px* pixels."""
    r_max = max(radii) or 1e-6
    scale = max_px / r_max
    return [int(r * scale) for r in radii]


def slice_color(i: int, n: int) -> tuple[int, int, int]:
    """HSV → RGB colour ramp (blue→red)."""
    hue = 220 / 360 * (1 - i / (n - 1))
    r, g, b = colorsys.hsv_to_rgb(hue, 0.8, 0.95)
    return int(r * 255), int(g * 255), int(b * 255)

# --------------------------------------------------------------------------- #
# Drawing primitives
# --------------------------------------------------------------------------- #

def draw_shape_3d(surface, shape: Shape, cx: int, cy: int):
    """Render an axisymmetric body as a stack of coloured ellipses."""
    scaled = scale_radii(shape.radii)
    n = len(scaled)
    y = cy - n * SLICE_PIX // 2
    for i, r_px in enumerate(reversed(scaled)):
        col = slice_color(i, n)
        ellipse = pygame.Rect(0, 0, 2 * r_px, int(0.7 * r_px))
        ellipse.center = (cx, y)
        pygame.draw.ellipse(surface, col, ellipse)
        y += SLICE_PIX


def draw_cross_section(surface, shape: Shape, x0: int, y0: int):
    """Draw the radius profile as a poly-line (cross-section view)."""
    scaled = scale_radii(shape.radii, max_px=120)
    n = len(scaled)
    pts = []
    y = y0 - n * SLICE_PIX // 2
    for r_px in reversed(scaled):
        pts.append((x0 + r_px, y))
        y += SLICE_PIX
    pygame.draw.line(surface, (100, 100, 100), (x0, y0 - n * SLICE_PIX // 2), (x0, y0 + n * SLICE_PIX // 2), 1)
    if len(pts) > 1:
        pygame.draw.lines(surface, (200, 240, 100), False, pts, 2)


def render_text(surface, font, txt: str, x: int, y: int, color=FG_COLOR):
    surface.blit(font.render(txt, True, color), (x, y))

# --------------------------------------------------------------------------- #
# Main HITL function
# --------------------------------------------------------------------------- #

def ask_scores_pygame(candidate_ids: List[int], population) -> Dict[int, int]:
    """Show interactive rating UI and return dict {candidate_id: score}."""
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Rate Shapes | ←/→ browse | ENTER finish")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(FONT_NAME, 20)

    scores: Dict[int, int] = {cid: None for cid in candidate_ids}
    idx = 0
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return {}
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return {}
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    idx = (idx + 1) % len(candidate_ids)
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    idx = (idx - 1) % len(candidate_ids)
                if pygame.K_1 <= event.key <= pygame.K_9 or event.key == pygame.K_0:
                    # record rating and update anchor/guard
                    rating = (event.key - pygame.K_0) if event.key != pygame.K_0 else 10
                    cid = candidate_ids[idx]
                    scores[cid] = rating
                    sh = population.shapes[cid]
                    sh.h_anchor = float(rating)
                    sh.anchor_r = sh.radii.copy()
                    sh.update_guard()
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if all(v is not None for v in scores.values()):
                        running = False

        screen.fill(BG_COLOR)
        shape = population.shapes[candidate_ids[idx]]
        cy = HEIGHT // 2 + 40
        draw_shape_3d(screen, shape, CX_3D, cy)
        draw_cross_section(screen, shape, CX_2D, cy)

        render_text(screen, font, f"Generation: {getattr(population, 'generation', '?')}", 20, 10)
        render_text(screen, font, f"Candidate {idx+1}/{len(candidate_ids)}  |  slices {len(shape.radii)}", 20, 35)
        render_text(screen, font, f"Spin score: {shape.t_spin:.4f}", 20, 60)
        rating = scores[candidate_ids[idx]]
        render_text(screen, font, f"Rating: {rating if rating is not None else '—'} (1-10)", 20, 85)
        render_text(screen, font, "Keys 1-9,0=rate  ←/→ browse  ENTER=done", 20, HEIGHT - 30)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    return scores
