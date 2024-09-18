import discord
from discord.ext import commands
import os
import datetime
import random
import asyncio
from keep_alive import keep_alive

# Set up intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

# Initialize bot
bot = commands.Bot(command_prefix='$', intents=intents)

# Token and global variables
TOKEN = os.getenv("TOKEN")
log_channel_id = None
reward_data = {}
last_claims = {}

# Role ID that can use commands
ALLOWED_ROLE_ID = 1285511769447600138
COOLDOWN_PERIOD = 86400
MENTION_ROLES = [1280007060930428969, 1278359492676943912]

# Remove the default help command
bot.remove_command('help')

# Check for admin or role permissions
def is_admin_or_role():
    def predicate(ctx):
        return ctx.author.guild_permissions.administrator or \
               any(role.id == ALLOWED_ROLE_ID for role in ctx.author.roles)
    return commands.check(predicate)

def has_role(user):
    return any(role.id == ALLOWED_ROLE_ID for role in user.roles)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.event
async def on_message(message):
    # Ignore messages from the bot and messages with unknown commands starting with the prefix
    if message.author == bot.user or not message.content.startswith('$'):
        return
    ctx = await bot.get_context(message)
    if not ctx.valid:
        return
    await bot.process_commands(message)

@bot.command(name='setlogchannel')
@is_admin_or_role()
async def set_log_channel(ctx, channel: discord.TextChannel):
    global log_channel_id
    log_channel_id = channel.id
    await ctx.send(f'Log channel set to {channel.mention}')

@bot.event
async def on_message_delete(message):
    if log_channel_id is None:
        return

    log_channel = bot.get_channel(log_channel_id)
    if not log_channel:
        print(f"Couldn't find log channel with ID {log_channel_id}")
        return

    # Get the user who deleted the message
    async for entry in message.guild.audit_logs(limit=1, action=discord.AuditLogAction.message_delete):
        deleter = entry.user if entry else "Unknown"
        break

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

@bot.command(name='daily')
async def daily(ctx):
    if not has_role(ctx.author):
        await ctx.send("You do not have the required role to claim rewards.")
        return

    user_id = ctx.author.id
    today = datetime.date.today()

    user_rewards = reward_data.get('rewards', [])
    last_claim = last_claims.get(user_id, today - datetime.timedelta(days=1))

    if (today - last_claim).total_seconds() < COOLDOWN_PERIOD:
        await ctx.send("You must wait 24 hours before claiming another reward.")
        return

    if not user_rewards:
        await ctx.send("No rewards available to claim<a:done:1285756541676421151>.")
        return

    # Prepare embed
    embed = discord.Embed(
        title="<a:Gift:1285755999399186495> Daily Rewards",
        description=f"Available rewards: {', '.join(user_rewards)}",
        color=discord.Color.green()
    )
    embed.add_field(name="Rewards Remaining", value=len(user_rewards), inline=False)

    # Create the button to claim a reward
    view = discord.ui.View()
    button = discord.ui.Button(
        label="Claim Reward",
        style=discord.ButtonStyle.primary,
        custom_id="claim_reward",
        emoji="<a:Gift:1285755999399186495>"
    )
    view.add_item(button)

    message = await ctx.send(embed=embed, view=view)

    # Delete the message after 3 minutes
    await asyncio.sleep(180)
    await message.delete()

@bot.command(name='setrewards')
@is_admin_or_role()
async def set_rewards(ctx, *rewards):
    today = datetime.date.today()
    reward_data['rewards'] = list(rewards)
    reward_data['date'] = today
    await ctx.send(f"Rewards for today set to: {', '.join(rewards)}")

@bot.command(name='addrewards')
@is_admin_or_role()
async def add_rewards(ctx, day: int, *rewards):
    date = datetime.date.today() + datetime.timedelta(days=day)
    reward_data[date] = list(rewards)
    await ctx.send(f"Rewards for {date} set to: {', '.join(rewards)}")

@bot.event
async def on_interaction(interaction):
    if interaction.type == discord.InteractionType.component and interaction.data['custom_id'] == 'claim_reward':
        user = interaction.user
        if not has_role(user):
            await interaction.response.send_message("You do not have the required role to claim rewards.", ephemeral=True)
            return

        today = datetime.date.today()
        user_rewards = reward_data.get('rewards', [])

        if not user_rewards:
            await interaction.response.send_message("No rewards available<a:done:1285756541676421151>.", ephemeral=True)
            return

        if (today - last_claims.get(user.id, today - datetime.timedelta(days=1))).total_seconds() < COOLDOWN_PERIOD:
            await interaction.response.send_message("You must wait 24 hours before claiming another reward<a:done:1285756541676421151>.", ephemeral=True)
            return

        # Claim a random reward
        claimed_reward = random.choice(user_rewards)
        user_rewards.remove(claimed_reward)
        reward_data['rewards'] = user_rewards
        last_claims[user.id] = today

        # Notify mentioned roles
        guild = interaction.guild
        role_mentions = ' '.join([f'<@&{role_id}>' for role_id in MENTION_ROLES])
        embed = discord.Embed(
            title="<a:tada:1285756673000083477> Reward Claimed",
            description=f"{interaction.user.mention} has claimed a reward: {claimed_reward} <a:Gift:1285755999399186495>",
            color=discord.Color.blue()
        )
        embed.add_field(name="Reward", value=claimed_reward, inline=False)
        embed.add_field(name="Claimed by", value=interaction.user.mention, inline=False)

        # Send the message with role mentions
        await guild.system_channel.send(content=role_mentions, embed=embed)

        await interaction.response.send_message(f"You claimed: {claimed_reward} <a:done:1285756541676421151>", ephemeral=True)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    elif isinstance(error, commands.CommandNotFound):
        pass  # Ignore unknown commands
    else:
        await ctx.send(f"An error occurred: {error}")

# Custom help command
@bot.command(name='help')
async def help_command(ctx):
    await ctx.send("Help command is disabled.")

keep_alive()  # Keep the bot alive
bot.run(TOKEN)
        
