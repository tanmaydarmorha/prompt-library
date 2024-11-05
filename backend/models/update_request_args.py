from pydantic import BaseModel


class UpdateRequestArgs(BaseModel):
    id: str
    prompt: str
    promptTitle: str
    promptDescription: str
    updatedBy: str
