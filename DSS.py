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


@client.event
async def on_ready():
    print("THE BOT IS READY")


@client.command()
async def load(ctx, extension):
    client.load_extension(f'cogs.{extension}')


for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')

df = pd.read_csv('http://s3.amazonaws.com/minecraftgodsbotbucket/begin-end.csv')
print(df)


client.run(os.getenv("DISCORD_BOT_TOKEN"))