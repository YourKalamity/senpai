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

import aiohttp
import asyncio
import asqlite
import discord
import json
import os
import pathlib
import sys
import shutil
import sqlite3
import traceback

from discord.ext import commands

def load_settings():
    try:
        if not pathlib.Path("settings.json").is_file():
            print("[INFO] Copying settings file")
            shutil.copy("assets/examplesettings.json", "settings.json")
        with open("settings.json") as settings_file:
            settings = json.load(settings_file)
    except Exception as e:
        print(f"[EXCP] {e}")
        print("[EXCP] Could not open settings file - Please check your permissions")
        return None
    
    for key, value in settings.items():
        if value == "" or value == []:
            new = ""
            while new == "":
                try:
                    new = input(f"Set {key} : ")
                    if value == "":
                        settings[key] = new
                    if value == []:
                        settings[key].append(new)
                except Exception:
                    pass

    try:
        with open("settings.json", "w") as settings_file:
            json.dump(settings, settings_file, indent=4)
    except Exception as e:
        print("[EXCP] Couldn't Save settings")
        return None
    print("[INFO] Loaded settings")
    return settings


class Senpai(discord.ext.commands.AutoShardedBot):
    def __init__(self, settings):
        self.settings = settings
        intents = discord.Intents(guilds=True, members=True, bans=True, messages=True, message_content=True, reactions=True)
        allowed_mentions = discord.AllowedMentions(everyone=False, roles=True)
        activity = discord.Game(self.settings["STATUS"])
        status = discord.Status.idle
        try:
            self.database = sqlite3.connect(self.settings["DATABASE"])
            print("[INFO] Connected to database")
        except Exception as e:
            print(f"[EXCP] {e}")
            print("[EXCP] Could not connect to database")
            sys.exit(1)
        
        super().__init__(
                command_prefix = self.settings["PREFIXES"],
                intents = intents,
                allowed_mentions = allowed_mentions,
                activity = activity,
                status = status,
                case_insensitive = True,
                application_id = self.settings["APPLICATION_ID"]
        )

    async def log_error(self, ctx, error):
        guild = self.get_guild(self.settings["GUILD"])
        channel = guild.get_channel(self.settings["ERROR_CHANNEL"])
        # Create hash for error for easier searching
        error_hash = hash(error)
        # Get full exception
        exception = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        # Get command invocation
        invocation = ctx.message.content
        # Format error message with traceback and invocation in embed
        embed = discord.Embed(title=f"Senpai ran into an error :( `{error_hash}`", description=f"```py\n{exception}\n```", color=0xff0000)
        embed.add_field(name="Command", value=f"```{invocation}```", inline=False)
        embed.add_field(name="Channel", value=f"```{ctx.channel}```", inline=False)
        embed.add_field(name="Author", value=f"```{ctx.author}```", inline=False)
        embed.add_field(name="Guild", value=f"```{ctx.guild}```", inline=False)
        embed.add_field(name="Message", value=f"```{ctx.message}```", inline=False)
        embed.add_field(name="Jump", value=f"[Jump to message]({ctx.message.jump_url})", inline=False)
        await channel.send(embed=embed)

        await ctx.send(f"Senpai ran into an error :( `{error_hash}`")

    def setup_db(self):
        cursor = self.database.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guilds (
                guild_id integer PRIMARY KEY,
                rule_channel integer,
                rule_message integer,
                log_channel integer,
                min_mod_role integer,
                stars_enabled boolean
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blacklist (
                user_id integer PRIMARY KEY,
                reason text
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stars (
                user_id integer,
                guild_id integer,
                stars integer,
                PRIMARY KEY (user_id, guild_id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS star_roles (
                guild_id integer,
                role_id integer,
                stars integer,
                PRIMARY KEY (guild_id, role_id)
            )
        ''')

    async def setup_hook(self):
        self.session: aiohttp.ClientSession = aiohttp.ClientSession() 
        self.tree.copy_global_to(guild=discord.Object(id=725325701321981962))
        await self.tree.sync(guild=discord.Object(id=725325701321981962))
        
        print(f"[COGS] Loading cogs...")
        cog = ""
        for filename in os.listdir("./cogs"):
            try:
                if filename.endswith(".py"):
                    cog = f"cogs.{filename[:-3]}"
                    await self.load_extension(cog)
                    print(f"[COGS] Loaded cog : {filename[:-3]}")
            except Exception as e:
               print(f"[COGS] Failed to load cog : {filename}")
               print(f"[EXCP] {e}")
        try:
            cog = "jishaku"
            await self.load_extension("jishaku")
            print("[COGS] Loaded cog : jishaku")
        except Exception as e:
            print(f"[COGS] Failed to load cog : jishaku")
            print(f"[EXCP] {e}")

    async def on_command_error(self, ctx, error):
        print(f"[EXCP] {error}")
        if type(error) == commands.CommandNotFound:
            return
        else:
            await self.log_error(ctx, error)
    
    

    def run(self, token=None):
        if token == None:
            token = self.settings["TOKEN"]
        self.setup_db()
        super().run(token)



def main():
    bot = Senpai(load_settings())
    print(f"[INFO] Connecting to Discord...")
    bot.run()


if __name__ == "__main__":
    os.chdir(sys.path[0])
    main()
