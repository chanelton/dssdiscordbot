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

target_guild_id = 781033657594675224  # DSS is 730215239760740353
announcements_channel = 781033658102054975  # DSS is 731625608521580624
access_key_id = os.environ["AWS_ACCESS_KEY_ID"]
secret_access_key = os.environ["AWS_SECRET_ACCESS_KEY"]
bucket_name = os.environ["S3_BUCKET_NAME"]
s3client = boto3.client('s3', aws_access_key_id=access_key_id,
                        aws_secret_access_key=secret_access_key)

deduct_embed = None
deduct_info = None


class Modding(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('MODDING READY.')

    @commands.command()
    async def give(self, ctx, *arg):
        culture = discord.utils.find(lambda r: r.name == 'Culture', ctx.message.guild.roles)
        exec = discord.utils.find(lambda r: r.name == 'Exec', ctx.message.guild.roles)
        if culture or exec in ctx.author.roles:
            active_ids = {}
            for channel in self.client.get_guild(target_guild_id).voice_channels:
                if not (channel.name == 'afk'): # change channel name later
                    if len(list(channel.voice_states.keys())) > 0:
                        # active_ids.append(list(channel.voice_states.keys())[0])
                        temp_dict = await self.calculate_points(channel.voice_states)
                        active_ids = temp_dict | active_ids
            active_ids_20 = dict.fromkeys(active_ids.keys(), 20)
            del active_ids_20[ctx.author.id]
            await self.add_points(active_ids_20)
            modsGiving = fromBucket("modsGiving.csv")
            append = pd.DataFrame([[datetime.datetime.now().replace(microsecond=0), ctx.author.id, 1]],
                                  columns=['date', 'display_name', 'count'])
            modsGiving = pd.concat([modsGiving, append], ignore_index=True)
            toBucket(modsGiving, 'modsGiving.csv')
            await ctx.send(f'{ctx.author.display_name} has graciously given 20 DSS Dollars to everyone in call! 😎')
        else:
            await ctx.send("You can't use that command.")

    @commands.command()
    async def take(self, ctx, *arg):
        if ctx.author.id == 298972130035499010:
            take_id = int(arg[0][3:][:-1])
            take_amount = float(arg[1])
            points = fromBucket('dssdollars.csv')
            curr_points = float(points[points['id'] == take_id].iloc[0, 1])
            embed = discord.Embed(title="Mod Deducting Points For Redeeming Prizes", description=f"Are you sure you wanna deduct {take_amount}?", color=0x0056d6)
            embed.add_field(name=f"{ctx.guild.get_member(take_id).display_name}'s Account Balance", value=f"Current: {curr_points}\nAfter: {curr_points-take_amount}", inline=False)
            global deduct_embed
            deduct_embed = await ctx.send(embed=embed)
            await self.react(deduct_embed, '✅')
            await self.react(deduct_embed, '🚫')
            global deduct_info
            deduct_info = [points, take_id, curr_points-take_amount, curr_points]
        else:
            await ctx.send("You can't use that command.")

    @commands.command()
    async def set(self, ctx, *arg):
        if ctx.author.id == 298972130035499010:
            set_id = int(arg[0][3:][:-1])
            set_amount = float(arg[1])
            points = fromBucket('dssdollars.csv')
            curr_points = float(points[points['id'] == set_id].iloc[0, 1])
            points.loc[points['id'] == set_id, 'points'] = set_amount
            embed = discord.Embed(title="Mod Setting Dollars in Emergencies",
                                  description="Beep Boop Coding", color=0x96d35f)
            embed.add_field(name="Success! Setting Complete.",
                            value=f"{ctx.guild.get_member(set_id).display_name}'s balance "
                                  f"has been set to {set_amount} from {curr_points}")
            await ctx.send(embed=embed)
            toBucket(points, "dssdollars.csv")
        else:
            await ctx.send("You can't use that command.")

    @staticmethod
    async def react(message, emoji):
        await message.add_reaction(emoji)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        global deduct_embed
        try:
            if not payload.member.bot and payload.message_id == deduct_embed.id:
                global deduct_info
                if str(payload.emoji) in '✅':
                    points = deduct_info[0]
                    take_id = deduct_info[1]
                    new_amount = deduct_info[2]
                    old_amount = deduct_info[3]
                    points.loc[points['id'] == take_id, 'points'] = new_amount
                    toBucket(points, "dssdollars.csv")
                    embed = discord.Embed(title="Mod Deducting Dollars For Redeeming Prizes",
                                          description=f"Swag Central 😎", color=0x96d35f)
                    embed.add_field(name="Success!! Amount has been deducted.",
                                    value=f"{self.client.get_guild(payload.guild_id).get_member(take_id).display_name}'s new balance is: {new_amount} dollars.\n"
                                          f"it Used to be {old_amount}.")
                    await deduct_embed.edit(embed=embed)
                elif str(payload.emoji) in '🚫':
                    take_id = deduct_info[1]
                    new_amount = deduct_info[2]
                    embed = discord.Embed(title="Mod Deducting Dollars For Redeeming Prizes", description=f"Swag Central 😎", color=0x96d35f)
                    embed.add_field(name="Deduction Denied.", value=f"{self.client.get_guild(payload.guild_id).get_member(take_id).display_name}'s balance is still: {new_amount} dollars.")
                    await deduct_embed.edit(embed=embed)
                deduct_info = None
                deduct_embed = None
        except AttributeError:
            pass

    @staticmethod
    async def add_points(dictionary):
        points = fromBucket('dssdollars.csv')
        for user_id in dictionary.keys():
            if user_id in list(points['id']):
                curr_points = points[points['id'] == user_id].iloc[0, 1]
                new_val = curr_points + dictionary[user_id]
                points.loc[points['id'] == user_id, 'points'] = new_val
            elif user_id not in list(points['id']):
                append = pd.DataFrame([[user_id, dictionary[user_id]]], columns=['id', 'points'])
                points = pd.concat([points, append], ignore_index=True)
        toBucket(points, "dssdollars.csv")


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
    client.add_cog(Modding(client))
