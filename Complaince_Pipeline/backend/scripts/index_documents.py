import os
import glob
import logging
from dotenv import load_dotenv 
load_dotenv(override=True)

#Define document loader and splitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

#Import Azure components
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import AzureSearch

#setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("indexer")

def index_documents():
    '''Read the pdf's -> chunks ->vectorize -> upload to vector database(Azure Air Search)'''

    #define paths and look for data folder
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_folder = os.path.join(current_dir,"../../backend/data")