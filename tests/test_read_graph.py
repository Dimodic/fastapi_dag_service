def test_read_graph_success(client):
    payload = {
        "nodes": [{"name": "A"}, {"name": "B"}],
        "edges": [{"source": "A", "target": "B"}]
    }
    create_resp = client.post("/api/graph/", json=payload)
    graph_id = create_resp.json()["id"]
    resp = client.get(f"/api/graph/{graph_id}/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == graph_id
    nodes = sorted([n["name"] for n in data["nodes"]])
    edges = [(e["source"], e["target"]) for e in data["edges"]]
    assert nodes == ["A", "B"]
    assert ("A", "B") in edges and len(edges) == 1

def test_read_graph_not_found(client):
    resp = client.get("/api/graph/9999/")
    assert resp.status_code == 404
    error = resp.json()
    assert error["message"] == "Graph not found"
