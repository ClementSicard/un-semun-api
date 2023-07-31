from typing import Any, Dict, List, Optional

from loguru import logger
from neo4j import EagerResult, GraphDatabase

from semun.types.record import Record
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
        records: List[Record],
        verbose: bool = False,
    ) -> None:
        """
        Return the documents and their relations based on their IDs.

        Parameters
        ----------
        `records` : `List[Record]`
            List of records to retrieve by ID
        `verbose` : `bool`, optional
            Controls the output verbose, by default `False`
        """
        query = """
        MATCH (n: Document)
        """

        for i, record in enumerate(records):
            query += f"""
            WHERE (d{record.id}: Document {{ id: {record.id} }})
            """
            if i != len(records) - 1:
                query += " OR\n"

        logger.debug(f"Query: {query}")
        summary: EagerResult = self.query(
            query=query,
            verbose=verbose,
            returnSummary=True,
        )
        if verbose:
            logger.success(
                f"Created {summary.counters.nodes_created} document(s) in"
                + f" {summary.result_available_after} ms."
            )

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
        except Exception as e:
            raise ConnectionError(
                f"Could not connect to the GraphDB at {self.URI} with auth {self.AUTH}"
            ) from e
