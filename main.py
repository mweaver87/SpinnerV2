import logging
import discord

from database.requests import db_initialize
from discord.ext import commands
from music import Player

logging.basicConfig(filename='spinnerV2log.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)s - %(message)s')

intents = discord.Intents.default()
intents.members = True

#Production
#bot = commands.Bot(command_prefix="'", intents=intents)

# Test
bot = commands.Bot(command_prefix="!", intents=intents)

db_initialize()


@bot.event
async def on_ready():
    logging.info(f"{bot.user.name} is ready.")
    print(f"{bot.user.name} is ready.")


async def setup():
    logging.info("Setting up the bot.")
    await bot.wait_until_ready()
    bot.add_cog(Player(bot))

logging.info("Starting Spinner application.")
bot.loop.create_task(setup())

#Production
#bot.run("OTI4MTUxNTc2MDkzMjY1OTUx.YdUmgw.Su8CIMXP-TdCX9Qg8QUYl7oWBqg")

#Test
bot.run("OTI5MTQ4MjgxMDY4NjA5NjE3.YdjGxA.StN-4Io37GHQvSnFTyj2MtL0qKw")


