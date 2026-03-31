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



