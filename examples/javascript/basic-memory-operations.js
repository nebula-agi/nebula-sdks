/**
 * Basic Memory Operations Example
 *
 * Demonstrates:
 * - Creating a collection
 * - Adding memories
 * - Searching memories
 * - Retrieving specific memories
 * - Deleting memories
 */

import { NebulaClient } from '@nebula-ai/sdk';

async function main() {
  // Initialize the client
  const client = new NebulaClient({
    apiKey: process.env.NEBULA_API_KEY
  });

  console.log('🚀 Starting Nebula SDK Basic Operations Example\n');

  // 1. Create a collection
  console.log('📁 Creating collection...');
  const collection = await client.createCollection({
    name: "Product Documentation",
    description: "Technical documentation for our products",
    metadata: {
      category: "docs",
      version: "1.0"
    }
  });
  console.log(`✅ Created collection: ${collection.name} (ID: ${collection.id})\n`);

  // 2. Add memories to the collection
  console.log('💾 Adding memories...');
  const memory1 = await client.addMemory({
    collectionId: collection.id,
    content: "Our API supports both REST and GraphQL interfaces for maximum flexibility.",
    metadata: {
      type: "api-info",
      section: "overview"
    }
  });
  console.log(`✅ Added memory 1: ${memory1.id}`);

  const memory2 = await client.addMemory({
    collectionId: collection.id,
    content: "Authentication requires an API key passed in the Authorization header.",
    metadata: {
      type: "api-info",
      section: "authentication"
    }
  });
  console.log(`✅ Added memory 2: ${memory2.id}\n`);

  // 3. Search for memories
  console.log('🔍 Searching for "authentication"...');
  const searchResults = await client.search({
    collectionId: collection.id,
    query: "how to authenticate",
    limit: 5
  });

  console.log(`Found ${searchResults.results.length} results:`);
  searchResults.results.forEach((result, idx) => {
    console.log(`  ${idx + 1}. [Score: ${result.score.toFixed(3)}] ${result.content.substring(0, 80)}...`);
  });
  console.log('');

  // 4. Retrieve a specific memory
  console.log('📖 Retrieving specific memory...');
  const retrievedMemory = await client.getMemory(memory1.id);
  console.log(`✅ Retrieved: ${retrievedMemory.content}\n`);

  // 5. Update a memory
  console.log('✏️  Updating memory...');
  const updatedMemory = await client.updateMemory({
    memoryId: memory1.id,
    content: "Our API supports REST, GraphQL, and WebSocket interfaces for maximum flexibility.",
    metadata: {
      type: "api-info",
      section: "overview",
      updated: true
    }
  });
  console.log(`✅ Updated memory: ${updatedMemory.content}\n`);

  // 6. List all memories in collection
  console.log('📋 Listing all memories...');
  const allMemories = await client.listMemories({
    collectionId: collection.id,
    limit: 10
  });
  console.log(`Total memories in collection: ${allMemories.results.length}\n`);

  // 7. Clean up - delete memories and collection
  console.log('🧹 Cleaning up...');
  await client.deleteMemory(memory1.id);
  await client.deleteMemory(memory2.id);
  await client.deleteCollection(collection.id);
  console.log('✅ Cleanup complete\n');

  console.log('✨ Example completed successfully!');
}

// Run the example
main().catch(error => {
  console.error('❌ Error:', error.message);
  process.exit(1);
});
