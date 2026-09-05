import discord
from discord.ext import commands
import random
import io
import os
from dotenv import load_dotenv
from PIL import Image, ImageDraw

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

UNAUTHORIZED_ROLE_NAME = "Unauthorized"
VERIFIED_ROLE_NAME = "User"

codes = {}  

def make_code_image(code: str) -> io.BytesIO:
    img = Image.new("RGB", (200, 80), color=(30, 30, 30))
    draw = ImageDraw.Draw(img)
    draw.text((40, 30), code, fill=(255, 255, 255))

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


async def get_or_create_role(guild, name):
    role = discord.utils.get(guild.roles, name=name)
    if role is None:
        role = await guild.create_role(name=name)
    return role

@bot.event
async def on_member_join(member):
    role = await get_or_create_role(member.guild, UNAUTHORIZED_ROLE_NAME)
    await member.add_roles(role)

    try:
        await member.send("Добро пожаловать! Для авторизации напиши `!verify`")
    except:
        pass


@bot.command()
async def verify(ctx):
    code = str(random.randint(100000, 999999))
    codes[ctx.author.id] = code

    image = make_code_image(code)
    file = discord.File(image, filename="code.png")

    await ctx.author.send("Введи код с картинки:", file=file)


@bot.event
async def on_message(message):
    
    if message.author.bot:
        return
    
    if message.type == discord.MessageType.new_member:
        await message.delete()
        return

    if message.author.bot:
        return
    
    if isinstance(message.channel, discord.DMChannel) and message.author.id in codes:
        if message.content.strip() == codes[message.author.id]:
            del codes[message.author.id]

            for guild in bot.guilds:
                member = guild.get_member(message.author.id)
                if member:
                    unauthorized = discord.utils.get(guild.roles, name=UNAUTHORIZED_ROLE_NAME)
                    verified = await get_or_create_role(guild, VERIFIED_ROLE_NAME)

                    if unauthorized:
                        await member.remove_roles(unauthorized)
                    await member.add_roles(verified)

            await message.channel.send("Авторизация пройдена!")
        else:
            await message.channel.send("Неверный код.")

    await bot.process_commands(message)


bot.run(TOKEN)