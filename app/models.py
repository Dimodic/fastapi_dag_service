from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from app.database import Base

class Graph(Base):
    __tablename__ = "graphs"
    id = Column(Integer, primary_key=True)

class Node(Base):
    __tablename__ = "nodes"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    graph_id = Column(Integer, ForeignKey("graphs.id", ondelete="CASCADE"), nullable=False)
    __table_args__ = (UniqueConstraint("graph_id", "name", name="uq_node_graph_name"),)

class Edge(Base):
    __tablename__ = "edges"
    id = Column(Integer, primary_key=True)
    graph_id = Column(Integer, ForeignKey("graphs.id", ondelete="CASCADE"), nullable=False)
    source_id = Column(Integer, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(Integer, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False)
    __table_args__ = (UniqueConstraint("graph_id", "source_id", "target_id", name="uq_edge_graph_src_tgt"),)
