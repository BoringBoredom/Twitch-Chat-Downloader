import json, os, requests, time, argparse, webbrowser

current_version = 0.12
try:
    r = requests.get("https://api.github.com/repos/BoringBoredom/Twitch-Chat-Downloader/releases/latest")
    new_version = float(r.json()["tag_name"])
    if new_version > current_version:
        webbrowser.open("https://github.com/BoringBoredom/Twitch-Chat-Downloader/releases/latest")
except:
    pass

with open('credentials.json', 'r') as f:
    credentials = json.load(f)
client_id = credentials['client_id']
client_secret = credentials['client_secret']

session = requests.Session()
session.headers = {'Client-ID': client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
response = requests.post(f"https://id.twitch.tv/oauth2/token?client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials")
time.sleep(0.08)
data = response.json()
session.headers['Authorization'] = f"Bearer {data['access_token']}"

def seconds_to_24h(time):
    hours = time // 3600
    minutes = (time // 60) % 60
    seconds = time % 60
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def get_user_id(channel):
    response = session.get(f"https://api.twitch.tv/helix/users?login={channel}")
    time.sleep(0.08)
    data = response.json()
    user_id = data['data'][0]['id']
    return user_id

def get_video_data(user_id= None, video_count= None, video_id= None):
    if user_id is not None:
        response = session.get(f"https://api.twitch.tv/helix/videos?user_id={user_id}&type=archive&first={video_count}")
    else:
        response = session.get(f"https://api.twitch.tv/helix/videos?id={video_id}")
    time.sleep(0.08)
    data = response.json()
    video_data = []
    for video in data['data']:
        split = video['duration'].split('h')
        hours = split[0]
        split = split[1].split('m')
        minutes = split[0]
        seconds = split[1].split('s')[0]
        duration = int(seconds) + int(minutes) * 60 + int(hours) * 3600
        user_name = video['user_name']
        video_data.append([video['id'], duration, user_name])
    video_data.reverse()
    return video_data

def extract(file, data, video):
    for comment in data['comments']:
        seconds = int(comment['content_offset_seconds'])
        timestamp = seconds_to_24h(seconds)
        file.write(f"[{video[0]}] [{timestamp}] {comment['commenter']['display_name']}: {comment['message']['body']}\n")
    return seconds

def download_chat(video_data):
    queue = []
    finished = []
    for video in video_data:
        queue.append(video[0])
    if queue[0] == queue[-1]:
        file = open(f"{video_data[0][2]} {queue[0]}.txt", "w", errors= 'ignore')
    else:
        file = open(f"{video_data[0][2]} {queue[0]} to {queue[-1]}.txt", "w", errors= 'ignore')
    for video in video_data:
        video_id = video[0]
        cursor = 'content_offset_seconds=0'
        while cursor:
            response = session.get(f"https://api.twitch.tv/v5/videos/{video_id}/comments?{cursor}")
            time.sleep(0.08)
            data = response.json()
            timestamp = extract(file, data, video)
            os.system('cls')
            print(f"Queue:            {queue}\nFinished:         {finished}\n\nCurrent video:      {video[0]}   {round(timestamp / video[1] * 100)} %")
            if '_next' in data:
                cursor = f"cursor={data['_next']}"
            else:
                cursor = None
                file.write("\n\n")
        finished.append(queue[0])
        del queue[0]
    os.system('cls')
    print(f"Queue:            {queue}\nFinished:         {finished}")
    file.close()

parser = argparse.ArgumentParser()
parser.add_argument("-v", "--video_id", help= "Chatlogs of video to download. Parameter to be used on its own.")
parser.add_argument("-c", "--channel", help= "Twitch channel to download chatlogs from. If number of past VODs is not specified it defaults to the latest VOD only.")
parser.add_argument("-n", "--number", help= "Number of past VODs to download chatlogs from (max 100). Parameter to be used in combination with -c")
args = parser.parse_args()
if args.video_id:
    video_data = get_video_data(video_id= args.video_id)
    download_chat(video_data)
elif args.channel and args.number:
    user_id = get_user_id(args.channel)
    video_data = get_video_data(user_id, args.number)
    download_chat(video_data)
elif args.channel:
    user_id = get_user_id(args.channel)
    video_data = get_video_data(user_id, 1)
    download_chat(video_data)
elif args.number:
    print("No channel specified.")
else:
    print("No parameter specified.")