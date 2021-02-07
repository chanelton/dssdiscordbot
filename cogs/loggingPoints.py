import calendar
from io import StringIO

import boto3
import discord
from discord.ext import commands, tasks
import numpy as np
import pandas as pd
import datetime
import re
import asyncio
import os

target_guild_id = 730215239760740353
announcements_channel = 731625608521580624
access_key_id = os.environ["AWS_ACCESS_KEY_ID"]
secret_access_key = os.environ["AWS_SECRET_ACCESS_KEY"]
bucket_name = os.environ["S3_BUCKET_NAME"]
s3client = boto3.client('s3', aws_access_key_id=access_key_id,
                        aws_secret_access_key=secret_access_key)


class Logging(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.cycle.start()

    @commands.Cog.listener()
    async def on_ready(self):
        print('LOGGING READY.')

    @tasks.loop(seconds=60)
    async def cycle(self):
        try:
            active_ids = await self.get_active_ppl()
            if len(active_ids) > 0:
                await self.add_points(active_ids)
        except AttributeError:
            pass

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.channel_id == announcements_channel and (not payload.member.bot):
            await self.add_points({payload.user_id: 0.1})

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            await self.add_points({message.author.id: 0.2})
        # await self.client.process_commands(message)

    @staticmethod
    async def add_points(dictionary):
        points = fromBucket('dssdollars.csv')
        for user_id in dictionary.keys():
            if user_id in list(points['id']):
                curr_points = points[points['id'] == user_id].iloc[0, 1]
                new_val = round(curr_points + dictionary[user_id], 2)
                points.loc[points['id'] == user_id, 'points'] = new_val
            elif user_id not in list(points['id']):
                append = pd.DataFrame([[user_id, dictionary[user_id]]], columns=['id', 'points'])
                points = pd.concat([points, append], ignore_index=True)
        toBucket(points, "dssdollars.csv")

    async def get_active_ppl(self):
        active_ids = {}
        for channel in self.client.get_guild(target_guild_id).voice_channels:
            if not (channel.name == 'Away From Keyboard 😵'):
                if len(list(channel.voice_states.keys())) > 0:
                    # active_ids.append(list(channel.voice_states.keys())[0])
                    temp_dict = await self.calculate_points(channel.voice_states)
                    active_ids.update(temp_dict)
        print(active_ids)
        return active_ids

    @staticmethod
    async def calculate_points(voice_states):
        user_points = {}
        for user_id in voice_states.keys():
            points = 1
            values = voice_states[user_id]
            if values.self_mute:
                points -= 1 / 2
            if values.self_deaf:
                points -= 1 / 2
            if values.self_video:
                points = points * 2
            user_points[user_id] = points
        return user_points


def fromBucket(key):
    obj = s3client.get_object(Bucket=bucket_name, Key=key)
    body = obj['Body']
    csv_string = body.read().decode('utf-8')
    data = pd.read_csv(StringIO(csv_string), index_col=0)
    return data


def toBucket(df, key):
    csv_buffer = StringIO()
    df.to_csv(csv_buffer)
    s3_resource = boto3.resource('s3', aws_access_key_id=access_key_id,
                                 aws_secret_access_key=secret_access_key)
    s3_resource.Object(bucket_name, key).put(Body=csv_buffer.getvalue())


def setup(client):
    client.add_cog(Logging(client))
