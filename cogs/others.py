import discord
from discord.ext import commands
from discord import app_commands

import os, random

class others(commands.Cog, description='Other commands'):
    def __init__(self, bot):
        self.bot = bot
        
        self.key_word =["@345922184017084427", "施奕安", "詩意安", "施亦安", "施易安", "失意安"]
        
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author != self.bot.user.name:
            for key in self.key_word:
                if key in message.content:
                    path = random.choice(os.listdir('C:/Users/anyu9/OneDrive - 國立中央大學/Pixiv_imgs/'))
                    await message.channel.send(file=discord.File(f'C:/Users/anyu9/OneDrive - 國立中央大學/Pixiv_imgs/{path}'))
        
    @app_commands.command(name='hello', description='Say hello to you.')
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'Hello <@{interaction.user.id}> !')
        
async def setup(bot):
    await bot.add_cog(others(bot))
    