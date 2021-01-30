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
target_channel_id = 781033719044767744

main_embed = None

from dssdiscordbot.DSS import s3client, bucket_name


class Checking(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('CHECKING READY.')
        await self.base_embed()

    async def base_embed(self):
        embed = discord.Embed(title="🤑 DSS DOLLASSSS 🤑",
                              description=f"**Click hyperlink for rewards**\nLast Updated: {datetime.datetime.now().replace(microsecond=0)}",
                              color=0x4e7a27, url="https://docs.google.com/spreadsheets"
                                                  "/d/1e3AyLUqBiZzejdhbBXw3HPL9S7jmf3P4mEE-15nfWrI/edit")
        embed.add_field(name="Top 5 Ballers:", value="later", inline=False)
        embed.add_field(name="Checker's Balance:", value="N/A\n \nHappy Spending :)", inline=False)
        embed.set_footer(text="React or unreact to this message to check your own balance!")
        global main_embed
        main_embed = await self.client.get_guild(target_guild_id).get_channel(target_channel_id).send(embed=embed)
        for i in ['🤑', '💰', '💲', '💵', '💸', '🧧', '😎']:
            await self.react(main_embed, i)

    @staticmethod
    async def react(message, emoji):
        await message.add_reaction(emoji)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not payload.member.bot:
            embed = discord.Embed(title="🤑 DSS DOLLASSSS 🤑",
                                  description=f"**Click hyperlink for rewards**\nLast Updated: {datetime.datetime.now().replace(microsecond=0)}",
                                  color=0x4e7a27, url="https://docs.google.com/spreadsheets"
                                                      "/d/1e3AyLUqBiZzejdhbBXw3HPL9S7jmf3P4mEE-15nfWrI/edit")
            embed.add_field(name="Top 5 Ballers:", value="later", inline=False)
            embed.add_field(name=f"{payload.member.display_name}'s Balance:",
                            value=f"{fromBucket('begin-end.csv')['time in call'][0]}\n \nHappy Spending :)",
                            inline=False)
            embed.set_footer(text="React or unreact to this message to check your own balance!")
            await main_embed.edit(embed=embed)


def fromBucket(key):
    obj = s3client.get_object(Bucket=bucket_name, Key=key)
    body = obj['Body']
    csv_string = body.read().decode('utf-8')
    data = pd.read_csv(StringIO(csv_string), index_col=0)
    return data


def setup(client):
    client.add_cog(Checking(client))
