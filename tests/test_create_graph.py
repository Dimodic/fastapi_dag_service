def test_create_graph_success_minimal(client):
    payload = {"nodes": [{"name": "A"}], "edges": []}
    response = client.post("/api/graph/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    graph_id = data["id"]
    get_resp = client.get(f"/api/graph/{graph_id}/")
    assert get_resp.status_code == 200
    graph = get_resp.json()
    assert graph["id"] == graph_id
    assert graph["nodes"] == [{"name": "A"}]
    assert graph["edges"] == []

def test_create_graph_success_with_edges(client):
    payload = {
        "nodes": [{"name": "A"}, {"name": "B"}, {"name": "C"}],
        "edges": [
            {"source": "A", "target": "B"},
            {"source": "A", "target": "C"},
            {"source": "B", "target": "C"}
        ]
    }
    response = client.post("/api/graph/", json=payload)
    assert response.status_code == 201
    graph_id = response.json()["id"]
    get_resp = client.get(f"/api/graph/{graph_id}/")
    data = get_resp.json()
    node_names = sorted([node["name"] for node in data["nodes"]])
    assert node_names == ["A", "B", "C"]
    edge_set = {(edge["source"], edge["target"]) for edge in data["edges"]}
    assert edge_set == {("A","B"), ("A","C"), ("B","C")}

def test_create_graph_empty_graph(client):
    payload = {"nodes": [], "edges": []}
    response = client.post("/api/graph/", json=payload)
    assert response.status_code == 201
    graph_id = response.json()["id"]
    get_resp = client.get(f"/api/graph/{graph_id}/")
    data = get_resp.json()
    assert data["nodes"] == []
    assert data["edges"] == []

def test_create_graph_duplicate_nodes(client):
    payload = {
        "nodes": [{"name": "X"}, {"name": "X"}],
        "edges": []
    }
    response = client.post("/api/graph/", json=payload)
    assert response.status_code == 400
    error = response.json()
    assert "Duplicate node name" in error["message"]

def test_create_graph_duplicate_edges(client):
    payload = {
        "nodes": [{"name": "A"}, {"name": "B"}],
        "edges": [
            {"source": "A", "target": "B"},
            {"source": "A", "target": "B"}
        ]
    }
    response = client.post("/api/graph/", json=payload)
    assert response.status_code == 400
    error_msg = response.json()["message"]
    assert "Duplicate edge" in error_msg

def test_create_graph_unknown_node_in_edge(client):
    payload = {
        "nodes": [{"name": "A"}],
        "edges": [
            {"source": "A", "target": "B"}
        ]
    }
    response = client.post("/api/graph/", json=payload)
    assert response.status_code == 400
    error_msg = response.json()["message"]
    assert "undefined node" in error_msg.lower()

def test_create_graph_self_loop(client):
    payload = {
        "nodes": [{"name": "Node1"}],
        "edges": [
            {"source": "Node1", "target": "Node1"}
        ]
    }
    response = client.post("/api/graph/", json=payload)
    assert response.status_code == 400
    error_msg = response.json()["message"]
    assert "Self-loop" in error_msg or "cycle" in error_msg

def test_create_graph_cycle_detected(client):
    payload = {
        "nodes": [{"name": "A"}, {"name": "B"}],
        "edges": [
            {"source": "A", "target": "B"},
            {"source": "B", "target": "A"}
        ]
    }
    response = client.post("/api/graph/", json=payload)
    assert response.status_code == 400
    assert "cycle" in response.json()["message"].lower()

def test_create_graph_invalid_name_characters(client):
    payload = {
        "nodes": [{"name": "Имя"}],
        "edges": []
    }
    response = client.post("/api/graph/", json=payload)
    assert response.status_code == 400
    assert "Invalid node name" in response.json()["message"]

def test_create_graph_name_too_long(client):
    long_name = "A" * 256
    payload = {
        "nodes": [{"name": long_name}],
        "edges": []
    }
    response = client.post("/api/graph/", json=payload)
    assert response.status_code == 400
    assert "Invalid node name" in response.json()["message"]

def test_create_multiple_graphs_isolation(client):
    payload1 = {
        "nodes": [{"name": "X"}, {"name": "Y"}],
        "edges": [{"source": "X", "target": "Y"}]
    }
    resp1 = client.post("/api/graph/", json=payload1)
    assert resp1.status_code == 201
    id1 = resp1.json()["id"]
    payload2 = {
        "nodes": [{"name": "X"}, {"name": "Z"}],
        "edges": [{"source": "X", "target": "Z"}]
    }
    resp2 = client.post("/api/graph/", json=payload2)
    assert resp2.status_code == 201
    id2 = resp2.json()["id"]
    assert id1 != id2

    graph1 = client.get(f"/api/graph/{id1}/").json()
    graph2 = client.get(f"/api/graph/{id2}/").json()
    edges1 = {(e["source"], e["target"]) for e in graph1["edges"]}
    edges2 = {(e["source"], e["target"]) for e in graph2["edges"]}
    assert edges1 == {("X", "Y")}
    assert edges2 == {("X", "Z")}
    nodes1 = {n["name"] for n in graph1["nodes"]}
    nodes2 = {n["name"] for n in graph2["nodes"]}
    assert nodes1 == {"X", "Y"}
    assert nodes2 == {"X", "Z"}
