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

target_guild_id = 781033657594675224


class Logging(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.DSSGuild = self.client.get_guild(781033657594675224)
        self.cycle.start()

    @commands.Cog.listener()
    async def on_ready(self):
        print('LOGGING READY.')

    @tasks.loop(seconds=3)  # set to 50
    async def cycle(self):
        try:
            active_ids = await self.get_active_ppl()
            # get points from database and add value
            # print(active_ids)
        except AttributeError:
            pass

    async def get_active_ppl(self):
        active_ids = {}
        for channel in self.client.get_guild(target_guild_id).voice_channels:
            if len(list(channel.voice_states.keys())) > 0:
                # active_ids.append(list(channel.voice_states.keys())[0])
                temp_dict = await self.calculate_points(channel.voice_states)
                active_ids = temp_dict | active_ids
        return active_ids

    @staticmethod
    async def calculate_points(voice_states):
        user_points = {}
        for user_id in voice_states.keys():
            points = 0.5
            values = voice_states[user_id]
            if values.self_mute:
                points -= 0.5 / 2
            if values.self_deaf:
                points -= 0.5 / 2
            if values.self_video:
                points = points * 2
            user_points[user_id] = points
        return user_points


def setup(client):
    client.add_cog(Logging(client))
