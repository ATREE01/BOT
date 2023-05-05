import discord
from discord.ext import commands
from discord import app_commands

import os, random
import json

import time
from colorama import Back, Fore, Style

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="$",intents=discord.Intents().all(),heartbeat_timeout=100)
    
    async def setup_hook(self):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and filename != "chatgpt.py": #remove chatgpt 
                await bot.load_extension(f"cogs.{filename[:-3]}")

    async def on_ready(self):
        await bot.change_presence(activity=discord.Game(name="戀上換裝娃娃"))
        prefx = (Back.BLACK + Fore.GREEN + time.strftime("%H:%M:%S", time.localtime()) + Back.RESET + Fore.WHITE + Style.BRIGHT)
        print(prefx + ' 目前登入身份：' + Fore.BLUE + self.user.name)
        sycned = await bot.tree.sync()
        print(prefx + " Slash CMDS Sycned " + Fore.YELLOW + str(len(sycned)) + " Commands" + Fore.RESET)

bot = Bot()

@bot.tree.command(name='help',description = "Shows help for ATREE_BOT's slash commands.")
@app_commands.describe(command = "The command to get help for")
async def help(interaction: discord.Interaction, command:str=None):
    
    emb = discord.Embed(title='Shows help for ATREE_BOT\'s slash commands.', color=discord.Color.blue(),
                        description=f'Use `/help <command>` to gain more information about that command '
                                    f':smiley:\n')
    
    # iterating trough cogs
    if command == None:
        in_cog = []
        for cog in bot.cogs:
            emb.add_field(name=f'`{cog}`', value=f"Description: {bot.cogs[cog].description}", inline=False)
            commands_name = ''
            for cmd in bot.get_cog(cog).get_app_commands():
                in_cog.append(cmd.name)
                if len(commands_name):
                    commands_name += ','    
                commands_name += f'`/{cmd.name}`'
            emb.add_field(name=f"{commands_name}",value='', inline=False)
            
        for cmd in bot.tree.get_commands():
            if cmd.name not in in_cog:
                emb.add_field(name=f'`/{cmd.name}`', value=f"Description: {cmd.description}",inline=False)
    else :
        flag = False
        for cmd in bot.tree.get_commands():
            if cmd.name == command:
                flag = True
                emb.add_field(name=f'`{cmd.name}`', value=f'Description: {cmd.description}',inline=False)
                break
        if not flag:
            emb.add_field(name='The command doesn\'t exist. Plese check the name of the command.',value='',inline=False)
    
    await interaction.response.send_message(embed = emb)

with open('./token.json', 'r', encoding='utf-8') as file:
    data = json.load(file)
bot.run(data['token'])
