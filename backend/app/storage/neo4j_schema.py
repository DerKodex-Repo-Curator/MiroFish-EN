"""
Neo4j Schema — Cypher queries for index creation and schema management.

Called by Neo4jStorage._ensure_schema() to set up vector + fulltext indexes.
Vector dimensions are determined by the embedding model (768 for nomic, 1536 for text-embedding-3-small, etc.).
"""

# Constraints
CREATE_GRAPH_UUID_CONSTRAINT = """
CREATE CONSTRAINT graph_uuid IF NOT EXISTS
FOR (g:Graph) REQUIRE g.graph_id IS UNIQUE
"""

CREATE_ENTITY_UUID_CONSTRAINT = """
CREATE CONSTRAINT entity_uuid IF NOT EXISTS
FOR (n:Entity) REQUIRE n.uuid IS UNIQUE
"""

CREATE_EPISODE_UUID_CONSTRAINT = """
CREATE CONSTRAINT episode_uuid IF NOT EXISTS
FOR (ep:Episode) REQUIRE ep.uuid IS UNIQUE
"""

# Fulltext indexes (for BM25 keyword search) — dimension-independent
CREATE_ENTITY_FULLTEXT_INDEX = """
CREATE FULLTEXT INDEX entity_fulltext IF NOT EXISTS
FOR (n:Entity) ON EACH [n.name, n.summary]
"""

CREATE_FACT_FULLTEXT_INDEX = """
CREATE FULLTEXT INDEX fact_fulltext IF NOT EXISTS
FOR ()-[r:RELATION]-() ON EACH [r.fact, r.name]
"""


def get_vector_index_queries(dimensions: int) -> list:
    """Return vector index creation queries for the given dimensionality."""
    return [
        f"""
        CREATE VECTOR INDEX entity_embedding IF NOT EXISTS
        FOR (n:Entity) ON (n.embedding)
        OPTIONS {{indexConfig: {{
            `vector.dimensions`: {dimensions},
            `vector.similarity_function`: 'cosine'
        }}}}
        """,
        f"""
        CREATE VECTOR INDEX fact_embedding IF NOT EXISTS
        FOR ()-[r:RELATION]-() ON (r.fact_embedding)
        OPTIONS {{indexConfig: {{
            `vector.dimensions`: {dimensions},
            `vector.similarity_function`: 'cosine'
        }}}}
        """,
    ]


# Non-vector schema queries (always safe to run)
CONSTRAINT_QUERIES = [
    CREATE_GRAPH_UUID_CONSTRAINT,
    CREATE_ENTITY_UUID_CONSTRAINT,
    CREATE_EPISODE_UUID_CONSTRAINT,
]

FULLTEXT_QUERIES = [
    CREATE_ENTITY_FULLTEXT_INDEX,
    CREATE_FACT_FULLTEXT_INDEX,
]

# Legacy: ALL_SCHEMA_QUERIES with default 768 dims for backwards compat
ALL_SCHEMA_QUERIES = CONSTRAINT_QUERIES + get_vector_index_queries(768) + FULLTEXT_QUERIES


def get_all_schema_queries(dimensions: int) -> list:
    """Return all schema queries for a given embedding dimensionality."""
    return CONSTRAINT_QUERIES + get_vector_index_queries(dimensions) + FULLTEXT_QUERIES
