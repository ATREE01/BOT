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
        self.jumpped = {}
        
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
        self.cnt = 0

    def init_guild(self, guild_id):
        self.guild_list.append(guild_id)
        self.is_playing[guild_id] = False
        self.is_paused[guild_id] = False
        self.is_loop[guild_id] = False
        self.skiped[guild_id] = False
        self.jumpped[guild_id] = False
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
                    info = (await asyncio.to_thread(ydl.extract_info, url=f'ytsearch:{item}', download=False))['entries'][0]
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
            return False
        return song

    def my_after(self, text_channel, guild_id):
        if not self.voice_channel[guild_id].is_connected():
            return
        coro = self.play_next(text_channel, guild_id)
        future = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)

    async def idle_detect(self, text_channel, guild_id):
        await asyncio.sleep(90)
        if self.is_playing[guild_id] == False:
            emb = discord.Embed(title='Idle for too long! Bye Bye~', color=discord.Color.red())
            await text_channel.send(embed = emb)
            await self.voice_channel[guild_id].disconnect()
            self.init_guild(guild_id)

    async def play_next(self, text_channel, guild_id):
        if self.skiped[guild_id] or self.jumpped[guild_id]: # if the song is skipped then there's no need to go through this function
            self.skiped[guild_id], self.jumpped[guild_id]= False, False
            return
        
        if self.is_loop[guild_id]:
            source = await discord.FFmpegOpusAudio.from_probe(self.now_playing[guild_id]['music_url'], **self.FFMEPEG_OPTIONS)
            self.voice_channel[guild_id].play(source,after=lambda e:self.my_after(text_channel, guild_id))
            
        else:
            try:
                await self.now_playing_info_msg[guild_id].delete()#刪除前面的音樂撥放訊息
            except: 
                pass
            
            self.music_queue[guild_id].pop(0)
            if len(self.music_queue[guild_id]) == 0:
                self.is_playing[guild_id] = False
                await self.idle_detect(text_channel, guild_id)
                return
            
            while len(self.music_queue[guild_id]) > 0 :
                self.now_playing[guild_id] = await self.search_YT(self.music_queue[guild_id][0]) # the music is not playable
                if self.now_playing[guild_id] == False:
                    await text_channel.send(f"Can not play this track \"{self.music_queue[guild_id][0]}\" skipping to next track.")
                    self.music_queue[guild_id].pop(0)
                else:
                    break
            else:
                self.is_playing[guild_id] = False
                await self.idle_detect(text_channel, guild_id)
                return
            
            self.now_playing_info_msg[guild_id] = await text_channel.send(embed=self.now_playing_info(guild_id))
            self.is_playing[guild_id] = True
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
        while len(self.music_queue[guild_id]) > 0 :
            self.now_playing[guild_id] = await self.search_YT(self.music_queue[guild_id][0]) # the music is not playable
            if self.now_playing[guild_id] == False:
                await text_channel.send(f"Can not play this track \"{self.music_queue[guild_id][0]}\" skipping to next track.")
                self.music_queue[guild_id].pop(0)
            else:
                break
        else:
            self.is_playing[guild_id] = False
            await self.idle_detect(text_channel, guild_id)
            return    
        
        if self.voice_channel[guild_id] == None or not self.voice_channel[guild_id].is_connected() : # able to play the music
            self.voice_channel[guild_id] = await voice_channel.connect()    

        await self.voice_channel[guild_id].move_to(voice_channel) # move to the voice channel
        self.now_playing_info_msg[guild_id] = await text_channel.send(embed=self.now_playing_info(guild_id))
        self.is_playing[guild_id] = True
        source = await discord.FFmpegOpusAudio.from_probe(self.now_playing[guild_id]['music_url'], **self.FFMEPEG_OPTIONS)
        self.voice_channel[guild_id].play(source,after=lambda e:self.my_after(text_channel, guild_id))
        
    
    @app_commands.command(name='play', description='Play the selected song from Youtube.')
    async def play(self,interaction: discord.Interaction, search: str = None):
        guild_id = interaction.guild_id
        text_channel = interaction.channel  
        try:         
            voice_channel = interaction.user.voice.channel
        except:
            await interaction.response.send_message("You are not in a voice channel.")
            return
        
        if guild_id not in self.guild_list:
            self.init_guild(guild_id)
    
        if search == None: # resume playing
            try:
                if self.is_playing[guild_id] and not self.voice_channel[interaction.guild_id].is_connected():#之前被強制中斷連線
                    self.voice_channel[guild_id] = await voice_channel.connect()  
                    self.is_playing[guild_id] = False
                    await interaction.response.send_message("Reconnected. ▶️")    
                    await self.play_music(text_channel, voice_channel, guild_id)
                if self.is_paused[guild_id]:         
                    self.is_paused[guild_id] = False
                    self.is_playing[guild_id] = True
                    self.voice_channel[guild_id].resume()
                    await interaction.response.send_message("Music resumed. ▶️")    
            except Exception as e:
                await interaction.response.send_message("Something went Wrond!.")
            return
            
        elif search != None: # add new song
            if search.startswith("https://www.youtube.com/playlist?list=") or search.startswith("https://music.youtube.com/playlist?list="): # add playlist
                playlist = Playlist(search)
                self.music_queue[guild_id].extend(playlist)
                await interaction.response.send_message(f"{len(playlist)} songs added to the queue.")
                
            elif search.startswith("https://www.youtube.com/watch?v=") or search.startswith("https://music.youtube.com/watch?v=") and "&list" in search: # a song in playlist
                search = search.split('&list')
                self.music_queue[guild_id].append(search[0])
                await interaction.response.send_message("Song added to the queue.")
                
            else: # single url or keyword
                self.music_queue[guild_id].append(search)
                await interaction.response.send_message('Song added to the queue.')         
                
        if not self.is_playing[guild_id] :
            await self.play_music(text_channel, voice_channel, guild_id)
            return

    @app_commands.command(name="jump", description='Jump to certain song')
    async def jump(self, interaction:discord.Interaction, index:int):
        if interaction.guild_id not in self.guild_list:

            await interaction.response.send_message("No music playing")
            return
        
        if not 0 < index <= len(self.music_queue[interaction.guild_id]):
            await interaction.response.send_message("Please input a valid index")
        else:
            self.jumpped[interaction.guild_id] = True
            self.music_queue[interaction.guild_id] = self.music_queue[interaction.guild_id][index - 1:]
            self.voice_channel[interaction.guild_id].stop()
            await self.now_playing_info_msg[interaction.guild_id].delete()
            await interaction.response.send_message(f"Jumpping to number {index}")
            text_channel, voice_channel = interaction.channel, interaction.user.voice.channel
            await self.play_music(text_channel, voice_channel, interaction.guild_id)
        
    @app_commands.command(name='pause', description='Pauses the currently song beign played.')
    async def pause(self,interaction:discord.Interaction):
        if interaction.guild_id not in self.guild_list or self.is_playing[interaction.guild_id] != True:
            await interaction.response.send_message("No music playing")
            return
        if self.is_playing[interaction.guild_id]:
            self.voice_channel[interaction.guild_id].pause()
            await interaction.response.send_message("Music paused. ⏸️")
        self.is_paused[interaction.guild_id] = True
            
    @app_commands.command(name='resume', description='Resume playing the current song.')
    async def resume(self,interaction:discord.Interaction):
        if interaction.guild_id not in self.guild_list or self.is_paused[interaction.guild_id] != True:
            await interaction.response.send_message("No music paused")
            return  
        if self.is_paused[interaction.guild_id]:
            self.is_playing[interaction.guild_id] = True
            self.is_paused[interaction.guild_id] = False
            self.voice_channel[interaction.guild_id].resume()
            await interaction.response.send_message("Music resumed. ▶️")
    
    @app_commands.command(name='skip', description='Skips the currently playing song.')
    async def skip(self,interaction: discord.Interaction):
        if interaction.guild_id not in self.guild_list or not self.is_playing[interaction.guild_id]:
            await interaction.response.send_message("No music playing")
            return 
        self.skiped[interaction.guild_id] = True
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
            tasks = [self.search_YT(self.music_queue[interaction.guild_id][i]) for i in range((page-1)*10, min((page)*10, len(self.music_queue[interaction.guild_id])))]
            results = await asyncio.gather(*tasks)
            for (index, song) in enumerate(results):
                try:
                    emb.add_field(name=('Looping' if self.is_loop[interaction.guild_id] and index != page*10 else ''), value=f"[{index + 1}. {song['title']}]({song['url']})", inline = False)
                except:
                    emb.add_field(name=(' - Looping' if self.is_loop[interaction.guild_id] and index != page*10 else ''), value=f"({index + 1}) Invalid", inline = False)
            emb.add_field(name=f'Pages: {page}/{len(self.music_queue[interaction.guild_id])//10 + 1}', value='', inline=False)
            await interaction.followup.send(embed=emb)
    
    @app_commands.command(name='shuffle',description='Shuffle the musics queue.')    
    async def shuffle(self, interaction:discord.Interaction):
        self.music_queue[interaction.guild_id][1:] = random.shuffle(self.music_queue[interaction.guild_id][1:])
        await interaction.response.send_message("Music queue shuffled.")
    
    @app_commands.command(name='loop',description='Loop the current playing music.')
    async def loop(self,interaction:discord.Interaction):
        if self.is_loop[interaction.guild_id] == False:
            self.is_loop[interaction.guild_id] = True
            await interaction.response.send_message("Looping currennt playing song.")
        else :
            self.is_loop[interaction.guild_id] = False
            await interaction.response.send_message("Stop looping current playing song.")

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
        self.init(interaction.guild_id)
  
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
    
    @app_commands.command(name="reset_player", description='Reset the bot status')
    async def reset_player(self, interaction:discord.Interaction):
        guild_id = interaction.guild_id
        if self.voice_channel[guild_id].isconnected():
            self.voice.channel[guild_id].disconnected()
        self.init_guild(interaction.guild)
        await interaction.response.send_message("Successful reset bot status")
        
async def setup(bot):
    await bot.add_cog(Music(bot))