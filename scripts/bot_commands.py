import datetime, json, os, random
import discord
from discord.ext import commands, tasks
import config
import reddit
from database import db

class BotCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="echo")
    async def echo(self, ctx, *, message: str=''):
        try:
            if message == '': 
                raise Exception
            elif message.__contains__("--"):
                # finding the number of time to repeat
                index = message.find('--')
                n = int(message[index+2:].strip())
                await ctx.send(f"{message[:index].strip()}\n" * n)
            else:
                await ctx.send(message)
        except:
            await ctx.send(f"Invalid command. Correct Syntax: `{config.prefix_cache[ctx.guild.id]}echo MESSAGE --number(optional)`")

    @commands.command(name="hello")
    async def hello(self, ctx):
        await ctx.send(f"Good Day, {ctx.author.mention}. Hope you are having a fantastic day. ")

    @commands.command(name="ping")
    async def ping(self, ctx):
        await ctx.send(f"Ping: {round(self.bot.latency * 1000)} ms. ")

    @commands.command(name="status")
    async def status(self, ctx):
        await ctx.send(f"{self.bot.user} operational. ")

    @commands.command(name="help")
    async def help_command(self, ctx):
        embed = discord.Embed(
            title="🤖 Bot Help Menu",
            description="Here are all available commands:",
            color=0x00ff00
        )

        # adding the general commands
        embed.add_field(
            name="\n📝 General Commands: ",
            value=f"`{config.prefix_cache[ctx.guild.id]}echo --number of times you want it to repeat(OPTIONAL)` - Repeats the message back to the channel.\n"
            f"`{config.prefix_cache[ctx.guild.id]}hello` - Greets the user.\n"
            f"`{config.prefix_cache[ctx.guild.id]}status` - Returns the status of the bot.\n"
            f"`{config.prefix_cache[ctx.guild.id]}ping` - Returns the latency of the BOT in milliseconds.\n"
            f"`{config.prefix_cache[ctx.guild.id]}list` - Returns all the available item names from the storage.\n"
            f"`{config.prefix_cache[ctx.guild.id]}list nsfw` - Returns all the available NSFW item names from the storage.\n"
            f"`{config.prefix_cache[ctx.guild.id]}list autodelete` - Returns all the scheduled channel names for automatic deletion.\n"
            f"`@Croissant [ask anything]` - Uses the AI to answer your question.\n",
            inline=False
        )

        # adding the complex commands
        embed.add_field(
            name="\n🧩 Complex Commands (Takes Arguments): ",
            value=f"`;ITEM_NAME` - Returns gif/image/video of the given name if the item was added.\n"
            f"`{config.prefix_cache[ctx.guild.id]}del number_of_messages_to_delete/all` - Deletes the number of messages given. If `all` is given, deletes all the messages in the channel.\n"
            f"`{config.prefix_cache[ctx.guild.id]}greet USERNAME ITEM_NAMES(for multiple items, separate each with space)` - Greets the given username with a gif/image/video.\n"
            f"`{config.prefix_cache[ctx.guild.id]}reddit SUBREDDIT_NAME` - Returns gif or images from subreddit.\n"
            f"`{config.prefix_cache[ctx.guild.id]}add NAME LINK` - Adds gif/image/video for later use.\n"
            f"`{config.prefix_cache[ctx.guild.id]}add nsfw NAME LINK` - Adds NSFW gif/image/video for later use in a separate storage.\n"
            f"`{config.prefix_cache[ctx.guild.id]}add AutoDelete CHANNEL_ID TIME(HOUR:MINUTE:SECOND)` - Adds given discord channel for automatic deletion after a given time.\n"
            f"`{config.prefix_cache[ctx.guild.id]}rmv NAME` - Removes gif/image/video of the given name from the storage.\n"
            f"`{config.prefix_cache[ctx.guild.id]}rmv AutoDelete CHANNEL_ID` - Removes the given discord channel from automatic deletion.\n"
            f"`{config.prefix_cache[ctx.guild.id]}set VARIABLE VALUE` - Sets the values of BOT config.(Must be used with caution.)\n"
            f"`{config.prefix_cache[ctx.guild.id]}random-line quran/sunnah/quote` - Returns a random line from the given file.",
            inline=False
        )

        await ctx.send(embed=embed)

    @commands.command(name="del")
    async def delete_messages(self, ctx, *, message: str = ''):
        try:
            if message == '':
                raise Exception

            # converting the message to int for deletion limit
            amount = int(message)
            # +1 to remove the command itself
            deleted_messages = await ctx.channel.purge(limit=amount+1)
            await ctx.send(f"Deleted {len(deleted_messages)} messages.", delete_after=5)
            deleted_messages.clear()
        except ValueError:
            if message == 'all':
                # bulk=True, for deleting the messages more efficiently
                deleted_messages = await ctx.channel.purge(limit=None, bulk=True)
                await ctx.send(
                    f"Deleted {len(deleted_messages)} messages.", delete_after=5
                )

                # clearing the deleted messages list as we don't need them
                deleted_messages.clear()
            else:
                raise Exception
        except:
            await ctx.send(f"Invalid command. Correct Syntax: `{config.prefix_cache[ctx.guild.id]}del number_of_messages_to_delete/all`")

    @commands.command(name="list")
    async def list_item(self, ctx, *, message: str = ""):
        try:
            if message == '':
                # converting the dict keys to a list for easier availability checking
                item_names = list(config.storage_dict_cache[ctx.guild.id].keys())
                await ctx.send(f"```Available items in storage are: \n{item_names}```")
            elif message.lower() == "nsfw": 
                # converting the dict keys to a list for easier availability checking
                item_names = list(config.nsfw_storage_dict_cache[ctx.guild.id].keys())
                await ctx.send(f"```Available items in nsfw storage are: \n{item_names}```")
            elif message.lower() == "autodelete":
                channel_names = []

                # converting the dict keys to a list for easier availability checking
                channel_list = list(config.auto_delete_cache[ctx.guild.id].keys())

                # getting and adding the channel names to the dictionary
                for channel in channel_list:
                    channel_name = self.bot.get_channel(int(channel)).name
                    channel_names.append(channel_name)

                await ctx.send(f"```Channels scheduled for automatic deletion: \n{channel_names}```")
            else:
                raise Exception
        except Exception as error:
            print(f"Error at listing items: {error}")
            await ctx.send(f"Invalid command. Correct Syntax: `{config.prefix_cache[ctx.guild.id]}list`" 
                           + f"\nFor NSFW contents, correct syntax: `{config.prefix_cache[ctx.guild.id]}list nsfw`"
                           + f"\nFor scheduled channels, correct syntax: `{config.prefix_cache[ctx.guild.id]}list autodelete`")

    @commands.command(name="greet")
    async def greet(self, ctx, *, message: str = ""):
        try:
            if message == '':
                raise Exception

            # extracting the necessary data for processing
            parts = message.split(' ')
            user_name = parts[0]
            item_names = []

            # getting the item names
            for part in parts[1:]:
                if part == "":
                    continue
                item_names.append(part)

            # sending the messages
            await ctx.send(f"Hello, {user_name}. ")
            await self.send_item(item_names, ctx.channel)
        except:
            await ctx.send(f"Invalid. Correct Syntax: `{config.prefix_cache[ctx.guild.id]}"
                           + "greet USERNAME ITEM_NAME(for multiple items, separate each with space)`")

    @commands.command(name="reddit")
    async def reddit(self, ctx, *, message: str = ""):
        try:
            if message == '':
                raise Exception
            if not config.REDDIT_ENABLED:
                await ctx.send("Reddit functionality is not available at this time.")
                return

            # creating a object for using the reddit api
            fetcher = reddit.Fetch()

            # extracting the data from the message
            parts = message.split(' ')

            if len(parts) != 1:
                raise Exception
            subreddit_name = message

            # getting the submission to send
            submission = await fetcher.get_submission(subreddit_name, ctx.guild.id)

            # returning the error message
            if type(submission) == str:
                await ctx.send(submission)
                return

            # removes the meme after delete_after if the url is NSFW
            if submission.is_nsfw:
                await ctx.send(f"{submission.title} \nBy: {submission.author}")
                await ctx.send(submission.url, delete_after=config.delete_after_cache[ctx.guild.id] 
                               if config.delete_after_cache[ctx.guild.id] != 0 else None)
            else:
                await ctx.send(f"{submission.title} \nBy: {submission.author}")
                await ctx.send(submission.url)
        except:
            await ctx.send(f"Invalid. Correct Syntax: `{config.prefix_cache[ctx.guild.id]}reddit SUBREDDIT_NAME`")

    @commands.command(name="add")
    async def add(self, ctx, *, message: str = ''):
        try:
            if message == '':
                raise Exception

            # extracting the data for the message
            parts = message.split(' ')

            # for non nsfw items
            if len(parts) == 2:
                item_name = parts[0].lower()
                item_url = parts[1]

                # adding the item to the dictionary
                config.storage_dict_cache[ctx.guild.id].update({item_name: item_url})
                # dumping the whole dict in a string for saving
                updated = json.dumps(config.storage_dict_cache[ctx.guild.id], ensure_ascii=False)
                # updating the database
                await db.set_variable(ctx.guild.id, "STORAGE", updated)

                await ctx.send(f"{item_name} added successfully.")
            elif parts[0].lower() == "nsfw":
                # for nsfw items
                item_name = parts[1]
                item_url = parts[2]

                # adding the item to the dictionary
                config.nsfw_storage_dict_cache[ctx.guild.id].update({item_name: item_url})
                # dumping the whole dict in a string for saving
                updated = json.dumps(config.nsfw_storage_dict_cache[ctx.guild.id], ensure_ascii=False)
                # updating the database
                await db.set_variable(ctx.guild.id, "NSFW_STORAGE", updated)

                await ctx.send(f"{item_name} added successfully.")
            elif parts[0].lower() == "autodelete":
                channel_id = parts[1]
                time = parts[2]

                channel = self.bot.get_channel(int(channel_id))

                # checking for validity
                if channel and channel in ctx.guild.channels:
                    try:
                        # checking for correct time format
                        datetime.datetime.strptime(time, "%H:%M:%S")
                    except:
                        await ctx.send(f"Invalid Time. Correct format: `HOUR:MINUTE:SECOND`" +
                                      f"\nFor example: `{config.prefix_cache[ctx.guild.id]}add autodelete 111111111111111111 12:00:00`")
                        return

                    # adding the channel_id and time in the dictionary
                    config.auto_delete_cache[ctx.guild.id].update({channel_id: time})
                    # dumping the whole dict in a string for saving
                    updated = json.dumps(config.auto_delete_cache[ctx.guild.id], ensure_ascii=False)
                    # updating the database
                    await db.set_variable(ctx.guild.id, "AUTO_DELETE", updated)

                    await ctx.send(f"**{channel.name}** scheduled for automatic deletion at **{time}** every day. ")
                else:
                    await ctx.send(f"{channel_id} is not a valid channel in this server. ")
            else:
                raise Exception
        except Exception:
            await ctx.send(
                f"Error. Correct Syntax: `{config.prefix_cache[ctx.guild.id]}add NAME LINK`"
                + f"\nFor nsfw content, Correct Syntax: `{config.prefix_cache[ctx.guild.id]}add nsfw NAME LINK`"
                + f"\nFor scheduled channels, correct syntax: `{config.prefix_cache[ctx.guild.id]}add autodelete CHANNEL_ID TIME(HOUR:MINUTE:SECOND)`")

    @commands.command(name="rmv")
    async def rmv(self, ctx, *, message: str = ''):
        try:
            if message == '':
                raise Exception

            parts = message.split(' ')

            if len(parts) == 1:
                item_name = message.lower()

                # checking if the item is in the dictionary
                if item_name not in config.storage_dict_cache[ctx.guild.id].keys() and item_name not in config.nsfw_storage_dict_cache[ctx.guild.id].keys():
                    await ctx.send(f"There is no '{item_name}' in storage. ")
                    await ctx.send(f"Use `{config.prefix_cache[ctx.guild.id]}list` to get the list of names.")
                else:
                    try:
                        # removing the item from the dictionary
                        config.storage_dict_cache[ctx.guild.id].pop(item_name)
                        # dumping the whole dict in a string for saving
                        updated = json.dumps(config.storage_dict_cache[ctx.guild.id], ensure_ascii=False)
                        # updating the database
                        await db.set_variable(ctx.guild.id, "STORAGE", updated)
                    # removing from nsfw dict on keyerror
                    except KeyError:
                        config.nsfw_storage_dict_cache[ctx.guild.id].pop(item_name)
                        # dumping the whole dict in a string for saving
                        updated = json.dumps(config.nsfw_storage_dict_cache[ctx.guild.id], ensure_ascii=False)
                        # updating the database
                        await db.set_variable(ctx.guild.id, "NSFW_STORAGE", updated)

                    await ctx.send(f"{item_name} removed successfully.")
            elif len(parts) == 2:
                if parts[0].lower() == "autodelete":
                    channel_id = parts[1]
                    channel = self.bot.get_channel(int(channel_id))

                    if channel:
                        # checking if the item is in the dictionary
                        if channel_id in config.auto_delete_cache[ctx.guild.id].keys():
                            config.auto_delete_cache[ctx.guild.id].pop(channel_id)
                            # dumping the whole dict in a string for saving
                            updated = json.dumps(config.auto_delete_cache[ctx.guild.id], ensure_ascii=False)
                            # updating the database
                            await db.set_variable(ctx.guild.id, "AUTO_DELETE", updated)

                            await ctx.send(f"Auto delete for channel **{channel.name}** removed successfully.")
                        else:
                            await ctx.send(f"There is no {channel_id} in storage scheduled for auto deletion. ")
                    else:
                        await ctx.send("Invalid channel id. ")
                else:
                    raise Exception
            else:
                raise Exception
        except:
            await ctx.send(f"Error. Correct Syntax: `{config.prefix_cache[ctx.guild.id]}rmv NAME`"
                           + f"\nFor scheduled channels, correct syntax: `{config.prefix_cache[ctx.guild.id]}rmv autodelete CHANNEL_ID`")

    @commands.command(name="set")
    async def set(self, ctx, *, message: str = ""):
        try:
            if message == "":
                raise Exception

            # extracting the data for the message
            parts = message.split(' ')
            variable = parts[0].upper()
            value = parts[1]

            shouldUpdate = False

            # checking for each case which variable to update
            match variable:
                case "ACTIVITY_CHANNEL_ID":
                    shouldUpdate = True
                    config.notify_channel_id_cache[ctx.guild.id] = int(value)
                case "PREFIX":
                    shouldUpdate = True
                    config.prefix_cache[ctx.guild.id] = value
                case "DELETE_AFTER":
                    shouldUpdate = True
                    config.delete_after_cache[ctx.guild.id] = int(value)
                case "SEARCH_LIMIT":
                    shouldUpdate = True
                    config.search_limit_cache[ctx.guild.id] = int(value)
                case "NSFW_ALLOWED":
                    # parsing the user input
                    if value.lower() == "true" :
                        value = True
                    elif value.lower() == "false":
                        value = False
                    else:
                        await ctx.send("Invalid value for NSFW_ALLOWED. Acceptable values are: true, false")
                        return
                    shouldUpdate = True
                    config.nsfw_allowed_cache[ctx.guild.id] = value

            if shouldUpdate:
                # updating the variable in the .env file
                await db.set_variable(ctx.guild.id, variable, str(value))

                await ctx.send(f"{variable} set to {value} successfully.")
            else:
                await ctx.send(
                    "Variable not found. Available variables are: PREFIX, DELETE_AFTER, SEARCH_LIMIT, NSFW_ALLOWED, ACTIVITY_CHANNEL_ID"
                )
        except:
            await ctx.send(f"Error. Correct Syntax: `{config.prefix_cache[ctx.guild.id]}set VARIABLE VALUE`")

    @commands.command(name="random-line")
    async def random_line(self, ctx, *, message: str = ""):
        try:
            if message == "":
                raise Exception

            # parsing the user input
            item_name = message.lower()
            file_name = item_name + ".txt"

            QUOTES = ["quran.txt", "sunnah.txt", "quote.txt"]
            folder = "assets/"

            if file_name in QUOTES:
                # since Bengali alphabet is in unicode, we need to open the file in unicode
                with open(os.path.join(folder, file_name), 'r', encoding="utf-8") as file:
                    lines = file.readlines()

                    # sending a random line from the user's desired type
                    await ctx.send(lines[random.randint(0, (len(lines)-1))])
            else:
                await ctx.send(f"{item_name} not found. Available files are: {QUOTES}")
        except:
            await ctx.send(f"Invalid. Correct Syntax: `{config.prefix_cache[ctx.guild.id]}" +
                           "random-line quran/sunnah/quote`")

    @commands.command(name="reload")
    async def reload_server_data(self, ctx):
        try:
            await config.load_all_data()
            await ctx.send("✅All Data Reloaded")
        except:
            await ctx.send("❌Failed to reload data.")

    async def send_item(self, item_names, message_channel):
        # looking for the correct link for each type
        for item_name in item_names:
            item_name = item_name.lower()

            if item_name in config.storage_dict_cache[message_channel.guild.id].keys():
                await message_channel.send(config.storage_dict_cache[message_channel.guild.id][item_name], 
                                           delete_after = config.delete_after_cache[message_channel.guild.id] 
                                           if config.delete_after_cache[message_channel.guild.id] != 0 else None)
            # checking for nsfw and permission
            elif item_name in config.nsfw_storage_dict_cache[message_channel.guild.id].keys():

                if message_channel.nsfw:
                    # sending the correct link for each type
                    await message_channel.send(config.nsfw_storage_dict_cache[message_channel.guild.id][item_name], 
                                               delete_after = config.delete_after_cache[message_channel.guild.id] 
                                               if config.delete_after_cache[message_channel.guild.id] != 0 else None)
                else:
                    await message_channel.send("Invalid channel for NSFW content. "
                                               + "Use the command in a NSFW channel. ")
            else:
                await message_channel.send(
                    f"There is no '{item_name}' in storage. Use `{config.prefix_cache[message_channel.guild.id]}list`" + 
                    f" to get the item names.\nFor NSFW contents, use `{config.prefix_cache[message_channel.guild.id]}list nsfw`"
                )

    async def delete_channel_message(self, channel_id: int):
        # getting the channel object from the channel id
        channel = self.bot.get_channel(channel_id)

        if channel:
            try:
                # bull=True deletes the messages more efficiently(used when deleting a lot of messages)
                deleted_messages = await channel.purge(limit=None, bulk=True)

                await channel.send(f"Deleted {len(deleted_messages)} messages.", delete_after=5)
                # clearing the deleted messages list as we don't need them
                deleted_messages.clear()
            except discord.Forbidden:
                await channel.send(f"Bot doesn't have permission to delete messages in: {channel.name}")
            except Exception as error:
                await channel.send(f"Error deleting messages in: {channel.name}-> {error}")
        else:
            await channel.send("Channel not found.")

    @tasks.loop(seconds=60)
    async def scheduler(self):
        # waiting for the bot to be ready
        await self.bot.wait_until_ready()

        # loading all the dict for each server
        for server_id, schedules in config.auto_delete_cache.items():
            # checking if the server has any scheduled channels
            if schedules:

                # deleting the scheduled channels
                for channel_id in schedules.keys():
                    # setting the timezone to Asia/Dhaka
                    offset = datetime.timezone(datetime.timedelta(hours=6))

                    # parsing the datetime data
                    now = datetime.datetime.now(offset).strftime("%H:%M:%S")
                    now = datetime.datetime.strptime(now, "%H:%M:%S")
                    time = datetime.datetime.strptime(schedules[channel_id], "%H:%M:%S")

                    duration = (now - time).total_seconds()

                    # to avoid multiple unwanted deletions
                    if duration < 60 and duration >= 0:
                        await self.delete_channel_message(int(channel_id))

    # serves as a setup for the scheduler to avoid errors, potentially before the bot is ready
    @scheduler.before_loop
    async def before_scheduler(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(BotCommands(bot))
