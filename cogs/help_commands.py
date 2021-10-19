from discord.ext import commands
from discord import Embed

class HelpCommands(commands.Cog):
    def __init__(self, client):
        self.client = client
    
    @commands.group(invoke_without_command=True)
    async def help(self, ctx):
        embed = Embed(title='Help', description='Use /help <command> for more info on a command', color=self.client.user.color)
        embed.add_field(name='Commands', value='ping, create, private_poll')
        if(ctx.author.guild_permissions.administrator):
            embed.add_field(name='Admin commands', value='setup, clear_polls')
        await ctx.send(embed=embed)

    @help.command()
    async def ping(self, ctx):
        embed = Embed(title='Ping', description='Get the current latency', color=self.client.user.color)
        await ctx.send(embed=embed)

    @help.command()
    async def create(self, ctx):
        embed = Embed(title='Create', description='Creates a poll, must have permission to create poll', color=self.client.user.color)
        await ctx.send(embed=embed)

    @help.command()
    async def private_poll(self, ctx):
        embed = Embed(title='Private poll', description='Creates a private poll, for private channels, must have permission to create poll', color=self.client.user.color)
        await ctx.send(embed=embed)

    @help.command()
    @commands.has_permissions(administrator=True)
    async def setup(self, ctx):
        embed = Embed(title='Setup', description='Sets up Poll Bot', color=self.client.user.color)
        await ctx.send(embed=embed)
    @setup.error
    async def setup_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = Embed(title='Help', description='Use poll.help <command> for more info on a command', color=self.client.user.color)
            embed.add_field(name='Commands', value='ping, create')
            await ctx.send(embed=embed)
            
    @help.command()
    @commands.has_permissions(administrator=True)
    async def clear_polls(self, ctx):
        embed = Embed(title='Clear Polls', description='Clears all polls, be careful, this cannot be undone', color=self.client.user.color)
        await ctx.send(embed=embed)
    @setup.error
    async def clear_polls_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = Embed(title='Help', description='Use poll.help <command> for more info on a command', color=self.client.user.color)
            embed.add_field(name='Commands', value='ping, create')
            await ctx.send(embed=embed)