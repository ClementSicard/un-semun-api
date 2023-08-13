import os
from typing import Any, Dict, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from undl.client import UNDLClient

undl = UNDLClient(verbose=True)

app = FastAPI(
    title="United Nations SemUN's API",
    debug=os.getenv("SEMUN_DEBUG", False),
    description="""
    This is the API for the United Nations SemUN's project.

    It will be queried by the frontend to get the data from the backend.
    It consists of two parts:

    1. Proxying calls to the United Nations Digital Library API
    2. Querying the SemUN graph database to get the results
    """,
    version="1.0.0",
)


origins = [
    "http://localhost",
    "http://localhost:3000",  # Adjust this to your frontend's address and port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"Status": "Ok 🚀"}


@app.get("/search")
def search(q: str, searchId: Optional[str] = None) -> Dict[str, Any]:
    return undl.query(prompt=q, searchId=searchId)


@app.post("/graph")
def getResultsGraph():
    return {"Not implemented yet": "🚧"}
