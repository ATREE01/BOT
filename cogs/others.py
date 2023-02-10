import discord
from discord.ext import commands
from discord import app_commands

import os, random

class others(commands.Cog, description='Other commands'):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author != self.bot.user.name:
            if '@345922184017084427' in message.content or '施奕安' in message.content:
                path = random.choice(os.listdir('C:/Users/anyu9/OneDrive - 國立中央大學/Pixiv_imgs/'))
                await message.channel.send(file=discord.File(f'C:/Users/anyu9/OneDrive - 國立中央大學/Pixiv_imgs/{path}'))
        
    @app_commands.command(name='hello', description='Say hello to you.')
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'Hello <@{interaction.user.id}> !')
        
async def setup(bot):
    await bot.add_cog(others(bot))
    