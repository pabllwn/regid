import discord
from discord.ext import commands
from collections import deque
import os

# تفعيل جميع النوايا (Intents)
intents = discord.Intents.all()

bot = commands.Bot(command_prefix='$', intents=intents)

TOKEN = os.getenv("TOKEN")
log_channel_id = None  # سيتم ضبطه من خلال الأمر setlogchannel
snipe_queue = deque(maxlen=5)  # تخزين آخر 5 رسائل محذوفة

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# أمر لضبط قناة السجل
@bot.command(name='setlogchannel')
@commands.has_permissions(administrator=true)
async def set_log_channel(ctx, channel: discord.TextChannel):
    global log_channel_id
    log_channel_id = channel.id
    await ctx.send(f'Log channel set to {channel.mention}')

# الانضمام إلى قناة صوتية محددة
@bot.command(name='join')
@commands.has_permissions(administrator=true)
async def join(ctx, channel: discord.VoiceChannel):
    if ctx.voice_client is not None:
        return await ctx.voice_client.move_to(channel)

    await channel.connect()
    await ctx.send(f'Joined {channel.name}')

# تسجيل الرسائل المحذوفة مع من قام بحذفها ومتى
@bot.event
async def on_message_delete(message):
    global log_channel_id

    # تخزين الرسالة المحذوفة لأمر snipe
    if message.content:
        snipe_queue.append((message.content, message.author.name, message.channel.name))

    if log_channel_id is None:
        return

    log_channel = bot.get_channel(log_channel_id)
    if not log_channel:
        return

    # جلب من قام بحذف الرسالة
    fetched_logs = await message.guild.audit_logs(limit=1, action=discord.AuditLogAction.message_delete).flatten()
    deleter = fetched_logs[0].user if fetched_logs else "Unknown"

    # تضمين تفاصيل الرسالة المحذوفة
    embed = discord.Embed(
        title="Message Deleted",
        color=discord.Color.red(),
        description=f"A message was deleted in {message.channel.mention}"
    )
    embed.add_field(name="Message", value=message.content or "No content", inline=False) 
    embed.add_field(name="Deleted by", value=str(deleter), inline=False)
    embed.add_field(name="Time", value=message.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    embed.set_footer(text=f"User: {message.author.name} | User ID: {message.author.id}")

    await log_channel.send(embed=embed)

# أمر لعرض آخر 5 رسائل محذوفة
@bot.command(name='snipe')
async def snipe(ctx):
    if not snipe_queue:
        await ctx.send("No messages to snipe!")
        return

    embed = discord.Embed(title="Last 5 Deleted Messages", color=discord.Color.blue())
    for i, (content, author, channel) in enumerate(snipe_queue, 1):
        embed.add_field(name=f"{i}. {author} in {channel}", value=content, inline=False)

    await ctx.send(embed=embed)

# التعامل مع أخطاء الأوامر
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    else:
        raise error

bot.run(TOKEN) 
