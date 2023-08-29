import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from undl.client import UNDLClient

from semun.graphdb import GraphDB

undl = UNDLClient(verbose=True)
graphDbClient = GraphDB()

queryCache: Dict[str, Any] = {}
graphCache: Dict[str, Any] = {}


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
    on_startup=[graphDbClient.checkConnection],
)


origins = [
    "http://localhost",
    "http://localhost:3000",  # Adjust this to your frontend's address and port
    "http://un-semun-frontend.un-semun.orb.local/",
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
    if q in queryCache:
        logger.success(f"Using cached query results for '{q}'")
        return queryCache[q]

    result = undl.query(prompt=q, searchId=searchId)
    queryCache[q] = result

    return result


@app.get("/getIds")
def getIds(q: str) -> Dict[str, Any]:
    if q in queryCache:
        logger.success(f"Using cached query results for '{q}'")
        response = queryCache[q]
        ids = [rec["id"] for rec in response["records"]]

        return {
            "total": response["total"],
            "hits": ids,
        }
    logger.info(f"No cache for query '{q}'. Getting IDs from UNDL")
    response = undl.getAllRecordIds(prompt=q)
    queryCache[q] = response

    return response


@app.get("/graph")
def getResultsGraph(q: str) -> Dict[str, Any]:
    """
    This function first gets the IDs of the records corresponding to the query
    results, then queries the Neo4j instance to get the corresponding graph DB
    objects.

    Parameters
    ----------
    `q` : `str`
        The prompt string

    Returns
    -------
    `List[Dict[str, Any]]`
        The graph DB objects corresponding to the query results
    """
    if q in graphCache:
        logger.success(f"Using cached graph results for '{q}'")
        return graphCache[q]

    ids = getIds(q=q)
    docs = graphDbClient.getAllDocumentsByIDs(ids=ids["hits"])

    graphologyConverted = GraphDB.convertToGraphology(docs)
    graphCache[q] = graphologyConverted

    return graphologyConverted


def getResultsFromIDs(ids: List[str]) -> Dict[str, Any]:
    """
    This function first gets the IDs of the records corresponding to the query
    results, then queries the Neo4j instance to get the corresponding graph DB
    objects.

    Parameters
    ----------
    `ids` : `List[str]`
        The prompt string

    Returns
    -------
    `List[Dict[str, Any]]`
        The graph DB objects corresponding to the query results
    """
    docs = graphDbClient.getAllDocumentsByIDs(ids=ids)

    graphologyConverted = GraphDB.convertToGraphology(docs)

    return graphologyConverted


@app.get("/query")
def query(q: str) -> Dict[str, Any]:
    """
    Queries the UNDL and the graph DB, then returns the combined
    results as a single JSON object.

    Parameters
    ----------
    `q` : `str`
        The prompt string

    Returns
    -------
    `Dict[str, Any]`
        The combined results of the query
    """
    searchResults = search(q=q)

    ids = [rec["id"] for rec in searchResults["records"]]

    logger.debug(f"Length of IDs: {len(ids)}")

    if q in graphCache:
        logger.success(f"Using cached graph results for '{q}'")
        graph = graphCache[q]

    else:
        graph = getResultsFromIDs(ids=ids)
        graphCache[q] = graph

    searchResults["graph"] = graph

    return searchResults
