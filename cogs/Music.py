import discord 
from discord.ext import commands
from discord import app_commands

from youtube_dl import YoutubeDL

class Music(commands.Cog, description='Commands for playing music from youtube.'):
    def __init__(self, bot):
        self.bot = bot
    
        self.is_playing = False
        self.is_paused = False
        
        self.music_queue = []
        self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
        self.FFMEPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        
        self.voice_channel = None
        
    def search_YT(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            print(item)
            try:
                info = ydl.extract_info(f'ytsearch:{item}',download = False)['entries'][0]
            except Exception:
                return False
        return {'title': info['title'],'source': info['formats'][0]['url']}

    def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True
            music_url = self.music_queue[0][0]['source']
            self.music_queue.pop(0)
            self.voice_channel.play(discord.FFmpegPCMAudio(music_url,**self.FFMEPEG_OPTIONS),after=lambda e:self.play_next())
        else:
            self.is_playing = False
            
    async def play_music(self,interaction: discord.Interaction):
        if len(self.music_queue) > 0 :
            self.is_playing = True
            music_url = self.music_queue[0][0]['source']
            if self.voice_channel == None or not self.voice_channel.is_connected():
                self.voice_channel = await self.music_queue[0][1].connect()
                if self.voice_channel == None:
                    await interaction.response.send_message("Could not connect to voice channel.")
                    return
            else :
                await self.voice_channel.move_to(self.music_queue[0][1])
            
            self.music_queue.pop(0)
            self.voice_channel.play(discord.FFmpegPCMAudio(music_url,**self.FFMEPEG_OPTIONS),after=lambda e:self.play_next())
                
        else :
            self.is_playing = False
            
    @app_commands.command(name='play', description='Play the selected song from Youtube.')
    async def play(self,interaction:discord.Interaction, arg: str):
        query = ' '.join(arg)
        try:
            voice_channel = interaction.user.voice.channel
            if self.is_paused and arg == None:
                self.voice_channel.resume()
            else:
                song = self.search_YT(query)
                if type(song) == type(True):
                    await interaction.response.send_message("Could not play the song. Try a another keyword.")
                else :
                    await interaction.response.send_message("Song Added to the queue")
                    self.music_queue.append([song,voice_channel])
                    if self.is_playing == False and len(self.music_queue) == 1:
                        await self.play_music(interaction)
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
            await self.play_music(interaction)
            await interaction.response.send_message("Music skiped. ⏭️")
    @app_commands.command(name='queue', description='Displays all the songs currently in the queue.')
    async def queue(self,interaction: discord.Interaction):
        res = ''
        for index, song in enumerate(self.music_queue):
            if index >= 10 :
                break
            res += self.music_queue[index][0]['title']+'\n'
        if res != '':
            await interaction.response.send_message(res)
        else :
            await interaction.response.send_message("No music in the queue.") 

    @app_commands.command(name='clear',description='Clear the songs in the queue.')
    async def clear(self,interaction:discord.Interaction):
        if self.voice_channel != None and self.is_playing:
            self.voice_channel.stop()
        self.music_queue = []
        await interaction.response.send_message("Music queue cleared.")
               
    @app_commands.command(name='leave',description="Leave voice channel")
    async def leave(self,interaction:discord.Interaction):
        self.is_playing = False
        self.is_paused = False
        await self.voice_channel.disconnect()
        await interaction.response.send_message("Bye Bye~. 👋")
             
async def setup(bot):
    await bot.add_cog(Music(bot))