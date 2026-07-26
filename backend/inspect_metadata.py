from agents.nodes import _retriever

nodes = _retriever.retrieve("penguins")
for n in nodes:
    print(n.node.metadata)
    print("---")