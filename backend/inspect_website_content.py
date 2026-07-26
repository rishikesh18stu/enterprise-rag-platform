from agents.nodes import _docstore

for node_id, node in _docstore.docs.items():
    if node.metadata.get("url"):
        print(f"Node ID: {node_id}")
        print(f"Full text length: {len(node.text)} characters")
        print(f"Full text:\n{node.text}")
        print("=" * 60)