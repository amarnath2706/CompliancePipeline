'''
Conncetor : It basically bridges the gap between our python coce and azure cloud(azure video indexer).
 '''

import os
import time
import logging
import requests
import yt_dlp
from azure.identity import DefaultAzureCredential

logger = logging.getLogger("video_indexer")

class VideoIndexerService:
    def __init__(self):
        self.account_id = os.getenv("AZURE_VI_ACCOUNT_ID")
        self.location = os.getenv("AZURE_VI_LOCATION")
        self.subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
        self.resource_group = os.getenv("AZURE_RESOURCE_GROUP")
        self.vi_name = os.getenv("AZURE_VI_NAME","project-brand-guardian-001") #check the name of the project in azure portal and update here
        self.credential = DefaultAzureCredential()

    #authentication method to get the access token 
    def get_access_token(self):
        '''
        Generates an ARM Access Token using Azure Identity's DefaultAzureCredential. This token is required for authenticating API requests to Azure Video Indexer.
        Without this we can't make a connection or communicate between python and azure video indexer service.
        '''
        try:
            logger.info("Authenticating with Azure to get access token...")
            token_object = self.credential.get_token("https://management.azure.com/.default")
            #access_token = token.token
            logger.info("Successfully obtained access token.")
            return token_object.token
        except Exception as e:
            logger.error(f"Error obtaining access token: {str(e)}")
            #raise Exception("Authentication failed. Please check your Azure credentials and try again.")
            raise

    #once the token is generated then we need to pass the token
    def get_account_token(self,arm_access_token):
        '''
        It exchages the ARM token for video indexer account team. so that we can integrate or work around with indexer.
        
        '''
        #try:
            #logger.info("Requesting account access token from Azure Video Indexer...")
        url = (
            f"https://management.azure.com/subscriptions/{self.subscription_id}"
            f"/resourceGroups/{self.resource_group}"
            f"/providers/Microsoft.VideoIndexer/accounts/{self.vi_name}"
            f"/generateAccessToken?api-version=2024-01-01"
        )
        headers = {"Authorization": f"Bearer {arm_access_token}"}
        payload = {"permissionType": "Contributor","scope": "Account"}
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"Failed to get the VI account token: {response.text}") 
        return response.json().get("accessToken")
    
    #Function to download the video from the given url and save it to local storage
    def download_youtube_video(self,url,output_path="temp_video.mp4"):
        '''
        It takes the video url and output path as input and downloads the video from the url and saves it to the output path.
        We are using yt-dlp library to download the video from youtube. 
        Basically it downloads the youtube video to the local file
        '''
        #try:
        logger.info(f"Downloading video (Youtube video) from URL: {url}")
        ydl_opts = {
            'format': 'best',
            'outtmpl': output_path, #output template, it will save the video with the name temp_video.mp4 in the current directory.
            'quiet': False,
            #'oveerwrites': True,
            'no_warnings': False,
            #Add these extra options to handle potential issues with certain videos
            'extractor-args': {'youtube': {'player_client': ['android','web']}},
            'http_headers': { 
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                
                }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            logger.info(f"Video downloaded successfully and saved to: {output_path}")
            return output_path
        except Exception as e:
            #logger.error(f"Error downloading video: {str(e)}")
            raise Exception(f"Failed to download video due to some error : {str(e)}. Please check the video URL and try again.")
        #except Exception as e:
            #logger.error(f"Error downloading video: {str(e)}")
        #raise Exception("Failed to download video. Please check the video URL and try again.")


    #Upload the video to azure video indexer
    def upload_video(self,video_path,video_name):
        arm_token = self.get_access_token()
        vi_token = self.get_account_token(arm_token)

        api_url = f"https://api.videoindexer.ai/{self.location}/Accounts/{self.account_id}/Videos"

        params = {
            "accessToken": vi_token,
            "name": video_name,
            "privacy": "Private",
            "indexingPreset": "Default",
            }
        logger.info(f"Uploading video : {video_path} to Azure Video Indexer: {video_name}")

        #open the file in binary mode and stream it on the azure. kind of opening the video and accessing it on the azure.
        with open(video_path,'rb') as video_file:
            #files = {'file': (video_name, video_file, 'video/mp4')}
            files = {'file' : video_file}
            response = requests.post(api_url, params=params, files=files)
        if response.status_code != 200:
            raise Exception(f"Failed to upload video in Azure: {response.text}")
        
    #wait for processing to upload the video
    def wait_for_processing(self,video_id):
        logger.info(f"Waiting for video ID {video_id} to be processed by Azure Video Indexer...")
        while True:
            arm_token = self.get_access_token()
            vi_token = self.get_account_token(arm_token)

            url = f"https://api.videoindexer.ai/{self.location}/Accounts/{self.account_id}/Videos"
            params = {"accessToken": vi_token}
            response = requests.get(url, params=params)
            data = response.json()

            state = data.get("state")
            if state == "Processed":
                return data
                logger.info(f"Video ID {video_id} has been processed successfully.")
                #break
            elif state == "Failed":
                raise Exception(f"Video ID {video_id} processing failed.")
            elif state == "Quarantined":
                raise Exception(f"Video ID {video_id} has been quarantined due to content policy violation.")
            logger.info(f"Status {state}......waiting for 30 seconds before checking again.")
            time.sleep(30)

    def extract_data(self,vi_json):
        '''
        It basically parses the JSON into our state format
        '''
        transcript_lines = []
        #it will take the entire json file and it will dig in to the json to find the transcript and it will extract the text from the transcript 
        # and it will store or append it in a list of transcript lines.
        #inshort - Massive json data gets created and we don't want all of that, we only want the text.
        for v in vi_json.get("videos",[]):
            for insights in v.get("insights",{}).get("transcript",[]):
                transcript_lines.append(insights.get("text",""))

        ocr_lines = [] 
        #stores the text that appears on the screen in the video. 
        #like if there is a news video and there is some text that appears on the screen then that will be captured in ocr lines.
        for v in vi_json.get("videos",[]):
            for insights in v.get("insights",{}).get("ocr",[]):
                ocr_lines.append(insights.get("text")) 
        return {
            "transcript": " ".join(transcript_lines),
            "ocr_text": ocr_lines,
            "video_metadata" : {
                "duration": vi_json.get("summarizedInsights",{}).get("duration"),
                #"platform": "YouTube"
                "platform": "youtube"
            }
        }        