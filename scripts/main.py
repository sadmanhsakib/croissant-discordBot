import discord
from discord.ext import commands
from groq import Groq
import config
import reddit
from database import db

# giving the permissions
intents = discord.Intents.default()
intents.message_content = True
intents.presences = True
intents.messages = True
intents.members = True
intents.guilds = True


async def get_prefix(bot, message):
    # returning the prefix for this server
    return config.prefix_cache[message.guild.id]


bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)
cog = None
groq_client = Groq(api_key=config.GROQ_API)


@bot.event
# when the bot starts
async def on_ready():
    global cog

    # connecting to the database
    await db.connect()
    # loading the data from the database
    await config.load_all_data()

    if config.REDDIT_ENABLED:
        # authenticating the reddit api
        await reddit.authenticate()

    # loading the command script
    await bot.load_extension("bot_commands")

    # importing and creating a cog object
    from bot_commands import BotCommands

    cog = BotCommands(bot)

    # this won't actually start until before_scheduler completes
    # the scheduler only starts after wait_until_ready() completes
    # scheduler is a background task, not a coroutine, so no need to await
    cog.scheduler.start()

    # prints a message in console when ready
    print(f"✅Logged in as: {bot.user}")


@bot.event
async def on_guild_join(guild):
    config.prefix_cache.update({guild.id: "-"})

    # setting the default values
    await config.set_default(guild.id)
    # loading the data from the database
    await config.load_all_data()

    # getting the general channel of the server that the BOT just joined
    channel = discord.utils.get(guild.text_channels, name="general")

    if channel and channel.permissions_for(guild.me).send_messages:
        # sending greeting messages
        await channel.send("Thank you for adding Croissant! ")
        await channel.send(
            "Croissant has a lot of commands, functionality and practical use cases."
        )
        await channel.send(
            f"That's why it's high recommended to read the concise README file.\n"
            + "You can read it by clicking in here: {config.README_URL}"
        )


@bot.event
async def on_guild_remove(guild):
    # removes all the data from the database and resets the variables
    await config.remove_data(guild.id)


@bot.event
# when the user sends a message in server
async def on_message(message):
    # prevents the bot from replying on its own messages
    if message.author == bot.user:
        return
    # reacting to hate messages
    if message.content.lower().__contains__("clanker"):
        await message.add_reaction("💢")
    # checking for mentions
    elif bot.user in message.mentions:
        # parsing the user input
        user_prompt = message.content.replace(bot.user.mention, "").strip()

        if not user_prompt:
            return

        # system prompt for the bot
        messages = [
            {
                "role": "system",
                "content": config.system_prompt,
            },
        ]

        # checking if the message is a reply
        if message.type == discord.MessageType.reply:
            # getting the message that the user replied to
            replied_message = await message.channel.fetch_message(
                message.reference.message_id
            )
            messages.append(
                {
                    "role": "assistant",
                    "content": replied_message.content,
                }
            )
            messages.append(
                {
                    "role": "user",
                    "content": user_prompt,
                }
            )
        else:
            messages.append(
                {
                    "role": "user",
                    "content": user_prompt,
                }
            )

        # getting the response from the bot
        chat_completion = groq_client.chat.completions.create(
            messages=messages,
            model=config.model,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
        )

        response = chat_completion.choices[0].message.content.strip()
        await message.channel.send(response)

    # replying to item requests
    if message.content.__contains__(";"):
        item_names = []
        parts = message.content.split(" ")

        # for every word in the message
        for part in parts:
            if part[0] == ";":
                try:
                    # checking if the item name is an actual request
                    if part[1] == " ":
                        return
                    else:
                        # removing the ; from the item name
                        item_names.append(part[1:])
                except IndexError:
                    return

        if item_names:
            # sending items if applicable
            await cog.send_item(item_names, message.channel)

    # processing the commands
    await bot.process_commands(message)


@bot.event
# called when a member of the server changes their activity
# before and after represents the member that has changed presence;
async def on_presence_update(before, after):
    channel_id = config.notify_channel_id_cache[after.guild.id]
    channel = bot.get_channel(channel_id)

    # prevents replying to bot's presence update
    # doesn't update presence if the presence_update_channel is none
    if not after.bot and int(channel_id) != 0:
        old_status = str(before.status)
        new_status = str(after.status)

        # if the user comes online
        if old_status == "offline" and new_status != "offline":
            # sends a greeting message
            await channel.send(f"Welcome back, {after.name}.")
        # if the user goes offline
        elif old_status != "offline" and new_status == "offline":
            await channel.send(f"Bye, {after.name}")


# starts the bot
bot.run(config.BOT_TOKEN)
