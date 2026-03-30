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