import os
import io
import logging
from datetime import datetime
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageFilter


# ============================================================
# LIVE DESIGN BOT
# Professional Discord Design Generator
# Version: 1.0.0
# ============================================================


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

BOT_NAME = "Live Design Studio"
VERSION = "1.0.0"

OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1920

BASE_DIR = Path(__file__).resolve().parent
DESIGNS_DIR = BASE_DIR / "designs"
DESIGNS_DIR.mkdir(exist_ok=True)

TOKEN = os.getenv("DISCORD_TOKEN")


# ------------------------------------------------------------
# Logging
# ------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(BOT_NAME)


# ------------------------------------------------------------
# Discord Intents
# ------------------------------------------------------------

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
)


# ------------------------------------------------------------
# Font Manager
# ------------------------------------------------------------

class FontManager:
    """
    Centralized font loading system.

    The system tries several common locations so the project
    can later include its own professional font package.
    """

    SEARCH_PATHS = [
        BASE_DIR / "fonts",
        Path("/usr/share/fonts"),
        Path("/usr/local/share/fonts"),
    ]

    FONT_NAMES = [
        "DejaVuSans-Bold.ttf",
        "DejaVuSans.ttf",
        "LiberationSans-Bold.ttf",
        "Arial.ttf",
    ]

    @classmethod
    def find_font(cls, size: int, bold: bool = True):
        candidates = []

        if bold:
            candidates.extend([
                "DejaVuSans-Bold.ttf",
                "LiberationSans-Bold.ttf",
                "Arial Bold.ttf",
            ])
        else:
            candidates.extend([
                "DejaVuSans.ttf",
                "LiberationSans-Regular.ttf",
                "Arial.ttf",
            ])

        for base in cls.SEARCH_PATHS:
            if not base.exists():
                continue

            for name in candidates:
                matches = list(base.rglob(name))

                if matches:
                    try:
                        return ImageFont.truetype(
                            str(matches[0]),
                            size=size,
                        )
                    except Exception:
                        pass

        return ImageFont.load_default()


# ------------------------------------------------------------
# Color Palettes
# ------------------------------------------------------------

PALETTES = {
    "purple": {
        "background": (20, 8, 40),
        "primary": (148, 70, 255),
        "secondary": (224, 80, 255),
        "accent": (255, 255, 255),
    },

    "blue": {
        "background": (5, 18, 45),
        "primary": (35, 120, 255),
        "secondary": (0, 220, 255),
        "accent": (255, 255, 255),
    },

    "red": {
        "background": (45, 5, 12),
        "primary": (255, 40, 70),
        "secondary": (255, 125, 30),
        "accent": (255, 255, 255),
    },

    "green": {
        "background": (4, 35, 25),
        "primary": (20, 220, 120),
        "secondary": (120, 255, 70),
        "accent": (255, 255, 255),
    },

    "gold": {
        "background": (35, 22, 5),
        "primary": (255, 190, 40),
        "secondary": (255, 230, 120),
        "accent": (255, 255, 255),
    },

    "pink": {
        "background": (40, 7, 28),
        "primary": (255, 50, 170),
        "secondary": (255, 120, 230),
        "accent": (255, 255, 255),
    },
}


# ------------------------------------------------------------
# Utility Functions
# ------------------------------------------------------------

def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


def hex_to_rgb(value):
    value = value.lstrip("#")

    if len(value) != 6:
        return 255, 255, 255

    try:
        return tuple(
            int(value[i:i + 2], 16)
            for i in (0, 2, 4)
        )
    except ValueError:
        return 255, 255, 255


def rounded_rectangle(
    draw,
    xy,
    radius,
    fill=None,
    outline=None,
    width=1,
):
    draw.rounded_rectangle(
        xy,
        radius=radius,
        fill=fill,
        outline=outline,
        width=width,
    )


def draw_centered_text(
    draw,
    canvas_width,
    y,
    text,
    font,
    fill,
):
    bbox = draw.textbbox((0, 0), text, font=font)

    text_width = bbox[2] - bbox[0]

    x = (canvas_width - text_width) / 2

    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill,
    )


# ------------------------------------------------------------
# Background Generator
# ------------------------------------------------------------

