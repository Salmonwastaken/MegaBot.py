#!/usr/bin env python3

# External Dependencies
import discord
import os
import logging
import datetime
import asyncio

from discord.ext import commands, tasks

# Internal functions
import functions.music as music
import functions.mascot as mascot


postHour = int(os.environ['postHour'])

logger = int(logging.getLogger('discord'))

utc = datetime.timezone.utc
time = datetime.time(hour=postHour, minute=30, tzinfo=utc)

token = os.environ['token']

class megaBot(discord.Client):
    musicChannel = os.environ['musicChannel']

    async def setup_hook(self):
        post_mascot.start(client)

    async def on_ready(self):
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')

    async def on_message(self, message):
        if message.author == client.user:
            return
        
        if message.channel.id == int(self.musicChannel):
            logger.debug("Found a message in music channel, calling musicHandler")
            handler = music.musicHandler(message)
            await handler.onMessage()

@tasks.loop(time=time)
async def post_mascot(client):
    logger.debug("Posting mascot")
    mascotPoster = mascot.poster(client)
    await mascotPoster.post()

intents = discord.Intents.default()
intents.message_content = True
client = megaBot(intents=intents)
client.run(token)
