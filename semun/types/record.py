from pydantic import BaseModel


class Record(BaseModel):
    recordId: str
