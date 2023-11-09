import os
import base64
import pickle
import json
import googleapiclient.discovery
import googleapiclient.errors
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

# Load the secret client info directly from CLIENT_CONFIG
def get_authenticated_service():
    creds = None

    # Load token from environment variable and decode from Base64
    base64_token = os.environ.get('TOKEN_PICKLE')
    token_pickle = base64.b64decode(base64_token)
    creds = pickle.loads(token_pickle)
    
    # Load client config from environment variable
    client_config = json.loads(os.environ.get('CLIENT_CONFIG_JSON'))

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing token...")
            creds.refresh(Request())
        else:
            print("No refresh token found, creating new token...")
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)

    return googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=creds)

# Get the current view count and update the title
def update_video_title_and_description(youtube, video_id):
    request = youtube.videos().list(
        part="snippet,statistics",
        id=video_id
    )
    response = request.execute()
    
    view_count = response['items'][0]['statistics']['viewCount']
    like_count = response['items'][0]['statistics']['likeCount']
    print(f"Current view count: {view_count}")
    print(f"Current like count: {like_count}")
    new_title = f"This Video Has {view_count} Views"
    new_description = f"This Video Has {like_count} Likes"
    
    # Update the video title
    request = youtube.videos().update(
        part="snippet",
        body={
            "id": video_id,
            "snippet": {
                "title": new_title,
                "categoryId": response['items'][0]['snippet']['categoryId'],
                "description": new_description
            }
        }
    )
    request.execute()
    
if __name__ == "__main__":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    youtube = get_authenticated_service()
    VIDEO_ID = "nTwzzbuElJI"  # Replace with your video ID
    update_video_title_and_description(youtube, VIDEO_ID)
