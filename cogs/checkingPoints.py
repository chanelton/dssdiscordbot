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
target_channel_id = 806691390372708362

main_embed = None

access_key_id = os.environ["AWS_ACCESS_KEY_ID"]
secret_access_key = os.environ["AWS_SECRET_ACCESS_KEY"]
bucket_name = os.environ["S3_BUCKET_NAME"]
s3client = boto3.client('s3', aws_access_key_id=access_key_id,
                        aws_secret_access_key=secret_access_key)


class Checking(commands.Cog):

    def __init__(self, client):
        self.client = client
    #    self.cycle.start()

    @commands.Cog.listener()
    async def on_ready(self):
        print('CHECKING READY.')
        await self.base_embed()

    # @tasks.loop(seconds=86400)
    # async def cycle(self):
    #     try:
    #         await self.base_embed()
    #     except AttributeError:
    #         pass

    async def base_embed(self):
        points = fromBucket("dssdollars.csv")
        top10 = points.sort_values('points', ascending=False)[:10]
        top10string = "".join([f"{self.client.get_guild(target_guild_id).get_member(top10.iloc[row, 0]).display_name} - {top10.iloc[row, 1]}\n" for row in np.arange(len(top10))])
        embed = discord.Embed(title="🤑 DSS DOLLASSSS 🤑",
                              description=f"**Click hyperlink for rewards**\nLast Updated: {datetime.datetime.now().replace(microsecond=0)}",
                              color=0x4e7a27, url="https://docs.google.com/spreadsheets"
                                                  "/d/1e3AyLUqBiZzejdhbBXw3HPL9S7jmf3P4mEE-15nfWrI/edit")
        embed.add_field(name="Top 10 Ballers ⛹️‍️:", value=top10string, inline=False)
        embed.add_field(name="Most Recent Checker's Balance:", value="N/A", inline=False)
        embed.add_field(name="Earn!",
                        value="+1 Dollar for Every Minute in Call!\n2x Dollars if you have cam on :0\n0 - 0.5x Points "
                              "if you're AFK/Muted/Deafened :(\n+0.10 Dollars for reacting to exec announcements\n+0.25 "
                              "Dollars for just sending messages\nCulture Com/Exec might randomly give free points at events;)\n \nHappy Spending :)")
        embed.set_footer(
            text="React to this message to check your own balance!\nDon't spam when its unresponsive🤬, its just a bit slow🤧"
                 "\nMessage Elton when you wanna redeem prizes.\n")
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/457065146519388173/805905097979854898/unknown.png")
        global main_embed
        main_embed = await self.client.get_guild(target_guild_id).get_channel(target_channel_id).send(embed=embed)
        for i in ['🤑', '💰', '💲', '💵', '💸', '🧧', '😎']:
            await self.react(main_embed, i)

    @staticmethod
    async def react(message, emoji):
        await message.add_reaction(emoji)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not payload.member.bot and payload.message_id == main_embed.id:
            dollar_thesaurus = np.random.choice(['BIG BUCKS', 'DSS Dollars', 'Units of Monetary Currency', 'Dollars of Cold Hard Cash', '$DSS Stonks📈'])
            points = fromBucket("dssdollars.csv")
            top10 = points.sort_values('points', ascending=False)[:10]
            top10string = "".join([
                                     f"{self.client.get_guild(target_guild_id).get_member(top10.iloc[row, 0]).display_name} - {top10.iloc[row, 1]}\n"
                                     for row in np.arange(len(top10))])
            embed = discord.Embed(title="🤑 DSS DOLLASSSS 🤑",
                                  description=f"**Click hyperlink for rewards**\nLast Updated: {datetime.datetime.now().replace(microsecond=0)}",
                                  color=0x4e7a27, url="https://docs.google.com/spreadsheets"
                                                      "/d/1e3AyLUqBiZzejdhbBXw3HPL9S7jmf3P4mEE-15nfWrI/edit")
            embed.add_field(name="Top 10 Ballers ⛹️‍️:", value=top10string, inline=False)
            if payload.member.id in list(points['id']):
                embed.add_field(name=f"Most Recent Checker's Balance ({payload.member.display_name}):",
                                value=f"{points[points['id'] == payload.member.id].iloc[0, 1]} {dollar_thesaurus}",
                                inline=False)
            else:
                embed.add_field(name=f"Most Recent Checker's Balance ({payload.member.display_name}):",
                                value=f"You Don't Have Any Points Yet :(\nHang out in calls to get started :)",
                                inline=False)
            embed.add_field(name="Earn!",
                            value="+1 Dollar for Every Minute in Call!\n2x Dollars if you have cam on :0\n0 - 0.5x Points "
                                  "if you're AFK/Muted/Deafened :(\n+0.10 Dollars for reacting to exec announcements\n+0.25 "
                                  "Dollars for just sending messages\nCulture Com/Exec might randomly give free points at events ;)\n \nHappy Spending :)")
            embed.set_footer(text="React to this message to check your own balance!\nDon't spam when its unresponsive🤬, its just a bit slow🤧"
                                  "\nMessage Elton when you wanna redeem prizes.\n")
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/457065146519388173/805905097979854898/unknown.png")
            await main_embed.edit(embed=embed)


def fromBucket(key):
    obj = s3client.get_object(Bucket=bucket_name, Key=key)
    body = obj['Body']
    csv_string = body.read().decode('utf-8')
    data = pd.read_csv(StringIO(csv_string), index_col=0)
    return data


def setup(client):
    client.add_cog(Checking(client))
