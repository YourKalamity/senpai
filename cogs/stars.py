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
import datetime

class Stars(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    


    def checkStarsEnabled(self, guild_id):
        cursor = self.bot.database.cursor()
        cursor.execute("SELECT stars_enabled FROM guilds WHERE guild_id = ?", (guild_id,))
        result = cursor.fetchone()
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
        if self.checkStarsEnabled(ctx.guild.id):
            return True
        else:
            ctx.send("Stars are not enabled in this server.")
            return False


    async def interaction_check(self, interaction):
        if self.checkStarsEnabled(interaction.guild.id):
            return True
        else:
            await interaction.response.send_message("Stars are not enabled in this server.")
            return False

    def getStars(self, user_id, guild_id):
        cursor = self.bot.database.cursor()
        cursor.execute("SELECT stars FROM stars WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None


    def getTopTenStars(self, guild_id):
        cursor = self.bot.database.cursor()
        cursor.execute("SELECT user_id, stars FROM stars WHERE guild_id = ? ORDER BY stars DESC LIMIT 10", (guild_id,))
        result = cursor.fetchall()
        if result:
            return result
        else:
            return None
    
    # Function that checks the star count of a user and assigns them the appropriate role, removing any other star roles they may have
    async def checkStarRoles(self, member):

        cursor = self.bot.database.cursor()
        cursor.execute("SELECT stars, role_id FROM star_roles WHERE guild_id = ?", (member.guild.id,))
        result = cursor.fetchall()
        if result:
            for role in member.roles:
                if role.id in [x[1] for x in result]:
                    await member.remove_roles(role)
            for star_count, role_id in reversed(result):
                starCount = self.getStars(member.id, member.guild.id)
                if starCount and starCount >= star_count:
                    await member.add_roles(member.guild.get_role(role_id))
                    return member.guild.get_role(role_id).name  
        else:
            for role in member.roles:
                if role.id in [x[1] for x in result]:
                    await member.remove_roles(role)
        return None
    
    
    @app_commands.command(description="Set a star role for a certain amount of stars.")
    @commands.has_permissions(manage_roles=True)
    async def setstarrole(self, interaction: discord.Interaction, stars: int, role: discord.Role):
        cursor = self.bot.database.cursor()
        cursor.execute("SELECT role_id FROM star_roles WHERE guild_id = ? AND stars = ?", (interaction.guild.id, stars))
        result = cursor.fetchone()
        if result:
            # Update star amount if role already in database
            cursor.execute("UPDATE star_roles SET stars = ? WHERE guild_id = ? AND role_id = ?", (stars, role.id, interaction.guild.id))
            self.bot.database.commit()
            await interaction.response.send_message(f"Updated star role for {stars} stars to {role}.")
        else:
            cursor.execute("INSERT INTO star_roles (guild_id, stars, role_id) VALUES (?, ?, ?)", (interaction.guild.id, stars, role.id))
            self.bot.database.commit()
            await interaction.response.send_message(f"Set star role for {stars} stars to {role}.")

    @app_commands.command(description="View your starcount.")
    async def stars(self, interaction: discord.Interaction):
        stars = self.getStars(interaction.user.id, interaction.guild.id)
        if stars:
            await interaction.response.send_message(f"You have {stars} stars.")
        else:
            await interaction.response.send_message("You have no stars.")


    @app_commands.command(description="View the top 10 users with the most stars.")
    async def topstars(self, interaction: discord.Interaction):
        top_ten = self.getTopTenStars(interaction.guild.id)
        if top_ten:
            message = "## Top 10 users with the most stars:\n"
            # Ensure users with the same amount of stars are tied
            for i, user in enumerate(top_ten):
                try:
                    member = await self.bot.fetch_user(user[0])
                except discord.NotFound:
                    member = user[0]
                message += f"{i+1}. {member} - **{user[1]}** stars\n"
            await interaction.response.send_message(message)
        else:
            await interaction.response.send_message("No users have any stars.")


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if str(payload.emoji) == "⭐":
            message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
            if payload.user_id != message.author.id:
                stars = self.getStars(message.author.id, payload.guild_id)
                if stars:
                    stars += 1
                    cursor = self.bot.database.cursor()
                    cursor.execute("UPDATE stars SET stars = ? WHERE user_id = ? AND guild_id = ?", (stars, message.author.id, payload.guild_id))
                    self.bot.database.commit()
                else:
                    cursor = self.bot.database.cursor()
                    cursor.execute("INSERT INTO stars VALUES (?, ?, ?)", (message.author.id, payload.guild_id, 1))
                    self.bot.database.commit()
        
        if payload.guild_id == 725325701321981962:
            # Give the user the appropriate star role
            guild = await self.bot.fetch_guild(payload.guild_id)
            member = await guild.fetch_member(payload.user_id)
            await self.checkStarRoles(member)

    

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if str(payload.emoji) == "⭐":
            message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
            if payload.user_id != message.author.id:
                stars = self.getStars(message.author.id, payload.guild_id)
                if stars:
                    stars -= 1
                    cursor = self.bot.database.cursor()
                    cursor.execute("UPDATE stars SET stars = ? WHERE user_id = ? AND guild_id = ?", (stars, message.author.id, payload.guild_id))
                    self.bot.database.commit()
                else:
                    cursor = self.bot.database.cursor()
                    cursor.execute("INSERT INTO stars VALUES (?, ?, ?)", (message.author.id, payload.guild_id, 1))
                    self.bot.database.commit()
        
        if payload.guild_id == 725325701321981962:
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
                stars = message.reactions[0].count
                # Check if the star record already exists for the user
                cursor = self.bot.database.cursor()
                cursor.execute("SELECT stars FROM stars WHERE user_id = ? AND guild_id = ?", (message.author.id, interaction.guild.id))
                result = cursor.fetchone()
                if result:
                    db_stars = result[0]
                    # Add the stars to the user's current star count
                    try:
                        cursor.execute("UPDATE stars SET stars = ? WHERE user_id = ? AND guild_id = ?", (db_stars + stars, message.author.id, interaction.guild.id))
                        self.bot.database.commit()
                    except Exception as e:
                        interaction.followup.send_message(f"Error adding stars to {message.author}: {e}")
                else:
                    # Create a new entry for the user
                    cursor = self.bot.database.cursor()
                    try:
                        cursor.execute("INSERT INTO stars VALUES (?, ?, ?)", (message.author.id, interaction.guild.id, stars))
                        self.bot.database.commit()
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
                        cursor.execute("SELECT stars FROM stars WHERE user_id = ? AND guild_id = ?", (message.author.id, interaction.guild.id))
                        result = cursor.fetchone()
                        if result:
                            db_stars = result[0]
                            # Add the stars to the user's current star count
                            try:
                                cursor.execute("UPDATE stars SET stars = ? WHERE user_id = ? AND guild_id = ?", (db_stars + stars, message.author.id, interaction.guild.id))
                                self.bot.database.commit()
                            except Exception as e:
                                interaction.followup.send_message(f"Error adding stars to {message.author}: {e}")
                        else:
                            # Create a new entry for the user
                            cursor = self.bot.database.cursor()
                            try:
                                cursor.execute("INSERT INTO stars VALUES (?, ?, ?)", (message.author.id, interaction.guild.id, stars))
                                self.bot.database.commit()
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

