import asyncio
import logging
from datetime import datetime, timedelta

import discord
from discord.ext import commands, tasks
from pytz import timezone


class Alert1234(commands.Cog):
    # pylint: disable=no-member
    def __init__(self, bot):
        self.bot = bot
        self.log = logging.getLogger(__name__)
        self.message_location = None  # Singular location and not per-guild because it's by design
        self.sent_message = None

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    def cog_unload(self):
        self.log.info("Cog unloaded; stopping 1234 and resetting message location to nowhere")
        self.message_location = None
        self.sent_message = None
        self.message_1234.cancel()

    @commands.command(name="1234", hidden=True)
    async def set_1234(self, ctx, requested_guild_id=None, requested_channel_id=None):
        # Temporary variable to compare with cog-level location
        preliminary_location = None

        # Parse the location to send the message
        if requested_guild_id is None:
            self.log.info("No location specified; sending in current channel")
            preliminary_location = ctx.message.channel
            # await ctx.send(f"{self.bot.icons['info']} No IDs specified. Sending message in current channel.")
        elif requested_channel_id is None:
            raise commands.BadArgument("Missing channel ID to send in server.")

        # Locate requested server and channel
        if preliminary_location is None:
            # Error checking if given IDs are not random strings
            try:
                requested_guild_id = int(requested_guild_id)
                requested_channel_id = int(requested_channel_id)
            except ValueError:
                self.log.error("Failed to parse server ID and/or text channel ID")
                raise commands.BadArgument("Given ID(s) were not a numerical value.")

            # Search for the server using its ID
            selected_guild = self.bot.get_guild(requested_guild_id)
            if selected_guild is None:
                self.log.error("Unable to find requested server")
                raise commands.BadArgument("Unable to find requested server")
            self.log.info(f"Found requested server (id: {selected_guild.id}, name: {selected_guild.name})")

            # Search for the channel using its ID
            selected_channel = selected_guild.get_channel(requested_channel_id)
            if selected_channel is None:
                self.log.error("Unable to find requested channel")
                raise commands.BadArgument("Specified text channel does not exist or read permission(s) were not given")
            self.log.info(f"Found requested text channel (id: {selected_channel.id}, name: {selected_channel.name})")

            preliminary_location = selected_channel
        
        self.message_location = preliminary_location

        # Check the channel permissions
        self_permissions = self.message_location.permissions_for(ctx.me)
        if not self_permissions.send_messages:
            self.log.error("Missing permission to send messages in the specified location")
            raise commands.BadArgument("Missing permission to send messages in that channel.")

        # Restart the task (the following condition will be used when discord.py 1.4.0 is released)
        # if self.message_1234.is_running():
        #     self.message_1234.restart()
        self.message_1234.cancel()
        await asyncio.sleep(1)
        self.message_1234.start()
    
    @commands.command(name="no1234", hidden=True)
    async def stop_1234(self, ctx):
        self.log.info("Manual override to stop 1234 received; stopping task")
        self.message_location = None
        self.sent_message = None
        self.message_1234.cancel()

    @tasks.loop()
    async def message_1234(self):
        # Python times, timezones, and daylight savings is hard
        utc = timezone("UTC")
        eastern = timezone("America/New_York")  # Accounts for daylight savings ("US/Eastern" is EST only)
        now = utc.localize(datetime.utcnow())
        if self.message_location is not None:
            today_12am = eastern.localize(datetime(now.year, now.month, now.day, 0, 34))
            today_12pm = eastern.localize(datetime(now.year, now.month, now.day, 12, 34))
            tomorrow_12am = eastern.localize(datetime(now.year, now.month, now.day + 1, 0, 34))

            debug_mode = False
            if debug_mode:
                self.log.info(f"UTC: {now.astimezone(utc)} | Eastern: {now.astimezone(eastern)}")
                self.log.info(f"UTC: {today_12am.astimezone(utc)} | Eastern: {today_12am.astimezone(eastern)}")
                self.log.info(f"UTC: {today_12pm.astimezone(utc)} | Eastern: {today_12pm.astimezone(eastern)}")
                self.log.info(f"UTC: {tomorrow_12am.astimezone(utc)} | Eastern: {tomorrow_12am.astimezone(eastern)}")
                self.log.info("DEBUG MODE ENABLED: Firing in the next 3 seconds")
                await asyncio.sleep(60)
            elif now <= today_12am:
                wait = (today_12am - now).total_seconds()
                self.log.info(f"Sending message at 12:34 AM ({str(timedelta(seconds=round(wait)))} left)")
                await discord.utils.sleep_until(today_12am)
            elif now <= today_12pm:
                wait = (today_12pm - now).total_seconds()
                self.log.info(f"Sending message at 12:34 PM ({str(timedelta(seconds=round(wait)))} left)")
                await discord.utils.sleep_until(today_12pm)
            else:
                wait = (tomorrow_12am - now).total_seconds()
                self.log.info(f"Sending message at 12:34 AM tomorrow ({str(timedelta(seconds=round(wait)))} left)")
                await discord.utils.sleep_until(tomorrow_12am)
        
        if self.bot.get_channel(self.message_location.id) is not None:
            self.log.info(f"Sending message to text channel"
                          f" (id: {self.message_location.id}, name: {self.message_location.name})")
            self.sent_message = await self.message_location.send("12:34")
        else:
            self.log.error("Channel disappeared before message was sent; stopping task")
            self.message_location = None
            self.message_1234.cancel()

    @message_1234.before_loop
    async def prep_1234(self):
        await self.bot.wait_until_ready()
    
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if self.sent_message is not None and self.sent_message.id == message.id:
            message_guild = message.guild
            message_deleter = None
            if message_guild.id == 143909103951937536 or message_guild.id == 276571138455502848:
                self_permissions = message.channel.permissions_for(message_guild.me)
                if self_permissions.view_audit_log:
                    async for entry in message_guild.audit_logs(limit=20, action=discord.AuditLogAction.message_delete):
                        if entry.target == message_guild.me:
                            message_deleter = entry.user
                            break

            if message_deleter is None:
                self.sent_message = await message.channel.send("Stop deleting my messages >:(")
            else:
                self.sent_message = await message.channel.send(f"{message_deleter.mention} Stop deleting my messages >:(")
            # Checking who deleted the message requires Audit Log permission
            # See Guild.audit_log on rtfm for more info


def setup(bot):
    bot.add_cog(Alert1234(bot))
