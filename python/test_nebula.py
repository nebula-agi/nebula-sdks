#!/usr/bin/env python3
"""
Simple test file for Nebula functionality
Replace the API key and cluster IDs with your own values
"""

from nebula import Nebula

def main():
    # Replace with your API key
    api_key = "key_8dLIxbjdJJcayoNemQcYGA==.b7JUWoaRebqmlSnFZylEYmMInaOoIgiuL3vjView5A8="
    
    # Initialize client
    client = Nebula(api_key=api_key, base_url="http://localhost:7272")
    print("✅ Connected to Nebula!")
    
    # Replace with your cluster IDs
    tech_cluster = "b6b6267c-c7c6-4a23-9893-b1989020c129"
    science_cluster = "b32917e8-01d4-4b1d-a423-c717db2decd5"
    history_cluster = "4693c82f-ba96-4c05-b16c-faecc6fe5aaa"
    
    # Test 1: Search with cluster filter
    print("\n=== Test 1: Technology Cluster Search ===")
    results = client.search(
        query="programming",
        collection_id=tech_cluster,
        limit=9
    )
    
    print(f"Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result.metadata.get('title', 'No title')} (Cluster: {result.collection_id})")
    
    # Test 2: Search with filters parameter
    print("\n=== Test 2: Science Cluster Search (using filters) ===")
    results = client.search(
        query="physics",
        collection_id=science_cluster,
        limit=9
    )
    
    print(f"Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result.metadata.get('title', 'No title')} (Cluster: {result.collection_id})")
    
    # Test 3: Search without filter
    print("\n=== Test 3: Search All Clusters ===")
    results = client.search(
        query="important",
        limit=5
    )
    
    print(f"Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result.metadata.get('title', 'No title')} (Cluster: {result.collection_id})")

if __name__ == "__main__":
    main() 