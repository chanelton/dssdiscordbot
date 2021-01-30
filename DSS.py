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


def fromBucket(key):
    obj = s3client.get_object(Bucket=bucket_name, Key=key)
    body = obj['Body']
    csv_string = body.read().decode('utf-8')
    data = pd.read_csv(StringIO(csv_string), index_col=0)
    return data


client.run(token)
