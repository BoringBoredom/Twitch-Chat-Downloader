import json, os, requests, time, argparse, webbrowser

current_version = 0.10
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

def format_time(time):
    hours = time // 3600
    minutes = (time - hours * 3600) // 60
    seconds = time - hours * 3600 - minutes * 60
    hours = str(hours)
    minutes = str(minutes)
    seconds = str(seconds)
    if len(hours) == 1:
        hours = '0' + hours
    if len(minutes) == 1:
        minutes = '0' + minutes
    if len(seconds) == 1:
        seconds = '0' + seconds
    return f"{hours}:{minutes}:{seconds}"

def get_user_id(channel):
    response = session.get(f"https://api.twitch.tv/helix/users?login={channel}")
    time.sleep(0.08)
    data = response.json()
    user_id = data['data'][0]['id']
    return user_id

def get_video_list(user_id, video_count):
    response = session.get(f"https://api.twitch.tv/helix/videos?user_id={user_id}&type=archive&first={video_count}")
    time.sleep(0.08)
    data = response.json()
    video_list = []
    for video in data['data']:
        video_list.append(video['id'])
    video_list.reverse()
    return video_list

def extract(file, data, video_id):
    for comment in data['comments']:
        timestamp = format_time(int(comment['content_offset_seconds']))
        file.write(f"[{video_id}] [{timestamp}] {comment['commenter']['display_name']}: {comment['message']['body']}\n")
    print(f"{timestamp} - {video_id}")

def download_chat(video_list, channel= ""):
    video_list_copy = video_list.copy()
    if channel != "":
        channel += " "
    if video_list[0] == video_list[-1]:
        file = open(f"{channel}{video_list[0]}.txt", "w", errors= 'ignore')
    else:
        file = open(f"{channel}{video_list[0]} to {video_list[-1]}.txt", "w", errors= 'ignore')
    print(f"Pending: {video_list_copy}")
    for video_id in video_list:
        response = session.get(f"https://api.twitch.tv/v5/videos/{video_id}/comments?content_offset_seconds=0")
        time.sleep(0.08)
        data = response.json()
        extract(file, data, video_id)
        cursor = None
        if '_next' in data:
            cursor = data['_next']
        while cursor:
            response = session.get(f"https://api.twitch.tv/v5/videos/{video_id}/comments?cursor={cursor}")
            time.sleep(0.08)
            data = response.json()
            extract(file, data, video_id)
            if '_next' in data:
                cursor = data['_next']
            else:
                cursor = None
                file.write("\n\n")
        del video_list_copy[0]
        print(f"Pending: {video_list_copy}")
    file.close()

parser = argparse.ArgumentParser()
parser.add_argument("-v", "--video_id", help= "Chatlogs of video to download. Parameter to be used on its own.")
parser.add_argument("-c", "--channel", help= "Twitch channel to download chatlogs from. If number of past VODs is not specified it defaults to the latest VOD only.")
parser.add_argument("-n", "--number", help= "Number of past VODs to download chatlogs from (max 100). Parameter to be used in combination with -c")
args = parser.parse_args()
if args.video_id:
    download_chat([args.video_id])
elif args.channel and args.number:
    user_id = get_user_id(args.channel)
    video_list = get_video_list(user_id, args.number)
    download_chat(video_list, args.channel)
elif args.channel:
    user_id = get_user_id(args.channel)
    video_list = get_video_list(user_id, 1)
    download_chat(video_list, args.channel)
elif args.number:
    print("No channel specified.")
else:
    print("No parameter specified.")