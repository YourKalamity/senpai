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

import aiofiles
import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import urllib.parse

class AnimeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    anime_group = app_commands.Group(name="anime", description="Anime related commands")

    async def find_anime(self, interaction: discord.Interaction, image_to_search: discord.Attachment):
        async with self.bot.session.get("https://api.trace.moe/search?anilistInfo&url={}".format(urllib.parse.quote_plus(image_to_search.url))) as response:
            await interaction.response.defer()

            json_response = await response.json()
            if json_response["error"] != "":
                return await interaction.followup.send(f'Failed to locate Anime matching {image_to_search.url}\nReason:'+json_response["error"])
            if json_response["result"][0]["similarity"] < 0.8:
                return await interaction.followup.send(f'Failed to locate Anime matching {image_to_search.url}\nReason: No similarity found, make sure a full screencap is provided')
        
        

        async with self.bot.session.get(json_response["result"][0]["video"]) as response:
            if response.status == 200:
                with open(f'senpai_downloads/{json_response["result"][0]["filename"]}', "wb") as file:
                    file.write(await response.read())


        embed = discord.Embed(color=0xfed3f5, title="Located Anime!")
        embed.add_field(name="Romaji Name", value=json_response["result"][0]["anilist"]["title"]["romaji"])
        embed.add_field(name="Native Name", value=json_response["result"][0]["anilist"]["title"]["native"])
        embed.add_field(name="Episode", value=json_response["result"][0]["episode"], inline=False)

        anilist_query = '''
        query ($id: Int) {
            Media (id: $id, type: ANIME) {
                id
                season
                seasonYear
                status
                averageScore
            }
        }
        '''

        variables = {'id':json_response["result"][0]["anilist"]["id"]}
        url = 'https://graphql.anilist.co'

        async with self.bot.session.post(url, json={'query': anilist_query,'variables': variables}) as response:
            info = await response.json()

        embed.add_field(name="AniList Link", value=f'[{json_response["result"][0]["anilist"]["title"]["romaji"]}](https://anilist.co/anime/{json_response["result"][0]["anilist"]["id"]})', inline=False)
        embed.add_field(name="Season", value=f'{info["data"]["Media"]["season"]} {info["data"]["Media"]["seasonYear"]}', inline=False)
        embed.add_field(name="Staus", value=f'{info["data"]["Media"]["status"]}', inline=True)
        embed.add_field(name="Score", value=f'{info["data"]["Media"]["averageScore"]/10}', inline=True)


        await interaction.followup.send(embed=embed, file=discord.File(f'senpai_downloads/{json_response["result"][0]["filename"]}', filename=json_response["result"][0]["filename"]))
        os.remove(f'senpai_downloads/{json_response["result"][0]["filename"]}')

    @anime_group.command(name="image_search")
    @app_commands.rename(image_to_search="image")
    @app_commands.describe(image_to_search="Screenshot of image to search database")
    async def image_search(self, interaction: discord.Interaction, image_to_search: discord.Attachment):
        return await self.find_anime(interaction, image_to_search)
    


async def setup(bot):
    await bot.add_cog(AnimeCog(bot))
