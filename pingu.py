import logging
import platform
import sys

import discord
from discord.ext import commands

import bot


# Log information to file and console
FORMAT = '[%(asctime)s] [%(levelname)s] %(name)s: %(message)s'
DATEFMT = '%m-%d-%Y %I:%M:%S %p'
logFormat = logging.Formatter(fmt=FORMAT, datefmt=DATEFMT)
logging.basicConfig(level=logging.INFO,
                    format=FORMAT,
                    datefmt=DATEFMT,
                    filename='pingu.log',
                    filemode='w')
consoleLogger = logging.StreamHandler(sys.stdout)
consoleLogger.setFormatter(logFormat)
logging.getLogger().addHandler(consoleLogger)

# Return logging information from this module
log = logging.getLogger('pingu')
log.info('Starting Pingu instance')

# Instantiate Pingu and apply default values
pingu = commands.Bot(command_prefix=bot.default['prefix'], description=bot.default['desc'])
pingu.default = bot.default
pingu.current = {'activity': None, 'desc': None, 'prefix': None, 'status': None}
pingu.icons = {'fail': ':x:', 'info': ':information_source:', 'success': ':white_check_mark:'}
pingu.njit_course_schedules = {}

# Load the specified default modules
for cog in bot.cogs:
    log.info(f'Loading cog module: {cog}')
    pingu.load_extension(f'cogs.{cog}')


@pingu.event
async def on_ready():
    """Prints information about the token being used, simple statistics of the bot being used,
    and the versions of the dependencies being used. Also sets one other default parameter of the bot.
    """
    total_servers = len(pingu.guilds)
    total_users = len(set(pingu.get_all_members()))
    log.info(f'\n---Initial Startup Information---\n'
             f'[ Bot Information ]\n'
             f'- Username: {pingu.user}\n'
             f'- ID: {pingu.user.id}\n'
             f'[ Connected To ]\n'
             f'- {total_servers} servers\n'
             f'- {total_users} unique users\n'
             f'[ Dependencies ]\n'
             f'- Python v{platform.python_version()}\n'
             f'- discord.py[voice] v{discord.__version__}\n'
             f'- Pingu v{bot.version}\n'
             f'---------------------------------')

    await pingu.change_presence(status=pingu.default['status'], activity=pingu.default['activity'])
    log.info('Instance is ready to receive commands')


@pingu.event
async def on_message(message):
    # Ignore messages from itself, other bots, or from DMs
    if message.author.bot or message.guild is None:
        return

    # Pass information to other cogs
    await pingu.process_commands(message)


@pingu.event
async def on_command_error(ctx, error):
    # Ignore malformed syntax or typos on a command by a user
    if isinstance(error, commands.CommandNotFound) or isinstance(error, commands.MissingRequiredArgument):
        return
    elif isinstance(error, commands.CommandError):
        await ctx.send(error)


if __name__ == '__main__':
    pingu.run(bot.token)
