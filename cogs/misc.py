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
from discord.ext import commands
from discord import app_commands
import pandas as pd
import time

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"[INFO] {self.bot.user} is ready on Discord.")

    @commands.command()
    async def sql(self, ctx, *args):
        print(ctx.message.content)
        start = time.time()
        if str(ctx.author.id) not in self.bot.settings["ADMINS"]:
            return
        sql = " ".join(args)

        if sql.startswith("```sql") and sql.endswith("```"):
            sql = sql[6:-3]
        elif sql.startswith("```") and sql.endswith("```"):
            sql = sql[3:-3]
        
        cursor = self.bot.database.cursor()
        try:
            await cursor.execute(sql)
            output = cursor.fetchall()

        except Exception as e:
            await ctx.send(f"```{e}```")
            return
        finally:
            cursor.close()
        
        # pretty print the output as a table using pandas
        if output:
            df = pd.DataFrame(output, columns=[x[0] for x in cursor.description])
            
        else:
            df = pd.DataFrame()

        # Send the output as embed
        embed = discord.Embed(title="SQL Query", description=f"```{sql}```", color=0x00ff00)
        embed.set_footer(text=f"Executed in {time.time() - start} seconds.")
        if len(df) > 0:
            embed.add_field(name="Output", value=f"```{df.to_string(index=False)}```")
        await ctx.send(embed=embed)

    @app_commands.command(description="Run a SQL query.")
    @commands.is_owner()
    async def sql(self, interaction: discord.Interaction, sql: str):

        start = time.time()
        if str(interaction.user.id) not in self.bot.settings["ADMINS"]:
            return


        if sql.startswith("```sql") and sql.endswith("```"):
            sql = sql[6:-3]
        elif sql.startswith("```") and sql.endswith("```"):
            sql = sql[3:-3]
        
        cursor = self.bot.database.cursor()
        try:
            await cursor.execute(sql)
            output = await cursor.fetchall()

        except Exception as e:
            await interaction.send(f"```{e}```")
            return
        finally:
            cursor.close()
        
        # pretty print the output as a table using pandas
        if output:
            df = pd.DataFrame(output, columns=[x[0] for x in cursor.description])
            
        else:
            df = pd.DataFrame()

        # Send the output as embed
        embed = discord.Embed(title="SQL Query", description=f"```{sql}```", color=0x00ff00)
        embed.set_footer(text=f"Executed in {time.time() - start} seconds.")
        if len(df) > 0:
            embed.add_field(name="Output", value=f"```{df.to_string(index=False)}```")
        await interaction.response.send_message()

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

    
        


async def setup(bot):
    await bot.add_cog(Misc(bot))