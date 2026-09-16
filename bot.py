"""
Live Design Studio
Professional Discord Design Bot
Version: 1.1.0
"""

from __future__ import annotations

import io
import logging
import os
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from designer import create_design
from ratings import (
    get_design_stats,
    get_global_stats,
    get_user_rating,
    save_rating,
)


# ============================================================
# CONFIGURATION
# ============================================================

BOT_NAME = "Live Design Studio"
VERSION = "1.1.0"

TOKEN = os.getenv("DISCORD_TOKEN")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(BOT_NAME)


# ============================================================
# DISCORD BOT
# ============================================================

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
)


# ============================================================
# DESIGN REGISTRY
# ============================================================
# Keeps information about designs while the bot is running.
# Persistent rating data is handled separately by ratings.py.
# ============================================================

design_registry: dict[str, dict] = {}


# ============================================================
# STYLE OPTIONS
# ============================================================

STYLE_CHOICES = [
    app_commands.Choice(
        name="💜 Purple",
        value="purple",
    ),
    app_commands.Choice(
        name="💙 Blue",
        value="blue",
    ),
    app_commands.Choice(
        name="❤️ Red",
        value="red",
    ),
    app_commands.Choice(
        name="💚 Green",
        value="green",
    ),
    app_commands.Choice(
        name="🏆 Gold",
        value="gold",
    ),
    app_commands.Choice(
        name="💗 Pink",
        value="pink",
    ),
]


# ============================================================
# RATING VIEW
# ============================================================

