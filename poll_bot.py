import os
import emoji as emojiMod
import discord
import pickle
import discord
from discord_slash import SlashCommand, SlashContext
from discord.ext import commands, tasks
from emoji.unicode_codes.en import EMOJI_ALIAS_UNICODE_ENGLISH
from cogs.help_commands import HelpCommands

TOKEN = os.environ['POLL_TEST_TOKEN']

#Classes
class Poll:
    def __init__(self, number:int, poll:str, message_id:int, server_id:int, emojis:dict, endTime:int, result_message_id:int, result_channel_id:int, delete_time:int, author_id:int, private:bool, closed:bool):
        self.poll = poll
        self.number = number
        self.message_id = message_id
        self.server_id = server_id
        self.emojis = emojis
        self.endTime = endTime
        self.result_message_id = result_message_id
        self.result_channel_id = result_channel_id
        self.delete_time = delete_time
        self.author_id = author_id
        self.private = private
        self.closed = closed

class Server:
    def __init__(self, channel_id:int, category_id:int, poll_number:int, polls:list):
        self.channel_id = channel_id
        self.category_id = category_id
        self.poll_number = poll_number
        self.polls = polls

#Variables
try:
    client = commands.Bot(command_prefix='pt.', intents=discord.Intents.all())
except:
    pass
client.remove_command('help')
slash = SlashCommand(client, sync_commands=True)

with open('data', 'rb') as input:
    try:
        servers = pickle.load(input)
    except:
        servers = {}

#Update function
async def update():
    global servers

    #test if there is a poll result category
    for id in servers:
        guild = client.get_guild(id)
        category = discord.utils.get(guild.categories, id=servers[id].category_id)
        if category == None:
            category = await guild.create_category('poll results')
            servers[id].category_id = category.id

    #updates data file
    open('data', 'w').write('')
    with open('data', 'wb') as output:
        pickle.dump(servers, output, pickle.HIGHEST_PROTOCOL)

##################
# ON READY EVENT #
##################

@client.event
async def on_ready():
    global servers
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f'{client.command_prefix}help')) #changes presence
    cooldown.start() #starts hourly loop
    print(f'Logged in as {client.user}')
    client.add_cog(HelpCommands(client)) #adds help commands cog

#Setup command
@slash.slash(name='setup', description='Setup the server with poll bot', guild_ids=[guild.id for guild in client.guilds])
async def _setup(ctx: SlashContext):
    global servers
    try:
        #Checks if poll bot has been set up
        if servers[ctx.channel.guild.id] != None:
            await ctx.send('Poll Bot has already been set up')
            return

    except KeyError:

        #Checks if sender is admin
        if not ctx.author.guild_permissions.administrator:
            await ctx.send('Get an admin to set up Poll Bot')
            return

        #Creates embed for instructions
        embed = discord.Embed(title='Setup', description='1. Set text channel, just type #<channel name>')
        await ctx.send(embed=embed)
        channel_id = await client.wait_for('message', check=lambda message: message.author == ctx.author and message.channel == ctx.channel)
        category = await ctx.guild.create_category('poll results')

        servers[ctx.guild.id] = Server(channel_id=int(channel_id.content[2:-1]), category_id=category.id, poll_number=0, polls=[])
        await update()
        await ctx.send('That\'s all for the setup')

#Ping command
@slash.slash(name='ping', description='PONG!', guild_ids=[guild.id for guild in client.guilds])
async def _ping(ctx: SlashContext):
    await ctx.send(f'Pong! Latency: {round(client.latency * 1000)}')

@client.command()
async def ping(ctx):
    await ctx.send(f'Pong! Latency: {round(client.latency * 1000)}')

