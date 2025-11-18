#!/usr/bin/env python3
"""
Conversation Messages Example for the Nebula Client SDK

This example demonstrates how to work with conversation messages using the
new get_conversation_messages method, which retrieves messages directly
from the conversations API for accurate chronological ordering.
"""

import os
from nebula import (
    NebulaClient,
    AsyncNebulaClient,
    NebulaException,
    NebulaClientException,
)
import asyncio


def sync_example():
    """Synchronous example of working with conversation messages"""

    # Initialize the client
    api_key = os.getenv("NEBULA_API_KEY")
    if not api_key:
        print("Please set the NEBULA_API_KEY environment variable")
        return

    try:
        client = Nebula(api_key=api_key)
        print("✅ Successfully initialized Nebula client")

        # Example 1: Create a cluster for our conversation
        print("\n📦 Creating a cluster for conversations...")
        cluster = client.create_cluster(
            name="Example Conversations",
            description="Cluster for testing conversation message retrieval",
        )
        print(f"✅ Created cluster: {cluster.name} (ID: {cluster.id})")

        # Example 2: Store conversation messages
        print("\n💬 Storing conversation messages...")

        # Create a conversation by storing the first message
        messages = [
            {
                "content": "Hello! How can I help you today?",
                "role": "assistant"
            },
            {
                "content": "I need help with my account settings",
                "role": "user"
            },
            {
                "content": "I'd be happy to help with your account settings. What specific issue are you experiencing?",
                "role": "assistant"
            },
            {
                "content": "I can't seem to update my profile picture",
                "role": "user"
            }
        ]

        # Store messages using store_memories (batches conversation messages)
        conversation_ids = client.store_memories([
            {
                "collection_id": cluster.id,
                "content": msg["content"],
                "role": msg["role"],
                "parent_id": None,  # First message creates new conversation
                "metadata": {
                    "conversation_type": "support",
                    "priority": "medium"
                }
            } for msg in messages
        ])

        conversation_id = conversation_ids[0]  # All messages go to same conversation
        print(f"✅ Stored {len(messages)} messages in conversation: {conversation_id}")

        # Example 3: Retrieve conversation messages
        print("\n🔍 Retrieving conversation messages...")

        retrieved_messages = client.get_conversation_messages(conversation_id)
        print(f"✅ Retrieved {len(retrieved_messages)} messages from conversation")

        # Display messages in chronological order
        for i, msg in enumerate(retrieved_messages, 1):
            role = msg.metadata.get("source_role", msg.metadata.get("role", "unknown"))
            content_preview = msg.content[:80] + "..." if len(msg.content) > 80 else msg.content
            print(f"  {i}. [{role.upper()}] {content_preview}")
            print(f"     ID: {msg.id}")
            print(f"     Created: {msg.created_at}")
            print()

        # Example 4: Add more messages to the conversation
        print("\n📝 Adding more messages to the conversation...")

        additional_messages = [
            {
                "content": "Let me guide you through updating your profile picture. First, go to your account settings.",
                "role": "assistant"
            },
            {
                "content": "Okay, I'm in my account settings now.",
                "role": "user"
            }
        ]

        # Store additional messages with the existing conversation_id
        more_ids = client.store_memories([
            {
                "collection_id": cluster.id,
                "content": msg["content"],
                "role": msg["role"],
                "parent_id": conversation_id,  # Append to existing conversation
                "metadata": {
                    "conversation_type": "support",
                    "step": "profile_update_guidance"
                }
            } for msg in additional_messages
        ])

        print(f"✅ Added {len(additional_messages)} more messages to conversation")

        # Example 5: Retrieve updated conversation
        print("\n🔄 Retrieving updated conversation...")
        updated_messages = client.get_conversation_messages(conversation_id)
        print(f"✅ Conversation now has {len(updated_messages)} total messages")

        # Show only the new messages
        for i, msg in enumerate(updated_messages[-len(additional_messages):], len(updated_messages)-len(additional_messages)+1):
            role = msg.metadata.get("source_role", msg.metadata.get("role", "unknown"))
            content_preview = msg.content[:80] + "..." if len(msg.content) > 80 else msg.content
            print(f"  {i}. [{role.upper()}] {content_preview}")

        print("\n🎉 Conversation messages example completed successfully!")

    except NebulaClientException as e:
        print(f"❌ Client error: {e}")
    except NebulaException as e:
        print(f"❌ API error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


async def async_example():
    """Asynchronous example of working with conversation messages"""

    # Initialize the async client
    api_key = os.getenv("NEBULA_API_KEY")
    if not api_key:
        print("Please set the NEBULA_API_KEY environment variable")
        return

    try:
        client = AsyncNebula(api_key=api_key)
        print("✅ Successfully initialized AsyncNebula client")

        # Example: Quick conversation retrieval demo
        print("\n⚡ Async conversation retrieval example...")

        # For this example, we'll assume you have a conversation ID from previous runs
        # In a real scenario, you'd store and retrieve the conversation ID
        example_conversation_id = "your-conversation-id-here"  # Replace with actual ID

        try:
            messages = await client.get_conversation_messages(example_conversation_id)
            print(f"✅ Retrieved {len(messages)} messages asynchronously")

            for i, msg in enumerate(messages[:3], 1):  # Show first 3 messages
                role = msg.metadata.get("source_role", msg.metadata.get("role", "unknown"))
                content_preview = msg.content[:60] + "..." if len(msg.content) > 60 else msg.content
                print(f"  {i}. [{role.upper()}] {content_preview}")

        except Exception as e:
            print(f"ℹ️  Note: Replace 'your-conversation-id-here' with an actual conversation ID to test async retrieval")
            print(f"    Error: {e}")

        print("\n🎉 Async conversation messages example completed!")

    except NebulaClientException as e:
        print(f"❌ Client error: {e}")
    except NebulaException as e:
        print(f"❌ API error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def main():
    """Main function - run both sync and async examples"""

    print("🚀 Nebula Client SDK - Conversation Messages Examples")
    print("=" * 55)

    print("\n📋 SYNCHRONOUS EXAMPLE:")
    print("-" * 25)
    sync_example()

    print("\n\n📋 ASYNCHRONOUS EXAMPLE:")
    print("-" * 27)

    # Run async example
    asyncio.run(async_example())


if __name__ == "__main__":
    main()


