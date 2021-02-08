import os
from io import StringIO

import boto3
import pandas as pd
from discord.ext import commands, tasks

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
            # get all active_ids and how many points they earned
            active_ids = await self.get_active_ppl()
            # only run if at least 1 person online
            if len(active_ids) > 0:
                # add points to csv
                await self.add_points(active_ids)
        except AttributeError:
            pass

    # listener event
    # everytime someone reacts to message in exec, earns 0.1 points
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # reacting in announcements channel and not bot
        if payload.channel_id == announcements_channel and (not payload.member.bot):
            # execute add
            await self.add_points({payload.user_id: 0.1})

    # listener event
    # everytime someone sends message, earns 0.2 points
    @commands.Cog.listener()
    async def on_message(self, message):
        # bots dont get points
        if not message.author.bot:
            # execute add
            await self.add_points({message.author.id: 0.2})

    # adding points message
    # straight to csv to bucket, no output
    @staticmethod
    async def add_points(dictionary): # takes dictionary of user_id:points
        # get csv file from bucket
        points = fromBucket('dssdollars.csv')
        # iterate thru dictionary
        for user_id in dictionary.keys():
            # if user already has points
            if user_id in list(points['id']):
                # get old points, add points, set val in csv
                curr_points = points[points['id'] == user_id].iloc[0, 1]
                new_val = round(curr_points + dictionary[user_id], 2)
                points.loc[points['id'] == user_id, 'points'] = new_val
            # if user doesn't have any points yet
            elif user_id not in list(points['id']):
                # make new dataframe with 1 row
                # user_id / points just earned
                append = pd.DataFrame([[user_id, dictionary[user_id]]], columns=['id', 'points'])
                points = pd.concat([points, append], ignore_index=True)
        # export to bucket
        toBucket(points, "dssdollars.csv")

    # gets all active ppl and how many points they will earn
    # returns dictionary
    async def get_active_ppl(self):
        # initiate empty dict
        active_ids = {}
        # iterate thru channels on server
        for channel in self.client.get_guild(target_guild_id).voice_channels:
            # no points earned in AFK channel
            if not (channel.name == 'Away From Keyboard 😵'):
                # no empty channel taken into account
                if len(list(channel.voice_states.keys())) > 0:
                    # adds dictionary for individual channel's active ppl
                    temp_dict = await self.calculate_points(channel.voice_states)
                    active_ids.update(temp_dict)
        print(active_ids)
        if len(active_ids) == 1:
            return dict.fromkeys(active_ids.keys(), 0.5)
        else:
            return active_ids

    # calculates how many points everyone active earns
    # takes in list of voice states
    # returns dictionary
    @staticmethod
    async def calculate_points(voice_states):
        user_points = {}
        for user_id in voice_states.keys():
            # base point value
            points = 1
            # gets voice_states
            values = voice_states[user_id]
            # lose points if muted
            if values.self_mute:
                points -= 1 / 2
            # lose points if deafened
            if values.self_deaf:
                points -= 1 / 2
            # double points if video on
            if values.self_video:
                points = points * 2
            user_points[user_id] = points
        return user_points


# gets file from bucket given name
def fromBucket(key):
    obj = s3client.get_object(Bucket=bucket_name, Key=key)
    body = obj['Body']
    csv_string = body.read().decode('utf-8')
    data = pd.read_csv(StringIO(csv_string), index_col=0)
    return data


# sends df into csv under given name
def toBucket(df, key):
    csv_buffer = StringIO()
    df.to_csv(csv_buffer)
    s3_resource = boto3.resource('s3', aws_access_key_id=access_key_id,
                                 aws_secret_access_key=secret_access_key)
    s3_resource.Object(bucket_name, key).put(Body=csv_buffer.getvalue())


def setup(client):
    client.add_cog(Logging(client))
