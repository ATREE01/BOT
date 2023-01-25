import discord
from discord.ext import commands
from discord import app_commands

import os 


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="$",intents=discord.Intents().all())
        
    async def setup_hook(self):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                await bot.load_extension(f"cogs.{filename[:-3]}")

    async def on_ready(self):
        print('目前登入身份：', bot.user)
        sycned = await bot.tree.sync()
        print("Slash CMDS Sycned " + str(len(sycned)) + " Commands")
        
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
               
@bot.tree.command(name='hello', description='Say hello to you.')
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f'Hello <@{interaction.user.id}> !')

token = 'MTA2NjcwMzM1NTI5ODE5MzQzOQ.GZBg8d.RrAbYeUbnSLuTIEZyQhDL1hHXHlXnTlGpIhv-Y'
bot.run(token)
        
