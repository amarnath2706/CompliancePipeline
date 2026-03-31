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
    

#Node 2: Compliance Checker or Auditor
def audio_content_node(state:VideoAuditState) -> Dict[str,Any]:
    """
    This node performs the "Retrieval augmented generation" to audit the content against the compliance requirements(brand video).
    """
    logger.info("----[Node:Auditor] querying knowledgebase and LLM")
    transcript = state.get("transcript","")
    if not transcript:
        logger.warning("No transcript available for auditing, So we are skipping the auditing process.")
        return {
            #"complaince_result": [],
            "final_status": "FAIL",
            "final_report": "No transcript available for auditing because the video processing failed. Please check the errors for more details.",
        }
    #initialize azure clients
    llm = AzureChatOpenAI(
        azure_deployment= os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION"),
        temperature = 0.0
    )

    embeddings = AzureOpenAIEmbeddings(
        azure_deployment="text-embedding-3-small",
        openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION"),
    )

    vector_store = AzureSearch(
        azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        azure_search_key=os.getenv("AZURE_SEARCH_API_KEY"), 
        index_name = os.getenv("AZURE_SEARCH_INDEX_NAME"),
        embedding_function=embeddings.embed_query 
    )