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