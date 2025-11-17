import { NebulaClient } from '../src/index';

// Example: Basic memory management with Nebula SDK
async function basicExample() {
  // Initialize the SDK
  const client = new NebulaClient({
    apiKey: process.env.NEBULA_API_KEY || 'your-api-key-here',
    baseUrl: 'https://api.nebulacloud.app',
    timeout: 30000
  });

  try {
    console.log('🚀 Creating a new cluster...');
    
    // Create a new cluster
    const cluster = await client.createCollection({
      name: 'SDK Example Project',
      description: 'A demonstration of the Nebula JavaScript SDK capabilities'
    });
    
    console.log('✅ Collection created:', cluster.name, 'with ID:', cluster.id);

    // Store some sample memories using the new unified Memory model
    console.log('📝 Storing sample memories...');
    
    const memories = [
      {
        collection_id: cluster.id,
        content: 'JavaScript is a versatile programming language used for web development.',
        metadata: { category: 'programming', difficulty: 'beginner' }
      },
      {
        collection_id: cluster.id,
        content: 'TypeScript adds static typing to JavaScript, making it more robust.',
        metadata: { category: 'programming', difficulty: 'beginner' }
      },
      {
        collection_id: cluster.id,
        content: 'The Nebula SDK provides powerful memory and search capabilities.',
        metadata: { category: 'programming', difficulty: 'beginner' }
      },
      {
        collection_id: cluster.id,
        content: 'Vector databases enable semantic search across large text collections.',
        metadata: { category: 'programming', difficulty: 'beginner' }
      }
    ];

    for (const memory of memories) {
      const memoryId = await client.storeMemory(memory);
      console.log('💾 Stored memory:', memoryId);
    }

    // Search for memories using the new search API
    console.log('🔍 Searching for JavaScript-related memories...');
    const searchResults = await client.search({
      query: 'JavaScript',
      collection_ids: [cluster.id],
      limit: 5,
      filters: { 'metadata.category': 'programming' }
    });

    console.log('📊 Search results:');
    searchResults.forEach((result, index) => {
      console.log(`${index + 1}. Score: ${result.score.toFixed(3)}`);
      console.log(`   Content: ${result.content?.substring(0, 80)}...`);
      console.log(`   ID: ${result.id}`);
      console.log('');
    });

    // List all memories using the new API
    console.log('📋 Listing all memories...');
    const allMemories = await client.listMemories({
      collection_ids: [cluster.id],
      limit: 10,
      offset: 0
      // Optional: Filter by metadata (MongoDB-like operators: $eq, $ne, $in, $nin, $exists, $and, $or)
      // metadata_filters: { 'metadata.content_type': { $ne: 'conversation' } }
    });
    console.log(`Found ${allMemories.length} memories in the cluster`);

    // Clean up - delete the cluster
    console.log('🧹 Cleaning up - deleting cluster...');
    await client.deleteCollection(cluster.id);
    console.log('✅ Collection deleted successfully');

  } catch (error) {
    console.error('❌ Error occurred:', error);
    
    if (error instanceof Error) {
      console.error('Error message:', error.message);
      console.error('Error name:', error.name);
    }
  }
}

