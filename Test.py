import discord 
from discord.ext import commands
from discord import app_commands

import yt_dlp
import requests

from pytube import Playlist

import asyncio

import random
import datetime

import os

class Music(commands.Cog, description='Commands for playing music from youtube.'):
    def __init__(self):
        self.guild_list = []
        
        self.is_playing = {}
        self.is_paused = {}
        self.is_loop = {}
        self.skiped = {}
        
        self.now_playing = {}
        self.now_playing_info_msg = {}
        
        self.music_queue = {}
        
        self.YDL_OPTIONS = {'format': 'bestaudio',
                            'noplaylist': True,
                            'quiet': True,
                            'postprocessors': [{  # Extract audio using ffmpeg
                                'key': 'FFmpegExtractAudio',
                                'preferredcodec': 'm4a',
                            }],
                            'flat_playlist': True,
                            'outtmpl': './Youtube/%(title)s.%(ext)s',
                            }
        
        self.FFMEPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        
        self.voice_channel = {}

    def init(self, guild_id):
        self.guild_list.append(guild_id)
        self.is_playing[guild_id] = False
        self.is_paused[guild_id] = False
        self.is_loop[guild_id] = False
        self.skiped[guild_id] = False
        self.now_playing[guild_id] = None
        self.now_playing_info_msg[guild_id] = None 
        
        self.music_queue[guild_id] = []
        
        self.voice_channel[guild_id] = None

    async def search_YT(self, item):
        try:
            with yt_dlp.YoutubeDL(self.YDL_OPTIONS) as ydl:
                if 'https' and 'youtube' in item:
                    info = await asyncio.to_thread(ydl.extract_info, url=item, download=False)   
                else :
                    info = await asyncio.to_thread(ydl.extract_info, url=f'ytsearch:{item}', download=False)['entries'][0]
            song = {
                'title': info['title'],
                'duration': info['duration'] if 'duration' in info else 'Live',
                'channel_name': info['channel'],
                'channel_url': info['channel_url'],
                'url': info['webpage_url'],
                'music_url': [_['url'] for _ in info['formats'] if _.get('format_note') == 'medium'][0],
                'thumbnail': info['thumbnail'],
            }
        except Exception as e:
            print(e)
            return False
        return song
 
# urls = ['https://www.youtube.com/watch?v=IpEVD2Gb_zg&list=RDYjrSkBjDVEw&index=8',
#        'https://www.youtube.com/watch?v=lBxOXJmIZTo&list=RDYjrSkBjDVEw&index=9',
#        'https://www.youtube.com/watch?v=SDk1RA4g8CA&list=RDYjrSkBjDVEw&index=11',
#        "https://www.youtube.com/watch?v=OIBODIPC_8Y&list=RDYjrSkBjDVEw&index=12&pp=8AUB",
#        "https://www.youtube.com/watch?v=OIBODIPC_8Y&list=RDYjrSkBjDVEw&index=12&pp=8AUB"]

import time
from pytube import Playlist

async def main():
    startTime = time.time()
    music = Music()
    urls = Playlist("https://www.youtube.com/playlist?list=PLv8IjO5oRjs9IbUktpXPNIxKq5I8Nz16v")
    tasks = [asyncio.create_task(music.search_YT(url)) for url in urls]
    results = await asyncio.gather(*tasks)
    print(len(results))
    print(time.time() - startTime)

    
if __name__ == '__main__':
    asyncio.run(main())
