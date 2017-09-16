#!/usr/bin/python
import praw, time, os, sys, traceback, twitter, string

REDDIT_USER_AGENT = "hwswap-alert by /u/nl_eddie"

def main():
	api = twitter.Api(consumer_key=os.environ['TWITTER_CONSUM_KEY'],
                  consumer_secret=os.environ['TWITTER_CONSUM_SCRT'],
                  access_token_key=os.environ['TWITTER_TKN_KEY'],
                  access_token_secret=os.environ['TWITTER_TKN_SCRT'])
	reddit = praw.Reddit(client_id=os.environ['REDDIT_ID'], 
						 client_secret=os.environ['REDDIT_SECRET'], 
						 user_agent=REDDIT_USER_AGENT)
	hwswap = reddit.subreddit('hardwareswap')
	curr_time = int(time.time()) - 180
	new_posts = hwswap.new(limit=100)

	watch_lists = parse_watch_lists(os.environ['HOME']+'/hwswap-alert/watch_lists.txt')
	
	for post in new_posts:
		time_diff = curr_time - post.created_utc
		print time_diff, post.link_flair_text, post.title
		if time_diff > 300:
			break
		elif time_diff < 0:
			continue
		title = [post.title.lower()]
		selftext = post.selftext.lower().split()
		link_flair = post.link_flair_text.lower()[0]
		for watch_list in watch_lists:
			keywords, flair = watch_list
			if post.link_flair_text is None:
				raise Exception('None post flair type.')
			if link_flair in flair.lower():
				if all(word.lower() in title+selftext for word in keywords):
					if len(watch_list) == 2:
						dm_title = '[{}] '.format(post.link_flair_text) + ' '.join(keywords) + '\n'
						post_title = post.title + '\n'
						post_link = 'https://www.reddit.com' + post.permalink
						text = str(dm_title) + str(post_title) + str(post_link)
						api.PostDirectMessage(text, screen_name="nay_linn")
						break

def parse_watch_lists(filename):
	watch_lists = []
	with open(filename) as f:
		for line in f:
			line = line.strip()
			if not line.startswith('#') and line:
				watch_list = line.split("|")
				if len(watch_list) < 2 or len(watch_list) > 3:
					raise IOError('Watch list file syntax error')
				else:
					watch_list[0] = watch_list[0].split()
					watch_lists.append(watch_list)
	return watch_lists

if __name__ == '__main__':
	try:
		start_time = time.time()
		log_file = open(os.environ['HOME']+'/hwswap-alert/log.txt', 'a')
		log_file.write('['+time.strftime("%Y/%m/%d - %I:%M:%S %p", time.localtime(start_time) )+'] ')
		main()
	except:
		log_file.write('Error: ')
		traceback.print_exc(file=log_file)
	else:
		log_file.write('No Errors ')
	finally:	
		log_file.write('Took {0:.2f} sec to run.\n'.format(time.time()-start_time))
		log_file.close()
