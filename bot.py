from discord.ext import commands
import discord
import sys
import os
import keep_alive
import asyncio
import core.utils as utl
import logging


Format = '%(asctime)s %(levelname)s: %(message)s, ' \
         'via line: %(lineno)d, ' \
         'in func: %(funcName)s, ' \
         'of file: %(pathname)s\n'

logging.basicConfig(
    filename='bot.log',
    level=logging.WARNING,
    format=Format
)
logging.captureWarnings(True)


intents = discord.Intents.all()
bot = commands.Bot(
    command_prefix='+',
    intents=intents,
    case_insensitive=True,
    owner_id=610327503671656449
)


@bot.event
async def on_ready():
    print(">--->> Bot is online <<---<")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name=f'+help'
        )
    )


@bot.command()
async def info(ctx):
    embed = discord.Embed(
        title='Bot information',
        colour=bot.user.colour
    )
    embed.set_thumbnail(url="https://i.imgur.com/MbzRNTJ.png")
    embed.set_author(name=bot.user.display_name, icon_url=bot.user.avatar_url)

    embed.add_field(
        name='Join Time',
        value=f'Joined at {bot.user.created_at}'
    )
    embed.add_field(
        name='Source Code',
        value='https://github.com/phantom0174/SQCS_bot'
    )
    await ctx.send(embed=embed)


# function for cogs management
def find_cog(path: str, target_cog: str, mode: str) -> (bool, str):
    trans_path = {
        "./cogs": "cogs.",
        "./cogs/sqcs_plugin": "cogs.sqcs_plugin."
    }
    for item in os.listdir(path):
        if item.startswith(target_cog) and item.endswith('.py'):
            if mode == 'load':
                bot.load_extension(
                    f'{trans_path.get(path)}{item[:-3]}'
                )
                return True, f':white_check_mark: Extension {item} loaded!'
            if mode == 'unload':
                bot.unload_extension(
                    f'{trans_path.get(path)}{item[:-3]}'
                )
                return True, f':white_check_mark: Extension {item} unloaded!'
            if mode == 'reload':
                bot.reload_extension(
                    f'{trans_path.get(path)}{item[:-3]}'
                )
                return True, f':white_check_mark: Extension {item} reloaded!'
    return False, ''


@bot.command()
@commands.has_any_role('總召', 'Administrator')
async def load(ctx, target_cog: str):
    find, msg = find_cog('./cogs', target_cog, 'load')
    if find:
        return await ctx.send(msg)

    find, msg = find_cog('./cogs/sqcs_plugin', target_cog, 'load')
    if find:
        return await ctx.send(msg)

    return await ctx.send(
        f':exclamation: There are no extension called {target_cog}!'
    )


@bot.command()
@commands.has_any_role('總召', 'Administrator')
async def unload(ctx, target_cog: str):
    find, msg = find_cog('./cogs', target_cog, 'unload')
    if find:
        return await ctx.send(msg)

    find, msg = find_cog('./cogs/sqcs_plugin', target_cog, 'unload')
    if find:
        return await ctx.send(msg)

    return await ctx.send(
        f':exclamation: There are no extension called {target_cog}!'
    )


@bot.command()
@commands.has_any_role('總召', 'Administrator')
async def reload(ctx, target_package: str):
    if target_package not in ['MAIN', 'SQCS']:
        find, msg = find_cog('./cogs', target_package, 'reload')
        if find:
            return await ctx.send(msg)

        find, msg = find_cog('./cogs/sqcs_plugin', target_package, 'reload')
        if find:
            return await ctx.send(msg)

        return await ctx.send(
            f':exclamation: There are no extension called {target_package}!'
        )

    if target_package == 'MAIN':
        for reload_filename in os.listdir('./cogs'):
            if reload_filename.endswith('.py'):
                bot.reload_extension(f'cogs.{reload_filename[:-3]}')
    elif target_package == 'SQCS':
        for reload_filename in os.listdir('./cogs/sqcs_plugin'):
            if reload_filename.endswith('.py'):
                bot.reload_extension(f'cogs/sqcs_plugin.{reload_filename[:-3]}')

    await ctx.send(':white_check_mark: Reload finished!')


@bot.command(aliases=['logout', 'shutdown'])
@commands.has_any_role('總召')
async def shut_down(ctx):
    await ctx.send(':white_check_mark: The bot is shutting down...')
    await bot.logout()
    await asyncio.sleep(1)
    sys.exit(0)


@bot.event
async def on_disconnect():
    report_channel = bot.get_channel(785146879004508171)
    await report_channel.send(f':exclamation: Bot disconnected! {utl.Time.get_info("whole")}')


for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')
for filename in os.listdir('./cogs/sqcs_plugin'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.sqcs_plugin.{filename[:-3]}')


keep_alive.keep_alive()

if __name__ == "__main__":
    bot.run(os.environ.get("TOKEN"))
