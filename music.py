import discord
import youtube_dl
import pafy
import asyncio
import logging
import datetime
import random

from database.requests import fetch_objects_server, fetch_objects_user, fetch_objects_user_song, fetch_user_liked, update_likes, update_played, create_object
from checks import check_bot_in_vc, check_does_queue_have_songs, check_music_playing, check_song_none, check_user_in_vc, check_user_with_bot

from discord.ext import commands


class Player(commands.Cog):

    ##### INITIALIZATION #####
    def __init__(self, bot):
        self.bot = bot
        self.song_queue = {}
        self.paused = {}
        self.skipped = {}
        self.setup()


    def setup(self):
        counter = 0
        for guild in self.bot.guilds:
            counter += 1
            self.song_queue[guild.id] = []
            self.paused[guild.id] = False
            self.skipped[guild.id] = False
        print(f"Spinner is in {counter} servers.")        


    ##### FUNCTIONS #####
    async def connect(self, ctx, play):
        """
            This will connect the bot to the channel.
        """

        await ctx.author.voice.channel.connect()
        embed = discord.Embed(title="Spinner[BOT] - Hey!", description="Connected...", colour=discord.Colour.green())
        embed.set_footer(text="Press 'help for help with commands.")
        await ctx.send(embed=embed)
        self.song_queue[ctx.guild.id] = []
        self.paused[ctx.guild.id] = False

        if not play:
            return await self.check_queue(ctx)


    async def disconnect(self, ctx):
        """
            This will disconnect the bot from the channel.
        """
        # NEED CHECKS

        if await self.check_bot_in_vc(ctx):
            await ctx.send("Left voice channel.")
            self.paused[ctx.guild.id] = False
            embed = discord.Embed(title="Spinner[BOT] - See ya!", description="Disconnected...", colour=discord.Colour.red())
            embed.set_footer(text="Thank you for using me!")
            await ctx.send(embed=embed)
            return await ctx.voice_client.disconnect()
        
        await ctx.send("I am not connected to a voice channel.")


    async def queue_song(self, ctx, song, info):
        """
            This will queue the song request after it found it. 
            It calls "search_songs" to request it. 
        """
        # NEED CHECKS
        counter = 0
        for search_result in song:
            queue_len = len(self.song_queue[ctx.guild.id])

            if queue_len < 10:
                song_info = {}
                song_info = info[counter]
   
                artist = song_info["artist"]
                track = song_info["track"]
                duration = song_info["duration"]

                embed = discord.Embed(title="Song queued!", description=f"Artist: {artist}\nTrack: {track}\nDuration: {duration}", colour=discord.Colour.teal())
                embed.set_footer(text=f"Added to the queue at position {queue_len}")
                await ctx.send(embed=embed)

                self.song_queue[ctx.guild.id].append(search_result)
                await asyncio.sleep(3)
            else:
                return await ctx.send("Queue full with 10 songs.")
            counter += 1


    async def save_play(self, ctx, song, ):
        server = ctx.guild.id
        user = ctx.author.name
        url = song
        last = str(datetime.datetime.now())

        fetched = await fetch_objects_user_song(server, user, url)

        try:
            liked = int(fetched[0]['liked'])
            count = int(fetched[0]['play_count']) + 1
        except:
            liked = False
            count = 1

        if fetched == "NA" or not fetched or fetched == None:
            await create_object(server, user, url, liked, count, last)
        else:
            await update_played(server, user, url, liked, count, last)

        db_value = await fetch_objects_server(server)


    async def search_songs(self, amount, song, get_url=False):
        """
            This looks for the song and returns it.
        """

        # YT Search
        info = await self.bot.loop.run_in_executor(None, lambda: youtube_dl.YoutubeDL({"format" : "bestaudio", "quiet": True}).extract_info(f"ytsearch{amount}:{song}", 
        download=False, ie_key="YoutubeSearch"))

        if len(info["entries"]) == 0:
            return None
        
        return [entry["webpage_url"] for entry in info["entries"]] if get_url else info



    async def check_queue(self, ctx):
        """
            This is the first part of the engine. It checks to see if there is anything in the queue. Times out after 2 minutes and disconnects.
        """    
        # NEED CHECKS

        counter = 0
        while counter < 300:
            await asyncio.sleep(1)
            counter += 1
            if await self.check_music_playing(ctx):
                return await self.play_song(ctx)

            if not await self.check_bot_in_vc(ctx):
                return logging.info("Disconnected.")

        return await self.disconnect(ctx)


    async def play_song(self, ctx):
        # NEED CHECKS
        song = self.song_queue[ctx.guild.id][0]
        await self.save_play(ctx, song)
        url = pafy.new(song).getbestaudio().url
        ctx.voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(executable="C:/ffmpeg/ffmpeg.exe", source=url)), after=lambda error: self.bot.loop.create_task(self.done_song(ctx)))
        ctx.voice_client.source.volume = 0.5
        await ctx.send(song)
        await self.play_embed(ctx, song)


    async def play_embed(self, ctx, song):

        song_info = {}
        song_info = await self.get_song_info(song)
        artist = song_info["artist"]
        track = song_info["track"]
        duration = song_info["duration"]   
        seconds = song_info['seconds']   

        poll = discord.Embed(title="Spinner[BOT] - Playing!", description=f"Artist: {artist}\nTrack: {track}\nDuration: {duration}", colour=discord.Colour.purple())
        poll.add_field(name="Love it!", value=":white_check_mark:")
        poll.add_field(name="No way!", value=":no_entry_sign:")
        poll.set_footer(text="You can vote while the song is playing.")

        poll_msg = await ctx.send(embed=poll)
        poll_id = poll_msg.id

        await poll_msg.add_reaction(u"\u2705") #yes
        await poll_msg.add_reaction(u"\U0001F6AB") #no

        poll_msg = await ctx.channel.fetch_message(poll_id)
        await asyncio.sleep(seconds)

        await self.save_reactions(ctx, poll_msg, song)



    async def save_reactions(self, ctx, reaction, url):
        server = ctx.guild.id
        user_save = ""
        url = url
        liked = False

        reacted = []
        for reaction in reaction.reactions:
            if reaction.emoji in u"\u2705":
                async for user in reaction.users():
                    if user.name not in reacted and not user.bot:
                        user_save = user.name
                        reacted.append(user.id)
                        liked = True
                        fetched = await fetch_objects_user_song(server, user_save, url)
                        if fetched == "NA" or not fetched or fetched == None:
                            await create_object(server, user_save, url, liked, 0, "0")
                        else:
                            await update_likes(server, user_save, url, liked)
            elif reaction.emoji in u"\U0001F6AB":
                async for user in reaction.users():
                    if user.name not in reacted and not user.bot:
                        user_save = user.name
                        reacted.append(user.id)
                        fetched = await fetch_objects_user_song(server, user_save, url)
                        if fetched == "NA" or not fetched or fetched == None:
                            await create_object(server, user_save, url, liked, 0, "0")
                        else:
                            await update_likes(server, user_save, url, liked)


    async def done_song(self, ctx):
        # NEED CHECKS

        self.song_queue[ctx.guild.id].pop(0)
        self.paused[ctx.guild.id] = False
        return await self.check_queue(ctx)


    async def pause(self, ctx):
        """
            Pause feature
        """
        # NEED CHECKS

        counter = 0
        self.paused[ctx.guild.id] = True
        ctx.voice_client.pause()
        await ctx.send("Spinner[BOT] - Pausing...")
        while counter < 600:
            await asyncio.sleep(1)
            counter += 1
            if self.paused[ctx.guild.id] is False:
                return logging.info("Resumed")  

            if not await self.check_bot_in_vc(ctx):
                return logging.info("Disconnected, unpaused.")

        return await self.disconnect(ctx)


    async def resume(self, ctx):
        """
            Resume feature
        """
        # NEED CHECKS

        self.paused[ctx.guild.id] = False
        ctx.voice_client.resume()
        await ctx.send("Spinner[BOT] - Resuming...")


    async def skip_song(self, ctx):
        ctx.voice_client.pause()
        await self.done_song(ctx)


    async def search(self, ctx, song):
        await ctx.send("Searching for the song. ")
        info = await self.search_songs(5, song)
        embed = discord.Embed(title=f"Results for '{song}':", description="*You can use these URL's to play an exact song if the one you want isn't there.\n", colour=discord.Colour.red())
        amount = 0
        for entry in info["entries"]:
            embed.description += f"[{entry['title']}]({entry['webpage_url']})\n"
            amount += 1
        embed.set_footer(text=f"Displaying the first {amount} results.")
        await ctx.send(embed=embed)


    async def list_songs(self, ctx):
        embed = discord.Embed(title="Song Queue", description="", colour=discord.Colour.dark_gold())
        i = 1
        for url in self.song_queue[ctx.guild.id]:
            if i > 1:
                embed.description += f"{i-1}) {url}\n"
            i += 1

        embed.set_footer(text="Thanks for using me!")
        await ctx.send(embed=embed)


    async def get_song_info(self, song):
        song_info = {}
        artist_temp = "NA"
        track_temp = "NA"
        duration_temp = "NA"
        dur_seconds = "NA"

        video = youtube_dl.YoutubeDL({}).extract_info(song, download=False)

        try:
            artist_temp = video['artist']
        except:
            logging.info("No artist for the song.")
        try:
            track_temp = video['track']
        except:
            logging.info("No track for the song.")
        try:
            dur_seconds = video['duration']
            seconds = video['duration']
            minutes = int(seconds/60)
            seconds = seconds - (minutes * 60)
            if seconds < 10:
                seconds = "0" + str(seconds)
            duration = str(minutes) + ":" + str(seconds)
            if minutes > 59:
                hours = int(minutes/60)
                minutes = minutes - (hours * 60)
                if minutes < 10:
                    minutes = "0" + str(minutes)
                    duration = str(hours) + ":" +str(minutes) + ":" + str(seconds)
            duration_temp = duration
        except:
            logging.info("Could not create a duration.")

        song_info["artist"] = artist_temp
        song_info["track"] = track_temp
        song_info["duration"] = duration_temp
        song_info["seconds"] = dur_seconds
        return song_info


    async def verify_track(self, ctx, song, artists):
        songs_info = []
        number = 1
        if artists:
            number = 5
            await ctx.send("Creating artist playlist...")
        else:
            await ctx.send("Searching for the song...")
        if not ("youtube.com/watch?" in song or "https://youtu.be/" in song or "https://open.spotify.com" in song):
            song += " song"
            counter = number + 1
            songs = []
            while len(songs) < number:
                songs = []
                songs_info = []
                result = await self.search_songs(counter, song, get_url=True)
                if result is None:
                    return await ctx.send("Could not find this song.")
                
                count_queued = 0
                for one in result:
                    song_info = {}
                    song_info = await self.get_song_info(one)
                    try:
                        seconds = song_info["seconds"]
                    except:
                        logging.warn("Cannot save seconds")
                    try:
                        artist = song_info["artist"]
                    except:
                        logging.warn("Cannot save artist")
                    try:
                        track = song_info["track"]
                    except:
                        logging.warn("Cannot save track")
                    try:
                        duration = song_info["duration"]
                    except:
                        logging.warn("Cannot save duration")
                    
                    if artist != "NA" and track != "NA" and duration != "NA" and  seconds < 1200:
                        match = False
                        
                        for inf in songs_info:
                            if inf["track"] == song_info["track"]:
                                match = True
                        if not match:
                            count_queued += 1
                            songs.append(one)
                            songs_info.append(song_info)
                        if count_queued == number:
                            return await self.queue_song(ctx, songs, songs_info)

                if len(result) < counter:
                    break
                counter += 5
            return await self.queue_song(ctx, songs, songs_info)
        else:
            songs_info = []
            songs = [song]
            song_info = {}
            song_info = await self.get_song_info(song)
            
            songs_info.append(song_info)          
            return await self.queue_song(ctx, songs, songs_info)

    async def suggest(self, ctx, playlist, randomize):
        song_number = 1
        if playlist:
            song_number = 5

        server = ctx.guild.id
        user = ctx.author.name
        shortlist = []
        info = []
        
        query = await fetch_user_liked(server)

        if randomize == True:
            for entity in query:
                if entity[3]:
                    match = False
                    for list in shortlist:
                        if list == entity[2]:
                            match = True
                    if not match:    
                        shortlist.append(entity[2])
        else:
            for entity in query:
                if entity[1] == user:
                    if entity[3]:
                        shortlist.append(entity[2])
        random.shuffle(shortlist)
        liked = len(shortlist)

        if randomize:
            if liked < 1:
                return await ctx.send("The server doesn't have any liked songs...")
            elif liked < 5:
                return await ctx.send("The server doesn't have enough liked songs...")
        else:
            if liked < 1:
                return await ctx.send("You haven't liked any songs...")
            elif liked < 5:
                return await ctx.send("You don't have enough liked songs to make a playlist (5 minimum)...")
        
        while len(shortlist) > song_number:
            pop = random.randint(0, len(shortlist) -1)
            shortlist.pop(pop)

        for one in shortlist:
            song_info = await self.get_song_info(one)
            info.append(song_info)

        return await self.queue_song(ctx, shortlist, info)        


    async def stats(self, ctx):
        server = ctx.guild.id
        user = ctx.author.name
        songs_played = 0
        unique_played = 0
        songs_liked = 0
        points = 0
        
        query = await fetch_objects_user(server, user)
        top_song = ""
        top_points = 0
        
        if query != "NA":
            for entity in query:
                song_points = 0
                if entity[4] > 0:
                    songs_played += entity[4]
                    unique_played += 1
                    song_points += 3 + (entity[4] * 1)
                if entity[3]:
                    songs_liked += 1
                    song_points += 5 
                points += song_points
                if song_points > top_points:
                    top_song = entity[2]
                    top_points = song_points

        top_song = await self.get_song_info(top_song)
                
        embed = discord.Embed(title="Spinner[BOT] - Stats!!!", description=f"--{user} stats--\nUnique Songs: {unique_played}\nTotal Plays: {songs_played}\nSongs Liked: {songs_liked}\n\nTop song:\n{top_song['track']}\nby {top_song['artist']}", colour=discord.Colour.dark_gold())
        embed.set_footer(text=f"Spinner[BOT] points: {points}")
        await ctx.send(embed=embed)


    ##### COMMANDS #####
    @commands.command(name="join")
    async def join_command(self, ctx):

        if not await check_user_in_vc(ctx):
            return await ctx.send("Must be in voice channel to play music.")

        if await check_user_with_bot(ctx):
            return await ctx.send("The user is already with the bot.")

        if await check_bot_in_vc(ctx):
            await ctx.voice_client.disconnect()

        await self.connect(ctx, False)

    
    @commands.command(name="leave")
    async def leave_command(self, ctx):

        if not await check_bot_in_vc(ctx):
            return await ctx.send("Spinner is already disconnected.")

        await self.disconnect(ctx)


    @commands.command(name="play")
    async def play_command(self, ctx, *, song=None):
        prev_connected = True

        if not await check_user_in_vc(ctx):
            return await ctx.send("Must be in VC to play music.")

        if not await check_bot_in_vc(ctx):
            await self.connect(ctx, True)
            prev_connected = False

        if not await check_user_with_bot(ctx):
            return await ctx.send("Must be in the same VC as bot to play music.")

        if song is None:
            await ctx.send("Pick a song to play")
            if not prev_connected:
                await self.check_queue(ctx)
            return 

        await self.verify_track(ctx, song, False)

        if not prev_connected:
            await self.check_queue(ctx)


    @commands.command(name="pause")
    async def pause_command(self, ctx):
        if not await check_user_in_vc(ctx):
            return await ctx.send("Must be in VC to pause music.")

        if not await check_bot_in_vc(ctx):
            return await ctx.send("Bot is not connected.")

        if not await check_user_with_bot(ctx):
            return await ctx.send("Must be in the same VC as bot to pause music.")

        if not await check_music_playing(ctx):
            return await ctx.send("Music isn't playing.")

        if self.paused[ctx.guild.id]:
            return await ctx.send("Music is already paused.")

        await self.pause(ctx)


    @commands.command(name="resume")
    async def resume_command(self, ctx):
        if not await check_user_in_vc(ctx):
            return await ctx.send("Must be in VC to resume music.")

        if not await check_bot_in_vc(ctx):
            return await ctx.send("Bot is not connected.")

        if not await check_user_with_bot(ctx):
            return await ctx.send("Must be in the same VC as bot to resume music.")

        if not await check_music_playing(ctx):
            return await ctx.send("Music isn't playing.")

        if not self.paused[ctx.guild.id]:
            return await ctx.send("Music isn't paused.")

        await self.resume(ctx)


    @commands.command(name="skip")
    async def skip_command(self, ctx):

        if not await check_bot_in_vc(ctx):
            return await ctx.send("Spinner[BOT] - I am not in any voice channels.")

        if not await check_user_in_vc(ctx):
            return await ctx.send("Spinner[BOT] - You must be in the channel to play music.")

        if not await check_user_with_bot(ctx):
            return await ctx.send("Spinner[BOT] - You need to be in the same channel to skip.")    

        if not await check_does_queue_have_songs(ctx):
            return await ctx.send("Spinner[BOT] - No song to skip.")  

        await self.skip_song(ctx)


    @commands.command(name="search")
    async def search_command(self, ctx, *, song=None):

        if await check_user_in_vc(ctx):
            return await ctx.send("Spinner[BOT] - urser is not in any voice channels.")

        if await check_bot_in_vc(ctx):
            return await ctx.send("Spinner[BOT] - I am not in any voice channels.")

        if not await check_user_with_bot(ctx):
            return await ctx.send("Spinner[BOT] - We are in different voice channels")

        if check_song_none(song):
            return await ctx.send("Include a term to search for.")

        await self.search(ctx, song)


    @commands.command(name="list")
    async def list_command(self, ctx):

        if not await check_user_in_vc(ctx):
            return await ctx.send("Spinner[BOT] - urser is not in any voice channels.")

        if not await check_bot_in_vc(ctx):
            return await ctx.send("Spinner[BOT] - I am not in any voice channels.")

        if not await check_user_with_bot(ctx):
            return await ctx.send("Spinner[BOT] - We are in different voice channels")

        if not len(self.song_queue[ctx.guild.id]) > 1:
            return await ctx.send("Spinner[BOT] - No song in queue.")  

        await self.list_songs(self.ctx)


    @commands.command(name="artist")
    async def artist_command(self, ctx, *, song=None):
        prev_connected = True
        if not await check_user_in_vc(ctx):
            return await ctx.send("Must be in VC to play music.")

        if not await check_bot_in_vc(ctx):
            await self.connect(ctx, True)
            prev_connected = False

        if not await check_user_with_bot(ctx):
            return await ctx.send("Must be in the same VC as bot to play music.")

        if await check_song_none(song):
            return await ctx.send("Include an artist to search for.")

        if ("youtube.com/watch?" in song or "https://youtu.be/" in song):
            return await ctx.send("Enter an artist name to search for.")

        song += " artist"

        await self.verify_track(ctx, song, True)

        if not prev_connected:
            await self.check_queue(ctx)
        

    @commands.command(name="suggest")
    async def suggest_command(self, ctx):
        prev_connected = True
        if not await  check_user_in_vc(ctx):
            return await ctx.send("Must be in VC to play music.")

        if not await check_bot_in_vc(ctx):
            await self.connect(ctx, True)
            prev_connected = False

        if not await check_user_with_bot(ctx):
            return await ctx.send("Must be in the same VC as bot to play music.")

        await self.suggest(ctx, True, True)

        if not prev_connected:
            await self.check_queue(ctx)


    @commands.command(name="playlist")
    async def playlist_command(self, ctx):
        prev_connected = True
        if not await  check_user_in_vc(ctx):
            return await ctx.send("Must be in VC to play music.")

        if not await check_bot_in_vc(ctx):
            await self.connect(ctx, True)
            prev_connected = False

        if not await check_user_with_bot(ctx):
            return await ctx.send("Must be in the same VC as bot to play music.")

        await self.suggest(ctx, True, True)

        if not prev_connected:
            await self.check_queue(ctx)


    @commands.command(name="random")
    async def random_command(self, ctx):
        prev_connected = True
        if not await  check_user_in_vc(ctx):
            return await ctx.send("Must be in VC to play music.")

        if not await check_bot_in_vc(ctx):
            await self.connect(ctx, True)
            prev_connected = False

        if not await check_user_with_bot(ctx):
            return await ctx.send("Must be in the same VC as bot to play music.")

        await self.suggest(ctx, True, True)

        if not prev_connected:
            await self.check_queue(ctx)


    @commands.command(name="mixedbag")
    async def mixedbag_command(self, ctx):
        prev_connected = True
        if not await  check_user_in_vc(ctx):
            return await ctx.send("Must be in VC to play music.")

        if not await check_bot_in_vc(ctx):
            await self.connect(ctx, True)
            prev_connected = False

        if not await check_user_with_bot(ctx):
            return await ctx.send("Must be in the same VC as bot to play music.")

        await self.suggest(ctx, True, True)

        if not prev_connected:
            await self.check_queue(ctx)


    @commands.command(name="stats")
    async def stats_command(self, ctx):
        await self.stats(ctx)

