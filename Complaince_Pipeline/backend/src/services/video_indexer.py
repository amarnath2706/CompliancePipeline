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