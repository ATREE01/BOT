import discord
from discord.ext import commands
from discord import app_commands

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

import time

import requests

import os 

class Download_Img(commands.Cog, description="Use to download photo from website."):
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name='download_img',description="download img from instagram or twitter")
    async def download_img(self, interaction: discord.Interaction, url:str):
        await interaction.response.defer()
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome('chromedriver',options = chrome_options)
        try:
            if "instagram" in url:
                driver.get(url)
                time.sleep(3)
                img_urls = set()
                try:
                    while True:
                        button = driver.find_element(By.CLASS_NAME, "_afxw")
                        datas = driver.find_elements(By.CLASS_NAME, "x5yr21d.xu96u03.x10l6tqk.x13vifvy.x87ps6o.xh8yej3")
                        for data in datas:
                            img_urls.add(data.get_attribute('src'))
                        button.click()
                        try:
                            button = driver.find_element(By.CLASS_NAME, "_afxw")
                        except: 
                            break
                except:
                    data = driver.find_element(By.CLASS_NAME, "x5yr21d.xu96u03.x10l6tqk.x13vifvy.x87ps6o.xh8yej3")
                    img_urls.add(data.get_attribute('src'))
                    
                for index, url in enumerate (img_urls):
                    response = requests.get(url)
                    if response.status_code:
                        with open(f"output{index}.png",'wb') as output:
                            output.write(response.content)  
                            await interaction.followup.send(file = discord.File(f"output{index}.png"))
                        os.remove(f"output{index}.png")
                        
            elif 'twitter' in url:
                driver.get(url)
                time.sleep(1)
                imgs = driver.find_elements(By.XPATH, "//img[@alt='圖片']")
                for index, img in enumerate (imgs):
                    img_url = img.get_attribute('src')
                    response = requests.get(img_url)
                    if response.status_code:
                        with open(f"output{index}.png",'wb') as output:
                            output.write(response.content)  
                            await interaction.followup.send(file = discord.File(f"output{index}.png")) 
                        os.remove(f"output{index}.png")
        except:
            await interaction.response.send_message("Incorrect URL!")
            
async def setup(bot):
    await bot.add_cog(Download_Img(bot))