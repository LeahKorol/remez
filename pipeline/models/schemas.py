"""
Pydantic models for request/response schemas
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class PipelineRequest(BaseModel):
    """Request model for pipeline execution"""

    year_start: int = Field(
        ..., description="Starting year for analysis", ge=2000, le=2030
    )
    year_end: int = Field(..., description="Ending year for analysis", ge=2000, le=2030)
    quarter_start: int = Field(..., ge=1, le=4, description="Starting quarter (1-4)")
    quarter_end: int = Field(..., ge=1, le=4, description="Ending quarter (1-4)")
    query_id: Optional[int] = Field(None, description="Optional query ID")

    def model_post_init(self, __context) -> None:
        """Validate date ranges"""
        if self.year_start > self.year_end:
            raise ValueError("year_start cannot be greater than year_end")

        if self.year_start == self.year_end and self.quarter_start > self.quarter_end:
            raise ValueError(
                "quarter_start cannot be greater than quarter_end for the same year"
            )


class PipelineResponse(BaseModel):
    """Response model for pipeline execution"""

    task_id: str = Field(..., description="Unique ID for tracking the pipeline task")
    status: str = Field(..., description="Current status of the pipeline")
    started_at: str = Field(..., description="Timestamp when the pipeline started")


class PipelineStatus(BaseModel):
    """Model for pipeline status information"""

    task_id: str = Field(..., description="Unique ID for tracking the pipeline task")
    status: str = Field(..., description="Current status of the pipeline")
    started_at: str = Field(..., description="Timestamp when the pipeline started")
    completed_at: Optional[str] = Field(
        None, description="Timestamp when the pipeline completed"
    )
    results_file: Optional[str] = Field(
        None, description="Path to results file if available"
    )
    error: Optional[str] = Field(None, description="Error message if pipeline failed")


class PipelineList(BaseModel):
    """Model for listing all pipeline tasks"""

    tasks: List[PipelineStatus] = Field(..., description="List of all pipeline tasks")
    total_count: int = Field(..., description="Total number of tasks")


class HealthResponse(BaseModel):
    """Health check response model"""

    status: str = Field(..., description="Health status")
    api_version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="Current timestamp")
    environment: str = Field(..., description="Current environment")


class AvailableDataResponse(BaseModel):
    """Available data response model"""

    available_quarters: List[str] = Field(..., description="All available quarters")
    complete_quarters: List[str] = Field(..., description="Quarters with complete data")
    file_details: Dict = Field(..., description="Detailed file information")
    total_quarters: int = Field(..., description="Total number of quarters")


class ErrorResponse(BaseModel):
    """Error response model"""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: str = Field(..., description="Error timestamp")
