import calendar
from io import StringIO

import boto3
import discord
from discord.ext import commands
import os
import numpy as np
import pandas as pd
import datetime
import re
from itertools import *
import functools

intents = discord.Intents.all()
client = commands.Bot(command_prefix=".", intents=intents)

token = os.environ["DISCORD_BOT_TOKEN"]
access_key_id = os.environ["AWS_ACCESS_KEY_ID"]
secret_access_key = os.environ["AWS_SECRET_ACCESS_KEY"]
bucket_name = os.environ["S3_BUCKET_NAME"]
s3client = boto3.client('s3', aws_access_key_id=access_key_id,
                        aws_secret_access_key=secret_access_key)


@client.event
async def on_ready():
    print("THE BOT IS READY")


@client.command()
async def load(ctx, extension):
    client.load_extension(f'cogs.{extension}')


for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')


# fun spam react
@client.event
async def on_raw_reaction_add(payload):
    if payload.member.id == 298972130035499010 and (str(payload.emoji) in '😈'):
        for emoji in ['🥳', '🏆', '😋', '🔥', '💯', '🚀', '😲', '🤯', '😤', '😎', '🏅']:
            await react(await client.get_channel(payload.channel_id).fetch_message(payload.message_id), emoji)


async def react(message, emoji):
    await message.add_reaction(emoji)


client.run(token)
