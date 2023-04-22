#!/usr/bin env python3

# External Dependencies
import discord
import os
import logging
import datetime
import asyncio

logger = logging.getLogger('discord')

# Internal functions
import functions.mascot as mascot
import functions.music as music

token = os.environ['token']

class megaBot(discord.Client):
    musicChannel = os.environ['musicChannel']

    async def on_ready(self):
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')

        while True:
            await asyncio.sleep(int(os.environ['globalInterval']))
            mascotPoster = mascot.poster(client)
            await mascotPoster.post()

    async def on_message(self, message):
        if message.author == client.user:
            return
        
        if message.channel.id == int(self.musicChannel):
            logger.debug("Found a message in music channel, calling musicHandler")
            handler = music.musicHandler(message)
            await handler.onMessage()

# Discord.py init
intents = discord.Intents.default()
intents.message_content = True

client = megaBot(intents=intents)
client.run(token)