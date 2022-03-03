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
import json
import os
import pathlib
import sys
import shutil
import sqlite3

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
        intents = discord.Intents(guilds=True, members=True, bans=True, messages=True)
        allowed_mentions = discord.AllowedMentions(everyone=False, roles=True)
        activity = discord.Game(self.settings["STATUS"])
        status = discord.Status.idle
        try:
            self.database = sqlite3.connect("senpai_database.db")
        except sqlite3.Error as e:
            print(e)
        super().__init__(
                command_prefix=self.settings["PREFIXES"],
                intents=intents,
                allowed_mentions=allowed_mentions,
                activity=activity,
                status=status,
                case_insensitive=True
        )

    def load_cogs(self):
        cog = ""
        for filename in os.listdir("./cogs"):
            try:
                if filename.endswith(".py"):
                    cog = f"cogs.{filename[:-3]}"
                    self.load_extension(cog)
                    print(f"[COGS] Loaded cog : {filename[:-3]}")
            except Exception as e:
               print(f"[COGS] Failed to load cog : {filename}")
               print(f"[EXCP] {e}")
        try:
            cog = "jishaku"
            self.load_extension("jishaku")
            print("[COGS] Loaded cog : jishaku")
        except Exception as e:
            print(f"[COGS] Failed to load cog : jishaku")
            print(f"[EXCP] {e}")
    
    def setup_db(self):
        cursor = self.database.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guilds (
                guild_id integer PRIMARY KEY,
                rule_channel integer,
                rule_message integer
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blacklist (
                user_id integer PRIMARY KEY,
                reason text
            )
        ''')

    def run(self, token=None):
        if token == None:
            token = self.settings["TOKEN"]
        self.setup_db()
        super().run(token)


def main():
    bot = Senpai(load_settings())
    print(f"[COGS] Loading cogs...")
    bot.load_cogs()
    print(f"[INFO] Connecting to Discord...")
    bot.run()

if __name__ == "__main__":
    os.chdir(sys.path[0])
    main()
