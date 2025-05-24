from pydantic import BaseModel, Field
from typing import List, Dict

class Node(BaseModel):
    name: str = Field(..., title="Name")

class Edge(BaseModel):
    source: str = Field(..., title="Source")
    target: str = Field(..., title="Target")

class GraphCreate(BaseModel):
    nodes: List[Node] = Field(..., title="Nodes")
    edges: List[Edge] = Field(..., title="Edges")

class GraphCreateResponse(BaseModel):
    id: int = Field(..., title="Id")

class GraphReadResponse(BaseModel):
    id: int = Field(..., title="Id")
    nodes: List[Node] = Field(..., title="Nodes")
    edges: List[Edge] = Field(..., title="Edges")

class AdjacencyListResponse(BaseModel):
    adjacency_list: Dict[str, List[str]] = Field(..., title="Adjacency List")

class ErrorResponse(BaseModel):
    message: str = Field(..., title="Message")
