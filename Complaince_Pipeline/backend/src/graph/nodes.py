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
#This function is responsible for coverting the video to text
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

    #RAG implementation
    ocr_text = state.get("ocr_text",[])
    query_text = f"{transcript} {', '.join(ocr_text)}"
    #perform similarity search on the vector database to fetch the relevant documents
    docs = vector_store.similarity_search(query_text, k=3)
    retrieved_rules = "\n\n",join([doc.page_content for doc in docs])

    #Define the system prompt
    system_prompt = f"""
        you are a senior brand compliance auditor.
        OFFICIAL REGULATORY RULES TO FOLLOW:
        {retrieved_rules}
        INSTRUCTIONS:
        1. Analyze the transcript and the OCR text below.
        2. Identify any vioalations of the rules.
        3. Return strictly JSON in the following format:
        {{
        "complaince_results":[
        {{
        "category": "Claim Validation",
        "severity": "CRITICAL",
        "description": "Explanation of the violation",
        }}
        ],
        "status" : "FAIL",
        "final_report":"Summary of findings..."
        }}
        If no violations are found, set "status" to "PASS" and "complaice_results" to []."""
    user_message = f"""
                  VIDEO_METADATA:{state.get('video_metadata',{})} 
                  TRANSCRIPT: {transcript}
                  ON-SCREEN TEXT(OCR): {ocr_text}
         """
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ])
        content = response.content
        #regular expression cleanup
        if "```" in content:
            content = re.search(r"```(?:json)?(.?)```",content,re.DOTALL).group(1)
        audit_data = json.loads(content.strip())
        return {
            "complaince_results" : audit_data.get("compiance_results",[]),
            "final_status" : audit_data.get("status","FAIL"),
            "final_report" : audit_data.get("final_report","No report generated.")
        }
    except Exception as e:
        logger.error(f"System Error in auditor node :{str(e)}")
        #logging the raw response
        logger.error(f"Raw LLM response : {response.content if 'response' in locals() else 'None'}")
        return {
            
            "final_status": "FAIL",
            "errors": [str(e)]
        }