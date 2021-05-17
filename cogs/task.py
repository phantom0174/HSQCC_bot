from core.db import self_client
from core.utils import Time
from cogs.sqcs_plugin.quiz import quiz_start, quiz_end
import discord
from discord.ext import tasks
from core.cog_config import CogExtension
from core.db import fluctlight_client
from itertools import cycle
from core.fluctlight_ext import Fluct


class Task(CogExtension):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.quiz_set_cursor = self_client["QuizSetting"]

        self.activity_loop = None

        self.parameters_set.start()
        self.quiz_auto.start()
        self.bot_activity.start()
        self.role_check.start()

    @tasks.loop(minutes=10)
    async def parameters_set(self):
        await self.bot.wait_until_ready()

        # fetching current non-bot member count
        fluctlight_cursor = fluctlight_client["MainFluctlights"]
        member_count = fluctlight_cursor.find({}).count()

        # fetching current guild activity percentage
        fluct_cursor = fluctlight_client["MainFluctlights"]
        week_active_match = {
            "deep_freeze": {
                "$ne": True
            },
            "week_active": {
                "$ne": False
            }
        }
        week_active_count = fluct_cursor.find(week_active_match).count()
        countable_member_count = fluct_cursor.find({"deep_freeze": {"$ne": 1}}).count()
        activity_percentage = round((week_active_count / countable_member_count) * 100, 4)

        self.activity_loop = cycle([
            discord.Activity(
                type=discord.ActivityType.watching,
                name=f'{member_count} 個活生生的搖光'
            ),
            discord.Activity(
                type=discord.ActivityType.listening,
                name=f'+help'
            ),
            discord.Activity(
                type=discord.ActivityType.watching,
                name=f'{activity_percentage}% 的活躍度...'
            )
        ])

    @tasks.loop(minutes=10)
    async def quiz_auto(self):
        await self.bot.wait_until_ready()

        guild = self.bot.get_guild(784607509629239316)
        report_channel = discord.utils.get(guild.text_channels, name='sqcs-report')

        quiz_status = self.quiz_set_cursor.find_one({"_id": 0})["event_status"]

        def quiz_ready_to_start():
            return Time.get_info('date') == 1 and Time.get_info('hour') >= 6 and not quiz_status

        def quiz_ready_to_end():
            return Time.get_info('date') == 7 and Time.get_info('hour') >= 23 and quiz_status

        if quiz_ready_to_start():
            await quiz_start(self.bot)
            await report_channel.send(f'[AUTO QUIZ START][{Time.get_info("whole")}]')
        elif quiz_ready_to_end():
            await quiz_end(self.bot)
            await report_channel.send(f'[AUTO QUIZ END][{Time.get_info("whole")}]')

    @tasks.loop(seconds=10)
    async def bot_activity(self):
        await self.bot.wait_until_ready()

        if self.activity_loop is not None:
            await self.bot.change_presence(activity=next(self.activity_loop))

    @tasks.loop(hours=2)
    async def role_check(self):
        await self.bot.wait_until_ready()

        guild = self.bot.get_guild(743507979369709639)
        auto_role = guild.get_role(823804080199565342)
        neutral_role = guild.get_role(823803958052257813)
        fluctlight_cursor = fluctlight_client["MainFluctlights"]

        for member in guild.members:
            if member.bot:
                continue

            if neutral_role in member.roles:
                member_active_data = fluctlight_cursor.find_one({"_id": member.id})
                if member_active_data is None:
                    await Fluct().reset_main(member.id, guild)
                    continue

                quiz_crt_count = member_active_data["quiz_correct_count"]
                lect_attend_count = member_active_data["lect_attend_count"]

                if quiz_crt_count >= 2 and lect_attend_count >= 4:
                    await member.remove_roles(neutral_role)
                    await member.add_roles(auto_role)
                    await member.send(':partying_face: 恭喜！你已升級為自由量子！')


def setup(bot):
    bot.add_cog(Task(bot))
