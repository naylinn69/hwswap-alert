#!/usr/bin/python
import string
import time
import os
import traceback
import praw
import twitter

# pylint: disable=W0311,C0330
REDDIT_USER_AGENT = "hwswap-alert by /u/nl_eddie"

def parse_watch_lists(filename):
    watch_lists = []
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if not line.startswith('#') and line:
                watch_list = line.split("|")
                if len(watch_list) != 3:
                    raise IOError('Watch list file syntax error')
                else:
                    # watch_list[0]: keyword
                    # watch_list[1]: exclude keyword
                    # watch_list[2]: flair
                    watch_list[0] = watch_list[0].split()
                    watch_list[1] = watch_list[1].split()
                    watch_lists.append(watch_list)
    return watch_lists

def check_for_keywords(post, watch_lists):
    replace_punctuation = string.maketrans(string.punctuation,
        ' '*len(string.punctuation))
    search_text = (post.title.lower()+post.selftext.lower()).encode(errors='ignore')
    search_text = search_text.translate(replace_punctuation).split()
    if post.link_flair_text is None:
        if '[W]' not in post.title.upper():
            raise Exception("Cannot parse post title for flair.\n" +
                post.title + "\n"+ post.permalink)
        have_words, want_words = post.title.upper().split('[W]')
        selling_keywords = ('paypal', 'local', 'cash')
        if any(word in want_words.lower() for word in selling_keywords):
            link_flair = 's'
        elif any(word in have_words.lower() for word in selling_keywords):
            link_flair = 'b'
        else:
            link_flair = 't'
    else:
        link_flair = post.link_flair_text.lower()[0]
    for watch_list in watch_lists:
        keywords, exclude, flair = watch_list
        if link_flair in flair.lower():
            if any(word.lower() in search_text for word in exclude):
                continue
            if all(word.lower() in search_text for word in keywords):
                return keywords


def send_dm(api, post, keywords):
    dm_title = 'Keywords for alert: ' + ' '.join(keywords) + '\n'
    post_title = post.title + '\n'
    post_link = 'https://www.reddit.com' + post.permalink
    dm = str(dm_title) + str(post_title) + str(post_link)
    api.PostDirectMessage(dm, screen_name="nay_linn")

def search_posts(posts, time_limit, watch_lists, twitter_api):
    for post in posts:
        time_diff = time.time() - post.created_utc
        print time_diff,
        print post.title.encode('ascii', 'ignore')
        if time_diff > time_limit:
            break
        elif time_diff < 0: # Invalid created time
            continue
        keywords = check_for_keywords(post, watch_lists)
        if keywords:
            send_dm(twitter_api, post, keywords)

def main():
    try:
        start_time = time.time()
        log_file = open(os.environ['HOME']+'/hwswap-alert/log.txt', 'a')
        log_file.write('['+time.strftime("%Y/%m/%d - %I:%M:%S %p",
            time.localtime(start_time))+'] ')
        twitter_api = twitter.Api(consumer_key=os.environ['TWITTER_CONSUM_KEY'],
            consumer_secret=os.environ['TWITTER_CONSUM_SCRT'],
            access_token_key=os.environ['TWITTER_TKN_KEY'],
            access_token_secret=os.environ['TWITTER_TKN_SCRT'])

        reddit = praw.Reddit(client_id=os.environ['REDDIT_ID'],
            client_secret=os.environ['REDDIT_SECRET'],
            user_agent=REDDIT_USER_AGENT)

        hwswap = reddit.subreddit('hardwareswap')
        new_posts = hwswap.new()
        watch_lists = parse_watch_lists(
            os.environ['HOME'] + '/hwswap-alert/watch_lists.txt')
        search_posts(new_posts, 300, watch_lists, twitter_api)
    except:
        log_file.write('Error: ')
        traceback.print_exc(file=log_file)
    else:
        log_file.write('No Errors ')
    finally:
        log_file.write('Took {0:.2f} sec to run.\n'.format(
            time.time()-start_time))
        log_file.close()

if __name__ == '__main__':
    main()