// Example: Conversation tracking with the new unified Memory model
async function conversationExample() {
  const client = new NebulaClient({
    apiKey: process.env.NEBULA_API_KEY || 'your-api-key-here'
  });

  try {
    // Create a cluster for conversations
    const cluster = await client.createCollection({
      name: 'Conversation Examples',
      description: 'Tracking AI conversations and responses'
    });

    console.log('💬 Storing conversation...');
    
    // Store conversation turns using the new unified Memory model
    const conversationMemories = [
      {
        collection_id: cluster.id,
        content: 'What is machine learning?',
        role: 'user',
        metadata: { topic: 'AI', difficulty: 'intermediate' }
      },
      {
        collection_id: cluster.id,
        content: 'Machine learning is a subset of artificial intelligence that enables computers to learn from data without being explicitly programmed. It focuses on developing algorithms that can access data and use it to learn for themselves.',
        role: 'assistant',
        metadata: { topic: 'AI', difficulty: 'intermediate' }
      },
      {
        collection_id: cluster.id,
        content: 'How does supervised learning work?',
        role: 'user',
        metadata: { topic: 'AI', subtopic: 'supervised-learning' }
      },
      {
        collection_id: cluster.id,
        content: 'Supervised learning works by training a model on labeled data. The model learns to map inputs to outputs based on example input-output pairs. Common algorithms include linear regression, decision trees, and neural networks.',
        role: 'assistant',
        metadata: { topic: 'AI', subtopic: 'supervised-learning' }
      }
    ];

    // Store all conversation memories at once
    const conversationIds = await client.storeMemories(conversationMemories);
    console.log('💬 Stored conversation with IDs:', conversationIds);

    // Search for related conversations
    console.log('🔍 Searching for AI-related conversations...');
    const conversations = await client.search({
      query: 'machine learning supervised',
      collection_ids: [cluster.id],
      limit: 5
    });

    console.log('📊 Found conversations:');
    conversations.forEach((conv, index) => {
      console.log(`${index + 1}. Score: ${conv.score.toFixed(3)}`);
      console.log(`   Content: ${conv.content?.substring(0, 100)}...`);
    });

    // Clean up
    await client.deleteCollection(cluster.id);
    console.log('✅ Conversation cluster cleaned up');

  } catch (error) {
    console.error('❌ Conversation example error:', error);
  }
}

// Example: Advanced search with graph results
async function advancedSearchExample() {
  const client = new NebulaClient({
    apiKey: process.env.NEBULA_API_KEY || 'your-api-key-here'
  });

  try {
    // Create a cluster for advanced search
    const cluster = await client.createCollection({
      name: 'Advanced Search Example',
      description: 'Demonstrating graph search capabilities'
    });

    // Store some knowledge graph data
    const knowledgeMemories = [
      {
        collection_id: cluster.id,
        content: 'Albert Einstein was a theoretical physicist who developed the theory of relativity.',
        metadata: { entity: 'Albert Einstein', type: 'person', field: 'physics' }
      },
      {
        collection_id: cluster.id,
        content: 'Theory of relativity describes the relationship between space and time.',
        metadata: { entity: 'Theory of Relativity', type: 'concept', field: 'physics' }
      },
      {
        collection_id: cluster.id,
        content: 'Physics is the natural science that studies matter and energy.',
        metadata: { entity: 'Physics', type: 'field', category: 'science' }
      }
    ];

    for (const memory of knowledgeMemories) {
      await client.storeMemory(memory);
    }

    // Perform advanced search that may return both chunk and graph results
    console.log('🔍 Performing advanced search...');
    const searchResults = await client.search({
      query: 'Einstein relativity physics',
      collection_ids: [cluster.id],
      limit: 10,
      searchSettings: {
        graph_settings: {
          enabled: true,
          bfs_enabled: true,
          bfs_max_depth: 2
        }
      }
    });

    console.log('📊 Advanced search results:');
    searchResults.forEach((result, index) => {
      console.log(`${index + 1}. Score: ${result.score.toFixed(3)}`);
      console.log(`   Type: ${result.source || 'chunk'}`);
      
      if (result.content) {
        console.log(`   Content: ${result.content.substring(0, 80)}...`);
      }
      
      if (result.graph_entity) {
        console.log(`   Entity: ${result.graph_entity.name} - ${result.graph_entity.description}`);
      }
      
      if (result.graph_relationship) {
        console.log(`   Relationship: ${result.graph_relationship.subject} ${result.graph_relationship.predicate} ${result.graph_relationship.object}`);
      }
      
      console.log('');
    });

    // Clean up
    await client.deleteCollection(cluster.id);
    console.log('✅ Advanced search cluster cleaned up');

  } catch (error) {
    console.error('❌ Advanced search example error:', error);
  }
}

// Run examples if this file is executed directly
if (require.main === module) {
  console.log('🌟 Nebula JavaScript SDK Examples\n');
  
  basicExample()
    .then(() => {
      console.log('\n🎉 Basic example completed!');
      return conversationExample();
    })
    .then(() => {
      console.log('\n🎉 Conversation example completed!');
      return advancedSearchExample();
    })
    .then(() => {
      console.log('\n🎉 Advanced search example completed!');
      console.log('\n✨ All examples completed successfully!');
    })
    .catch((error) => {
      console.error('\n💥 Examples failed:', error);
      process.exit(1);
    });
}

export { basicExample, conversationExample, advancedSearchExample };
