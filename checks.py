    ##### CHECKS #####
async def check_song_none(self, song):
    try:
        if song is None:
            return True
        else:
            return False
    except:
        return True


async def check_user_in_vc(self, ctx):
    try:
        if ctx.author.voice:
            return True
        else:
            return False
    except:
        return False


async def check_bot_in_vc(self, ctx):
    try:
        if ctx.voice_client:
            return True
        else:
            return False
    except:
        return False


async def check_user_with_bot(self, ctx):
    try:
        if ctx.author.voice.channel is ctx.voice_client.channel:
            return True
        else:
            return False
    except:
        return False


async def check_does_queue_have_songs(self, ctx):
    try:
        if len(self.song_queue[ctx.guild.id]) > 0:
            return True
        else:
            return False
    except:
        return False


async def check_music_playing(self, ctx):
    try:
        if not len(self.song_queue[ctx.guild.id]) == 0:
            return True
        else:
            return False
    except:
        return False