#!/usr/bin/env python3

# Senpai v2 - A Discord bot created with discord.py
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
import discord.ui
from discord.ext import commands
from discord import app_commands
import pandas as pd
import time
import os

class SimpleNavigation(discord.ui.View):
    def __init__(self, pages: list):
        super().__init__()
        self.pages = pages
        self.current_page = 0
        self.children[0].disabled = True
        if len(self.pages) == 1:
            self.children[1].disabled = True

    def disableEnableButtons(self):
        if self.current_page == 0:
            self.children[0].disabled = True
        elif self.current_page == len(self.pages) - 1:
            self.children[1].disabled = True
        else:
            self.children[0].disabled = False
            self.children[1].disabled = False

    @discord.ui.button(label='Back', style=discord.ButtonStyle.blurple)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self.disableEnableButtons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
        

    @discord.ui.button(label='Forward', style=discord.ButtonStyle.blurple)
    async def forward(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.disableEnableButtons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"[INFO] {self.bot.user} is ready on Discord.")

    @app_commands.command(description="Run a SQL query.")
    @commands.is_owner()
    async def sql(self, interaction: discord.Interaction, sql: str):
        start = time.time()
        async with self.bot.database.execute(sql) as cursor:
            await cursor.execute(sql)
            result = await cursor.fetchall()
        
            if result:
                
                df = pd.DataFrame(result)
            else:
                df = "No output."
        
        end = round((time.time() - start) * 1000, 2)

        # Page embeds if more than 20 rows use forward and back buttons to navigate
        if isinstance(df, pd.DataFrame):
            if len(df) > 10:
                pages = []
                for i in range(0, len(df), 10):
                    embed = discord.Embed(title="SQL Query", description=f"```sql\n{sql}```", color=0xfadadd)
                    embed.add_field(name="Result", value=f"```{df[i:i+10]}```", inline=False)
                    embed.set_footer(text=f"Executed in {end}ms")
                    pages.append(embed)
                await interaction.response.send_message(embed=pages[0], view=SimpleNavigation(pages))
            else:
                embed = discord.Embed(title="SQL Query", description=f"```sql\n{sql}```", color=0xfadadd)
                embed.add_field(name="Result", value=f"```{df}```", inline=False)
                embed.set_footer(text=f"Executed in {end}ms")
                await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(title="SQL Query", description=f"```sql\n{sql}```", color=0xfadadd)
            embed.add_field(name="Result", value=f"```{df}```", inline=False)
            embed.set_footer(text=f"Executed in {end}ms")
            await interaction.response.send_message(embed=embed)


    # Enable stars in a server (only by an adminstrator)
    @app_commands.command(description="Enable stars in this server.")
    @commands.has_permissions(administrator=True)
    async def enablestars(self, interaction: discord.Interaction):
        cursor = self.bot.database.cursor()
        await cursor.execute("SELECT stars_enabled FROM guilds WHERE guild_id = ?", (interaction.guild.id,))
        result = cursor.fetchone()
        if result:
            if result[0]:
                await interaction.response.send_message("Stars are already enabled in this server.")
            else:
                await cursor.execute("UPDATE guilds SET stars_enabled = 1 WHERE guild_id = ?", (interaction.guild.id,))
                self.bot.database.commit()
                await interaction.response.send_message("Stars enabled.")
        else:
            await cursor.execute("INSERT INTO guilds VALUES (?, 1)", (interaction.guild.id,))
            await self.bot.database.commit()
            await interaction.response.send_message("Stars enabled.")
    
    # Disable stars in a server (only by an adminstrator)
    @app_commands.command(description="Disable stars in this server.")
    @commands.has_permissions(administrator=True)
    async def disablestars(self, interaction: discord.Interaction):
        cursor = self.bot.database.cursor()
        await cursor.execute("SELECT stars_enabled FROM guilds WHERE guild_id = ?", (interaction.guild.id,))
        result = cursor.fetchone()
        if result:
            if not result[0]:
                await interaction.response.send_message("Stars are already disabled in this server.")
            else:
                await cursor.execute("UPDATE guilds SET stars_enabled = 0 WHERE guild_id = ?", (interaction.guild.id,))
                await self.bot.database.commit()
                await interaction.response.send_message("Stars disabled.")
        else:
            await cursor.execute("INSERT INTO guilds VALUES (?, 0)", (interaction.guild.id,))
            await self.bot.database.commit()
            await interaction.response.send_message("Stars disabled.")

    @app_commands.command(description="Load a cog.")
    @commands.is_owner()
    async def load(self, interaction: discord.Interaction, cog: str):
        try:
            await self.bot.load_extension(f"cogs.{cog}")
        except Exception as e:
            await interaction.response.send_message(f"```py\n{e}```", ephemeral=True)
        else:
            await interaction.response.send_message(f"Loaded {cog}.")

    @app_commands.command(description="Unload a cog.")
    @commands.is_owner()
    async def unload(self, interaction: discord.Interaction, cog: str):
        try:
            await self.bot.unload_extension(f"cogs.{cog}")
        except Exception as e:
            await interaction.response.send_message(f"```py\n{e}```", ephemeral=True)
        else:
            await interaction.response.send_message(f"Unloaded {cog}.")

    @app_commands.command(description="Reload a cog.")
    @commands.is_owner()
    async def reload(self, interaction: discord.Interaction, cog: str):
        if cog == "all":
            for file in os.listdir("./cogs"):
                if file.endswith(".py"):
                    cog = file[:-3]
                    try:
                        await self.bot.reload_extension(f"cogs.{cog}")
                    except Exception as e:
                        await interaction.channel.send(f"```py\n{e}```")
                    else:
                        await interaction.channel.send(f"Reloaded {cog}.")
            await interaction.channel.send("Reloaded all cogs.")
            return
                    
        cog = cog.lower()
        try:
            await self.bot.reload_extension(f"cogs.{cog}")
        except Exception as e:
            await interaction.response.send_message(f"```py\n{e}```", ephemeral=True)
        else:
            await interaction.response.send_message(f"Reloaded {cog}.")


    @app_commands.command(description="Sync slash commands.")
    @commands.is_owner()
    async def sync(self, interaction: discord.Interaction):
        await self.bot.sync_commands()
        await interaction.response.send_message("Synced slash commands.")





async def setup(bot):
    await bot.add_cog(Misc(bot))