#!/usr/bin/env python3

# Senpai v2 - A Discord bot created with LightSage's discord.py fork
# https://github.com/YourKalamity/senpai
#
# ISC LICENSE
#
# Copyright (C) 2021-present YourKalamity
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#

import discord
from discord.ext import commands
from discord import app_commands

class ConfigCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    config_group = app_commands.Group(name="config", description="Bot configuration")

    @config_group.command(name="logs")
    @app_commands.checks.has_permissions(administrator=True)
    async def logs(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer()
        cursor = self.bot.database.cursor()
        cursor.execute("SELECT guild_id FROM guilds WHERE guild_id = ?", (interaction.guild.id,))
        data = cursor.fetchall()
        if len(data) == 0:
            cursor.execute("INSERT INTO guilds(guild_id, log_channel) VALUES(?, ?,)", (interaction.guild.id, channel.id,))
        else:
            cursor.execute("UPDATE guilds SET log_channel = ? WHERE guild_id = ?", (channel.id, interaction.guild.id,))
        self.bot.database.commit()
        await interaction.followup.send("Updated log channel for this server!")
        return

    @config_group.command(name="mod")
    @app_commands.checks.has_permissions(administrator=True)
    async def mod(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.defer()
        cursor = self.bot.database.cursor()
        cursor.execute("SELECT guild_id FROM guilds WHERE guild_id = ?", (interaction.guild.id,))
        data = cursor.fetchall()
        if len(data) == 0:
            cursor.execute("INSERT INTO guilds(guild_id, min_mod_role) VALUES(?, ?,)", (interaction.guild.id, role.id,))
        else:
            cursor.execute("UPDATE guilds SET min_mod_role = ? WHERE guild_id = ?", (role.id, interaction.guild.id,))
        self.bot.database.commit()
        await interaction.followup.send("Updated moderator role for this server!")
        return


async def setup(bot):
    await bot.add_cog(ConfigCog(bot))
