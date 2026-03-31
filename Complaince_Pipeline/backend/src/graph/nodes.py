import json
import os
import logging
import re
from typing import Dict, Any, List, Optional

from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_community.vectorstores import AzureSearch
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

#In the "state.py" we have define the schema and we are going to import it
from backend.src.graph.state import VideoAuditState, ComplianceIssue

#import service 
from backend.src.services.video_indexer import VideoIndexerService

#configure the logger
logger = logging.getLogger("brand-guardian")
#logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logging.basicConfig(level=logging.INFO)

#Build the node
#Node 1 : Indexer
def index_video_node(state: VideoAuditState) -> Dict[str,Any]:
    """This is going to download the youtube video from the url.
       Then it uploads to the Azure video indexer 
       Finally it extracts the insights"""
    logger.info("Starting video indexing for URL: %s", state['video_url'])
    
    video_url = state.get("video_url")
    video_id_input = state.get("video_id","vid_demo")

    logger.info(f"---------[Node:Indexer] Processing : {video_url}")
    
    #download the video and save it locally under the name "temp_video.mp4"
    local_filename = "temp_audit_video.mp4"

    try: 
        vi_service = VideoIndexerService() 
        #download
        if "youtube.com" in video_url or "youtu.be" in video_url:
            logger.info("Downloading video from YouTube...")
            local_path = vi_service.download_youtube_video(video_url, output_path=local_filename)
        else:
            raise Exception("Please provide a valid YouTube URL.")
        #upload
        azure_video_id = vi_service.upload_video(local_path,video_name=video_id_input)
        logger.info(f"Upload Success and the video uploaded to Azure Video Indexer with ID: {azure_video_id}") 

        #cleanup
        if os.path.exists(local_path):
            os.remove(local_path)
            logger.info("Local video file removed after upload.")

        #wait
        raw_insights = vi_service.wait_for_processing(azure_video_id)

        #extract the data
        cleaned_data = vi_service.extract_data(raw_insights)
        logger.info("----------[Node:Indexer] data extraction completed successfully ----------.")
        return cleaned_data
    
    except Exception as e:
        logger.error("Error occurred while processing the video: %s", str(e))
        return {
            "errors": [str(e)],
            "final_status": "FAIL",
            "transcript": "",
            "ocr_text": [],
        }