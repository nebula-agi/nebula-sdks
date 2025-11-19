#!/usr/bin/env python3
"""
Basic usage example for the Nebula Client SDK

This example demonstrates the core functionality of the SDK:
- Creating clusters
- Storing memories
- Retrieving memories
- Chatting with agents
"""

import os

from nebula import (
    Nebula,
    NebulaClientException,
    NebulaException,
)


def main():
    """Main example function"""

    # Initialize the client
    # You can either pass the API key directly or set it as an environment variable
    api_key = os.getenv("NEBULA_API_KEY")
    if not api_key:
        print("Please set the NEBULA_API_KEY environment variable")
        return

    try:
        nebula = Nebula(api_key=api_key)
        print("✅ Successfully initialized Nebula client")

        # Example 1: Create a cluster
        print("\n📦 Creating a cluster...")
        cluster = nebula.create_cluster(
            name="Customer Support Knowledges",
            description="Cluster of customer support interactions and solutions",
            metadata={"category": "support", "owner": "support-team", "version": "1.0"},
        )
        print(f"✅ Created cluster: {cluster.name} (ID: {cluster.id})")

        # Example 2: Store memories
        print("\n💾 Storing memories...")

        memory1 = nebula.store(
            agent_id="customer-support-bot",
            content="Customer prefers email communication over phone calls",
            metadata={
                "user_id": "user-123",
                "preference_type": "communication",
                "source": "chat_interaction",
            },
            collection_id=cluster.id,
        )
        print(f"✅ Stored memory 1: {memory1.content[:50]}...")

        memory2 = nebula.store(
            agent_id="customer-support-bot",
            content="Customer reported login issues with mobile app on iOS",
            metadata={
                "user_id": "user-123",
                "issue_type": "login",
                "platform": "ios",
                "priority": "high",
            },
            collection_id=cluster.id,
        )
        print(f"✅ Stored memory 2: {memory2.content[:50]}...")

        memory3 = nebula.store(
            agent_id="customer-support-bot",
            content="Customer mentioned they work in healthcare and need HIPAA compliance",
            metadata={
                "user_id": "user-123",
                "industry": "healthcare",
                "compliance": "HIPAA",
                "priority": "critical",
            },
            collection_id=cluster.id,
        )
        print(f"✅ Stored memory 3: {memory3.content[:50]}...")

        # Example 3: Search memories
        print("\n🔍 Searching memories...")

        # Fast BFS search
        results = nebula.search(
            query="user-123 preferences and issues",
            collection_ids=[cluster.id],
            limit=5,
            search_settings={"search_mode": "fast"},
        )
        print(f"✅ Retrieved {len(results)} memories with fast search")
        for i, result in enumerate(results, 1):
            print(f"  {i}. Score: {result.score:.3f} - {result.content[:80]}...")

        # SuperBFS search (default)
        results = nebula.search(
            query="What are the key considerations for helping user-123?",
            collection_ids=[cluster.id],
            limit=3,
            search_settings={"search_mode": "super"},
        )
        print(f"\n✅ Retrieved {len(results)} memories with SuperBFS search")
        for i, result in enumerate(results, 1):
            print(f"  {i}. Score: {result.score:.3f} - {result.content[:80]}...")

        # Example 4: Chat with agent
        print("\n💬 Chatting with agent...")

        response = nebula.chat(
            agent_id="customer-support-bot",
            message="How should I approach helping user-123 with their current issue?",
            conversation_id="example-conversation",
            model="gpt-4",
            temperature=0.7,
            collection_id=cluster.id,
        )
        print(f"✅ Agent response: {response.content}")
        print(f"   Citations: {len(response.citations)} sources referenced")

        # Example 5: Search across cluster
        print("\n🔎 Searching across cluster...")

        search_results = nebula.search(
            query="healthcare compliance", collection_ids=[cluster.id], limit=3
        )
        print(f"✅ Found {len(search_results)} results")
        for i, result in enumerate(search_results, 1):
            print(f"  {i}. Score: {result.score:.3f} - {result.content[:80]}...")

        # Example 6: Get cluster information
        print("\n📊 Getting cluster information...")

        cluster_info = nebula.get_cluster(cluster.id)
        print(f"✅ Cluster: {cluster_info.name}")
        print(f"   Description: {cluster_info.description}")
        print(f"   Memory count: {cluster_info.memory_count}")
        print(f"   Created: {cluster_info.created_at}")

        # Example 7: List memories in cluster
        print("\n📋 Listing memories in cluster...")

        memories = nebula.get_cluster_memories(cluster.id, limit=10)
        print(f"✅ Found {len(memories)} memories in cluster")
        for i, memory in enumerate(memories, 1):
            print(f"  {i}. {memory.content[:60]}...")

        # Example 8: Health check
        print("\n🏥 Checking API health...")

        health = nebula.health_check()
        print(f"✅ API Status: {health.get('status', 'unknown')}")
        print(f"   Version: {health.get('version', 'unknown')}")

        print("\n🎉 All examples completed successfully!")

    except NebulaClientException as e:
        print(f"❌ Client error: {e}")
    except NebulaException as e:
        print(f"❌ API error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main()
