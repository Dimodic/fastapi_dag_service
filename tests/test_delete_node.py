def test_delete_node_success(client):
    payload = {
        "nodes": [{"name": "A"}, {"name": "B"}, {"name": "C"}],
        "edges": [
            {"source": "A", "target": "B"},
            {"source": "A", "target": "C"},
            {"source": "B", "target": "C"}
        ]
    }
    graph_id = client.post("/api/graph/", json=payload).json()["id"]

    del_resp = client.delete(f"/api/graph/{graph_id}/node/B")
    assert del_resp.status_code == 204

    get_resp = client.get(f"/api/graph/{graph_id}/")
    data = get_resp.json()
    node_names = {node["name"] for node in data["nodes"]}
    assert "B" not in node_names and node_names == {"A", "C"}
    remaining_edges = {(e["source"], e["target"]) for e in data["edges"]}
    assert remaining_edges == {("A", "C")}

    adj = client.get(f"/api/graph/{graph_id}/adjacency_list").json()["adjacency_list"]
    assert set(adj.keys()) == {"A", "C"}
    assert adj["A"] == ["C"]
    assert adj["C"] == []

    rev = client.get(f"/api/graph/{graph_id}/reverse_adjacency_list").json()["adjacency_list"]
    assert set(rev.keys()) == {"A", "C"}
    assert rev["C"] == ["A"]
    assert rev["A"] == []

def test_delete_node_not_found(client):
    payload = {"nodes": [{"name": "Only"}], "edges": []}
    graph_id = client.post("/api/graph/", json=payload).json()["id"]
    resp = client.delete(f"/api/graph/{graph_id}/node/NonExistent")
    assert resp.status_code == 404
    error = resp.json()
    assert error["message"] == "Node not found"

def test_delete_node_graph_not_found(client):
    resp = client.delete("/api/graph/99999/node/AnyNode")
    assert resp.status_code == 404
    assert resp.json()["message"] == "Graph not found"
