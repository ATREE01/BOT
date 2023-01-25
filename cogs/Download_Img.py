import discord
from discord.ext import commands
from discord import app_commands

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

import time

import requests
from bs4 import BeautifulSoup 

import os 



class Download_Img(commands.Cog, description="Use to download photo from website."):
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name='download_img_insta',description="download img from instagram")
    async def download_img_insta(self, interaction: discord.Interaction, url:str):
        """use for download img from instagram"""
        await interaction.response.defer()
        if "instagram" in url:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            driver = webdriver.Chrome('chromedriver',options = chrome_options)
            driver.get(url)
            time.sleep(3)
            img_urls = set()
            try:
                while True:
                    button = driver.find_element(By.CLASS_NAME, "_afxw")
                    soup = BeautifulSoup(driver.page_source, "lxml")
                    datas = soup.find_all('li', class_="_acaz")
                    for data in datas:
                        img_urls.add(str(data.img.get('src')))
                    button.click()
                    try:
                        button = driver.find_element(By.CLASS_NAME, "_afxw")
                    except: 
                        break
            except:
                soup = BeautifulSoup(driver.page_source, "lxml")
                img_urls.add(str(soup.find_all(class_="x87ps6o")[0].get('src')))
            for index, url in enumerate (img_urls):
                response = requests.get(url)
                if response.status_code:
                    with open(f"output{index}.png",'wb') as output:
                        output.write(response.content)  
                        await interaction.followup.send(file = discord.File(f"output{index}.png"))
                    os.remove(f"output{index}.png")
        else:
            await interaction.response.send_message("Incorrect URL!")
   
async def setup(bot):
    await bot.add_cog(Download_Img(bot))
        
