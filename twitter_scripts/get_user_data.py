import datetime
import json
import sys
import time
from time import strftime
import tweepy
from util import send_notification

INPUT_FILENAME = 'data/username_to_user_id.json'
OUTPUT_FILENAME = 'data/username_to_user_data.json'

config = open(sys.argv[1]).read().split()
consumer_key = config[0]
consumer_secret = config[1]
access_token = config[2]
access_token_secret = config[3]

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)

usernames = json.load(open(INPUT_FILENAME)).keys()
username_to_user_data = json.load(open(OUTPUT_FILENAME))
suspended_users = set(json.load(open('data/suspended_users.json')))

def dump():
	json.dump(username_to_user_data, open(OUTPUT_FILENAME, 'w'))
	json.dump(list(suspended_users), open('data/suspended_users.json', 'w'))

def print_update():
	sys.stdout.write('\n' + str(len(username_to_user_data.keys())) + '/' + str(len(usernames)-len(suspended_users)) + ' collected')
	sys.stdout.flush()

def count_down(minutes=0, seconds=0):
	try:
		for i in xrange(minutes*60 + seconds,0,-1):
		    time.sleep(1)
		    min_str = str(i/60)
		    sec_str = str(i%60)
		    if (i/60 < 10):
		    	min_str = '0' + min_str
		    if (i%60 < 10):
		    	sec_str = '0' + sec_str
		    time_str = '\tTime until next request: ' + min_str+':'+sec_str + '\r'
		    sys.stdout.write(time_str + ' ')
		    sys.stdout.flush()
	except KeyboardInterrupt:
		print_update()
		dump()
		quit()

def get_user_data_from_username(username):
	user_data = api.get_user(username)._json
	count_down(seconds=6)
	update_str = str(len(username_to_user_data.keys())+1) + '/' + str(len(usernames)-len(suspended_users)) + ' collected: ' + username + ' ' + str(user_data['id'])
	remaining_secs = (len(usernames) - len(username_to_user_data.keys()) - len(suspended_users)) * 6
	comp_time = datetime.datetime.fromtimestamp(int(datetime.datetime.now().strftime('%s')) + remaining_secs)
	update_str = update_str + '; estimated completion time: ' + comp_time.strftime('%a %H:%M')
	print update_str
	return user_data

def run():
	try:
		for username in usernames:
			if not username in username_to_user_data.keys() and username not in suspended_users:
				try:
					username_to_user_data[username] = get_user_data_from_username(username)
				except tweepy.RateLimitError:
					dump()
					count_down(minutes=15)
				except tweepy.error.TweepError as ex:
					print username
					suspended_users.add(username)
		print_update()
		dump()
	except KeyboardInterrupt:
		print_update()
		dump()
		quit()

print len(usernames)
print len(suspended_users)
while len(username_to_user_data) < (len(usernames) - len(suspended_users)):
	try:
		run()
	except KeyboardInterrupt:
		print_update()
		dump()
		quit()


send_notification('All user data gathered.')
