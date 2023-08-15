from typing import Any, Dict, List, Optional

from loguru import logger
from neo4j import EagerResult, GraphDatabase, Record

from semun.utils.graphdb import GraphDBConsts


class GraphDB:
    """
    GraphDB class is a class that handles the connection to a `neo4j` GraphDB.
    """

    _instance: Optional["GraphDB"] = None

    def __new__(cls) -> "GraphDB":
        """
        GraphDB constructor to ensure singleton pattern.

        Returns
        -------
        `GraphDB`
            The GraphDB instance
        """
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls)
            logger.success("Created a new GraphDB instance")

        return cls._instance

    def __init__(self) -> None:
        """
        GraphDB constructor
        """
        self.URI = GraphDBConsts.URI
        self.AUTH = GraphDBConsts.AUTH
        self.driver = GraphDatabase.driver(self.URI, auth=self.AUTH)

    def __del__(self) -> None:
        """
        GraphDB destructor: when object gets destroyed, close the driver
        """
        self.driver.close()

    def query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        returnSummary: bool = False,
        verbose: bool = False,
    ) -> List[Record] | EagerResult:
        """
        Execute a query on the GraphDB.

        Parameters
        ----------
        `query` : `str`
            Query to execute
        `params` : `Optional[Dict[str, Any]]`, optional
            Parameters of the query to be replaced, by default `None`
        `returnSummary` : `bool`, optional
            Return the summary or not. If `True`, returns the summary,
            otherwise returns the records, by default `False`
        `verbose` : `bool`, optional
            Controls the verbose of the output, by default `False`

        Returns
        -------
        `List[Record] | EagerResult`
            List of records returned by the query
        """
        querySummary = self.driver.execute_query(
            query_=query,
            parameters_=params,
        )

        records, summary, _ = querySummary

        if verbose:
            logger.debug(
                "The query `{query}` returned {records_count} records in {time} ms.".format(
                    query=summary.query,
                    records_count=len(records),
                    time=summary.result_available_after,
                )
            )

        return summary if returnSummary else records

    def getAllDocumentsByIDs(
        self,
        ids: List[str],
        verbose: bool = False,
    ) -> List[Record]:
        """
        Return the documents and their relations based on their IDs.

        Parameters
        ----------
        `records` : `List[Record]`
            List of records to retrieve by ID
        `verbose` : `bool`, optional
            Controls the output verbose, by default `False`
        """
        ids = [f'"{i}"' for i in ids]

        query = f"""
        WITH [{", ".join(ids)}] AS ids
        MATCH (n: Document)
        WHERE n.id IN ids
        OPTIONAL MATCH (n)-[r]-(m)
        RETURN n, r, m
        """

        logger.debug(f"Query: {query}")
        records: List[Record] = self.query(
            query=query,
            verbose=verbose,
        )
        logger.success(f"Found {len(records)} documents")

        return records

    def checkConnection(self) -> None:
        """
        Check if the connection to the GraphDB is successful.

        Raises
        ------
        `ConnectionError`
            If the connection is not successful
        """
        try:
            self.driver.verify_connectivity()
            logger.success("Successfully connected to the GraphDB")
        except Exception as e:
            raise ConnectionError(
                f"Could not connect to the GraphDB at {self.URI} with auth {self.AUTH}"
            ) from e

    @staticmethod
    def convertToGraphology(records: List[Record]) -> Dict[str, Any]:
        """
        Graphology library in Typescript expects a certain format to load the graph from.
        This function converts the records returned by the GraphDB to the format expected by Graphology.

        Here is the expected format by Graphology:

        ```json
        {
            "nodes": [
                {
                    "key": "...",
                    "attributes": {
                        "id": "...",
                        "title": "...",
                        ...
                    }
                }
            ],
            "edges": [
                {
                    "source": "...",
                    "target": "...",
                },
                ...
            ]
        }
        ```

        Parameters
        ----------
        `records` : `List[Record]`
            _description_

        Returns
        -------
        `Dict[str, Any]`
            _description_
        """
        nodesSet = {}
        edges = []

        for item in records:
            n = item["n"]
            m = item.get("m")
            r = item.get("r")

            nodesSet[n.get("id")] = {"key": n.get("id"), "attributes": dict(n)}

            if m:
                nodesSet[m.get("id")] = {"key": m.get("id"), "attributes": dict(m)}
                edgeData = {
                    "source": n.get("id"),
                    "target": m.get("id"),
                }
                if r:
                    edgeData["attributes"] = dict(r)

                edges.append(edgeData)

        nodes = list(nodesSet.values())
        logger.info([nodes[i]["attributes"]["id"] for i in range(len(nodes))])

        return {"nodes": nodes, "edges": edges}
