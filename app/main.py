from fastapi import FastAPI, Depends, HTTPException, Path, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import Base, engine, SessionLocal
import re

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="FastAPI", version="0.1.0", lifespan=lifespan)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, str):
        content = {"message": exc.detail}
    elif isinstance(exc.detail, dict) and "message" in exc.detail:
        content = {"message": exc.detail["message"]}
    else:
        content = {"message": exc.detail}
    return JSONResponse(status_code=exc.status_code, content=content)


def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def detect_cycle(nodes: list, edges: list) -> bool:
    graph_adj = {name: [] for name in nodes}
    for (src, tgt) in edges:
        graph_adj[src].append(tgt)
    visited = set()
    in_stack = set()

    def dfs(node: str) -> bool:
        if node in in_stack:
            return True
        if node in visited:
            return False
        visited.add(node)
        in_stack.add(node)
        for nei in graph_adj.get(node, []):
            if dfs(nei):
                return True
        in_stack.remove(node)
        return False

    for n in nodes:
        if dfs(n):
            return True
    return False


from fastapi import APIRouter

router = APIRouter(prefix="/api/graph")


@router.post("/",
             summary="Create Graph",
             description="Ручка для создания графа, принимает граф в виде списка вершин и списка ребер.",
             response_model=schemas.GraphCreateResponse,
             status_code=201,
             responses={
                 400: {"model": schemas.ErrorResponse, "description": "Failed to add graph"}
             }
             )
def create_graph(graph: schemas.GraphCreate, db: Session = Depends(get_db)):
    node_names = [node.name for node in graph.nodes]
    edge_pairs = [(edge.source, edge.target) for edge in graph.edges]

    if len(node_names) != len(set(node_names)):
        seen = set()
        dup_name = None
        for name in node_names:
            if name in seen:
                dup_name = name
                break
            seen.add(name)
        raise HTTPException(status_code=400, detail=f"Duplicate node name '{dup_name}'")

    pattern = re.compile(r'^[A-Za-z0-9]{1,255}$')
    for name in node_names:
        if not pattern.match(name):
            raise HTTPException(status_code=400,
                                detail="Invalid node name. Names must be 1-255 characters long and use only Latin letters.")

    if len(edge_pairs) != len(set(edge_pairs)):
        seen_edges = set()
        dup_edge = None
        for e in edge_pairs:
            if e in seen_edges:
                dup_edge = e
                break
            seen_edges.add(e)
        if dup_edge:
            src, tgt = dup_edge
            raise HTTPException(status_code=400, detail=f"Duplicate edge from '{src}' to '{tgt}'")

    node_set = set(node_names)
    for (src, tgt) in edge_pairs:
        if src not in node_set or tgt not in node_set:
            raise HTTPException(status_code=400, detail="Edge references an undefined node.")

    for (src, tgt) in edge_pairs:
        if src == tgt:
            raise HTTPException(status_code=400, detail=f"Self-loop detected on node '{src}'")

    if detect_cycle(node_names, edge_pairs):
        raise HTTPException(status_code=400, detail="Graph contains a cycle and cannot be added.")

    new_graph = models.Graph()
    db.add(new_graph)
    db.flush()

    name_to_node = {}
    for name in node_names:
        node = models.Node(name=name, graph_id=new_graph.id)
        db.add(node)
        name_to_node[name] = node
    db.flush()

    for (src, tgt) in edge_pairs:
        source_node = name_to_node[src]
        target_node = name_to_node[tgt]
        edge = models.Edge(graph_id=new_graph.id, source_id=source_node.id, target_id=target_node.id)
        db.add(edge)

    return schemas.GraphCreateResponse(id=new_graph.id)


@router.get("/{graph_id}/",
            summary="Read Graph",
            description="Ручка для чтения графа в виде списка вершин и списка ребер.",
            response_model=schemas.GraphReadResponse,
            responses={
                404: {"model": schemas.ErrorResponse, "description": "Graph entity not found"}
            }
            )
