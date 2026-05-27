import random
import asyncpraw, asyncprawcore
import config

reddit = None

async def authenticate():
    global reddit

    # if already authenticated
    if reddit is not None:
        return True

    try:
        # authenticating with the api with the credentials
        reddit = asyncpraw.Reddit(
            client_id=config.CLIENT_ID,
            client_secret=config.CLIENT_SECRET,
            username=config.REDDIT_USERNAME,
            password=config.REDDIT_PASSWORD,
            user_agent="Pain au Chocolat (by u/Herr_Sakib)",
        )

        # verify authentication
        user = await reddit.user.me()
        print("✅Logged in as: ", user.name)
        return True
    except Exception as e:
        print(f"❌ Reddit authentication failed: {e}")
        reddit = None
        return False

# this class represents each submission
class Submission:
    def __init__(self, submission):
        self.url = submission.url
        self.title = submission.title
        self.author = str(submission.author) if submission.author else "[deleted]"
        self.is_nsfw = submission.over_18


# this class fetches data from reddit and returns to Submission
class Fetch:
    def __init__(self):
        global reddit
        
        if reddit is None:
            raise RuntimeError("Reddit not authenticated. Call authenticate() first. ")
        
        self.reddit = reddit

    async def get_submission(self, subreddit_name, server_id: int):
        # getting the subreddit
        subreddit = await self.reddit.subreddit(subreddit_name)
        # fetches the actual subreddit data
        try:
            await subreddit.load()
        except asyncprawcore.exceptions.NotFound:
            return f"❌ Subreddit r/{subreddit_name} not found"
        except asyncprawcore.exceptions.Forbidden:
            return f"❌ Access to r/{subreddit_name} is restricted"

        # returning error message for permission error
        if subreddit.over18 and not config.nsfw_allowed_cache[server_id]:
            return f"🔞 NSFW content is disabled. To enable itm type: `{config.prefix_cache[server_id]}set nsfw_allowed true`"

        submission_list = []
        try:
            # getting a random post from the subreddit
            async for submission in subreddit.new(limit=config.search_limit_cache[server_id]):
                # checking if the post is an image or gif and not stickied
                # these extra parentheses creates a tuple, basically we are supplying a tuple as argument
                if not submission.stickied and submission.url.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    submission_list.append(Submission(submission))
        except asyncprawcore.exceptions.Forbidden:
            return f"❌ Cannot fetch posts from r/{subreddit_name} (possibly quarantined)."
        except Exception as e:
            return f"❌ Error fetching posts: {e}"
        
        if not submission_list:
            return f"🖼️ No image/GIF posts found in r/{subreddit_name} (checked {config.search_limit_cache[server_id]} posts)."
        
        # returning a random submission from the list
        return random.choice(submission_list)
