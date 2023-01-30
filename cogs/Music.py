import discord 
from discord.ext import commands
from discord import app_commands

from youtube_dl import YoutubeDL
from pytube import Playlist
from pytube import YouTube

import asyncio
from asyncore import loop

import random
import datetime
class Music(commands.Cog, description='Commands for playing music from youtube.'):
    def __init__(self , bot):
        self.bot = bot
    
        self.is_playing = False
        self.is_paused = False
        self.is_loop = False
        
        self.now_playing = None
        
        self.music_queue = []

        self.YDL_OPTIONS = {'format': 'bestaudio',
                            'noplaylist': 'True',
                            'quiet': True,
                            }
        self.FFMEPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        
        self.voice_channel = None
            
    def search_YT(self):
        try:
            with YoutubeDL(self.YDL_OPTIONS) as ydl:
                item = self.music_queue[0]
                if 'https' in item:
                    info = ydl.extract_info(item,download = False)   
                    song = {
                        'title': info['title'],
                        'duration': info['duration'],
                        'channel_name': info['channel'],
                        'channel_url': info['channel_url'],
                        'url': info['webpage_url'],
                        'music_url': info['formats'][0]['url'],
                        'thumbnail': info['thumbnail'],
                    }
                else :
                    info = ydl.extract_info(f'ytsearch:{item}' ,download = False)['entries'][0]
                    song = {
                        'title': info['title'],
                        'duration': info['duration'],
                        'channel_name': info['channel'],
                        'channel_url': info['channel_url'],
                        'url': info['webpage_url'],
                        'music_url': info['formats'][0]['url'],
                        'thumbnail': info['thumbnail'],
                    }
            return song
        except Exception:
            return False

    def my_after(self, text_channel):
        coro = self.play_next(text_channel)
        future = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)

    async def play_next(self, text_channel):
        if self.is_loop == True:
            self.voice_channel.play(discord.FFmpegPCMAudio(self.now_playing['music_url'],**self.FFMEPEG_OPTIONS),after=lambda e:self.my_after(text_channel))
        else:
            self.music_queue.pop(0)
            if len(self.music_queue) == 0:
                self.is_playing = False
                print("it's ended")
                await asyncio.sleep(90)
                emb = discord.Embed(title='Idle for too long!', color=discord.Color.red())
                await self.voice_channel.disconnect()
                await text_channel.send(embed = emb)
                self.is_playing = False
                self.is_paused = False
                self.voice_channel = None
                return
            self.now_playing = self.search_YT()
            self.is_playing = True
            await text_channel.send(embed=(self.now_playing_info()))
            self.voice_channel.play(discord.FFmpegPCMAudio(self.now_playing['music_url'],**self.FFMEPEG_OPTIONS),after=lambda e:self.my_after(text_channel))
            
            
    def now_playing_info(self):
        emb = discord.Embed(title='Now playing: 🎵', color=discord.Color.blue())
        emb.set_thumbnail(url=self.now_playing['thumbnail'])
        emb.add_field(name='Title:', value=f"[{self.now_playing['title']}]({self.now_playing['url']})")
        emb.add_field(name='Channel:', value=f"[{self.now_playing['channel_name']}]({self.now_playing['channel_url']})")
        emb.add_field(name='Duration:', value=datetime.timedelta(seconds = self.now_playing['duration']))
        return emb
        
    async def play_music(self,text_channel, voice_channel):
        if len(self.music_queue) > 0 :
            self.now_playing = self.search_YT()
            if self.now_playing == False:
                await text_channel.send("Can not play this track skipping to next track.")
                self.music_queue.pop(0)
                await self.play_music(text_channel, voice_channel)
                return
            elif self.voice_channel == None or not self.voice_channel.is_connected():
                self.voice_channel = await voice_channel.connect()
                if self.voice_channel == None:
                    await text_channel.send("Could not connect to voice channel.")
            await self.voice_channel.move_to(voice_channel)
            await text_channel.send(embed=self.now_playing_info())
            self.is_playing = True
            self.voice_channel.play(discord.FFmpegPCMAudio(self.now_playing['music_url'],**self.FFMEPEG_OPTIONS),after=lambda e:self.my_after(text_channel))
        else :
            self.is_playing = False
    
    @app_commands.command(name='play', description='Play the selected song from Youtube.')
    async def play(self,interaction:discord.Interaction, search: str = None):
        text_channel = interaction.channel           
        voice_channel = interaction.user.voice.channel                   
        try:
            if self.is_paused and search == None:
                self.is_paused = False
                self.is_playing = True
                self.voice_channel.resume()
                await interaction.response.send_message("Music resumed. ▶️")
            elif search != None:
                if 'playlist' in search:
                    playlist = Playlist(search)
                    for url in playlist:
                        self.music_queue.append(url)
                    await interaction.response.send_message(f"{len(playlist)} songs added to the queue.")
                elif 'RD' and 'list' in search:
                    search = search.split('&list')
                    self.music_queue.append(search[0])
                    await interaction.response.send_message("Song added to the queue.")
                else:
                    self.music_queue.append(search)
                    await interaction.response.send_message('Song added to the queue.')    
            if self.is_playing and not self.voice_channel.is_connected():
                self.is_playing = False
                self.is_paused = False
            if not self.is_playing :
                await self.play_music(text_channel, voice_channel)
        except:
            await interaction.response.send_message("You are not in a voice channel!")
    
    @app_commands.command(name='pause', description='Pauses the currently song beign played.')
    async def pause(self,interaction:discord.Interaction):
        if self.is_playing:
            self.is_playing = False
            self.is_paused = True
            self.voice_channel.pause()
            await interaction.response.send_message("Music paused. ⏸️")
        elif self.is_paused:
            self.voice_channel.resume()
            await interaction.response.send_message("Music resumed. ▶️")
            
    @app_commands.command(name='resume', description='Resume playing the current song.')
    async def resume(self,interaction:discord.Interaction):
        if self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.voice_channel.resume()
            await interaction.response.send_message("Music resumed. ▶️")
    
    @app_commands.command(name='skip', description='Skips the currently playing song.')
    async def skip(self,interaction: discord.Interaction):
        if self.voice_channel != None and self.voice_channel:
            self.voice_channel.stop()
            self.music_queue.pop(0)
            await interaction.response.send_message("Music skiped. ⏭️")
            text_channel = interaction.channel
            voice_channel = interaction.user.voice.channel
            await self.play_music(text_channel, voice_channel)
            
    @app_commands.command(name='queue', description='Displays all the songs currently in the queue.')
    async def queue(self,interaction: discord.Interaction, page: int=1):
        await interaction.response.defer()
        if not len(self.music_queue):
            await interaction.followup.send("No music in the queue.") 
        else:
            emb = discord.Embed(title=f'Music queue Total : {len(self.music_queue)}', color=discord.Color.blue())
            for i in range((page-1)*10, min((page)*10, len(self.music_queue))):
                song = YouTube(self.music_queue[i])
                emb.add_field(name=f"({i+1}) {song.title}" + (' - Looping' if self.is_loop and i != page*10 else ''), value='', inline = False)
            emb.add_field(name=f'Pages: {page}/{len(self.music_queue)//10 + 1}', value='', inline=False)
            await interaction.followup.send(embed=emb)
    
    @app_commands.command(name='shuffle',description='Shuffle the musics queue.')    
    async def shuffle(self, interaction:discord.Interaction):
        temp = self.music_queue[1:]
        random.shuffle(temp)
        self.music_queue[1:] = temp
        await interaction.response.send_message("Music queue shuffled.")
    
    @app_commands.command(name='loop',description='Loop the current playing music.')
    async def loop(self,interaction:discord.Interaction):
        if self.is_loop == False:
            self.is_loop = True
            await interaction.response.send_message("Looping.")
        else :
            self.is_loop = False
            await interaction.response.send_message("Unlooped.")

    @app_commands.command(name='clear',description='Clear the songs in the queue.')
    async def clear(self,interaction:discord.Interaction):
        self.music_queue = []
        await interaction.response.send_message("Music queue cleared.")
               
    @app_commands.command(name='remove',description='Remove certain music in the queue.')
    async def remove(self, interaction:discord.Interaction, index: int):
        try:
            self.music_queue.pop(index-1)
            await interaction.response.send_message("Music removed.")
        except:
            await interaction.response.send_message("Index out of range.")
    
    @app_commands.command(name='leave',description="Leave voice channel")
    async def leave(self,interaction:discord.Interaction):
        await self.voice_channel.disconnect()
        await interaction.response.send_message("Bye Bye~. 👋")
        self.is_playing = False
        self.is_paused = False
        self.music_queue.clear()
        self.voice_channel = None
  

async def setup(bot):
    await bot.add_cog(Music(bot))