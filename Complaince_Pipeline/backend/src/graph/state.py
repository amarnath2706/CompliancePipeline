import operator
from typing import Annotated, Any, Dict, List, Optional , TypedDict

#define the schema for a single complaince result
class ComplianceResult(TypedDict):
    category: str
    description: str
    severity: str
    timestamp: str
    details: Optional[str]

#define the global graph state
class VideoAuditState(TypedDict):
    """It defines the data schema for langgraph execution content"""
    #input parameters
    video_url : str
    video_id: str

    #ingestion and the extracted data
    local_file_path : Optional[str]
    video_metadata : Dict[str, Any] #example {'duration': 120, 'format': 'mp4', 'resolution': '1920x1080'}
    transcript : Optional[str] #fully extracted speech to text
    ocr_text : List[str]