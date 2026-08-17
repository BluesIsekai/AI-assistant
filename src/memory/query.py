import re


def normalize_query(query: str) -> str:
    query = query.lower().strip()

    query = re.sub(
        r"\b(what|who|where|when|why|how|which|does|do|is|are|did|can)\b",
        " ",
        query,
    )

    query = re.sub(r"\b(the user|user|my|me|i)\b", " ", query)

    query = re.sub(r"[^a-z0-9\s]", " ", query)

    query = re.sub(r"\s+", " ", query).strip()

    return query