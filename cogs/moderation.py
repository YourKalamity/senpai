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
import typing

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    @commands.has_permissions(administrator = True)
    async def ruleconf(self, ctx, *args):
        if args[0].startswith("https://discord.com/channels/"):
            link = args[0].split("/")
            if int(link[4]) == ctx.guild.id:
                channel_id, msg_id = int(link[5]), int(link[6])
            else:
                return
        else:
            if len(args) == 2:
                channel_id, msg_id = args[0], args[1]
        try:
            channel = await self.bot.fetch_channel(int(channel_id))
        except discord.NotFound:
            await ctx.send("That's not a valid channel specified")
        if channel:
            try:
                message = await channel.fetch_message(int(msg_id))
            except discord.NotFound:
                await ctx.send("That's not a valid message specified")
            if message:
                cursor = self.bot.database.cursor()
                await cursor.execute("SELECT guild_id FROM guilds WHERE guild_id = ?", (ctx.guild.id,))
                data = await cursor.fetchall()
                if len(data) == 0:
                    await cursor.execute("INSERT INTO guilds(guild_id, rule_channel, rule_message) VALUES(?, ?, ?)", (ctx.guild.id, channel.id, message.id,))
                    await self.bot.database.commit()
                    await ctx.send("Added rules channel for this server!")
                    return
                else:
                    await cursor.execute("UPDATE guilds SET rule_channel = ?, rule_message = ? WHERE guild_id = ?", (channel.id, message.id, ctx.guild.id,))
                    await self.bot.database.commit()
                    await ctx.send("Updated rules channel for this server!")
                    return
    
    @commands.command()
    async def rule(self, ctx, rule_number):
        try:
            rule_number = int(rule_number)
        except Exception:
            pass
        if isinstance(rule_number, int) is False:
            rule_number = None
        cursor = self.bot.database.cursor()
        await cursor.execute("SELECT rule_channel, rule_message FROM guilds WHERE guild_id = ?", (ctx.guild.id,))
        data = await cursor.fetchall()
        if len(data) == 0:
            await ctx.send("No rules channel has been set for this server")
        try:
            channel_id, message_id = data[0]
            channel = await self.bot.fetch_channel(channel_id)
        except discord.NotFound:
            await ctx.send("That's not a valid channel specified")
        if channel:
            try:
                message = await channel.fetch_message(message_id)
            except discord.NotFound:
                await ctx.send("That's not a valid message specified")
            if message:
                message_split = message.content.splitlines()
                if rule_number in range(1, len(message_split) + 1):
                    await ctx.send(message_split[rule_number - 1])
                else:
                    await ctx.send(message.content)



    

async def setup(bot):
    await bot.add_cog(Moderation(bot))
    