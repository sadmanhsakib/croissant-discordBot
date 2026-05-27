import os, json
import dotenv

dotenv.load_dotenv()

# variables from the .env file
BOT_TOKEN = os.getenv("BOT_TOKEN")
README_URL = os.getenv("README_URL")
DATABASE_URL = os.getenv("DATABASE_URL")
GROQ_API = os.getenv("GROQ_API")

REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("SECRET")

if not CLIENT_ID or not CLIENT_SECRET or not REDDIT_PASSWORD or not REDDIT_USERNAME:
    print("❌ Reddit credentials are not set in the .env file. Reddit functionality will be disabled.")
    REDDIT_ENABLED = False

# master variables from database
system_prompt=None
model=None
max_tokens=None
temperature=None

# server specific variables from database
prefix_cache = None
search_limit_cache = None
nsfw_allowed_cache = None
delete_after_cache = None
notify_channel_id_cache = None
storage_dict_cache = None
nsfw_storage_dict_cache = None
auto_delete_cache = None


async def load_all_data():
    from database import db

    # master variables
    global system_prompt, model, max_tokens, temperature

    system_prompt = await db.get_variable("SYSTEM_PROMPT")
    model = await db.get_variable("MODEL")
    max_tokens = int(await db.get_variable("MAX_TOKENS"))
    temperature = float(await db.get_variable("TEMPERATURE"))

    # server specific variables
    global prefix_cache, search_limit_cache, nsfw_allowed_cache, delete_after_cache
    global notify_channel_id_cache, storage_dict_cache, nsfw_storage_dict_cache
    global auto_delete_cache

    # loading the dictionaries
    prefix_cache = await db.load_all_variables("PREFIX")

    search_limit_cache = await db.load_all_variables("SEARCH_LIMIT")
    for key in search_limit_cache:
        search_limit_cache[key] = int(search_limit_cache[key])

    nsfw_allowed_cache = await db.load_all_variables("NSFW_ALLOWED")
    for key in nsfw_allowed_cache:
        nsfw_allowed_cache[key] = True if nsfw_allowed_cache[key].lower() == "true" else False

    delete_after_cache = await db.load_all_variables("DELETE_AFTER")
    for key in delete_after_cache:
        delete_after_cache[key] = int(delete_after_cache[key])

    notify_channel_id_cache = await db.load_all_variables("ACTIVITY_CHANNEL_ID")
    for key in notify_channel_id_cache:
        notify_channel_id_cache[key] = int(notify_channel_id_cache[key])

    storage_dict_cache = await db.load_all_variables("STORAGE")
    for key in storage_dict_cache:
        storage_dict_cache[key] = json.loads(storage_dict_cache[key])

    nsfw_storage_dict_cache = await db.load_all_variables("NSFW_STORAGE")
    for key in nsfw_storage_dict_cache:
        nsfw_storage_dict_cache[key] = json.loads(nsfw_storage_dict_cache[key])

    auto_delete_cache = await db.load_all_variables("AUTO_DELETE")
    for key in auto_delete_cache:
        auto_delete_cache[key] = json.loads(auto_delete_cache[key])


async def set_default(server_id: int):
    from database import db

    # setting the default values (called when joined in a  new server)
    await db.set_variable(server_id, "PREFIX", "-")
    await db.set_variable(server_id, "SEARCH_LIMIT", "50")
    await db.set_variable(server_id, "NSFW_ALLOWED", "false")
    await db.set_variable(server_id, "DELETE_AFTER", "0")
    await db.set_variable(server_id, "ACTIVITY_CHANNEL_ID", "0")
    await db.set_variable(server_id, "STORAGE", "{}")
    await db.set_variable(server_id, "NSFW_STORAGE", "{}")
    await db.set_variable(server_id, "AUTO_DELETE", "{}")

    print("✅Successfully set the default values for this server!")

async def remove_data(server_id: int):
    from database import db

    global prefix_cache, search_limit_cache, nsfw_allowed_cache, delete_after_cache
    global notify_channel_id_cache, storage_dict_cache, nsfw_storage_dict_cache
    global auto_delete_cache
    
    # removing the server's data from the local variables and dictionaries
    prefix_cache.pop(server_id)
    search_limit_cache.pop(server_id)
    nsfw_allowed_cache.pop(server_id)
    delete_after_cache.pop(server_id)
    notify_channel_id_cache.pop(server_id)  
    nsfw_storage_dict_cache.pop(server_id)
    auto_delete_cache.pop(server_id)
    
    # removing the data from the database
    await db.delete_all_variables(server_id)

    print("✅Successfully removed the data from the database!")
