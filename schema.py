from pydantic import BaseModel, Field
from typing import List, Optional

class DisruptionEvent(BaseModel):
    event_id: str = Field(..., description="Unique ID for the disruption")
    impacted_node_id: str = Field(..., description="The specific supplier node that went offline")
    severity: str = Field(..., description="High, Medium, or Low")
    description: str = Field(..., description="Context of the failure (e.g., Port Strike)")

class DisruptionReport(BaseModel):
    events: List[DisruptionEvent] = Field(description="A list of multiple concurrent disruption events")

class AlternateRoute(BaseModel):
    original_path: List[str]
    new_path: List[str]
    estimated_delay_hours: int

class SupplyChainState(BaseModel):
    timestamp: str
    active_disruptions: List[DisruptionEvent] = []
    failed_nodes_cascade: List[str] = [] # The 'blast radius'
    active_reroutes: List[AlternateRoute] = []