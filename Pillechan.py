import tweepy
import time
import os


# Get authentication data from the environment used #########################
CONSUMER_KEY = os.environ['CONSUMER_KEY']  
CONSUMER_SECRET = os.environ['CONSUMER_SECRET']
ACCESS_KEY = os.environ['ACCESS_KEY']
ACCESS_SECRET = os.environ['ACCESS_SECRET']

authorisation = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
authorisation.set_access_token(ACCESS_KEY, ACCESS_SECRET)

api = tweepy.API(authorisation)
############################################################################


def get_all_tweets(tweet):
    screen_name = tweet.user.screen_name
    lastTweetId = tweet.id
    #initialize a list to hold all the tweepy Tweets
    allTweets = []
    #make initial request for most recent tweets (200 is the maximum allowed count)
    new_tweets = api.user_timeline(screen_name = screen_name,count=200)
    allTweets.extend(new_tweets)
    #save the id of the oldest tweet less one
    oldest = allTweets[-1].id - 1
    #keep grabbing tweets until there are no tweets left to grab
    while len(new_tweets) > 0 and oldest >= lastTweetId:
        print(f"getting tweets before {oldest}")
        #all subsiquent requests use the max_id param to prevent duplicates
        new_tweets = api.user_timeline(screen_name = screen_name,count=200,max_id=oldest)
        #save most recent tweets
        allTweets.extend(new_tweets)
        #update the id of the oldest tweet less one
        oldest =allTweets[-1].id - 1
        print(f"...{len(allTweets)} tweets downloaded so far")
    outtweets = [tweet.id for tweet in allTweets]
    return outtweets

def get_tweets_after(tweetId):
    thread = []
    res = api.get_status(tweetId, tweet_mode='extended')
    allTillThread = get_all_tweets(res)
    thread.append(res)
    if allTillThread[-1] > res.id:
        print("Not able to retrieve so older tweets")
        return thread
    print("downloaded required tweets")
    startIndex = allTillThread.index(res.id)
    print("Finding useful tweets")
    quietLong = 0
    while startIndex!=0 and quietLong<25:
        nowIndex = startIndex-1
        nowTweet = api.get_status(allTillThread[nowIndex], tweet_mode='extended')
        if nowTweet.in_reply_to_status_id == thread[-1].id:
            quietLong = 0
            #print("Reached a useful tweet to be included in thread")
            thread.append(nowTweet)
        else:
            quietLong = quietLong + 1
        startIndex = nowIndex
    return thread

def get_tweets_before(tweetId):
    thread = []
    res = api.get_status(tweetId, tweet_mode='extended')
    while res.in_reply_to_status_id is not None:
        res = api.get_status(res.in_reply_to_status_id, tweet_mode='extended')
        thread.append(res)
    return thread[::-1]

def getAllTweetsInThread(tweetId):
    tweetsAll = []
    print("Getting all tweets before this tweet")
    tweetsAll = get_tweets_before(tweetId)
    print(len(tweetsAll))
    print("Getting all tweets after this tweet")
    tweetsAll.extend(get_tweets_after(tweetId))
    return tweetsAll

def printAllTweet(tweets):
    global direct_message
    direct_message = ''
    if len(tweets)>0:
        print("Thread Messages include:-")
        for tweetId in range(len(tweets)):
            print(str(tweetId+1)+". "+tweets[tweetId].full_text)
            #####################################################################
            direct_message += str(tweetId+1)+". "+tweets[tweetId].full_text + '\n\n'
            #####################################################################
            print("")

    else:
        print("No Tweet to print")

# This section just has basic functions for read and write

FILE_NAME = 'identity.txt'

################## RETRIEVES THE LAST SEEN ID ###################
def retrieve_last_seen_id(file_name):
    f_read = open(file_name, 'r')  # opens file in read mode
    last_seen_id = int(f_read.read().strip()) 
    f_read.close()
    return last_seen_id
######################################################

################### STORES LAST SEEN ID #######################
def store_last_seen_id(last_seen_id, file_name):
    f_write = open(file_name, 'w')
    f_write.write(str(last_seen_id))
    f_write.close()
    return
######################################################

######################################################
last_seen_id = 0

def handle_last_seen_id():   
    global last_seen_id
    last_seen_id = retrieve_last_seen_id(FILE_NAME)
    
    mentions = api.mentions_timeline(
                        last_seen_id,  
                        tweet_mode='extended')
    
    for mention in reversed(mentions):
        global direct_message
        if last_seen_id != mention.id:
            last_seen_id = mention.id
            store_last_seen_id(last_seen_id, FILE_NAME)
            allTweets = getAllTweetsInThread(last_seen_id)
            print("==============================================")
            printAllTweet(allTweets)
            print("==============================================")
            
            recipient_id = mention.user.id   # sending the direct message
            direct_message = api.send_direct_message(recipient_id, direct_message)
  

while True:
    try:
        handle_last_seen_id()
    except tweepy.error.RateLimitError:
        print("Rate exceeded. \n")
    time.sleep(15)
