# hitl_pygame.py
"""
Graphical HITL rating tool (Pygame version).

• Keys 1-9,0      → rate current candidate 1-10  (0 == 10)
• ← / → or A / D  → browse candidates
• RETURN / ENTER  → finish and return scores
• ESC             → abort without saving

Visuals
-------
Each candidate is drawn as a stack of thin 3-D “discs” in perspective.
Slice i gets an ellipse whose x-radius = r_i and y-radius = 0.35·r_i
so it reads as a turned cylinder.  Largest radius auto-scales to 300 px.

Usage
-----
scores = ask_scores_pygame(candidate_ids, population)
"""

import math
from typing import Dict, List
import colorsys
import pygame
import config as C
from shape import Shape


# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
WIDTH, HEIGHT = 900, 640
MARGIN_TOP = 40
BG_COLOR = (30, 30, 30)
FG_COLOR = (230, 230, 230)
DISC_COLOR = (90, 180, 250)
FONT_NAME = "consolas"
FPS = 60


# --------------------------------------------------------------------------- #
# Helper: convert metres → screen px given max radius
# --------------------------------------------------------------------------- #
def scale_radii(radii: List[float], max_px: int = 300) -> List[int]:
    r_max = max(radii)
    scale = max_px / r_max
    return [int(r * scale) for r in radii]

def slice_color(i: int, n: int) -> tuple[int, int, int]:
    """
    Return an RGB tuple for slice i out of n, using an HSV hue sweep.
    Hue goes 220° (blue) → 0° (red).
    """
    hue = 220/360 * (1 - i/(n-1))          # 0..1   (blue→red)
    r, g, b = colorsys.hsv_to_rgb(hue, 0.8, 0.95)
    return int(r*255), int(g*255), int(b*255)
    
# --------------------------------------------------------------------------- #
def draw_shape(surface, shape: Shape, cx: int, cy: int):
    """Render a stack of colored ellipses (largest radius on bottom)."""
    scaled = scale_radii(shape.radii)
    n = len(scaled)
    slice_h = 6  # px thickness for each disc

    current_y = cy - n * slice_h // 2
    for i, r_px in enumerate(reversed(scaled)):        # bottom-to-top
        color = slice_color(i, n)
        ellipse = pygame.Rect(0, 0, 2*r_px, int(0.7*r_px))
        ellipse.center = (cx, current_y)
        pygame.draw.ellipse(surface, color, ellipse)
        current_y += slice_h


# --------------------------------------------------------------------------- #
def render_text(surface, font, txt: str, x: int, y: int, color=FG_COLOR):
    img = font.render(txt, True, color)
    surface.blit(img, (x, y))


# --------------------------------------------------------------------------- #
def ask_scores_pygame(candidate_ids: List[int], population) -> Dict[int, int]:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Rate Shapes 1-10   |   ←/→ next   ENTER = done")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(FONT_NAME, 20)

    scores: Dict[int, int] = {cid: None for cid in candidate_ids}
    idx_pointer = 0  # index in candidate_ids list

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return {}  # aborted
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE,):
                    pygame.quit()
                    return {}  # aborted
                # browse
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    idx_pointer = (idx_pointer + 1) % len(candidate_ids)
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    idx_pointer = (idx_pointer - 1) % len(candidate_ids)
                # rate 1-9,0 (0 == 10)
                if pygame.K_1 <= event.key <= pygame.K_9:
                    scores[candidate_ids[idx_pointer]] = event.key - pygame.K_0
                if event.key == pygame.K_0:
                    scores[candidate_ids[idx_pointer]] = 10
                # finish
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if all(v is not None for v in scores.values()):
                        running = False

        # drawing
        screen.fill(BG_COLOR)
        cid = candidate_ids[idx_pointer]
        shape = population.shapes[cid]

        # draw shape
        draw_shape(screen, shape, WIDTH // 2, HEIGHT // 2 + 40)

        # HUD
        render_text(
            screen,
            font,
            f"Candidate {cid}  |  Slice count: {len(shape.radii)}",
            20,
            10,
        )
        render_text(
            screen,
            font,
            f"Spin score: {shape.t_spin:.4f}",
            20,
            35,
        )
        rating = scores[cid]
        render_text(
            screen,
            font,
            f"Current rating: {rating if rating is not None else '—'}",
            20,
            60,
        )
        render_text(
            screen,
            font,
            "Keys: 1-9,0 = rate   ←/→ = browse   ENTER = finish",
            20,
            HEIGHT - 30,
        )

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    return scores