def read_graph(graph_id: int = Path(..., title="Graph Id"), db: Session = Depends(get_db)):
    graph = db.get(models.Graph, graph_id)
    if graph is None:
        raise HTTPException(status_code=404, detail="Graph not found")

    nodes = db.query(models.Node).filter(models.Node.graph_id == graph_id).all()
    edges = db.query(models.Edge).filter(models.Edge.graph_id == graph_id).all()

    name_by_id = {node.id: node.name for node in nodes}
    node_list = [schemas.Node(name=node.name) for node in nodes]
    edge_list = [schemas.Edge(source=name_by_id[edge.source_id], target=name_by_id[edge.target_id]) for edge in edges]

    return schemas.GraphReadResponse(id=graph_id, nodes=node_list, edges=edge_list)


@router.get("/{graph_id}/adjacency_list",
            summary="Get Adjacency List",
            description="Ручка для чтения графа в виде списка смежности.\nСписок смежности представлен в виде пар ключ - значение, где\n- ключ - имя вершины графа,\n- значение - список имен всех смежных вершин (всех потомков ключа).",
            response_model=schemas.AdjacencyListResponse,
            responses={
                404: {"model": schemas.ErrorResponse, "description": "Graph entity not found"}
            }
            )
def get_adjacency_list(graph_id: int = Path(..., title="Graph Id"), db: Session = Depends(get_db)):
    graph = db.get(models.Graph, graph_id)
    if graph is None:
        raise HTTPException(status_code=404, detail="Graph not found")

    nodes = db.query(models.Node).filter(models.Node.graph_id == graph_id).all()
    edges = db.query(models.Edge).filter(models.Edge.graph_id == graph_id).all()

    name_by_id = {node.id: node.name for node in nodes}
    adjacency: dict[str, list[str]] = {node.name: [] for node in nodes}
    for edge in edges:
        src_name = name_by_id[edge.source_id]
        tgt_name = name_by_id[edge.target_id]
        adjacency[src_name].append(tgt_name)
    for neighbors in adjacency.values():
        neighbors.sort()
    return schemas.AdjacencyListResponse(adjacency_list=adjacency)


@router.get("/{graph_id}/reverse_adjacency_list",
            summary="Get Reverse Adjacency List",
            description="Ручка для чтения транспонированного графа в виде списка смежности.\nСписок смежности представлен в виде пар ключ - значение, где\n- ключ - имя вершины графа,\n- значение - список имен всех смежных вершин (всех предков ключа в исходном графе).",
            response_model=schemas.AdjacencyListResponse,
            responses={
                404: {"model": schemas.ErrorResponse, "description": "Graph entity not found"}
            }
            )
def get_reverse_adjacency_list(graph_id: int = Path(..., title="Graph Id"), db: Session = Depends(get_db)):
    graph = db.get(models.Graph, graph_id)
    if graph is None:
        raise HTTPException(status_code=404, detail="Graph not found")

    nodes = db.query(models.Node).filter(models.Node.graph_id == graph_id).all()
    edges = db.query(models.Edge).filter(models.Edge.graph_id == graph_id).all()

    name_by_id = {node.id: node.name for node in nodes}
    reverse_adj: dict[str, list[str]] = {node.name: [] for node in nodes}
    for edge in edges:
        src_name = name_by_id[edge.source_id]
        tgt_name = name_by_id[edge.target_id]
        reverse_adj[tgt_name].append(src_name)
    for neighbors in reverse_adj.values():
        neighbors.sort()
    return schemas.AdjacencyListResponse(adjacency_list=reverse_adj)


@router.delete("/{graph_id}/node/{node_name}",
               summary="Delete Node",
               description="Ручка для удаления вершины из графа по ее имени.",
               status_code=204,
               responses={
                   404: {"model": schemas.ErrorResponse, "description": "Graph entity not found"}
               }
               )
def delete_node(graph_id: int = Path(..., title="Graph Id"),
                node_name: str = Path(..., title="Node Name"),
                db: Session = Depends(get_db)):
    graph = db.get(models.Graph, graph_id)
    if graph is None:
        raise HTTPException(status_code=404, detail="Graph not found")
    node = db.query(models.Node).filter(models.Node.graph_id == graph_id, models.Node.name == node_name).one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    db.delete(node)
    return Response(status_code=204)


app.include_router(router)
