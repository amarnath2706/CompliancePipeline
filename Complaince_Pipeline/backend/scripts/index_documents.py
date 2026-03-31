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

    #check the environment variables
    logger.info("="*60)
    logger.info("Checking environment variables...")
    logger.info(f"AZURE_OPENAI_ENDPOINT: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
    logger.info(f"AZURE_OPENAI_API_VERSION: {os.getenv('AZURE_OPENAI_API_VERSION')}")
    logger.info(f"Embedding Deployment: {os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT','text-embedding-3-small')}")
    logger.info(f"AZURE_SEARCH_ENDPOINT: {os.getenv('AZURE_SEARCH_ENDPOINT')}")
    logger.info(f"AZURE_SEARCH_INDEX_NAME: {os.getenv('AZURE_SEARCH_INDEX_NAME')}")
    logger.info("="*60)

    #Validate the required environment variables
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        #"AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME",
        "AZURE_SEARCH_ENDPOINT",
        "AZURE_SEARCH_API_KEY",
        "AZURE_SEARCH_INDEX_NAME"
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please check your .env file and ensure all the set the missing environment variables and try again.")
        return
    
    #initialize the embedding model
    try:
        logger.info("Initializing Azure OpenAI Embedding model...")
        embeddings = AzureOpenAIEmbeddings(
            azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT","text-embedding-3-small"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"), 
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION","2026-06-01"),   
        )
        logger.info("Azure OpenAI Embedding model initialized successfully.")

    except Exception as e:
        logger.error(f"Error initializing Azure OpenAI Embedding model: {str(e)}")
        logger.error("Please check your environment variables related to Azure OpenAI and try again.")      
        return
    
    #Initialize the vector database - Azure AI Search
    try:
        logger.info("Initializing Azure AI Search Vector store...")
        embeddings = AzureOpenAIEmbeddings(
            azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            azure_search_key=os.getenv("AZURE_SEARCH_API_KEY"),
            index_name = index_name,
            embedding_function = embeddings.embed_query,
        )
        logger.info(f"Azure AI Search Vector store initialized successfully for the index : {index_name}")

    except Exception as e:
        logger.error(f"Error initializing Azure AI Search: {str(e)}")
        logger.error("Please check your environment variables related to Azure AI Search and try again.")      
        return
    
    #find PDF files in the data folder
    pdf_files = glob.glob(os.path.join(data_folder, "*.pdf"))