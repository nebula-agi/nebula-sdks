import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';

function createClient({ baseUrl, apiKey }) {
  // Detect if this is a Nebula API key (public.raw format)
  const isNebulaApiKey = (token) => {
    if (!token) return false;
    const parts = token.split('.');
    if (parts.length !== 2) return false;
    const [publicPart, rawPart] = parts;
    return publicPart.startsWith('key_') && rawPart && rawPart.length > 0;
  };

  const defaultHeaders = (includeContentType = true) => {
    const headers = {};

    if (isNebulaApiKey(apiKey)) {
      headers['X-API-Key'] = apiKey;
    } else {
      headers['Authorization'] = `Bearer ${apiKey}`;
    }

    if (includeContentType) {
      headers['Content-Type'] = 'application/json';
    }

    return headers;
  };
  const request = async (path, opts = {}) => {
    const res = await fetch(`${baseUrl.replace(/\/$/, '')}${path}`, {
      ...opts,
      headers: { ...defaultHeaders(opts.includeContentType), ...(opts.headers || {}) },
    });
    if (!res.ok) {
      const body = await res.text();
      throw new Error(`HTTP ${res.status}: ${body}`);
    }
    const ct = res.headers.get('content-type') || '';
    const responseData = ct.includes('application/json') ? await res.json() : await res.text();

    // Handle response.results unwrapping like the SDKs
    if (responseData && typeof responseData === 'object' && 'results' in responseData) {
      return responseData.results;
    }
    return responseData;
  };
  return {
    listClusters: async ({ limit = 100, offset = 0 } = {}) => request(`/v1/collections?limit=${limit}&offset=${offset}`),
    getCluster: async (id) => request(`/v1/collections/${id}`),
    getClusterByName: async (name) => request(`/v1/collections/name/${encodeURIComponent(name)}`),
    createCluster: async ({ name, description }) => request(`/v1/collections`, { method: 'POST', body: JSON.stringify({ name, description }) }),
    deleteCluster: async (id) => request(`/v1/collections/${id}`, { method: 'DELETE' }),
    search: async ({ query, clusterIds, limit = 10 }) => {
      // Simplified search settings - backend handles hybrid search automatically
      const searchSettings = {
        limit,
        filters: {
          collection_ids: { $overlap: Array.isArray(clusterIds) ? clusterIds : [clusterIds] },
        },
      };

      return request(`/v1/memories/search`, {
        method: 'POST',
        body: JSON.stringify({
          query,
          search_settings: searchSettings,
        })
      });
    },
    storeMemory: async ({ clusterId, content, role, parentId, metadata }) => {
      // Handle conversation mode
      if (role) {
        let conversationId = parentId;
        if (!conversationId) {
          const created = await request('/v1/conversations', { method: 'POST', body: JSON.stringify({}) });
          conversationId = created.id;
        }

        const payload = {
          messages: [{
            content: String(content || ''),
            role: role,
            metadata: metadata || {},
          }],
          collection_id: clusterId,
        };

        await request(`/v1/conversations/${conversationId}/messages`, {
          method: 'POST',
          body: JSON.stringify(payload)
        });
        return { id: conversationId };
      }

      // Handle memory mode (document upload)
      const contentText = String(content || '');
      const docMetadata = { ...metadata };
      docMetadata.memory_type = 'memory';

      const data = {
        metadata: JSON.stringify(docMetadata),
        ingestion_mode: 'fast',
        collection_ids: JSON.stringify([clusterId]),
        raw_text: contentText,
      };

      return request('/v1/memories', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams(data)
      });
    },
    listMemories: async ({ clusterIds, limit = 100, offset = 0 }) => {
      const ids = Array.isArray(clusterIds) ? clusterIds : [clusterIds];
      return request(`/v1/memories?limit=${limit}&offset=${offset}&collection_ids=${encodeURIComponent(JSON.stringify(ids))}`);
    },
    getMemory: async (id) => request(`/v1/memories/${id}`),
    deleteMemory: async (id) => request(`/v1/memories/${id}`, { method: 'DELETE' }),
    listConversations: async ({ limit = 100, offset = 0 } = {}) => request(`/v1/conversations?limit=${limit}&offset=${offset}`),
    createConversation: async () => request(`/v1/conversations`, { method: 'POST', body: JSON.stringify({}) }),
    addConversationMessage: async ({ conversationId, messages, clusterId }) => request(`/v1/conversations/${conversationId}/messages`, { method: 'POST', body: JSON.stringify({ messages, collection_id: clusterId }) }),
    healthCheck: async () => request('/health'),
    rag: async ({ query, model, stream = false }) => request(`/v1/retrieval/rag`, { method: 'POST', body: JSON.stringify({ query, rag_generation_config: { model, stream } }) }),
  };
}

export async function startServer({ baseUrl, apiKey, transport = 'sse' }) {
  const client = createClient({ baseUrl, apiKey });
  const server = new Server({ name: 'nebula-mcp-node' });

  server.tool('add_memory', async ({ cluster_id, content, role, parent_id, metadata }) => {
    const data = await client.storeMemory({
      clusterId: cluster_id,
      content,
      role,
      parentId: parent_id,
      metadata
    });
    return { content: [{ type: 'text', text: JSON.stringify(data) }] };
  });

  server.tool('search_memories', async ({ query, cluster_ids, limit }) => {
    const data = await client.search({ query, clusterIds: cluster_ids, limit });
    return { content: [{ type: 'text', text: JSON.stringify(data) }] };
  });


  let transportInstance;
  if (transport === 'stdio') {
    transportInstance = new StdioServerTransport();
  } else {
    transportInstance = new SSEServerTransport({ port: process.env.PORT ? Number(process.env.PORT) : 3956 });
  }
  await server.connect(transportInstance);
}


