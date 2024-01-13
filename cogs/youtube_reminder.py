import json
import asyncio
import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import discord
from discord.ext import tasks, commands
from discord import app_commands

class Youtube_Reminder(commands.Cog, description="Commands for youtube remineder"):
    def __init__(self, bot):
        self.bot = bot
        

        self.BASEURL = "https://www.youtube.com/@"
        self.BASEURL2= "https://youtube.com/@"
        self.remind_before_min = 30
        
        self.init_database()
        self.chrome_option = self.init_chrome_option(Options())
        self.dectect_update.start()
    
    def init_chrome_option(self, options=Options):
        options.add_argument("--headless")
        options.add_argument("window-size=1600,800")
        options.add_argument('--log-level=3')
        return options
        
    def init_database(self):
        with open("cogs/record/guild_text_list.json", "r") as f:
            self.guild_text_list = json.load(f)
        with open("cogs/record/remind_list.json", "r") as f:
            self.remind_list = json.load(f)
        with open("cogs/record/last_stream.json", "r") as f:
            self.last_stream = json.load(f)
        with open("cogs/record/last_video.json", "r") as f:
            self.last_video = json.load(f)   
    
    @app_commands.command(name='set_channel', description="Set this channel for remind message")
    async def set_channel(self, interaction:discord.Interaction):
        text_channel = interaction.channel.id
        guild_id = interaction.guild_id
        self.guild_text_list[str(guild_id)] = text_channel
        await interaction.response.send_message("Setting complete.")
        with open("cogs/record/guild_text_list.json", "w") as f:
            json.dump(self.guild_text_list, f, indent=4)
    
    @app_commands.command(name="add_youtube_channel", description="Add youtube channel you want to receive remind.")
    @app_commands.describe(channel_url = "e.g. \"https://www.youtube.com/@*channel_name*\"")
    async def add_channel(self, interaction: discord.Interaction, channel_url: str ):
        guild_id = interaction.guild_id
        if str(guild_id) not in self.guild_text_list:
            await interaction.response.send_message("Haven't set the channel for remind. Must use \"set_channel\" first.")
        else:
            if (not channel_url.startswith(self.BASEURL)) and (not channel_url.startswith(self.BASEURL2)):
                await interaction.response.send_message("Please check your URL and try again.")
            else:
                youtube_channel = channel_url.split('/')[-1]
                if youtube_channel not in self.remind_list:
                    self.remind_list[youtube_channel] = [str(guild_id)]
                    await interaction.response.send_message("Channel added successfully.")
                elif str(guild_id) not in self.remind_list[youtube_channel]:
                    self.remind_list[youtube_channel].append(str(guild_id))
                    await interaction.response.send_message("Channel added successfully.")
                else:
                    await interaction.response.send_message("Channel already existed.")
                with open("cogs/record/remind_list.json", "w") as f:
                    json.dump(self.remind_list, f, indent=4)
                  
    @app_commands.command(name="show_remind_list", description="Show youtube channel in remind list.")
    async def show_remind_list(self, interaction: discord.Interaction):
        guild_id = interaction.guild_id
        emb = discord.Embed(title='List of channel to be remind.', color=discord.Color.blue())
        cnt = 0
        for channel in self.remind_list:
            if str(guild_id) in self.remind_list[channel]:
                cnt += 1
                emb.add_field(name=f"`{channel}`", value='', inline=False)
        
        if cnt == 0:
            emb.add_field(name='You havent\'t add any channel yet!', value='', inline=False)
        
        await interaction.response.send_message(embed = emb)        
        
    @app_commands.command(name="remove_youtube_channel", description="Remove channel setted for remind.") 
    @app_commands.describe(name="e.g. @\"channelname\"")
    async def Remove_Youtube(self, interaction: discord.Interaction, name: str):
        guild_id = interaction.guild_id
        if str(guild_id) in self.remind_list[name]:
            self.remind_list[name].remove(str(guild_id))
            await interaction.response.send_message("Succellfully remove channel.")
        else:
            await interaction.response.send_message("Please check the name and try again.")
    
    async def scrawler(self, driver, channel: str):
        # remind for stream
        url_stream = self.BASEURL + f'{channel[1:]}/streams'
        driver.get(url_stream)
        await asyncio.sleep(0.5)
        channel_name = driver.find_element(By.XPATH, "//*[@id='text']").text
        streams = driver.find_elements(By.XPATH, "//*[@id='contents']/ytd-rich-item-renderer")
        lastest_stream = None
        for i in range(len(streams) - 1, -1, -1):
            if streams[i].text[0: 4] == '即將直播':
                lastest_stream = streams[i]
                break
        if lastest_stream != None:
            isSuccess = True
            try:
                stream_time = lastest_stream.find_element(By.XPATH, "//*[@id='metadata-line']/span[2]").text
                title = lastest_stream.find_element(By.XPATH, "//*[@id='video-title']").text
                link = lastest_stream.find_element(By.XPATH, "//*[@id='video-title-link']").get_attribute('href')
            except Exception as e:
                isSuccess = False
            
            if isSuccess and link != self.last_stream[channel]:
                live_date = stream_time.split('：')[1].split(' ')[0]
                now_date = datetime.date.today().strftime("%Y/%#m/%#d")
                # print(live_date, now_date)
                if live_date == now_date:
                    now_time = [datetime.datetime.now().hour, datetime.datetime.now().minute]
                    live_time = [0, 0]
                    if stream_time[-5].isdigit():
                        live_time[0] = int(stream_time[-5 : -3])
                    else:
                        live_time[0] = int(stream_time[-4 : -3])
                    live_time[1] = int(stream_time[-2: ])
                    if (live_time[0] * 60 + live_time[1]) -  (now_time[0] * 60 + now_time[1]) <= self.remind_before_min :
                        self.last_stream[channel] = link
                        for guild_id in self.remind_list[channel]:
                            text_channel = self.bot.get_channel(int(self.guild_text_list[str(guild_id)]))
                            try:
                                await text_channel.send(f"**New steam at {live_time[0]} : {live_time[1]:0>2}**\n{channel_name} has a new stream: \n {title}  !\n{link} ")
                            except:
                                pass
                        with open("cogs/record/last_stream.json", "w") as f:
                            json.dump(self.last_stream, f, indent=4)
        #remind for video          
        url_video = self.BASEURL + f'{channel[1:]}/videos'
        driver.get(url_video)
        await asyncio.sleep(0.5)
        lastest_video =  driver.find_element(By.XPATH, "//*[@id=\"contents\"]/ytd-rich-item-renderer[1]")
        link = lastest_video.find_element(By.CLASS_NAME, "yt-simple-endpoint.inline-block.style-scope.ytd-thumbnail").get_attribute("href")
        if  link != self.last_video[channel] and self.last_video[channel] != None:
            for guild_id in self.remind_list[channel]:
                text_channel = self.bot.get_channel(int(self.guild_text_list[str(guild_id)]))
                await text_channel.send(f"**Video reminder**\n {channel_name} upload a new video {link}")
        self.last_video[channel] = link
        with open("cogs/record/last_video.json", "w") as f:
            json.dump(self.last_video, f, indent=4)     


    @tasks.loop(minutes = 15)  
    async def dectect_update(self): #TODO : find all scheduled stream and remind for the last one
        print(datetime.datetime.now(), "Start checking update")
        driver = webdriver.Chrome(service=Service('chromedriver.exe'), options=self.chrome_option)       
        for channel in self.remind_list:
            if channel not in self.last_stream:
                self.last_stream[channel] = None
            if channel not in self.last_video:
                self.last_video[channel] = None    
            await self.scrawler(driver, channel)
        driver.close()
            
    @dectect_update.before_loop
    async def before_detect(self):
        await self.bot.wait_until_ready()
        
async def setup(bot):
    await bot.add_cog(Youtube_Reminder(bot))
    