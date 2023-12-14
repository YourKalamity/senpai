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
import datetime
from cogs.misc import SimpleNavigation


class Stars(commands.Cog):

    stars_enabled_cache = {}

    def __init__(self, bot):
        self.bot = bot
    

    async def checkStarsEnabled(self, guild_id):
        if guild_id in self.stars_enabled_cache:
            return self.stars_enabled_cache[guild_id]

        async with self.bot.database.cursor() as cursor:
            await cursor.execute("SELECT stars_enabled FROM guilds WHERE guild_id = ?", (guild_id,))
            result = await cursor.fetchone()
            self.stars_enabled_cache[guild_id] = result[0]
        if result:
            return result[0]
        else:
            return False
        
    
    async def cog_app_command_error(self, interaction, error):
        if error == commands.errors.CheckFailure:
            return
    
    async def cog_command_error(self, ctx, error):
        if error == commands.errors.CheckFailure:
            return


    async def cog_check(self, ctx):
        if await self.checkStarsEnabled(ctx.guild.id):
            return True
        else:
            ctx.send("Stars are not enabled in this server.")
            return False


    async def interaction_check(self, interaction):
        if await self.checkStarsEnabled(interaction.guild.id):
            return True
        else:
            await interaction.response.send_message("Stars are not enabled in this server.")
            return False


    async def getStars(self, user_id, guild_id):
        async with self.bot.database.cursor() as cursor:
            await cursor.execute("SELECT stars FROM stars WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
            result = await cursor.fetchone()
        if result:
            return result[0]
        else:
            return None


    async def getTopStars(self, guild_id):
        async with self.bot.database.cursor() as cursor:
            await cursor.execute("SELECT user_id, stars FROM stars WHERE guild_id = ? ORDER BY stars DESC", (guild_id,))
            result = await cursor.fetchall()
        if result:
            return result
        else:
            return None


    # Function that checks the star count of a user and assigns them the appropriate role, removing any other star roles they may have
    async def checkStarRoles(self, member):
        async with self.bot.database.cursor() as cursor:
            # Get all star roles for the guild and sort them by star count in descending order
            await cursor.execute("SELECT role_id, stars FROM star_roles WHERE guild_id = ? ORDER BY stars DESC", (member.guild.id,))
            star_roles = await cursor.fetchall()

            # Get the star count of the member
            await cursor.execute("SELECT stars FROM stars WHERE user_id = ? AND guild_id = ?", (member.id, member.guild.id))
            star_count = await cursor.fetchone()

            #  Get highest star role for the member
            if star_count:
                for role in star_roles:
                    if star_count[0] >= role[1]:
                        star_role = member.guild.get_role(role[0])
                        break
            else:
                star_role = None

            # Check if member has the star role
            if star_role in member.roles:
                return
            
            # Remove all star roles from the member
            for role in star_roles:
                role = member.guild.get_role(role[0])
                if role in member.roles:
                    await member.remove_roles(role)

            # Add the star role to the member
            if star_role:
                await member.add_roles(star_role)
                return star_role
            else:
                return None


    async def addStarsToRecord(self, user_id, guild_id, new_stars):
        async with self.bot.database.cursor() as cursor:
            try:
                await cursor.execute("""
                    INSERT INTO stars (user_id, guild_id, stars)
                    VALUES (?, ?, ?) 
                    ON CONFLICT(user_id, guild_id) DO 
                        UPDATE SET stars = stars + excluded.stars
                """, (user_id, guild_id, new_stars))
                await self.bot.database.commit()
            except Exception as e:
                return e
    

    @app_commands.command(description="Set a star role for a certain amount of stars.")
    @commands.has_permissions(manage_roles=True)
    async def setstarrole(self, interaction: discord.Interaction, stars: int, role: discord.Role):
        async with self.bot.database.cursor() as cursor:
            await cursor.execute("SELECT role_id FROM star_roles WHERE guild_id = ? AND stars = ?", (interaction.guild.id, stars))
            result = cursor.fetchone()
            if result:
                # Update star amount if role already in database
                await cursor.execute("UPDATE star_roles SET stars = ? WHERE guild_id = ? AND role_id = ?", (stars, role.id, interaction.guild.id))
                self.bot.database.commit()
                await interaction.response.send_message(f"Updated star role for {stars} stars to {role}.")
            else:
                await cursor.execute("INSERT INTO star_roles (guild_id, stars, role_id) VALUES (?, ?, ?)", (interaction.guild.id, stars, role.id))
                self.bot.database.commit()
                await interaction.response.send_message(f"Set star role for {stars} stars to {role}.")

    @app_commands.command(description="View your starcount.")
    async def stars(self, interaction: discord.Interaction):
        stars = await self.getStars(interaction.user.id, interaction.guild.id)
        if stars:
            await interaction.response.send_message(f"You have {stars} stars.")
        else:
            await interaction.response.send_message("You have no stars.")


    @app_commands.command(description="View the users with the most stars.")
    async def topstars(self, interaction: discord.Interaction):
        top = await self.getTopStars(interaction.guild.id)
        if top:

            pages = []
            # Create embeds for each page with 10 rows each
            for i in range(0, len(top), 10):
                embed = discord.Embed(title="Top Stars", color=0xfadadd)
                page_data = ""
                for j in range(i, i + 10):
                    
                    if j >= len(top):
                        break
                    user = interaction.guild.get_member(top[j][0])
                    if user:
                        page_data += f"*{j + 1}*. **{user.name}**#{user.discriminator} - **{top[j][1]}** stars\n"
                    else:
                        try:
                            user = await self.bot.fetch_user(top[j][0])
                        except discord.NotFound:
                            page_data += f"*{j + 1}*. **{top[j][0]}** - **{top[j][1]}** stars\n"
                        
                        else:
                            page_data += f"*{j + 1}*. **{user.name}**#{user.discriminator} - **{top[j][1]}** stars\n"

                embed.add_field(name="Results", value=page_data)
                embed.set_thumbnail(url=interaction.guild.icon.url)
    
                pages.append(embed)
                
        # Send the embeds as a paginated message
        await interaction.response.send_message(embed=pages[0], view=SimpleNavigation(pages))


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if str(payload.emoji) == "⭐":
            message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
            if payload.user_id != message.author.id:
                await self.addStarsToRecord(message.author.id, payload.guild_id, 1)
        
            # Give the user the appropriate star role
            guild = await self.bot.fetch_guild(payload.guild_id)
            member = await guild.fetch_member(payload.user_id)
            await self.checkStarRoles(member)

    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if str(payload.emoji) == "⭐":
            message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
            if payload.user_id != message.author.id:
                await self.addStarsToRecord(message.author.id, payload.guild_id, -1)

            # Give the user the appropriate star role
            guild = await self.bot.fetch_guild(payload.guild_id)
            member = await guild.fetch_member(payload.user_id)
            await self.checkStarRoles(member)


    @app_commands.command(description="Iterate through all users with stars and give them the appropriate star role.")
    @commands.has_permissions(administrator=True)
    async def givestarroles(self, interaction: discord.Interaction):
        # Dictionary to store the star role added to each user
        star_roles = {}
        output = await interaction.channel.send("Giving star roles...")
        await interaction.response.defer(thinking=True)
        for member in interaction.guild.members:
            given_role = await self.checkStarRoles(member)
            if given_role:
                star_roles[member] = given_role
            # Edit the output message to show the star role given to each user
            message = "## Star roles given:\n"
            for member, role in star_roles.items():
                message += f"1. {member} - {role}\n"
            await output.edit(content=message)
        await interaction.channel.send("Done!")


    @app_commands.command(description="Iterate through all messages in the current channel and add stars to the database.")
    @commands.has_permissions(administrator=True)
    async def addstars(self, interaction: discord.Interaction):
        # Have an output message that is edited to show the star count for each user
        await interaction.response.defer(thinking=True)
        output = await interaction.channel.send("Adding stars...")
        # Initialize a 2D array to store the star count for each user
        stars_dictionary = {}
        last_edited = None
        # Iterate through each message
        async for message in interaction.channel.history(limit=None):
            # Check if the message has a star
            if "⭐" in [str(reaction.emoji) for reaction in message.reactions]:
                # Get the number of stars
                for reaction in message.reactions:
                    if str(reaction.emoji) == "⭐":
                        stars = reaction.count
                        break

                await self.addStarsToRecord(message.author.id, interaction.guild.id, stars)
            
                
                # Update the stars_dictionary with the added stars
                if message.author.id in stars_dictionary:
                    stars_dictionary[message.author.id] += stars
                else:
                    stars_dictionary[message.author.id] = stars
            # Check if 10 seconds have passed since the output message was last edited
            if last_edited is None or (datetime.datetime.now() - last_edited).total_seconds() >= 5:
                # Generate the new output message based on the current contents of the stars_dictionary
                output_message = "Adding stars...\n"
                for user_id, stars in stars_dictionary.items():
                    try:
                        user = await self.bot.fetch_user(user_id)
                        output_message += f"{user.name}#{user.discriminator}: {stars} stars\n"
                    except Exception as e:
                        output_message += f"{user_id}: {stars} stars\n"
                    
                # Edit the output message with the new data
                await output.edit(content=output_message)
                # Update the last_edited variable
                last_edited = datetime.datetime.now()

        # Generate the final output message
        output_message = "Finished adding stars. Here is the star count for each user:\n"
        for user_id, stars in stars_dictionary.items():
            try:
                user = await self.bot.fetch_user(user_id)
                output_message += f"{user.name}#{user.discriminator}: {stars} stars\n"
            except Exception as e:
                output_message += f"{user_id}: {stars} stars\n"

        # Edit the output message with the final data
        await output.edit(content="All done!")
        await interaction.followup.send(output_message)


    @app_commands.command(description="Iterate through all messages in the current server and add stars to the database.")
    @commands.has_permissions(administrator=True)
    async def addstarsall(self, interaction: discord.Interaction):
        # Have an output message that is edited to show the star count for each user
        await interaction.response.defer(thinking=True)
        output = await interaction.channel.send("Adding stars...")
        # Initialize a dictionary to store the star count for each user
        stars_dictionary = {}
        last_edited = None
        output_message = "Adding stars...\n"
        # Iterate through each channel
        for channel in interaction.guild.text_channels:
            if isinstance(channel, discord.TextChannel):
                async for message in channel.history(limit=None):
                    # Check if the message has a star
                    if "⭐" in [str(reaction.emoji) for reaction in message.reactions]:
                        # Get the number of stars
                        stars = message.reactions[0].count
                        # Check if the star record already exists for the user
                        cursor = self.bot.database.cursor()
                        try:
                            await cursor.execute("""
                                INSERT INTO stars (user_id, guild_id, stars)
                                VALUES (?, ?, ?) 
                                ON CONFLICT(user_id, guild_id) DO 
                                    UPDATE SET stars = stars + excluded.stars
                            """, (message.author.id, interaction.guild.id, stars))
                            await self.bot.database.commit()
                        except Exception as e:
                            interaction.followup.send_message(f"Error adding stars to {message.author}: {e}")
                        
                        # Update the stars_dictionary with the added stars
                        if message.author.id in stars_dictionary:
                            stars_dictionary[message.author.id] += stars
                        else:
                            stars_dictionary[message.author.id] = stars
                    # Check if 10 seconds have passed since the output message was last edited
                    if last_edited is None or (datetime.datetime.now() - last_edited).total_seconds() >= 5:
                        # Generate the new output message based on the current contents of the stars_dictionary
                        output_message = f"Adding stars for Current Channel: {channel}\n"
                        for user_id, stars in stars_dictionary.items():
                            try:
                                user = await self.bot.fetch_user(user_id)
                                output_message += f"{user.name}#{user.discriminator}: {stars} stars\n"
                            except Exception as e:
                                output_message += f"{user_id}: {stars} stars\n"

                        # Edit the output message with the new data
                        await output.edit(content=output_message)
                        # Update the last_edited variable
                        last_edited = datetime.datetime.now()

        # Generate the final output message
        output_message = "Finished adding stars. Here is the star count for each user:\n"
        for user_id, stars in stars_dictionary.items():
            try:
                user = await self.bot.fetch_user(user_id)
                output_message += f"{user.name}#{user.discriminator}: {stars} stars\n"
            except Exception as e:
                output_message += f"{user_id}: {stars} stars\n"

        # Edit the output message with the final data
        await output.edit(content="All done!")
        await interaction.followup.send(output_message)


async def setup(bot):
    await bot.add_cog(Stars(bot))