#Create command
@slash.slash(name='create', description='Creates a poll', guild_ids=[guild.id for guild in client.guilds])
async def _create(ctx: SlashContext, poll, hours_live, emoji_1, emoji_2, emoji_3=None, emoji_4=None, emoji_5=None, emoji_6=None, emoji_7=None, emoji_8=None):
    global servers

    server_id = ctx.channel.guild.id
    poll_number = servers[server_id].poll_number + 1
    pollChannel = client.get_channel(servers[server_id].channel_id)
    await ctx.send('Loading...')
    #Checks
    try:
        if servers[server_id] != None:
            pass
    except KeyError:
        await ctx.send('You have not setup the Poll Bot yet')
        return
    if not ctx.author.permissions_in(pollChannel).send_messages:
        await ctx.send('You do not have permissions to make a poll')
        return

    #Gets live time
    try:
        time = int(hours_live)
    except:
        await ctx.send('Hours live must be an number')
        return
    #Gets emojis
    emojiHolder = [emoji_1, emoji_2, emoji_3, emoji_4, emoji_5, emoji_6, emoji_7, emoji_8]
    emojiList = []
    customEmojis = []

    for emoji in ctx.guild.emojis:
        customEmojis.append(f'<:{emoji.name}:{emoji.id}>')
    for emoji in emojiHolder:
        if str(emoji) != 'None':
            if emoji in emojiMod.EMOJI_ALIAS_UNICODE_ENGLISH.values():
                emojiList.append(emoji)
            elif emojiMod.demojize(emoji) in EMOJI_ALIAS_UNICODE_ENGLISH.keys():
                emojiList.append(emoji)
            elif emoji in customEmojis:
                emojiList.append(emoji)
            else:
                await ctx.send(f'{emoji} is not a valid emoji')
                return
    if len(emojiList) != len(set(emojiList)):
        await ctx.send('Cannot have duplicate emojis')
        return
    
    emojiDict = {}
    for emoji in emojiList:
        emojiDict[emoji] = []
    
    #Sends poll
    embed = discord.Embed(title=f'Poll #{poll_number}', description=f'**{poll}**')
    embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
    message = await pollChannel.send(embed=embed)
    for emoji in emojiList:
        await message.add_reaction(emoji)
    
    #Creates final poll result channel
    resultChannel = await ctx.channel.guild.create_text_channel(name=f'poll-results-{poll_number}', category=discord.utils.get(ctx.guild.categories, id=servers[server_id].category_id))
    await resultChannel.set_permissions(ctx.guild.default_role, view_channel=False)
    await resultChannel.set_permissions(ctx.author, manage_channels=True)

    #Sends final poll result message
    embed = discord.Embed(title=f'Poll #{poll_number}', description=f'**{poll}**')
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
    embed.add_field(name=poll, value='** **', inline=False)
    for emoji in emojiDict:
        embed.add_field(name=emoji, value=f'0%, 0 votes\n', inline=False)
    resultMessage = await resultChannel.send(embed=embed)
    await resultMessage.pin()

    #Finising stuff
    servers[server_id].poll_number += 1
    servers[server_id].polls.append(Poll(
        poll=poll, message_id=message.id, server_id=server_id, emojis=emojiDict, endTime=time, number=poll_number, 
        result_message_id=resultMessage.id, result_channel_id=resultChannel.id, delete_time=time+168, author_id=ctx.author.id, private=False, closed=False
        ))
    await ctx.channel.send('Successfully created poll!')
    await update()

#Private poll command
@slash.slash(name='private_poll', description='Creates a private poll', guild_ids=[guild.id for guild in client.guilds])
async def _private_poll(ctx: SlashContext, poll, hours_live, emoji_1, emoji_2, emoji_3=None, emoji_4=None, emoji_5=None, emoji_6=None, emoji_7=None, emoji_8=None):
    global servers

    server_id = ctx.channel.guild.id
    poll_number = servers[server_id].poll_number + 1
    pollChannel = client.get_channel(servers[server_id].channel_id)
    await ctx.send('Loading...')
    #Checks
    try:
        if servers[server_id] != None:
            pass
    except KeyError:
        await ctx.send('You have not setup the Poll Bot yet')
        return
    if not ctx.author.permissions_in(pollChannel).send_messages:
        await ctx.send('You do not have permissions to make a poll')
        return

    #Gets live time
    try:
        time = int(hours_live)
    except:
        await ctx.send('Hours live must be an number')
        return
    #Gets emojis
    emojiHolder = [emoji_1, emoji_2, emoji_3, emoji_4, emoji_5, emoji_6, emoji_7, emoji_8]
    emojiList = []
    customEmojis = []

    for emoji in ctx.guild.emojis:
        customEmojis.append(f'<:{emoji.name}:{emoji.id}>')
    for emoji in emojiHolder:
        if str(emoji) != 'None':
            if emoji in emojiMod.EMOJI_ALIAS_UNICODE_ENGLISH.values():
                emojiList.append(emoji)
            elif emojiMod.demojize(emoji) in EMOJI_ALIAS_UNICODE_ENGLISH.keys():
                emojiList.append(emoji)
            elif emoji in customEmojis:
                emojiList.append(emoji)
            else:
                await ctx.send(f'{emoji} is not a valid emoji')
                return
    if len(emojiList) != len(set(emojiList)):
        await ctx.send('Cannot have duplicate emojis')
        return
    
    emojiDict = {}
    for emoji in emojiList:
        emojiDict[emoji] = []
    
    #Sends poll
    embed = discord.Embed(title=f'Poll #{poll_number}', description=f'**{poll}**')
    embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
    message = await ctx.channel.send(embed=embed)
    for emoji in emojiList:
        await message.add_reaction(emoji)
    try:
        await message.pin()
    except:
        pass
    
    #Creates final poll result channel
    resultChannel = await ctx.channel.guild.create_text_channel(name=f'poll-results-{poll_number}', category=discord.utils.get(ctx.guild.categories, id=servers[server_id].category_id))
    await resultChannel.set_permissions(ctx.guild.default_role, view_channel=False)
    await resultChannel.set_permissions(ctx.author, manage_channels=True)

    #Sends final poll result message
    embed = discord.Embed(title=f'Poll #{poll_number}', description=f'**{poll}**')
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
    embed.add_field(name=poll, value='** **', inline=False)
    for emoji in emojiDict:
        embed.add_field(name=emoji, value=f'0%, 0 votes\n', inline=False)
    resultMessage = await resultChannel.send(embed=embed)
    await resultMessage.pin()

    #Finising stuff
    servers[server_id].poll_number += 1
    servers[server_id].polls.append(Poll(
        poll=poll, message_id=message.id, server_id=server_id, emojis=emojiDict, endTime=time, number=poll_number, 
        result_message_id=resultMessage.id, result_channel_id=resultChannel.id, delete_time=time+168, author_id=ctx.author.id, private=False, closed=False
        ))
    await update()
    
