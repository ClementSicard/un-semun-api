import os

from loguru import logger


class GraphDBConsts:
    """
    GraphDBConsts is a class that contains constants for the GraphDB handler.
    """

    url = os.getenv("GRAPHDB_URL", "neo4j.un-semun.orb.local")

    # GraphDB URI, from Docker compose environment
    URI = f"bolt://{url}:7687"

    logger.warning(f"GraphDB URI: {URI}")
    USER = None
    PASSWORD = None
    AUTH = (USER, PASSWORD)
