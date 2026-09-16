"""
Professional Live Design Engine
================================

Responsible for:
- Canvas creation
- Dynamic layouts
- Gradient backgrounds
- Glow effects
- Decorative elements
- Typography
- Style presets
- Design composition

The Discord bot should call this module instead of handling
visual-generation logic directly.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont, ImageFilter


# ============================================================
# GLOBAL SETTINGS
# ============================================================

WIDTH = 1080
HEIGHT = 1920

PROJECT_ROOT = Path(__file__).resolve().parent


# ============================================================
# STYLE CONFIGURATION
# ============================================================

@dataclass(frozen=True)
class StyleConfig:
    name: str
    background_top: tuple[int, int, int]
    background_bottom: tuple[int, int, int]
    primary: tuple[int, int, int]
    secondary: tuple[int, int, int]
    text: tuple[int, int, int]
    muted_text: tuple[int, int, int]
    panel_alpha: int
    glow_strength: int
    shape_density: int
    corner_radius: int


STYLES: dict[str, StyleConfig] = {

    "purple": StyleConfig(
        name="Purple",
        background_top=(10, 5, 25),
        background_bottom=(38, 8, 70),
        primary=(157, 72, 255),
        secondary=(238, 75, 255),
        text=(255, 255, 255),
        muted_text=(205, 190, 225),
        panel_alpha=175,
        glow_strength=190,
        shape_density=22,
        corner_radius=42,
    ),

    "blue": StyleConfig(
        name="Blue",
        background_top=(3, 10, 28),
        background_bottom=(5, 45, 90),
        primary=(30, 120, 255),
        secondary=(0, 220, 255),
        text=(255, 255, 255),
        muted_text=(190, 220, 245),
        panel_alpha=175,
        glow_strength=190,
        shape_density=22,
        corner_radius=42,
    ),

    "red": StyleConfig(
        name="Red",
        background_top=(28, 3, 8),
        background_bottom=(75, 8, 20),
        primary=(255, 45, 70),
        secondary=(255, 130, 35),
        text=(255, 255, 255),
        muted_text=(245, 195, 195),
        panel_alpha=175,
        glow_strength=190,
        shape_density=22,
        corner_radius=42,
    ),

    "green": StyleConfig(
        name="Green",
        background_top=(2, 22, 15),
        background_bottom=(4, 65, 42),
        primary=(25, 230, 125),
        secondary=(145, 255, 75),
        text=(255, 255, 255),
        muted_text=(190, 235, 210),
        panel_alpha=175,
        glow_strength=190,
        shape_density=22,
        corner_radius=42,
    ),

    "gold": StyleConfig(
        name="Gold",
        background_top=(24, 15, 3),
        background_bottom=(65, 40, 5),
        primary=(255, 190, 40),
        secondary=(255, 230, 120),
        text=(255, 255, 255),
        muted_text=(240, 220, 175),
        panel_alpha=175,
        glow_strength=180,
        shape_density=20,
        corner_radius=42,
    ),

    "pink": StyleConfig(
        name="Pink",
        background_top=(30, 3, 22),
        background_bottom=(75, 5, 48),
        primary=(255, 45, 175),
        secondary=(255, 125, 230),
        text=(255, 255, 255),
        muted_text=(240, 195, 225),
        panel_alpha=175,
        glow_strength=195,
        shape_density=24,
        corner_radius=42,
    ),
}


# ============================================================
# FONT SYSTEM
# ============================================================

class FontSystem:
    """
    Searches for usable fonts on the server.

    A custom fonts/ directory can later be added to the project.
    """

    SEARCH_ROOTS = [
        PROJECT_ROOT / "fonts",
        Path("/usr/share/fonts"),
        Path("/usr/local/share/fonts"),
        Path("/usr/share/fonts/truetype"),
    ]

    BOLD_NAMES = (
        "DejaVuSans-Bold.ttf",
        "LiberationSans-Bold.ttf",
    )

    REGULAR_NAMES = (
        "DejaVuSans.ttf",
        "LiberationSans-Regular.ttf",
    )

    @classmethod
    def load(cls, size: int, bold: bool = True):
        names = (
            cls.BOLD_NAMES
            if bold
            else cls.REGULAR_NAMES
        )

        for root in cls.SEARCH_ROOTS:

            if not root.exists():
                continue

            for font_name in names:

                matches = list(root.rglob(font_name))

                if not matches:
                    continue

                try:
                    return ImageFont.truetype(
                        str(matches[0]),
                        size=size,
                    )
                except OSError:
                    continue

        return ImageFont.load_default()


# ============================================================
# COLOR UTILITIES
# ============================================================

def rgba(
    color: tuple[int, int, int],
    alpha: int,
) -> tuple[int, int, int, int]:
    return color[0], color[1], color[2], alpha


def lerp(
    start: tuple[int, int, int],
    end: tuple[int, int, int],
    amount: float,
) -> tuple[int, int, int]:

    amount = max(0.0, min(1.0, amount))

    return tuple(
        int(
            start[index]
            + (end[index] - start[index]) * amount
        )
        for index in range(3)
    )


# ============================================================
# BACKGROUND ENGINE
# ============================================================

class BackgroundEngine:

    @staticmethod
    def gradient(
        style: StyleConfig,
    ) -> Image.Image:

        image = Image.new(
            "RGBA",
            (WIDTH, HEIGHT),
        )

        pixels = image.load()

        for y in range(HEIGHT):

            progress = y / (HEIGHT - 1)

            color = lerp(
                style.background_top,
                style.background_bottom,
                progress,
            )

            for x in range(WIDTH):
                pixels[x, y] = (
                    color[0],
                    color[1],
                    color[2],
                    255,
                )

        return image

    @staticmethod
    def add_glows(
        image: Image.Image,
        style: StyleConfig,
        seed: int,
    ) -> Image.Image:

        random.seed(seed)

        glow_layer = Image.new(
            "RGBA",
            image.size,
            (0, 0, 0, 0),
        )

        draw = ImageDraw.Draw(glow_layer)

        positions = [
            (
                random.randint(-200, 300),
                random.randint(-100, 500),
                style.primary,
            ),
            (
                random.randint(700, 1150),
                random.randint(400, 1000),
                style.secondary,
            ),
            (
                random.randint(-100, 500),
                random.randint(1250, 1900),
                style.secondary,
            ),
        ]

        for x, y, color in positions:

            radius = random.randint(300, 550)

            draw.ellipse(
                (
                    x - radius,
                    y - radius,
                    x + radius,
                    y + radius,
                ),
                fill=rgba(
                    color,
                    style.glow_strength,
                ),
            )

        glow_layer = glow_layer.filter(
            ImageFilter.GaussianBlur(150)
        )

        return Image.alpha_composite(
            image,
            glow_layer,
        )


# ============================================================
# DECORATION ENGINE
# ============================================================

class DecorationEngine:

    @staticmethod
    def grid(
        image: Image.Image,
        opacity: int = 15,
    ) -> Image.Image:

        layer = Image.new(
            "RGBA",
            image.size,
            (0, 0, 0, 0),
        )

        draw = ImageDraw.Draw(layer)

        spacing = 80

        for x in range(
            0,
            WIDTH + spacing,
            spacing,
        ):
            draw.line(
                [(x, 0), (x, HEIGHT)],
                fill=(255, 255, 255, opacity),
                width=1,
            )

        for y in range(
            0,
            HEIGHT + spacing,
            spacing,
        ):
            draw.line(
                [(0, y), (WIDTH, y)],
                fill=(255, 255, 255, opacity),
                width=1,
            )

        return Image.alpha_composite(
            image,
            layer,
        )

    @staticmethod
    def particles(
        image: Image.Image,
        style: StyleConfig,
        seed: int,
    ) -> Image.Image:

        random.seed(seed)

        layer = Image.new(
            "RGBA",
            image.size,
            (0, 0, 0, 0),
        )

        draw = ImageDraw.Draw(layer)

        for _ in range(style.shape_density):

            x = random.randint(30, WIDTH - 30)
            y = random.randint(30, HEIGHT - 30)

            size = random.randint(2, 8)

            color = (
                style.primary
                if random.random() > 0.5
                else style.secondary
            )

            draw.ellipse(
                (
                    x - size,
                    y - size,
                    x + size,
                    y + size,
                ),
                fill=rgba(
                    color,
                    random.randint(80, 190),
                ),
            )

        return Image.alpha_composite(
            image,
            layer,
        )

    @staticmethod
    def diagonal_lines(
        image: Image.Image,
        style: StyleConfig,
    ) -> Image.Image:

        layer = Image.new(
            "RGBA",
            image.size,
            (0, 0, 0, 0),
        )

        draw = ImageDraw.Draw(layer)

        for offset in range(
            -HEIGHT,
            WIDTH,
            140,
        ):

            draw.line(
                [
                    (offset, HEIGHT),
                    (offset + HEIGHT, 0),
                ],
                fill=rgba(
                    style.primary,
                    18,
                ),
                width=2,
            )

        return Image.alpha_composite(
            image,
            layer,
        )


# ============================================================
# PANEL ENGINE
# ============================================================

class PanelEngine:

    @staticmethod
    def create_main_panel(
        image: Image.Image,
        style: StyleConfig,
    ) -> Image.Image:

        panel = Image.new(
            "RGBA",
            image.size,
            (0, 0, 0, 0),
        )

        draw = ImageDraw.Draw(panel)

        x1 = 65
        y1 = 330
        x2 = WIDTH - 65
        y2 = 1460

        # Glow behind panel
        glow = Image.new(
            "RGBA",
            image.size,
            (0, 0, 0, 0),
        )

        glow_draw = ImageDraw.Draw(glow)

        for spread in range(60, 5, -5):

            alpha = int(
                8 + (60 - spread) * 0.8
            )

            glow_draw.rounded_rectangle(
                (
                    x1 - spread,
                    y1 - spread,
                    x2 + spread,
                    y2 + spread,
                ),
                radius=(
                    style.corner_radius
                    + spread
                ),
                outline=rgba(
                    style.primary,
                    alpha,
                ),
                width=4,
            )

        glow = glow.filter(
            ImageFilter.GaussianBlur(18)
        )

        image = Image.alpha_composite(
            image,
            glow,
        )

        # Main glass panel
        draw.rounded_rectangle(
            (
                x1,
                y1,
                x2,
                y2,
            ),
            radius=style.corner_radius,
            fill=(
                5,
                5,
                14,
                style.panel_alpha,
            ),
            outline=rgba(
                style.primary,
                220,
            ),
            width=3,
        )

        # Inner frame
        draw.rounded_rectangle(
            (
                x1 + 15,
                y1 + 15,
                x2 - 15,
                y2 - 15,
            ),
            radius=style.corner_radius - 8,
            outline=rgba(
                style.secondary,
                65,
            ),
            width=2,
        )

        # Top accent line
        draw.rounded_rectangle(
            (
                x1 + 80,
                y1 + 35,
                x2 - 80,
                y1 + 42,
            ),
            radius=5,
            fill=rgba(
                style.primary,
                200,
            ),
        )

        return Image.alpha_composite(
            image,
            panel,
        )


# ============================================================
# TYPOGRAPHY ENGINE
# ============================================================

class TypographyEngine:

    @staticmethod
    def centered_text(
        draw: ImageDraw.ImageDraw,
        text: str,
        y: int,
        font,
        fill,
    ):

        bbox = draw.textbbox(
            (0, 0),
            text,
            font=font,
        )

        width = bbox[2] - bbox[0]

        x = (WIDTH - width) / 2

        draw.text(
            (x, y),
            text,
            font=font,
            fill=fill,
        )

    @staticmethod
    def centered_with_shadow(
        draw: ImageDraw.ImageDraw,
        text: str,
        y: int,
        font,
        fill,
        shadow=(0, 0, 0, 180),
    ):

        bbox = draw.textbbox(
            (0, 0),
            text,
            font=font,
        )

        text_width = bbox[2] - bbox[0]

        x = (WIDTH - text_width) / 2

        # Deep shadow
        draw.text(
            (x + 6, y + 8),
            text,
            font=font,
            fill=shadow,
        )

        # Main text
        draw.text(
            (x, y),
            text,
            font=font,
            fill=fill,
        )

    @staticmethod
    def fit_text(
        text: str,
        max_width: int,
        start_size: int,
        bold: bool = True,
    ):

        size = start_size

        while size >= 20:

            font = FontSystem.load(
                size,
                bold=bold,
            )

            bbox = font.getbbox(text)

            width = bbox[2] - bbox[0]

            if width <= max_width:
                return font

            size -= 4

        return FontSystem.load(
            20,
            bold=bold,
        )


# ============================================================
# DESIGN COMPOSER
# ============================================================

class DesignComposer:
    """
    High-level composition system.

    A design is constructed through independent layers.
    This allows future AI modules to replace individual
    components without rewriting the Discord bot.
    """

    def __init__(
        self,
        name: str,
        style: str = "purple",
        headline: str = "LIVE NOW",
        subtitle: str = "",
        seed: Optional[int] = None,
    ):

        self.name = name.strip() or "PLAYER"

        self.style_key = (
            style.lower().strip()
        )

        if self.style_key not in STYLES:
            self.style_key = "purple"

        self.style = STYLES[
            self.style_key
        ]

        self.headline = (
            headline.strip()
            or "LIVE NOW"
        )

        self.subtitle = subtitle.strip()

        self.seed = (
            seed
            if seed is not None
            else random.randint(
                1,
                999_999_999,
            )
        )

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    def draw_header(
        self,
        image: Image.Image,
    ) -> Image.Image:

        layer = Image.new(
            "RGBA",
            image.size,
            (0, 0, 0, 0),
        )

        draw = ImageDraw.Draw(layer)

        small_font = FontSystem.load(
            32,
            bold=True,
        )

        title_font = FontSystem.load(
            76,
            bold=True,
        )

        TypographyEngine.centered_text(
            draw,
            "LIVE DESIGN",
            80,
            small_font,
            rgba(
                self.style.secondary,
                255,
            ),
        )

        TypographyEngine.centered_with_shadow(
            draw,
            self.headline.upper(),
            130,
            title_font,
            rgba(
                self.style.text,
                255,
            ),
        )

        return Image.alpha_composite(
            image,
            layer,
        )

    # --------------------------------------------------------
    # Main Name
    # --------------------------------------------------------

    def draw_name(
        self,
        image: Image.Image,
    ) -> Image.Image:

        layer = Image.new(
            "RGBA",
            image.size,
            (0, 0, 0, 0),
        )

        draw = ImageDraw.Draw(layer)

        font = TypographyEngine.fit_text(
            self.name.upper(),
            max_width=850,
            start_size=112,
            bold=True,
        )

        TypographyEngine.centered_with_shadow(
            draw,
            self.name.upper(),
            1500,
            font,
            rgba(
                self.style.text,
                255,
            ),
        )

        return Image.alpha_composite(
            image,
            layer,
        )

    # --------------------------------------------------------
    # Subtitle
    # --------------------------------------------------------

    def draw_subtitle(
        self,
        image: Image.Image,
    ) -> Image.Image:

        if not self.subtitle:
            return image

        layer = Image.new(
            "RGBA",
            image.size,
            (0, 0, 0, 0),
        )

        draw = ImageDraw.Draw(layer)

        font = TypographyEngine.fit_text(
            self.subtitle,
            max_width=850,
            start_size=38,
            bold=False,
        )

        TypographyEngine.centered_text(
            draw,
            self.subtitle,
            1630,
            font,
            rgba(
                self.style.muted_text,
                255,
            ),
        )

        return Image.alpha_composite(
            image,
            layer,
        )

    # --------------------------------------------------------
    # Decorative Corners
    # --------------------------------------------------------

    def draw_corners(
        self,
        image: Image.Image,
    ) -> Image.Image:

        layer = Image.new(
            "RGBA",
            image.size,
            (0, 0, 0, 0),
        )

        draw = ImageDraw.Draw(layer)

        size = 45
        margin = 35
        thickness = 5

        corners = [
            (margin, margin, 1, 1),
            (WIDTH - margin, margin, -1, 1),
            (margin, HEIGHT - margin, 1, -1),
            (
                WIDTH - margin,
                HEIGHT - margin,
                -1,
                -1,
            ),
        ]

        for x, y, sx, sy in corners:

            draw.line(
                [
                    (x, y),
                    (
                        x + sx * size,
                        y,
                    ),
                ],
                fill=rgba(
                    self.style.primary,
                    240,
                ),
                width=thickness,
            )

            draw.line(
                [
                    (x, y),
                    (
                        x,
                        y + sy * size,
                    ),
                ],
                fill=rgba(
                    self.style.primary,
                    240,
                ),
                width=thickness,
            )

        return Image.alpha_composite(
            image,
            layer,
        )

    # --------------------------------------------------------
    # Footer
    # --------------------------------------------------------

    def draw_footer(
        self,
        image: Image.Image,
    ) -> Image.Image:

        layer = Image.new(
            "RGBA",
            image.size,
            (0, 0, 0, 0),
        )

        draw = ImageDraw.Draw(layer)

        font = FontSystem.load(
            24,
            bold=False,
        )

        text = "LIVE DESIGN STUDIO"

        TypographyEngine.centered_text(
            draw,
            text,
            1815,
            font,
            rgba(
                self.style.muted_text,
                190,
            ),
        )

        return Image.alpha_composite(
            image,
            layer,
        )

    # --------------------------------------------------------
    # Main Composition
    # --------------------------------------------------------

    def render(self) -> Image.Image:

        image = BackgroundEngine.gradient(
            self.style
        )

        image = BackgroundEngine.add_glows(
            image,
            self.style,
            self.seed,
        )

        image = DecorationEngine.diagonal_lines(
            image,
            self.style,
        )

        image = DecorationEngine.grid(
            image,
            opacity=10,
        )

        image = DecorationEngine.particles(
            image,
            self.style,
            self.seed,
        )

        image = PanelEngine.create_main_panel(
            image,
            self.style,
        )

        image = self.draw_header(
            image
        )

        image = self.draw_name(
            image
        )

        image = self.draw_subtitle(
            image
        )

        image = self.draw_corners(
            image
        )

        image = self.draw_footer(
            image
        )

        return image.convert("RGB")

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    def save(
        self,
        output_path: str | Path,
        quality: int = 95,
    ) -> Path:

        output = Path(output_path)

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        image = self.render()

        image.save(
            output,
            format="PNG",
            optimize=True,
        )

        return output


# ============================================================
# PUBLIC API
# ============================================================

def create_design(
    name: str,
    style: str = "purple",
    headline: str = "LIVE NOW",
    subtitle: str = "",
    seed: Optional[int] = None,
) -> Image.Image:

    composer = DesignComposer(
        name=name,
        style=style,
        headline=headline,
        subtitle=subtitle,
        seed=seed,
    )

    return composer.render()


def save_design(
    name: str,
    output_path: str | Path,
    style: str = "purple",
    headline: str = "LIVE NOW",
    subtitle: str = "",
    seed: Optional[int] = None,
) -> Path:

    composer = DesignComposer(
        name=name,
        style=style,
        headline=headline,
        subtitle=subtitle,
        seed=seed,
    )

    return composer.save(
        output_path
    )


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    output = (
        PROJECT_ROOT
        / "designs"
        / "preview.png"
    )

    save_design(
        name="ZAIKO",
        output_path=output,
        style="purple",
        headline="LIVE NOW",
        subtitle="CUSTOM LIVE DESIGN",
        seed=12345,
    )

    print(
        f"Design created successfully: {output}"
    )
