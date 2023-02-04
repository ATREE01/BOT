import asyncio

import discord
from discord.ext import commands
from discord import app_commands

from dotenv import load_dotenv

import json

import openai

class chat_bot(commands.Cog, description='This is a chat bot.'):
    def __init__(self, bot):
        self.bot = bot

        
    def chatgpt_response(self, prompt):
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            temperature=1,
            max_tokens=500,
        )
        response_dict = response.get("choices")
        if response_dict and len(response_dict) > 0:
            prompt_response = response_dict[0]['text']
        return prompt_response
    
    @app_commands.command(name='chat', description="Talk to chat_bot.")
    async def chat(self, interaction: discord.Interaction,prompt: str=None):
        await interaction.response.defer()
        try:  
            bot_response = self.chatgpt_response(prompt)
            await interaction.followup.send(f'{interaction.user}:\n{prompt}\nマリン:\n{bot_response.strip()}')
        except:
            await interaction.response.send_message("Please try another sentence.")
    
    @app_commands.command(name='gen_img', description='Create an original image given a text prompt')        
    async def gen_img(self, interaction: discord.Interaction, prompt: str=None):
        await interaction.response.defer()
        response = openai.Image.create(
            prompt = prompt,
            n = 1,
            size = "1024x1024"
        )
        img_url = response['data'][0]['url']
        await interaction.followup.send(f'{img_url}')
    
with open('./cogs/key.json', 'r', encoding='utf-8') as file:
    data = json.load(file)
openai.api_key = data["chatgpt_api_key"]
        
async def setup(bot):
    await bot.add_cog(chat_bot(bot))