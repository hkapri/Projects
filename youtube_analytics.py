from googleapiclient.discovery import build
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from dateutil import parser, relativedelta
from isodate import parse_duration
import json


# Required details to call the youtube api.
youtube_api_key = '<Your youtube api key here>'
api_service_name = "youtube"
api_version = "v3"


def get_youtube_data(query):
    # This method will divide different phases of youtube scrapping for better understanding of code.
    channel_id = get_channel_id(query.strip())  # fetch the channelid of the youtube channel
    response_data = fetch_youtube_data(channel_id) # Fetch and prepare data
    return response_data if response_data else False


def get_channel_id(search_query):
    """ This method will fetch the channel id based from the upi based on name or username"""
    channel_id = ''
    try:
        if '@' in search_query:
            web_url = f"https://www.youtube.com/{search_query.replace(' ', '')}/about"
            response = requests.get(web_url)
            contents = BeautifulSoup(response.content, 'html.parser').contents
            if contents:
                channel_id = contents[1].find('meta', itemprop="channelId").attrs.get('content') if contents else False
        else:
            youtube = build(api_service_name, api_version, developerKey=youtube_api_key)
            request = youtube.search().list(
                part="snippet",
                maxResults=1,
                q=search_query
            )
            response = request.execute()
            if response.get('items'):
                channel_id = response.get('items')[0].get('id').get('channelId')
    except Exception as e:
        return False
    return channel_id

def fetch_youtube_data(channel_id):
    """ This method will fetch basics information about channel and the playlist"""
    # Get credentials and create an API client
    youtube = build(api_service_name, api_version, developerKey=youtube_api_key)

    # Get channel statistics
    request = youtube.channels().list(part="snippet,contentDetails,statistics", id=channel_id)
    response = request.execute()
    result = response.get('items', {})
    final_data = False
    if result:
        try:
            snippet = result[0].get('snippet', {})
            playlist_id = result[0].get('contentDetails', {}).get('relatedPlaylists', {}).get('uploads')
            statistics = result[0].get('statistics', {})
            final_data = {'country': snippet.get('country'), 'title': snippet.get('title', ''),
                          'description': snippet.get('description'), 'view_count': statistics.get('viewCount'),
                          'subscriber_count': statistics.get('subscriberCount'),
                          'video_count': statistics.get('videoCount'),
                          'banner': snippet.get('thumbnails', {}).get('medium', {}).get('url'),
                          'channel_id': channel_id}
            # Get Video ids
            all_video_ids = get_video_from_playlist(youtube, playlist_id)
            #  Get video information
            video_data = get_video_information(youtube, all_video_ids)
            # Analyse Data
            analysed_data = process_and_analyse_data(video_data)
            # Prepare Data to return
            final_data = format_data_present(analysed_data, final_data)
        except:
            return False

    return final_data


def get_video_from_playlist(youtube, playlist_id):
    """ This will fetch all the videos from the playlist"""
    request = youtube.playlistItems().list(part="snippet,contentDetails", playlistId=playlist_id, maxResults=50)
    response = request.execute()
    all_videos = [items.get('contentDetails', {}).get('videoId') for items in response.get('items', [])]
    next_page_token = response.get('nextPageToken', False)
    while next_page_token:
        request = youtube.playlistItems().list(part="snippet,contentDetails", playlistId=playlist_id,
                                               maxResults=50, pageToken=next_page_token)
        response = request.execute()
        next_data = [items.get('contentDetails', {}).get('videoId') for items in response.get('items', [])]
        all_videos.extend(next_data)
        next_page_token = response.get('nextPageToken', False)
    return all_videos


def get_video_information(youtube, all_video_ids):
    """ This method will fetch the information of all the videos """
    all_video_info = []
    for i in range(0, len(all_video_ids), 50):
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=','.join(all_video_ids[i:i + 50]),
        )
        response = request.execute()
        snippet_to_track = ['title', 'description', 'tags', 'publishedAt']
        statistics_to_track = ['viewCount', 'likeCount', 'favoriteCount', 'commentCount']
        content_to_track = ['duration', 'definition', 'caption']
        for item in response.get('items', []):
            video_info = dict()
            snippet = item.get('snippet', {})
            statistics = item.get('statistics', {})
            content_details = item.get('contentDetails', {})
            video_info.update({data: snippet.get(data) for data in snippet_to_track})
            video_info.update({data: statistics.get(data) for data in statistics_to_track})
            video_info.update({data: content_details.get(data) for data in content_to_track})
            all_video_info.append(video_info)
    video_data = pd.DataFrame(all_video_info)
    return video_data


