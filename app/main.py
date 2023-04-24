#!/usr/bin env python3

# External Dependencies
import discord
import os
import logging
import datetime
import asyncio

from discord.ext import commands, tasks

logger = logging.getLogger('discord')

# Internal functions
import functions.mascot as mascot
import functions.music as music

token = os.environ['token']
utc = datetime.timezone.utc
time = datetime.time(hour=20, minute=00, tzinfo=utc)

class megaBot(discord.Client):
    musicChannel = os.environ['musicChannel']

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
    async def post_mascot(self):
        mascotPoster = mascot.poster(client)
        await mascotPoster.post()

# Discord.py init
intents = discord.Intents.default()
intents.message_content = True

client = megaBot(intents=intents)
client.run(token)
