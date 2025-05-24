def test_adjacency_and_reverse_lists(client):
    payload = {
        "nodes": [{"name": "A"}, {"name": "B"}, {"name": "C"}],
        "edges": [
            {"source": "A", "target": "B"},
            {"source": "A", "target": "C"},
            {"source": "B", "target": "C"}
        ]
    }
    graph_id = client.post("/api/graph/", json=payload).json()["id"]

    resp_adj = client.get(f"/api/graph/{graph_id}/adjacency_list")
    assert resp_adj.status_code == 200
    adj_data = resp_adj.json()["adjacency_list"]
    assert set(adj_data.keys()) == {"A", "B", "C"}
    assert sorted(adj_data["A"]) == ["B", "C"]
    assert adj_data["B"] == ["C"]
    assert adj_data["C"] == []

    resp_rev = client.get(f"/api/graph/{graph_id}/reverse_adjacency_list")
    assert resp_rev.status_code == 200
    rev_data = resp_rev.json()["adjacency_list"]
    assert set(rev_data.keys()) == {"A", "B", "C"}
    assert rev_data["A"] == []
    assert rev_data["B"] == ["A"]
    assert rev_data["C"] == ["A", "B"] or rev_data["C"] == ["B", "A"]
    assert rev_data["C"] == ["A", "B"]

def test_adjacency_list_graph_not_found(client):
    resp = client.get("/api/graph/12345/adjacency_list")
    assert resp.status_code == 404
    assert resp.json()["message"] == "Graph not found"

def test_reverse_adjacency_list_graph_not_found(client):
    resp = client.get("/api/graph/12345/reverse_adjacency_list")
    assert resp.status_code == 404
    assert resp.json()["message"] == "Graph not found"