class RatingView(discord.ui.View):
    """
    Interactive 1–5 star rating interface.
    """

    def __init__(
        self,
        design_id: str,
    ):
        super().__init__(
            timeout=86400
        )

        self.design_id = design_id

    async def submit_rating(
        self,
        interaction: discord.Interaction,
        rating: int,
    ):

        try:

            result = save_rating(
                design_id=self.design_id,
                user_id=str(
                    interaction.user.id
                ),
                rating=rating,
            )

            average = result["average"]
            count = result["count"]

            if result["action"] == "created":
                message = "הדירוג שלך נשמר!"
            else:
                message = "הדירוג שלך עודכן!"

            await interaction.response.send_message(
                (
                    f"✅ **{message}**\n\n"
                    f"⭐ הדירוג שלך: **{rating}/5**\n"
                    f"📊 ממוצע: **{average}/5**\n"
                    f"👥 מספר דירוגים: **{count}**"
                ),
                ephemeral=True,
            )

        except Exception:

            logger.exception(
                "Rating submission failed"
            )

            if not interaction.response.is_done():

                await interaction.response.send_message(
                    "❌ לא הצלחנו לשמור את הדירוג.",
                    ephemeral=True,
                )

    @discord.ui.button(
        label="1 ⭐",
        style=discord.ButtonStyle.secondary,
    )
    async def rating_one(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.submit_rating(
            interaction,
            1,
        )

    @discord.ui.button(
        label="2 ⭐",
        style=discord.ButtonStyle.secondary,
    )
    async def rating_two(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.submit_rating(
            interaction,
            2,
        )

    @discord.ui.button(
        label="3 ⭐",
        style=discord.ButtonStyle.primary,
    )
    async def rating_three(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.submit_rating(
            interaction,
            3,
        )

    @discord.ui.button(
        label="4 ⭐",
        style=discord.ButtonStyle.primary,
    )
    async def rating_four(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.submit_rating(
            interaction,
            4,
        )

    @discord.ui.button(
        label="5 ⭐",
        style=discord.ButtonStyle.success,
    )
    async def rating_five(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.submit_rating(
            interaction,
            5,
        )


# ============================================================
# /DESIGN
# ============================================================

@bot.tree.command(
    name="design",
    description="Create a professional custom live design",
)
@app_commands.describe(
    name="השם שיופיע בעיצוב",
    style="סגנון וצבע של העיצוב",
    headline="הכותרת הראשית",
    subtitle="טקסט נוסף, אופציונלי",
)
@app_commands.choices(
    style=STYLE_CHOICES
)
async def design_command(
    interaction: discord.Interaction,
    name: str,
    style: app_commands.Choice[str],
    headline: str,
    subtitle: str = "",
):

    await interaction.response.defer()

    try:

        # ----------------------------------------------------
        # Generate unique design ID
        # ----------------------------------------------------

        timestamp = datetime.now(
            timezone.utc
        ).strftime(
            "%Y%m%d%H%M%S%f"
        )

        design_id = (
            f"{interaction.user.id}-"
            f"{timestamp}"
        )

        # ----------------------------------------------------
        # Generate image
        # ----------------------------------------------------

        image = create_design(
            name=name,
            style=style.value,
            headline=headline,
            subtitle=subtitle,
        )

        # ----------------------------------------------------
        # Convert PIL image to PNG
        # ----------------------------------------------------

        buffer = io.BytesIO()

        image.save(
            buffer,
            format="PNG",
            optimize=True,
        )

        buffer.seek(0)

        file = discord.File(
            buffer,
            filename="live-design.png",
        )

        # ----------------------------------------------------
        # Register design
        # ----------------------------------------------------

        design_registry[design_id] = {
            "design_id": design_id,
            "user_id": str(
                interaction.user.id
            ),
            "name": name,
            "style": style.value,
            "headline": headline,
            "subtitle": subtitle,
            "created_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        # ----------------------------------------------------
        # Create embed
        # ----------------------------------------------------

        embed = discord.Embed(
            title="🎨 העיצוב שלך מוכן!",
            description=(
                "עיצוב לייב חדש נוצר במיוחד עבורך.\n\n"
                f"👤 **שם:** {name}\n"
                f"🎨 **סגנון:** {style.name}\n"
                f"📝 **כותרת:** {headline}\n"
                f"🆔 **Design ID:** `{design_id}`"
            ),
            color=discord.Color.blurple(),
        )

        embed.set_image(
            url="attachment://live-design.png"
        )

        embed.set_footer(
            text=(
                f"{BOT_NAME} • "
                f"Rate this design below ⭐"
            )
        )

        # ----------------------------------------------------
        # Send result
        # ----------------------------------------------------

        await interaction.followup.send(
            embed=embed,
            file=file,
            view=RatingView(
                design_id
            ),
        )

        logger.info(
            "Design generated | id=%s | user=%s | style=%s",
            design_id,
            interaction.user.id,
            style.value,
        )

    except Exception:

        logger.exception(
            "Design generation failed"
        )

        await interaction.followup.send(
            (
                "❌ **שגיאה ביצירת העיצוב**\n"
                "נסה שוב בעוד רגע."
            ),
            ephemeral=True,
        )


# ============================================================
# /RATE
# ============================================================

@bot.tree.command(
    name="rate",
    description="Rate a design from 1 to 5 stars",
)
@app_commands.describe(
    design_id="ה-ID של העיצוב",
    rating="הדירוג שלך",
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

    try:

        result = save_rating(
            design_id=design_id,
            user_id=str(
                interaction.user.id
            ),
            rating=rating.value,
        )

        stats = get_design_stats(
            design_id
        )

        await interaction.response.send_message(
            (
                "⭐ **הדירוג נשמר בהצלחה!**\n\n"
                f"🆔 עיצוב: `{design_id}`\n"
                f"⭐ הדירוג שלך: **{rating.value}/5**\n"
                f"📊 ממוצע: **{stats['average']}/5**\n"
                f"👥 דירוגים: **{stats['count']}**"
            ),
            ephemeral=True,
        )

    except ValueError as error:

        await interaction.response.send_message(
            f"❌ {error}",
            ephemeral=True,
        )

    except Exception:

        logger.exception(
            "Rate command failed"
        )

        await interaction.response.send_message(
            "❌ אירעה שגיאה בשמירת הדירוג.",
            ephemeral=True,
        )


# ============================================================
# /STATS
# ============================================================

@bot.tree.command(
    name="stats",
    description="Show design community statistics",
)
async def stats_command(
    interaction: discord.Interaction,
):

    try:

        stats = get_global_stats()

        distribution = stats[
            "distribution"
        ]

        embed = discord.Embed(
            title="📊 Live Design Studio",
            description=(
                "סטטיסטיקות הדירוגים של הקהילה"
            ),
            color=discord.Color.blurple(),
        )

        embed.add_field(
            name="🎨 Designs Rated",
            value=str(
                stats[
                    "total_designs_rated"
                ]
            ),
            inline=True,
        )

        embed.add_field(
            name="⭐ Total Ratings",
            value=str(
                stats[
                    "total_ratings"
                ]
            ),
            inline=True,
        )

        embed.add_field(
            name="👥 Users",
            value=str(
                stats[
                    "total_users"
                ]
            ),
            inline=True,
        )

        embed.add_field(
            name="🌟 Average Rating",
            value=(
                f"**{stats['average']}/5**"
            ),
            inline=False,
        )

        embed.add_field(
            name="📈 Distribution",
            value=(
                f"⭐ 1 — {distribution['1']}\n"
                f"⭐⭐ 2 — {distribution['2']}\n"
                f"⭐⭐⭐ 3 — {distribution['3']}\n"
                f"⭐⭐⭐⭐ 4 — {distribution['4']}\n"
                f"⭐⭐⭐⭐⭐ 5 — {distribution['5']}"
            ),
            inline=False,
        )

        embed.set_footer(
            text=BOT_NAME
        )

        await interaction.response.send_message(
            embed=embed
        )

    except Exception:

        logger.exception(
            "Stats command failed"
        )

        await interaction.response.send_message(
            "❌ לא הצלחנו לטעון את הסטטיסטיקות.",
            ephemeral=True,
        )


# ============================================================
# /MYRATING
# ============================================================

@bot.tree.command(
    name="myrating",
    description="Check your rating for a design",
)
@app_commands.describe(
    design_id="ה-ID של העיצוב",
)
async def myrating_command(
    interaction: discord.Interaction,
    design_id: str,
):

    try:

        rating = get_user_rating(
            design_id=design_id,
            user_id=str(
                interaction.user.id
            ),
        )

        if rating is None:

            await interaction.response.send_message(
                (
                    "ℹ️ עדיין לא דירגת את העיצוב הזה."
                ),
                ephemeral=True,
            )

            return

        stars = "⭐" * rating

        await interaction.response.send_message(
            (
                "🎨 **הדירוג שלך**\n\n"
                f"🆔 עיצוב: `{design_id}`\n"
                f"⭐ דירוג: {stars} **({rating}/5)**"
            ),
            ephemeral=True,
        )

    except Exception:

        logger.exception(
            "My rating command failed"
        )

        await interaction.response.send_message(
            "❌ לא הצלחנו למצוא את הדירוג.",
            ephemeral=True,
        )


# ============================================================
# BOT READY
# ============================================================

@bot.event
async def on_ready():

    logger.info(
        "Logged in as %s",
        bot.user,
    )

    try:

        synced_commands = await bot.tree.sync()

        logger.info(
            "Synced %s slash commands",
            len(synced_commands),
        )

        logger.info(
            "%s v%s is online",
            BOT_NAME,
            VERSION,
        )

    except Exception:

        logger.exception(
            "Failed to synchronize slash commands"
        )


# ============================================================
# STARTUP
# ============================================================

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