class BackgroundEngine:
    """
    Generates a layered visual background.

    This is intentionally separated from the main designer so
    future AI-generated backgrounds can replace this engine.
    """

    @staticmethod
    def create(palette):
        image = Image.new(
            "RGB",
            (OUTPUT_WIDTH, OUTPUT_HEIGHT),
            palette["background"],
        )

        # Large blurred light sources
        glow = Image.new(
            "RGBA",
            image.size,
            (0, 0, 0, 0),
        )

        glow_draw = ImageDraw.Draw(glow)

        primary = palette["primary"]
        secondary = palette["secondary"]

        glow_draw.ellipse(
            (-350, -250, 750, 850),
            fill=(*primary, 150),
        )

        glow_draw.ellipse(
            (450, 1050, 1400, 2050),
            fill=(*secondary, 120),
        )

        glow_draw.ellipse(
            (650, 250, 1250, 850),
            fill=(*primary, 80),
        )

        glow = glow.filter(
            ImageFilter.GaussianBlur(180)
        )

        image = Image.alpha_composite(
            image.convert("RGBA"),
            glow,
        )

        # Diagonal graphic shapes
        shapes = Image.new(
            "RGBA",
            image.size,
            (0, 0, 0, 0),
        )

        shape_draw = ImageDraw.Draw(shapes)

        shape_draw.polygon(
            [
                (0, 500),
                (1080, 250),
                (1080, 330),
                (0, 600),
            ],
            fill=(*primary, 70),
        )

        shape_draw.polygon(
            [
                (0, 1450),
                (1080, 1250),
                (1080, 1320),
                (0, 1530),
            ],
            fill=(*secondary, 45),
        )

        shapes = shapes.filter(
            ImageFilter.GaussianBlur(2)
        )

        image = Image.alpha_composite(
            image,
            shapes,
        )

        # Fine grid
        grid = Image.new(
            "RGBA",
            image.size,
            (0, 0, 0, 0),
        )

        grid_draw = ImageDraw.Draw(grid)

        spacing = 80

        for x in range(0, OUTPUT_WIDTH, spacing):
            grid_draw.line(
                [(x, 0), (x, OUTPUT_HEIGHT)],
                fill=(255, 255, 255, 12),
                width=1,
            )

        for y in range(0, OUTPUT_HEIGHT, spacing):
            grid_draw.line(
                [(0, y), (OUTPUT_WIDTH, y)],
                fill=(255, 255, 255, 12),
                width=1,
            )

        image = Image.alpha_composite(
            image,
            grid,
        )

        return image


# ------------------------------------------------------------
# Design Generator
# ------------------------------------------------------------