#Clear all results (Admin only)
@slash.slash(name='clear_polls', description='Clears all polls, be careful', guild_ids=[guild.id for guild in client.guilds])
async def _clear_polls(ctx:SlashContext):
    global servers

    server_id = ctx.guild.id
    if ctx.author.guild_permissions.administrator != True:
        await ctx.send('Do not have permissions!')
        return
    await ctx.send('Are you sure you want to delete **ALL** polls from this server?')
    try:
        check = await client.wait_for('message', check=lambda message: message.author==ctx.author and message.channel==ctx.channel, timeout=30)
    except:
        await ctx.channel.send('Canceled deletion of polls')
        return
    if check.content.lower() in ['yes', 'ye', 'y', 'yea', 'yeah']:
        for poll in servers[server_id].polls:
            print(servers[server_id].polls)
            channel = client.get_channel(poll.result_channel_id)
            await channel.delete()
        servers[server_id].polls = []
        await ctx.channel.send('Done deleting polls!')
    else:
        await ctx.channel.send('Canceled deletion of polls')
        return
    await update()

#Reaction function
@client.event
async def on_raw_reaction_add(payload):
    global servers

    server_id = payload.guild_id
    message = await client.get_channel(payload.channel_id).fetch_message(payload.message_id)
    if client.get_user(payload.user_id) != client.user and message.author == client.user:
        await message.remove_reaction(payload.emoji, payload.member)
        for poll in servers[server_id].polls:

            #Checks if voter has already voted
            if poll.message_id == payload.message_id:
                voted = False
                for emoji in poll.emojis:
                    if payload.member.id in poll.emojis[emoji]:
                            voted = True
                #if not voted
                if not voted:
                    poll.emojis[str(payload.emoji)].append(payload.member.id)
                    
                    #creates new embed
                    votes = 0
                    for emoji in poll.emojis:
                        votes += len(poll.emojis[emoji])
                    author = await client.fetch_user(poll.author_id)
                    embed = discord.Embed(title=f'Poll #{servers[poll.server_id].poll_number}', description=f'**{poll.poll}**')
                    embed.set_author(name=author.display_name, icon_url=author.avatar_url)
                    for emoji in poll.emojis:
                        if votes != 0:
                            embed.add_field(name=emoji, value=f'{int(round(len(poll.emojis[emoji])/votes, 2)*100)}%, {len(poll.emojis[emoji])} votes\n', inline=False)
                        else:
                            embed.add_field(name=emoji, value=f'0%, 0 votes\n', inline=False)
                    #changes embed and changes channel permissions
                    channel = client.get_channel(poll.result_channel_id)
                    message = await channel.fetch_message(poll.result_message_id)
                    await message.edit(embed=embed)
                    await channel.set_permissions(payload.member, view_channel=True)
                    await channel.send(f'**{payload.member.display_name} Has voted {payload.emoji}**')
    await update()

#Main loop
@tasks.loop(hours=1)
async def cooldown():
    global servers

    for server_id in servers:
        for poll in servers[server_id].polls:
            channel = client.get_channel(poll.result_channel_id)
            poll.endTime -= 1
            poll.delete_time -= 1
            if poll.delete_time <= 0:
                await channel.delete()
                servers[server_id].polls.remove(poll)
            if poll.endTime <= 0 and not poll.closed:
                await channel.send(f'**Poll #{poll.number} is closed, will delete result channel in 7 days!**')
                if not poll.private:
                    await channel.set_permissions(channel.guild.default_role, view_channel=True)
                if poll.private:
                    message = await channel.fetch_message(poll.message_id)
                    await message.unpin()
                poll.closed = True 

    await update()

client.run(TOKEN)
