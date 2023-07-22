# import discord
# from discord.ext import commands
import asyncio
import discord

server_id = "704170052156391424"
channel_id = "1131780877853147206"
app_id = "1131781773257355377"
pubkey = "824ff71423a0ed4b10c6ba943f14da1918a9f743e4b4b12207a6548242ac42d6"
token = "MTEzMTc4MTc3MzI1NzM1NTM3Nw.GgUzMz._zOWFD-FgwmulbAN2QEfBUMmZI8nmEU6ihJ0KA"


with open("phrase_output_1.txt") as f:
    captions = [
        l.replace("Image caption: ", "")
        for l in f.readlines()
        if l.lower().startswith("image caption:")
    ]

for caption in captions:
    print(caption)

# This example requires the 'message_content' intent.

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


async def my_background_task():
    await client.wait_until_ready()
    counter = 0
    channel = client.get_channel(id=channel_id)
    while not client.is_closed():
        counter += 1
        await channel.send(counter)
        await asyncio.sleep(60)  # task runs every 60 seconds


@client.event
async def on_ready():
    print("Logged in as")
    print(client.user.name)
    print(client.user.id)
    print("------")


async def main():
    async with client:
        client.loop.create_task(my_background_task())
        await client.start(token)
    # await create_db_pool() # again, no need to run with AbstractLoopEvent if you can await
    # await bot.start(TOKEN)


asyncio.run(main())


# # Create instance of bot
# bot = commands.Bot(command_prefix='!')
#
# @bot.event
# async def on_ready():
#     print(f'We have logged in as {bot.user}')
#
#
# #@bot.command()
# #async def send_message(ctx, *, message):
# #    # Replace 'channel_id_here' with your channel's ID
# #    channel = bot.get_channel(channel_id)
# #    await channel.send(message)
#
# @bot.event
# async def on_ready():
#     print(f'We have logged in as {bot.user}')
#     channel = bot.get_channel(channel_id)  # Replace 'channel_id_here' with your channel's ID
#     await channel.send(f"/imagine {captions[1]}")  # Replace 'Your message here' with your message
#
#
# # Replace 'your_token_here' with your bot's token
# bot.run(token)
#
#