class DesignGenerator:
    """
    Main professional design engine.

    Future versions can connect this class to an AI image
    generation model while keeping the Discord interface
    unchanged.
    """

    def __init__(
        self,
        name,
        style,
        color,
        headline,
        subtitle="",
    ):
        self.name = name.strip()
        self.style = style.strip()
        self.color = color.lower().strip()
        self.headline = headline.strip()
        self.subtitle = subtitle.strip()

        if self.color not in PALETTES:
            self.color = "purple"

        self.palette = PALETTES[self.color]

    def create(self):
        image = BackgroundEngine.create(
            self.palette
        )

        image = self.add_header(image)
        image = self.add_main_panel(image)
        image = self.add_name(image)
        image = self.add_footer(image)
        image = self.add_glow_details(image)

        return image.convert("RGB")

    def add_header(self, image):
        draw = ImageDraw.Draw(image)

        small_font = FontManager.find_font(
            34,
            bold=True,
        )

        title_font = FontManager.find_font(
            72,
            bold=True,
        )

        draw_centered_text(
            draw,
            OUTPUT_WIDTH,
            90,
            "LIVE DESIGN",
            small_font,
            self.palette["secondary"],
        )

        draw_centered_text(
            draw,
            OUTPUT_WIDTH,
            145,
            self.style.upper(),
            title_font,
            self.palette["accent"],
        )

        return image

    def add_main_panel(self, image):
        overlay = Image.new(
            "RGBA",
            image.size,
            (0, 0, 0, 0),
        )

        draw = ImageDraw.Draw(overlay)

        panel_x1 = 70
        panel_y1 = 350
        panel_x2 = OUTPUT_WIDTH - 70
        panel_y2 = 1450

        # Outer glow
        glow = Image.new(
            "RGBA",
            image.size,
            (0, 0, 0, 0),
        )

        glow_draw = ImageDraw.Draw(glow)

        for spread in range(50, 5, -5):
            alpha = clamp(
                int(40 * (1 - spread / 55)),
                5,
                40,
            )

            glow_draw.rounded_rectangle(
                (
                    panel_x1 - spread,
                    panel_y1 - spread,
                    panel_x2 + spread,
                    panel_y2 + spread,
                ),
                radius=50 + spread,
                outline=(
                    *self.palette["primary"],
                    alpha,
                ),
                width=4,
            )

        glow = glow.filter(
            ImageFilter.GaussianBlur(15)
        )

        image = Image.alpha_composite(
            image,
            glow,
        )

        draw = ImageDraw.Draw(overlay)

        rounded_rectangle(
            draw,
            (
                panel_x1,
                panel_y1,
                panel_x2,
                panel_y2,
            ),
            45,
            fill=(8, 8, 18, 165),
            outline=(
                *self.palette["primary"],
                210,
            ),
            width=3,
        )

        # Inner frame
        rounded_rectangle(
            draw,
            (
                panel_x1 + 18,
                panel_y1 + 18,
                panel_x2 - 18,
                panel_y2 - 18,
            ),
            35,
            outline=(
                *self.palette["secondary"],
                70,
            ),
            width=2,
        )

        image = Image.alpha_composite(
            image,
            overlay,
        )

        return image

    def add_name(self, image):
        draw = ImageDraw.Draw(image)

        name_font = FontManager.find_font(
            100,
            bold=True,
        )

        headline_font = FontManager.find_font(
            48,
            bold=True,
        )

        # Main name
        draw_centered_text(
            draw,
            OUTPUT_WIDTH,
            1510,
            self.name.upper(),
            name_font,
            self.palette["accent"],
        )

        # Headline
        if self.headline:
            draw_centered_text(
                draw,
                OUTPUT_WIDTH,
                1630,
                self.headline.upper(),
                headline_font,
                self.palette["secondary"],
            )

        # Subtitle
        if self.subtitle:
            subtitle_font = FontManager.find_font(
                32,
                bold=False,
            )

            draw_centered_text(
                draw,
                OUTPUT_WIDTH,
                1700,
                self.subtitle,
                subtitle_font,
                (220, 220, 230),
            )

        return image

    def add_footer(self, image):
        draw = ImageDraw.Draw(image)

        footer_font = FontManager.find_font(
            24,
            bold=False,
        )

        footer_text = (
            f"{BOT_NAME} • {VERSION}"
        )

        draw_centered_text(
            draw,
            OUTPUT_WIDTH,
            1825,
            footer_text,
            footer_font,
            (180, 180, 195),
        )

        return image

    def add_glow_details(self, image):
        """
        Adds small professional visual accents.
        """

        overlay = Image.new(
            "RGBA",
            image.size,
            (0, 0, 0, 0),
        )

        draw = ImageDraw.Draw(overlay)

        primary = self.palette["primary"]

        # Corner accents
        accent_size = 35
        thickness = 5

        corners = [
            (40, 40, 1, 1),
            (OUTPUT_WIDTH - 40, 40, -1, 1),
            (40, OUTPUT_HEIGHT - 40, 1, -1),
            (
                OUTPUT_WIDTH - 40,
                OUTPUT_HEIGHT - 40,
                -1,
                -1,
            ),
        ]

        for x, y, sx, sy in corners:
            draw.line(
                [
                    (x, y),
                    (x + sx * accent_size, y),
                ],
                fill=(*primary, 230),
                width=thickness,
            )

            draw.line(
                [
                    (x, y),
                    (x, y + sy * accent_size),
                ],
                fill=(*primary, 230),
                width=thickness,
            )

        image = Image.alpha_composite(
            image,
            overlay,
        )

        return image


# ------------------------------------------------------------
# Discord UI
# ------------------------------------------------------------

class RatingView(discord.ui.View):
    """
    Interactive 1-5 star rating system.
    """

    def __init__(self, design_id):
        super().__init__(
            timeout=3600
        )

        self.design_id = design_id

    async def register_rating(
        self,
        interaction,
        rating,
    ):
        await interaction.response.send_message(
            f"⭐ קיבלנו את הדירוג שלך: **{rating}/5**\n"
            f"Design ID: `{self.design_id}`",
            ephemeral=True,
        )

    @discord.ui.button(
        label="⭐",
        style=discord.ButtonStyle.secondary,
    )
    async def one_star(
        self,
        interaction,
        button,
    ):
        await self.register_rating(
            interaction,
            1,
        )

    @discord.ui.button(
        label="⭐⭐",
        style=discord.ButtonStyle.secondary,
    )
    async def two_star(
        self,
        interaction,
        button,
    ):
        await self.register_rating(
            interaction,
            2,
        )

    @discord.ui.button(
        label="⭐⭐⭐",
        style=discord.ButtonStyle.primary,
    )
    async def three_star(
        self,
        interaction,
        button,
    ):
        await self.register_rating(
            interaction,
            3,
        )

    @discord.ui.button(
        label="⭐⭐⭐⭐",
        style=discord.ButtonStyle.primary,
    )
    async def four_star(
        self,
        interaction,
        button,
    ):
        await self.register_rating(
            interaction,
            4,
        )

    @discord.ui.button(
        label="⭐⭐⭐⭐⭐",
        style=discord.ButtonStyle.success,
    )
    async def five_star(
        self,
        interaction,
        button,
    ):
        await self.register_rating(
            interaction,
            5,
        )


