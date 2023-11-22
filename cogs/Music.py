import discord 
from discord.ext import commands
from discord import app_commands

import yt_dlp

from pytube import Playlist

import asyncio

import random
import datetime

import os
class Music(commands.Cog, description='Commands for playing music from youtube.'):
    def __init__(self , bot):
        self.bot = bot
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

    def search_YT(self, item):
        with yt_dlp.YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                if 'https' and 'youtube' in item:
                    info = ydl.extract_info(item,download = False)   
                else :
                    info = ydl.extract_info(f'ytsearch:{item}' ,download = False)['entries'][0]
                song = {
                    'title': info['title'],
                    'duration': info['duration'] if 'duration' in info else 'Live',
                    'channel_name': info['channel'],
                    'channel_url': info['channel_url'],
                    'url': info['webpage_url'],
                    'music_url': [_['url'] for _ in info['formats'] if _.get('format_note') == 'medium'][0],
                    'thumbnail': info['thumbnail'],
                }
            except:
                return False
        return song

    def my_after(self, text_channel, guild_id):
        coro = self.play_next(text_channel, guild_id)
        future = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)

    async def idle_detect(self, text_channel, guild_id):
        await asyncio.sleep(90)
        if self.is_playing[guild_id] == False:
            emb = discord.Embed(title='Idle for too long!', color=discord.Color.red())
            await self.voice_channel[guild_id].disconnect()
            await text_channel.send(embed = emb)
            self.init(guild_id)

    async def play_next(self, text_channel, guild_id):
        if self.skiped[guild_id] == True:
            self.skiped[guild_id] = False
            return
        if self.is_loop[guild_id] == True:
            source = await discord.FFmpegOpusAudio.from_probe(self.now_playing[guild_id]['music_url'], **self.FFMEPEG_OPTIONS)
            self.voice_channel[guild_id].play(source,after=lambda e:self.my_after(text_channel, guild_id))
        else:
            if self.now_playing_info_msg[guild_id] != None:
                await self.now_playing_info_msg[guild_id].delete()#刪除前面的音樂撥放訊息
            self.music_queue[guild_id].pop(0)
            if len(self.music_queue[guild_id]) == 0:
                self.is_playing[guild_id] = False
                await self.idle_detect(text_channel, guild_id)
                return
            
            self.now_playing[guild_id] = self.search_YT(self.music_queue[guild_id])
            while self.now_playing[guild_id] == False and len(self.music_queue[guild_id]) > 0:
                await text_channel.send(f"Can not play this track \"{self.music_queue[guild_id][0]}\" skipping to next track.")
                self.music_queue[guild_id].pop(0)
                self.now_playing_info_msg[guild_id] = None
                await self.now_playing_info_msg[guild_id].delete()
                self.now_playing[guild_id] = self.search_YT(self.music_queue[guild_id])
                if len(self.music_queue[guild_id] == 0):
                    return
            
            self.is_playing[guild_id] = True
            self.now_playing_info_msg[guild_id] = await text_channel.send(embed=(self.now_playing_info(guild_id)))
            source = await discord.FFmpegOpusAudio.from_probe(self.now_playing[guild_id]['music_url'], **self.FFMEPEG_OPTIONS)
            self.voice_channel[guild_id].play(source,after=lambda e:self.my_after(text_channel, guild_id))
            
    def now_playing_info(self, guild_id):
        emb = discord.Embed(title='Now playing 🎵: ', color=discord.Color.blue())
        emb.set_thumbnail(url=self.now_playing[guild_id]['thumbnail'])
        emb.add_field(name='Title:', value=f"[{self.now_playing[guild_id]['title']}]({self.now_playing[guild_id]['url']})", inline=False)
        emb.add_field(name='Channel:', value=f"[{self.now_playing[guild_id]['channel_name']}]({self.now_playing[guild_id]['channel_url']})")
        emb.add_field(name='Duration:', value='Live' if self.now_playing[guild_id]['duration'] == 'Live' else datetime.timedelta(seconds = self.now_playing[guild_id]['duration']))
        return emb
        
    async def play_music(self,text_channel, voice_channel, guild_id):
        if len(self.music_queue[guild_id]) > 0 :
            self.now_playing[guild_id] = self.search_YT(self.music_queue[guild_id][0])
            if self.now_playing[guild_id] == False:
                await text_channel.send(f"Can not play this track \"{self.music_queue[guild_id][0]}\" skipping to next track.")
                self.music_queue[guild_id].pop(0)
                await self.play_music(text_channel, voice_channel, guild_id)
                return
            elif self.voice_channel[guild_id] == None or not self.voice_channel[guild_id].is_connected() :
                self.voice_channel[guild_id] = await voice_channel.connect()    
                   
            await self.voice_channel[guild_id].move_to(voice_channel)
            self.now_playing_info_msg[guild_id] = await text_channel.send(embed=self.now_playing_info(guild_id))
            self.is_playing[guild_id] = True
            source = await discord.FFmpegOpusAudio.from_probe(self.now_playing[guild_id]['music_url'], **self.FFMEPEG_OPTIONS)
            self.voice_channel[guild_id].play(source,after=lambda e:self.my_after(text_channel, guild_id))
        else :
            self.is_playing[guild_id] = False
            await self.idle_detect(text_channel, guild_id)
    
    @app_commands.command(name='play', description='Play the selected song from Youtube.')
    async def play(self,interaction: discord.Interaction, search: str = None):
        text_channel = interaction.channel  
        try:         
            voice_channel = interaction.user.voice.channel
        except:
            await interaction.response.send_message("You are not in a voice channel.")
            return
        if interaction.guild_id not in self.guild_list:
            self.init(interaction.guild_id)
        try:
            if self.is_paused[interaction.guild_id] and search == None:
                self.is_paused[interaction.guild_id] = False
                self.is_playing[interaction.guild_id] = True
                self.voice_channel[interaction.guild_id].resume()
                await interaction.response.send_message("Music resumed. ▶️")
                return
            elif search != None:
                if 'playlist' in search:
                    playlist = Playlist(search)
                    for url in playlist:
                        self.music_queue[interaction.guild_id].append(url)
                    await interaction.response.send_message(f"{len(playlist)} songs added to the queue.")
                elif 'RD' and 'list' in search:
                    search = search.split('&list')
                    self.music_queue[interaction.guild_id].append(search[0])
                    await interaction.response.send_message("Song added to the queue.")
                else:
                    self.music_queue[interaction.guild_id].append(search)
                    await interaction.response.send_message('Song added to the queue.')         
            if not self.is_playing[interaction.guild_id] :
                await self.play_music(text_channel, voice_channel, interaction.guild_id)
                
            if self.is_playing[interaction.guild_id] and not self.voice_channel[interaction.guild_id].is_connected():#被強制中斷
                self.is_playing[interaction.guild_id] = False
                self.is_paused[interaction.guild_id] = False
        except:
            pass
    
    @app_commands.command(name='pause', description='Pauses the currently song beign played.')
    async def pause(self,interaction:discord.Interaction):
        if interaction.guild_id not in self.guild_list:
            await interaction.response.send_message("No music playing")
            return
        if self.is_playing[interaction.guild_id]:
            self.voice_channel[interaction.guild_id].pause()
            await interaction.response.send_message("Music paused. ⏸️")
        elif self.is_paused[interaction.guild_id]:
            self.voice_channel[interaction.guild_id].resume()
            await interaction.response.send_message("Music resumed. ▶️")
        self.is_playing[interaction.guild_id] = not self.is_playing[interaction.guild_id]
        self.is_paused[interaction.guild_id] = not self.is_paused[interaction.guild_id]
            
    @app_commands.command(name='resume', description='Resume playing the current song.')
    async def resume(self,interaction:discord.Interaction):
        if interaction.guild_id not in self.guild_list:
            await interaction.response.send_message("No music playing")
            return  
        if self.is_paused[interaction.guild_id]:
            self.is_playing[interaction.guild_id] = True
            self.is_paused[interaction.guild_id] = False
            self.voice_channel[interaction.guild_id].resume()
            await interaction.response.send_message("Music resumed. ▶️")
    
    @app_commands.command(name='skip', description='Skips the currently playing song.')
    async def skip(self,interaction: discord.Interaction):
        if interaction.guild_id not in self.guild_list:
            await interaction.response.send_message("No music playing")
            return        
        self.skiped[interaction.guild_id] = True
        if self.voice_channel[interaction.guild_id] != None and self.voice_channel[interaction.guild_id]:
            self.voice_channel[interaction.guild_id].stop()
            self.music_queue[interaction.guild_id].pop(0)
            await self.now_playing_info_msg[interaction.guild_id].delete()
            await interaction.response.send_message("Music skiped. ⏭️")
            text_channel, voice_channel = interaction.channel, interaction.user.voice.channel
            await self.play_music(text_channel, voice_channel, interaction.guild_id)
            
    @app_commands.command(name='queue', description='Displays all the songs currently in the queue.')
    async def queue(self,interaction: discord.Interaction, page: int=1):
        if not len(self.music_queue[interaction.guild_id]):
            await interaction.followup.send("No music in the queue.") 
        else:
            await interaction.response.defer()
            emb = discord.Embed(title=f'Music queue Total : {len(self.music_queue[interaction.guild_id])}', color=discord.Color.blue())
            for i in range((page-1)*10, min((page)*10, len(self.music_queue[interaction.guild_id]))):
                try:
                    song = self.search_YT(self.music_queue[interaction.guild_id][i])
                    emb.add_field(name=f"({i+1}) " + (' - Looping' if self.is_loop[interaction.guild_id] and i != page*10 else ''), value=f"[{song['title']}]({song['url']})", inline = False)
                except:
                    emb.add_field(name=f"({i+1}) Invalid" + (' - Looping' if self.is_loop[interaction.guild_id] and i != page*10 else ''), value='', inline = False)
            emb.add_field(name=f'Pages: {page}/{len(self.music_queue[interaction.guild_id])//10 + 1}', value='', inline=False)
            await interaction.followup.send(embed=emb)
    
    @app_commands.command(name='shuffle',description='Shuffle the musics queue.')    
    async def shuffle(self, interaction:discord.Interaction):
        temp = self.music_queue[interaction.guild_id][1:]
        random.shuffle(temp)
        self.music_queue[interaction.guild_id][1:] = temp
        await interaction.response.send_message("Music queue shuffled.")
    
    @app_commands.command(name='loop',description='Loop the current playing music.')
    async def loop(self,interaction:discord.Interaction):
        if self.is_loop[interaction.guild_id] == False:
            self.is_loop[interaction.guild_id] = True
            await interaction.response.send_message("Looping.")
        else :
            self.is_loop[interaction.guild_id] = False
            await interaction.response.send_message("Unlooped.")

    @app_commands.command(name='clear',description='Clear the songs in the queue.')
    async def clear(self,interaction:discord.Interaction):
        self.music_queue[interaction.guild_id] = self.music_queue[interaction.guild_id][:1]
        await interaction.response.send_message("Music queue cleared.")
               
    @app_commands.command(name='remove',description='Remove certain music in the queue.')
    async def remove(self, interaction:discord.Interaction, index: int):
        try:
            self.music_queue[interaction.guild_id].pop(index-1)
            await interaction.response.send_message("Music removed.")
        except:
            await interaction.response.send_message("Index out of range.")
    
    @app_commands.command(name='leave',description="Leave voice channel")
    async def leave(self,interaction:discord.Interaction):
        await self.voice_channel[interaction.guild_id].disconnect()
        await interaction.response.send_message("Bye Bye~. 👋")
        self.is_playing[interaction.guild_id]= False
        self.is_paused[interaction.guild_id] = False
        self.music_queue[interaction.guild_id].clear()
        self.voice_channel[interaction.guild_id] = None
  
    @app_commands.command(name="download_music", description='Download song or playlisg from youtube.\n `Notice:` A playlist that\'s too long is not recommend.')
    async def download(self, interaction:discord.Interaction, url: str):
        await interaction.response.defer()
        if 'https' and 'youtube' in url: 
            try:
                with yt_dlp.YoutubeDL(self.YDL_OPTIONS) as ydl:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, ydl.download, url)
                for music in os.listdir('./Youtube'):
                    await interaction.followup.send(file=discord.File(f'./Youtube/{music}'))
                    os.remove(f'./Youtube/{music}')
                await interaction.followup.send("Complete downloading.")
            except:
                await interaction.followup.send('Download failed')
        else :
            await interaction.response.send_message("Please enter a correct URL!")
    
async def setup(bot):
    await bot.add_cog(Music(bot))