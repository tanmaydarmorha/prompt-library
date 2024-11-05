from pydantic import BaseModel


class CreateRequestArgs(BaseModel):
    prompt: str
    promptTitle: str
    promptDescription: str
    createdBy: str
