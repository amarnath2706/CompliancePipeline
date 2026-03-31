import operator
from typing import Annotated, Any, Dict, List, Optional , TypedDict

#define the schema for a single complaince result
#Error report structure
class ComplianceIssue(TypedDict):
    category: str
    description: str
    severity: str
    timestamp: str
    details: Optional[str]

#define the global graph state
#This basically defines the state that gets passed around in the agentic workflow.
class VideoAuditState(TypedDict):
    """It defines the data schema for langgraph execution content
    Main container : It holds the all the information about the audit right from the initial URL to the final report."""

    #input parameters
    video_url : str
    video_id: str

    #ingestion and the extracted data
    local_file_path : Optional[str]
    video_metadata : Dict[str, Any] #example {'duration': 120, 'format': 'mp4', 'resolution': '1920x1080'}
    transcript : Optional[str] #fully extracted speech to text
    ocr_text : List[str]

    #Analysis output
    #It stores the list of all the violations found by AI
    complaince_result : Annotated[List[ComplianceIssue], operator.add]

    #final delivarables:
    final_status : str  # pass|fail
    final_report : str #markdown format

    #system observability
    #errors : API timeout, system level errors
    errors : Annotated[List[str], operator.add]