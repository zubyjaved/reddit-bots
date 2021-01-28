import praw
import json
from fuzzywuzzy import fuzz
from datetime import datetime
import time

# Checks comment logs so bot doesn't reply to same comment.
def is_logged(filename, comment_id):
    with open(filename) as f:
        data = json.load(f)
    logs = data["logs"]
    for log in logs:
        if log["comment_id"] == comment_id:
            return True
    return False

# Writes reddit comment and bots response to given file.
def log_comment(filename, data, comment):
    with open(filename) as f:
        logs = json.load(f)
    temp = logs["logs"]
    obj = {
        "comment":comment.body,
        "reply":data["text"],
        "ratio":data["ratio"],
        "time":datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "season":data["season"],
        "episode":data["episode"],
        "comment_id":comment.id,
        "line_id":data["id"]
    }
    temp.append(obj)
    with open(filename, 'w') as f:
        json.dump(logs, f, indent=4)

# Function is called when bot replies to a comment.
# Increments the reply_count of line from given id.
def increm_reply_count(filename, id):
    with open(filename) as f:
        data = json.load(f)
    lines = data["lines"]
    for line in lines:
        if line["id"] == id:
            count = line["reply_count"] +1
            line["reply_count"] = count
            print(count)
            print(isinstance(count, str))
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
                return

# Given a reddit comment, returns the most identical line
#   that the character has responded to.
def get_best_match(comment, lines):
    highestRatio = 0
    bestLine = lines[0]
    for line in lines:
        text = line["line"]
        ratio = fuzz.ratio(comment, text)
        if ratio >= highestRatio:
            bestLine = line
            highestRatio = ratio
    return {
        "text":bestLine["response"]["text"],
        "ratio":highestRatio,
        "season":bestLine["season"],
        "episode":bestLine["episode"],
        "id":bestLine["id"]
    }

# Makes sure every few comments are unique.
# Ex. if unique_factor is set to 5, past 5 comments must be unique.
def is_unique_comment(filename, line_id):
    unique_factor = 5
    with open(filename) as f:
        data = json.load(f)
    logs = data["logs"]
    length = len(logs)
    index = len(logs)
    for i in range(index, length):
        if line_id == logs[i]["line_id"]:
            return False
    return True

def show_bot_output(comment, obj):
    print(comment)
    print(obj["text"])
    print(obj["ratio"])
    print()

def not_a_bot(author, bots):
    for bot in bots:
        if author == bot:
            return False
    return True   

# Checks stream of new comments and replies to 
# comments that match the minimum ratio specified.
def reply_comments(bot_name, lines_file, accepted_log, rejected_log):

    # Create instance of reddit account and subreddit.
    reddit = praw.Reddit(bot_name)
    # Open file of character's lines.
    with open(lines_file) as f:
        data = json.load(f)
    lines = data["lines"]
    # Check every new comment and tries to find the closest matching line
    # that the character has responded to.
    #
    # Every match returns a ratio.
    # If the min_ratio is over specified value, the bot will reply to the comment.
    min_ratio = 60
    min_rej_ratio = 50
    max_comments = 100
    for submission in reddit.subreddit("all").rising(limit=25):
        comments = list(submission.comments)
        for comment in comments:
            bots = ["dwight-schrute-bot", "MichaelGScottBot", "andy-bernard-bot"]
            min_comment_len = 20
            if (not_a_bot(comment.author, bots) and len(comment.body) >= min_comment_len):
                # Gets character's best matched reply to comment.
                obj = get_best_match(comment.body, lines)
                ratio = obj["ratio"]
                if ratio > 40: 
                    print("COMMENT " + comment.body + " , RATIO : " + str(ratio))
                # If ratio meets set minimum, log comment & reply in accepted.
                if ratio >= min_ratio:
                    log = accepted_log
                    if not is_logged(log, comment.id) and is_unique_comment(log, obj["id"]):
                        print("ACCEPTED")
                        log_comment(log, obj, comment)
                        comment.reply(obj["text"])
                        increm_reply_count(lines_file, obj["id"])
                        show_bot_output(comment.body, obj)
                # If ratio meets rejected minimum, log comment & reply in rejected. 
                elif ratio >= min_rej_ratio and not is_logged(rejected_log, comment.id):
                    print("REJECTED")
                    log_comment(rejected_log, obj, comment)
                    show_bot_output(comment.body, obj)

# Replies to comments & logs replies.
def run_bot(name, folder):
    print("RUNNING " + name)
    replies = folder + '/replies.json'
    accepted = folder + '/accepted_log.json'
    rejected = folder + '/rejected_log.json'
    reply_comments(name, replies, accepted, rejected)

def sleep_time(sleep_len):
    print("SLEEPING FOR " + str(sleep_len/60) + " MINUTES")
    time.sleep(sleep_len)

if __name__ == "__main__":
    sleep_len = 300
    while (True):
        run_bot('MichaelGScottBot', 'michael')
        sleep_time(sleep_len)
        run_bot('dwight-schrute-bot', 'dwight')
        sleep_time(sleep_len)
        # run_bot('andy-bernard-bot', 'andy')
