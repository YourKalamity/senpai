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

class FunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="Jhinify a message.")
    async def jhinify(self, interaction: discord.Interaction, *, message: str):
        # Replaces all instances of "four" with "4" and "for" with "4" 

        message = message.replace("four", "4")
        message = message.replace("for", "4")   

        # split the message into a list of words
        words = message.split(" ")
        # replace first character of each word with "jh"
        for i in range(len(words)):
            words[i] = "jh" + words[i][1:]

        # join the list of words into a string with 4 words per line
        message = ""
        for i in range(0, len(words), 4):
            message += " ".join(words[i:i+4]) + "\n"

        await interaction.response.send_message(message)

async def setup(bot):
    await bot.add_cog(FunCog(bot))

        

