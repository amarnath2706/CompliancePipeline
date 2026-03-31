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
    if not pdf_files:
        logger.warning(f"No PDF files found in the data folder: {data_folder}. Please add some PDF files and try again.")
    logger.info(f"Found {len(pdf_files)} PDF files in the data folder. Starting the indexing process : {[os.path.basename(f) for f in pdf_files]}")


    all_splits = [] 

    #process each PDF file
    for pdf_path in pdf_files:
        try:
            logger.info(f"Processing file: {os.path.basename(pdf_path)}")
            #load the document
            loader = PyPDFLoader(pdf_path)
            raw_docs = loader.load()

            #split the document into chunks
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            splits = text_splitter.split_documents(raw_docs)
            for split in splits:
                #It stamps each chunk with the file name    
                split.metadata["source"] = os.path.basename(pdf_path) #add source metadata to each chunk
            all_splits.extend(splits)
            logger.info(f"File {os.path.basename(pdf_path)} processed successfully with {len(splits)} chunks created.")

        except Exception as e:
            logger.error(f"Error processing file {os.path.basename(pdf_path)}: {str(e)}")
            logger.error("Skipping this file and continuing with the next one.") 

    #upload the chunks to vector database (Azure AI Search)
        if all_splits:
            #logger.info(f"Total {len(all_splits)} chunks to be uploaded to Azure AI Search.")
            logger.info(f"Uploading {len(all_splits)} chunks to Azure AI Search Index '{index_name}'")
            try:
                #azure search accepts batches automatically via this method
                vector_store.add_documents(all_splits)
                logger.info("="*60)
                logger.info("Indexing completed successfully! and Knowledge base is ready for the auditing process.")
                logger.info(f"Total chunks indexed : {len(all_splits)}")
                logger.info("="*60) 
            except Exception as e:
                logger.error(f"Error uploading document chunks to Azure AI Search: {str(e)}")
                logger.error("Please check your Azure AI Search configuration and try again.")
        else:
            logger.warning("No document chunks were created from the PDF files. Please check the PDF files and try again.")

if __name__ == "__main__":
    index_documents()