from pydantic import BaseModel
from datetime import datetime

class Prompt(BaseModel):
    id: str  # this field is for the MongoDB ObjectId
    prompt: str
    promptTitle: str
    promptDescription: str
    createdBy: str
    createdDateTime: datetime
    lastUpdatedBy: str
    lastUpdatedDateTime: datetime

    class Config:
        # To allow the use of ObjectId as a string
        arbitrary_types_allowed = True
