import discord
from discord.ext import commands
from collections import deque
import os

intents = discord.Intents.all()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='$', intents=intents)

TOKEN = os.getenv("TOKEN")
log_channel_id = None  # Will be set by the user via command
snipe_queue = deque(maxlen=5)  # Stores the last 5 deleted messages

# Disable default help command
bot.remove_command('help')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command(name='setlogchannel')
@commands.has_permissions(administrator=True)
async def set_log_channel(ctx, channel: discord.TextChannel):
    global log_channel_id
    log_channel_id = channel.id
    await ctx.send(f'Log channel set to {channel.mention}')
    print(f'Log channel ID set to: {log_channel_id}')  # Log for debugging

@bot.command(name='join')
@commands.has_permissions(administrator=True)
async def join(ctx):
    # Check if the user is in a voice channel
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if ctx.voice_client is not None:
            if ctx.voice_client.channel == channel:
                await ctx.send("I am already in your voice channel.")
                return
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
        await ctx.send(f'Joined {channel.name}')
    else:
        await ctx.send("You need to be in a voice channel for me to join!")

@bot.event
async def on_message_delete(message):
    global log_channel_id

    # Add deleted message to snipe queue
    if message.content:
        snipe_queue.append((message.content, message.author.name, message.channel.id))

    if log_channel_id is None:
        return

    log_channel = bot.get_channel(log_channel_id)
    if not log_channel:
        print(f"Couldn't find log channel with ID {log_channel_id}")  # Debug log
        return

    # Fetch audit logs to find out who deleted the message
    async for entry in message.guild.audit_logs(limit=1, action=discord.AuditLogAction.message_delete):
        deleter = entry.user if entry else "Unknown"
        break  # Exit loop after first entry

    # Create and send the embed to the log channel
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

@bot.command(name='snipe')
async def snipe(ctx):
    channel_id = ctx.channel.id  # Get the current channel ID
    # Filter messages to show only those from the current channel
    filtered_messages = [msg for msg in snipe_queue if msg[2] == channel_id]

    if not filtered_messages:
        await ctx.send("No messages to snipe in this channel!")
        return

    embed = discord.Embed(title="Last 5 Deleted Messages", color=discord.Color.blue())
    for i, (content, author, _) in enumerate(filtered_messages, 1):
        embed.add_field(name=f"{i}. {author}", value=content, inline=False)

    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    else:
        raise error

# Disable help command response
@bot.command(name='help')
async def help_command(ctx):
    pass  # Do nothing when $help is used

bot.run(TOKEN)