def process_and_analyse_data(df):
    """ Data cleaning"""
    analysed_data = dict()
    neumeric_cols = ['viewCount', 'likeCount', 'favoriteCount', 'commentCount']
    df[neumeric_cols] = df[neumeric_cols].apply(pd.to_numeric, errors='coerce', axis=1)
    df['publishedAt'] = df['publishedAt'].apply(lambda l: parser.parse(l).date())
    df['publishDayName'] = df['publishedAt'].apply(lambda l: l.strftime('%A'))
    df['publishedAt'] = df['publishedAt'].apply(lambda l: l.strftime('%B-%d-%Y'))
    df['videoDuration'] = df['duration'].apply(lambda l: parse_duration(l)).astype('timedelta64[s]')
    df['tagCount'] = df['tags'].apply(lambda l: len(l) if l else 0)
    df['duration_hrs'] = df['videoDuration'].apply(lambda l: int(relativedelta.relativedelta(seconds=l).hours))
    df['duration_mins'] = df['videoDuration'].apply(lambda l: int(relativedelta.relativedelta(seconds=l).minutes))
    df['duration_sec'] = df['videoDuration'].apply(lambda l: int(relativedelta.relativedelta(seconds=l).seconds))
    all_tags = []
    for tags in df['tags']:
        all_tags.extend(tags) if tags else False
    unique_tags = set(all_tags)
    video_performance = df.sort_values(by=['viewCount'], ascending=False)[['title', 'publishedAt', 'publishDayName',
                                                                           'duration_hrs', 'duration_mins',
                                                                           'duration_sec', 'viewCount', 'likeCount']]
    video_length = df.sort_values(by=['videoDuration'], ascending=False)[['title', 'publishedAt', 'publishDayName',
                                                                           'duration_hrs', 'duration_mins',
                                                                           'duration_sec', 'viewCount', 'likeCount']]
    analysed_data.update({'bestPerformingVideos': video_performance.head().reset_index().to_json(),
                          'worstPerformingVideo': video_performance.tail().reset_index().to_json(),
                          'mostLikedVideo': df.sort_values(by=['likeCount'], ascending=False).
                         head(1)[['title', 'publishedAt', 'publishDayName', 'duration_hrs', 'duration_mins',
                                  'duration_sec', 'viewCount', 'likeCount']].reset_index().to_json(),
                          'longestVideo': video_length.head(1).reset_index().to_json(),
                          'shortestVideo': video_length.tail(1).reset_index().to_json(),
                          'averageVideoDuration': np.mean(df['videoDuration']),
                          'unique_tags': unique_tags,
                          'uploadSchedule': df['publishDayName'].value_counts().to_json()
                          })
    return analysed_data


def format_data_present(video_data, final_data):
    """ Convert the data to presentable form"""
    best_videos = json.loads(video_data.get('bestPerformingVideos'))
    worst_videos = json.loads(video_data.get('worstPerformingVideo'))
    liked_video = json.loads(video_data.get('mostLikedVideo'))
    best_data = format_video_data(best_videos, [['Best Performing Videos', 'Views', 'Likes']])
    worst_data = format_video_data(worst_videos, [['Worst Performing Videos', 'Views', 'Likes']])
    longest_video = json.loads(video_data.get('longestVideo'))
    shortest_video = json.loads(video_data.get('shortestVideo'))
    updload_schedule = json.loads(video_data.get('uploadSchedule'))
    schedule_data = [['Day', 'Videos']]
    schedule_data.extend([[key, data] for key, data in updload_schedule.items()])
    avg_hrs = int(relativedelta.relativedelta(seconds=video_data.get('averageVideoDuration')).hours)
    avg_mins = int(relativedelta.relativedelta(seconds=video_data.get('averageVideoDuration')).minutes)
    avg_secs = int(relativedelta.relativedelta(seconds=video_data.get('averageVideoDuration')).seconds)
    final_data.update({'best_videos': best_data,
                       'worst_videos': worst_data,
                       'longest_video': f"{longest_video.get('duration_hrs').get('0')}:"
                                        f"{longest_video.get('duration_mins').get('0')}:"
                                        f"{longest_video.get('duration_sec').get('0')}",
                       'shortest_video': f"{shortest_video.get('duration_hrs').get('0')}:"
                                         f"{shortest_video.get('duration_mins').get('0')}:"
                                         f"{1 if shortest_video.get('duration_sec').get('0') == 0 else shortest_video.get('duration_sec').get('0')}",
                       'average_video': f"{avg_hrs}:{avg_mins}:{1 if avg_secs == 0 else avg_secs}",
                       'upload_schedule': schedule_data,
                       'most_liked_video': {'title': liked_video.get('title', {}).get('0'),
                                            'views': liked_video.get('viewCount', {}).get('0'),
                                            'likes': liked_video.get('likeCount', {}).get('0'),
                                            'duration': f"{liked_video.get('duration_hrs').get('0')}:"
                                                        f"{liked_video.get('duration_mins').get('0')}:"
                                                        f"{liked_video.get('duration_sec').get('0')}",
                                            'published_on': f"{liked_video.get('publishDayName', {}).get('0')}-"
                                                            f"{liked_video.get('publishedAt', {}).get('0')}"}
                       })
    return final_data


def format_video_data(data, required_data):
    """ Get required data from the dataframe """
    data_to_fetch = ['title', 'viewCount', 'likeCount']
    for i in range(0, len(data.get('index'))):
        tmp_data = []
        for item in data_to_fetch:
            tmp_data.append(data.get(item, {}).get(str(i)))
        required_data.append(tmp_data)
    return required_data


if __name__ == '__main__':
    # User can use the name or the unique username of channel
    # name like My Channel
    # username like @mychannel
    channel = 'code Basics'
    print(get_youtube_data(channel))