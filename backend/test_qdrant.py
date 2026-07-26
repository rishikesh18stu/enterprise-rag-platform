from qdrant_client import QdrantClient

# Connect to the Qdrant instance running in Docker
client = QdrantClient(url="http://localhost:6333")

# Ask Qdrant what collections currently exist (should be empty)
collections = client.get_collections()
print("Connected successfully!")
print(collections)