# ------------------------------------------------------------
# Slash Commands
# ------------------------------------------------------------

@bot.tree.command(
    name="design",
    description="Create a professional custom live design",
)
@app_commands.describe(
    name="The name displayed on the design",
    style="Design style, for example Gaming or Anime",
    color="Purple, Blue, Red, Green, Gold or Pink",
    headline="Main text displayed on the design",
    subtitle="Optional secondary text",
)
async def design_command(
    interaction: discord.Interaction,
    name: str,
    style: str,
    color: str,
    headline: str,
    subtitle: str = "",
):
    await interaction.response.defer()

    try:
        generator = DesignGenerator(
            name=name,
            style=style,
            color=color,
            headline=headline,
            subtitle=subtitle,
        )

        image = generator.create()

        timestamp = datetime.utcnow().strftime(
            "%Y%m%d_%H%M%S"
        )

        design_id = (
            f"{interaction.user.id}_{timestamp}"
        )

        output_path = (
            DESIGNS_DIR /
            f"{design_id}.png"
        )

        image.save(
            output_path,
            format="PNG",
            optimize=True,
        )

        embed = discord.Embed(
            title="🎨 העיצוב שלך מוכן!",
            description=(
                "יצרנו עבורך עיצוב מותאם אישית.\n\n"
                f"**שם:** {name}\n"
                f"**סגנון:** {style}\n"
                f"**צבע:** {color}\n"
                f"**Design ID:** `{design_id}`"
            ),
            color=discord.Color.from_rgb(
                *PALETTES.get(
                    color.lower(),
                    PALETTES["purple"],
                )["primary"]
            ),
        )

        embed.set_footer(
            text=f"{BOT_NAME} v{VERSION}"
        )

        file = discord.File(
            output_path,
            filename="design.png",
        )

        embed.set_image(
            url="attachment://design.png"
        )

        await interaction.followup.send(
            embed=embed,
            file=file,
            view=RatingView(design_id),
        )

    except Exception as error:
        logger.exception(
            "Design generation failed"
        )

        await interaction.followup.send(
            "❌ הייתה שגיאה ביצירת העיצוב.\n"
            "המערכת שמרה את השגיאה ללוג.",
            ephemeral=True,
        )


@bot.tree.command(
    name="rate",
    description="Rate a generated design",
)
@app_commands.describe(
    design_id="The Design ID",
    rating="Rating from 1 to 5",
)
@app_commands.choices(
    rating=[
        app_commands.Choice(
            name="⭐ 1",
            value=1,
        ),
        app_commands.Choice(
            name="⭐⭐ 2",
            value=2,
        ),
        app_commands.Choice(
            name="⭐⭐⭐ 3",
            value=3,
        ),
        app_commands.Choice(
            name="⭐⭐⭐⭐ 4",
            value=4,
        ),
        app_commands.Choice(
            name="⭐⭐⭐⭐⭐ 5",
            value=5,
        ),
    ]
)
async def rate_command(
    interaction: discord.Interaction,
    design_id: str,
    rating: app_commands.Choice[int],
):
    await interaction.response.send_message(
        f"⭐ הדירוג נשמר!\n\n"
        f"Design: `{design_id}`\n"
        f"Rating: **{rating.value}/5**",
        ephemeral=True,
    )


# ------------------------------------------------------------
# Bot Events
# ------------------------------------------------------------

@bot.event
async def on_ready():
    logger.info(
        "Logged in as %s",
        bot.user,
    )

    try:
        synced = await bot.tree.sync()

        logger.info(
            "Synced %s slash commands",
            len(synced),
        )

    except Exception:
        logger.exception(
            "Failed to sync slash commands"
        )


# ------------------------------------------------------------
# Startup
# ------------------------------------------------------------

def main():
    if not TOKEN:
        raise RuntimeError(
            "DISCORD_TOKEN environment variable "
            "is missing."
        )

    logger.info(
        "Starting %s v%s",
        BOT_NAME,
        VERSION,
    )

    bot.run(TOKEN)


if __name__ == "__main__":
    main()
