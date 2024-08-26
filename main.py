import json
import os
import discord
from discord.ext import commands
from keep_alive import keep_alive

keep_alive()
# إعدادات Discord Intents
intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.guilds = True
intents.reactions = True
intents.presences = True
intents.voice_states = True
intents.message_content = True  # يجب تفعيل هذا في إعدادات البوت على Discord Developer Portal

# تهيئة البوت
bot = commands.Bot(command_prefix="!", intents=intents)

keep_alive()

# إعدادات البوت
TOKEN = os.getenv("TOKEN")
GUILD_ID = '1276712128505446490'  # ID الخاص بالسيرفر
REGISTER_CHANNEL_ID = '1277774462527475763'  # ID الخاص بالشات المحددة لتسجيل الأوامر
LOG_CHANNEL_ID = '1277773976483004476'  # ID الخاص بالشات المحددة لتسجيل الأعضاء المسجلين
REMOVE_ROLE_ID = '1277773566523215922'  # ID الرتبة التي سيتم إزالتها
GIVE_ROLE_ID = '1277773778461392937'  # ID الرتبة التي سيتم إعطاؤها
REGISTERED_USERS_FILE = 'registered_users.json'
ADMIN_ID = ['826571466815569970']  # ID الخاص بك

# تحميل المستخدمين المسجلين من الملف
if os.path.exists(REGISTERED_USERS_FILE):
    with open(REGISTERED_USERS_FILE, 'r') as file:
        registered_users = json.load(file)
else:
    registered_users = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    guild = bot.get_guild(int(GUILD_ID))
    if guild is None:
        print("Guild not found!")
        return

    register_channel = bot.get_channel(int(REGISTER_CHANNEL_ID))
    log_channel = bot.get_channel(int(LOG_CHANNEL_ID))
    if register_channel is None:
        print("Register channel not found!")
        return
    if log_channel is None:
        print("Log channel not found!")
        return

    member = guild.get_member(message.author.id)
    if member is None:
        print("Member not found!")
        return

    if message.content == '&reg':
        if message.channel.id == int(REGISTER_CHANNEL_ID):
            if str(message.author.id) in registered_users:
                await message.author.send('You are already registered.')
            else:
                registered_users[str(message.author.id)] = True
                with open(REGISTERED_USERS_FILE, 'w') as file:
                    json.dump(registered_users, file)

                # إعطاء الدور الجديد وإزالة الدور القديم
                role_to_remove = guild.get_role(int(REMOVE_ROLE_ID))
                role_to_give = guild.get_role(int(GIVE_ROLE_ID))
                if role_to_remove:
                    await member.remove_roles(role_to_remove)
                if role_to_give:
                    await member.add_roles(role_to_give)

                # إرسال رسالة تأكيد في الخاص
                await message.author.send('You have been successfully registered, your roles have been updated.<:wow:1275021465531449355>')

                # إرسال رسالة إلى الشات المحدد
                current_time = message.created_at.strftime('%Y-%m-%d %H:%M:%S')
                await log_channel.send(f'{message.author.mention} has been successfully registered at {current_time}.')
        else:
            await message.author.send(f'Please use the registration command in this channel: {register_channel.mention}')
    elif message.content.startswith('&send'):
        if message.author.id == int(ADMIN_ID):
            await register_channel.send("**<a:kroos:1202320599062683679> HeLLo @everyone type &reg to be registered and get <@&1277773778461392937> role**")
        else:
            await message.author.send('<:TDC_chloe_sideeye:786392061930504193> You do not have permission to execute this command.')

bot.run(TOKEN)
