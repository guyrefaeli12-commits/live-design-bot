"""
Live Design Studio
Professional Discord Design Bot
"""

from __future__ import annotations

import io
import logging
import os
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image

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

TOKEN = os.getenv("DISCORD_TOKEN")

BOT_NAME = "Live Design Studio"
VERSION = "1.0.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(BOT_NAME)


# ============================================================
# DISCORD SETUP
# ============================================================

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
)


# ============================================================
# DESIGN STORAGE
# ============================================================

design_cache: dict[str, dict] = {}


# ============================================================
# RATING VIEW
# ============================================================

class RatingView(discord.ui.View):

    def __init__(self, design_id: str):
        super().__init__(timeout=86400)

        self.design_id = design_id

    async def rate(
        self,
        interaction: discord.Interaction,
        rating: int,
    ):

        try:

            user_id = str(
                interaction.user.id
            )

            result = save_rating(
                design_id=self.design_id,
                user_id=user_id,
                rating=rating,
            )

            action = result["action"]

            if action == "created":
                message = "הדירוג שלך נשמר! ⭐"
            else:
                message = "הדירוג שלך עודכן! ⭐"

            average = result["average"]
            count = result["count"]

            await interaction.response.send_message(
                (
                    f"✅ {message}\n\n"
                    f"**הדירוג שלך:** {rating}/5\n"
                    f"**ממוצע:** {average}/5\n"
                    f"**מספר דירוגים:** {count}"
                ),
                ephemeral=True,
            )

        except Exception:

            logger.exception(
                "Failed to save rating"
            )

            if not interaction.response.is_done():

                await interaction.response.send_message(
                    "❌ לא הצלחנו לשמור את הדירוג.",
                    ephemeral=True,
                )

    @discord.ui.button(
        label="⭐",
        style=discord.ButtonStyle.secondary,
    )
    async def one(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.rate(
            interaction,
            1,
        )

    @discord.ui.button(
        label="⭐⭐",
        style=discord.ButtonStyle.secondary,
    )
    async def two(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.rate(
            interaction,
            2,
        )

    @discord.ui.button(
        label="⭐⭐⭐",
        style=discord.ButtonStyle.primary,
    )
    async def three(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.rate(
            interaction,
            3,
        )

    @discord.ui.button(
        label="⭐⭐⭐⭐",
        style=discord.ButtonStyle.primary,
    )
    async def four(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.rate(
            interaction,
            4,
        )

    @discord.ui.button(
        label="⭐⭐⭐⭐⭐",
        style=discord.ButtonStyle.success,
    )
    async def five(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await self.rate(
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
    style="סגנון: gaming, anime, streamer וכו'",
    color="purple / blue / red / green / gold / pink",
    headline="הכותרת הראשית",
    subtitle="טקסט נוסף, אופציונלי",
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

        timestamp = datetime.now(
            timezone.utc
        ).strftime(
            "%Y%m%d%H%M%S"
        )

        design_id = (
            f"{interaction.user.id}-"
            f"{timestamp}"
        )

        # ----------------------------------------------------
        # Generate design
        # ----------------------------------------------------

        image = create_design(
            name=name,
            style=color,
            headline=headline,
            subtitle=subtitle,
        )

        # ----------------------------------------------------
        # Convert image to Discord attachment
        # ----------------------------------------------------

        buffer = io.BytesIO()

        image.save(
            buffer,
            format="PNG",
        )

        buffer.seek(0)

        file = discord.File(
            buffer,
            filename="live-design.png",
        )

        # ----------------------------------------------------
        # Cache design metadata
        # ----------------------------------------------------

        design_cache[design_id] = {
            "design_id": design_id,
            "user_id": str(
                interaction.user.id
            ),
            "name": name,
            "style": style,
            "color": color,
            "headline": headline,
            "subtitle": subtitle,
            "created_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        # ----------------------------------------------------
        # Embed
        # ----------------------------------------------------

        embed = discord.Embed(
            title="🎨 העיצוב שלך מוכן!",
            description=(
                "יצרנו עבורך עיצוב מותאם אישית.\n\n"
                f"👤 **שם:** {name}\n"
                f"🎨 **סגנון:** {style}\n"
                f"🌈 **צבע:** {color}\n"
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
                f"v{VERSION}"
            )
        )

        # ----------------------------------------------------
        # Send
        # ----------------------------------------------------

        await interaction.followup.send(
            embed=embed,
            file=file,
            view=RatingView(
                design_id
            ),
        )

        logger.info(
            "Design generated successfully: %s",
            design_id,
        )

    except Exception:

        logger.exception(
            "Design generation failed"
        )

        await interaction.followup.send(
            (
                "❌ הייתה שגיאה ביצירת העיצוב.\n"
                "בדוק את הלוגים של הבוט."
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
    rating="דירוג בין 1 ל-5",
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
                "⭐ **הדירוג נשמר!**\n\n"
                f"**עיצוב:** `{design_id}`\n"
                f"**הדירוג שלך:** "
                f"{rating.value}/5\n"
                f"**ממוצע:** "
                f"{stats['average']}/5\n"
                f"**דירוגים:** "
                f"{stats['count']}"
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
            "Rating command failed"
        )

        await interaction.response.send_message(
            "❌ שגיאה בשמירת הדירוג.",
            ephemeral=True,
        )


# ============================================================
# /STATS
# ============================================================

@bot.tree.command(
    name="stats",
    description="Show community design statistics",
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
            title="📊 Design Studio Statistics",
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
            name="🌟 Average",
            value=(
                f"{stats['average']}/5"
            ),
            inline=False,
        )

        embed.add_field(
            name="Rating Distribution",
            value=(
                f"⭐ 1: {distribution['1']}\n"
                f"⭐⭐ 2: {distribution['2']}\n"
                f"⭐⭐⭐ 3: {distribution['3']}\n"
                f"⭐⭐⭐⭐ 4: {distribution['4']}\n"
                f"⭐⭐⭐⭐⭐ 5: {distribution['5']}"
            ),
            inline=False,
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
                "ℹ️ עדיין לא דירגת את העיצוב הזה.",
                ephemeral=True,
            )

            return

        stars = "⭐" * rating

        await interaction.response.send_message(
            (
                f"🎨 **הדירוג שלך**\n\n"
                f"עיצוב: `{design_id}`\n"
                f"דירוג: {stars} ({rating}/5)"
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
# BOT EVENTS
# ============================================================

@bot.event
async def on_ready():

    logger.info(
        "Connected as %s",
        bot.user,
    )

    try:

        synced = await bot.tree.sync()

        logger.info(
            "Successfully synced %s commands",
            len(synced),
        )

        logger.info(
            "%s is online!",
            BOT_NAME,
        )

    except Exception:

        logger.exception(
            "Failed to synchronize commands"
        )


# ============================================================
# STARTUP
# ============================================================

def main():

    if not TOKEN:

        raise RuntimeError(
            "DISCORD_TOKEN environment variable "
            "is not configured."
        )

    logger.info(
        "Starting %s v%s",
        BOT_NAME,
        VERSION,
    )

    bot.run(TOKEN)


if __name__ == "__main__":
    main()
