import os
import base64
import json
import sys

import googleapiclient.discovery
import googleapiclient.errors
import google.oauth2.credentials

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow


SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"


def write_refreshed_token(creds):
    output_file = os.environ.get("TOKEN_JSON_OUT_FILE")

    if not output_file:
        return

    token_json = creds.to_json()
    token_base64 = base64.b64encode(token_json.encode("utf-8")).decode("utf-8")

    with open(output_file, "w", encoding="utf-8") as token_file:
        token_file.write(token_base64)


def load_client_config():
    raw_client_config = os.environ.get("CLIENT_CONFIG_JSON")

    if not raw_client_config:
        raise RuntimeError("CLIENT_CONFIG_JSON is missing")

    return json.loads(raw_client_config)


def load_saved_credentials():
    base64_token = os.environ.get("TOKEN_JSON_BASE64")

    if not base64_token:
        return None

    token_json = base64.b64decode(base64_token).decode("utf-8")
    token_info = json.loads(token_json)

    return google.oauth2.credentials.Credentials.from_authorized_user_info(
        token_info,
        SCOPES,
    )


def create_credentials_locally(client_config):
    print("No valid saved token found")

    if os.environ.get("GITHUB_ACTIONS") == "true":
        raise RuntimeError(
            "TOKEN_JSON_BASE64 is missing or invalid. Generate it locally first, then save it as a GitHub secret"
        )

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=0)

    write_refreshed_token(creds)
    return creds


def get_authenticated_service():
    client_config = load_client_config()
    creds = load_saved_credentials()

    if creds and creds.valid:
        return googleapiclient.discovery.build(
            API_SERVICE_NAME,
            API_VERSION,
            credentials=creds,
        )

    if creds and creds.expired and creds.refresh_token:
        print("Refreshing YouTube token")
        creds.refresh(Request())
        write_refreshed_token(creds)

        return googleapiclient.discovery.build(
            API_SERVICE_NAME,
            API_VERSION,
            credentials=creds,
        )

    creds = create_credentials_locally(client_config)

    return googleapiclient.discovery.build(
        API_SERVICE_NAME,
        API_VERSION,
        credentials=creds,
    )


def update_video_title_and_description(youtube, video_id):
    response = youtube.videos().list(
        part="snippet,statistics",
        id=video_id,
    ).execute()

    if not response.get("items"):
        raise RuntimeError(f"No YouTube video found for id {video_id}")

    video = response["items"][0]
    snippet = video["snippet"]
    statistics = video["statistics"]

    view_count = statistics.get("viewCount", "0")
    like_count = statistics.get("likeCount", "0")

    print(f"Current view count: {view_count}")
    print(f"Current like count: {like_count}")

    new_title = f"This Video Has {view_count} Views"
    new_description = f"This Video Has {like_count} Likes"

    youtube.videos().update(
        part="snippet",
        body={
            "id": video_id,
            "snippet": {
                "title": new_title,
                "categoryId": snippet["categoryId"],
                "description": new_description,
            },
        },
    ).execute()

    print("Updated YouTube video title and description")


if __name__ == "__main__":
    try:
        youtube = get_authenticated_service()
        video_id = "nTwzzbuElJI"
        update_video_title_and_description(youtube, video_id)
    except Exception as error:
        print(f"Error: {error}")
        sys.exit(1)