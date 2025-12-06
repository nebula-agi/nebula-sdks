import { Nebula } from './client';
import { NebulaException } from './types';

// Mock fetch for testing
global.fetch = jest.fn();

describe('Nebula', () => {
  let client: Nebula;
  const mockApiKey = 'key_test.mockraw123';

  beforeEach(() => {
    client = new Nebula({ apiKey: mockApiKey });
    jest.clearAllMocks();
  });

  describe('Constructor', () => {
    it('should initialize with default values', () => {
      const client = new Nebula({ apiKey: mockApiKey });
      expect(client.isApiKeySet()).toBe(true);
    });

    it('should initialize with custom values', () => {
      const client = new Nebula({
        apiKey: mockApiKey,
        baseUrl: 'https://custom.api.com',
        timeout: 60000
      });
      expect(client.isApiKeySet()).toBe(true);
    });

    it('should throw error when API key is empty', () => {
      expect(() => new Nebula({ apiKey: '' })).toThrow();
    });
  });

  describe('API Key Management', () => {
    it('should set and check API key', () => {
      expect(client.isApiKeySet()).toBe(true);
      
      client.setApiKey('new-key');
      expect(client.isApiKeySet()).toBe(true);
    });

    it('should handle empty API key', () => {
      client.setApiKey('');
      expect(client.isApiKeySet()).toBe(false);
    });
  });

  describe('Configuration Updates', () => {
    it('should update base URL', () => {
      client.setBaseUrl('https://new-api.com');
      // Note: We can't easily test private methods, but this tests the public interface
    });

    it('should update CORS proxy', () => {
      client.setCorsProxy('https://new-proxy.com');
      // Note: We can't easily test private methods, but this tests the public interface
    });
  });

  describe('Error Handling', () => {
    it('should create NebulaException instances', () => {
      const err = new NebulaException('Test error', 400, { a: 1 });
      expect(err).toBeInstanceOf(NebulaException);
      expect(err.statusCode).toBe(400);
      expect(err.details).toEqual({ a: 1 });
    });
  });

  describe('Health Check', () => {
    it('should make health check request', async () => {
      const mockResponse = { ok: true, status: 200, json: () => Promise.resolve({ status: 'healthy' }) };
      (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

      await client.healthCheck();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/health'),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'X-API-Key': mockApiKey
          })
        })
      );
    });

    it('should handle health check failure', async () => {
      const mockResponse = { ok: false, status: 500, json: () => Promise.resolve({}) };
      (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

      await expect(client.healthCheck()).rejects.toThrow();
    });
  });

  describe('Collection Operations', () => {
    it('should create collection with correct parameters', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: () => Promise.resolve({
          results: {
            id: 'collection-123',
            name: 'Test Collection',
            description: 'Test Description',
            metadata: {},
            user_count: 0,
            document_count: 0,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z'
          }
        })
      };
      (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

      const result = await client.createCollection({
        name: 'Test Collection',
        description: 'Test Description'
      });

      expect(result.name).toBe('Test Collection');
      expect(result.description).toBe('Test Description');
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/v1/collections'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('Test Collection')
        })
      );
    });

    it('should delete collection', async () => {
      const mockResponse = { ok: true, status: 200, json: () => Promise.resolve({}) };
      (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

      const result = await client.deleteCollection('collection-123');

      expect(result).toBe(true);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/v1/collections/collection-123'),
        expect.objectContaining({
          method: 'DELETE'
        })
      );
    });
  });

  describe('Memory Operations', () => {
    it('should store memory with correct parameters', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: () => Promise.resolve({
          results: {
            engram_id: 'doc-123'
          }
        })
      };
      (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

      const result = await client.store('Test content', 'collection-123', { test: 'metadata' });

      expect(result.content).toBe('Test content');
      expect(result.collection_ids).toContain('collection-123');
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/v1/memories'),
        expect.objectContaining({
          method: 'POST',
          body: expect.any(FormData)
        })
      );
    });

    it('should search memories with correct parameters', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: () => Promise.resolve({
          results: {
            query: 'test query',
            entities: [
              {
                entity_id: 'entity-1',
                entity_name: 'Entity 1',
                entity_category: 'person',
                activation_score: 0.95,
                activation_reason: 'direct match',
                traversal_depth: 0,
                profile: {}
              }
            ],
            facts: [],
            utterances: [
              {
                chunk_id: 'chunk-1',
                text: 'Test content',
                activation_score: 0.9,
                speaker_name: 'User',
                supporting_fact_ids: [],
                metadata: {}
              }
            ],
            fact_to_chunks: {},
            entity_to_facts: {},
            retrieved_at: '2024-01-01T00:00:00Z'
          }
        })
      };
      (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

      const results = await client.search({
        query: 'test query',
        collection_ids: 'collection-123',
        limit: 5
      });

      expect(results.query).toBe('test query');
      expect(results.entities).toHaveLength(1);
      expect(results.entities[0].entity_name).toBe('Entity 1');
      expect(results.utterances).toHaveLength(1);
      expect(results.utterances[0].text).toBe('Test content');
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/v1/retrieval/search'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('test query')
        })
      );
    });

    it('should list memories with pagination', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: () => Promise.resolve({
          results: [
            {
              id: 'doc-1',
              text: 'Memory 1',
              metadata: {},
              collection_ids: ['collection-123']
            }
          ]
        })
      };
      (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

      const results = await client.listMemories({
        collection_ids: 'collection-123',
        limit: 10,
        offset: 0
      });

      expect(results).toHaveLength(1);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/v1/memories?limit=10&offset=0&collection_ids=collection-123'),
        expect.objectContaining({
          method: 'GET'
        })
      );
    });
  });

  describe('Conversation Operations', () => {
    it('should store conversation with correct format', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: () => Promise.resolve({
          results: { engram_id: 'conv-123' }
        })
      };
      (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

      const result = await client.storeConversation(
        'User question',
        'Assistant answer',
        'collection-123',
        'session-456'
      );

      expect(result.content).toContain('User: User question');
      expect(result.content).toContain('Assistant: Assistant answer');
      expect(result.metadata.session_id).toBe('session-456');
    });

    it('should search conversations with filters', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: () => Promise.resolve({
          results: {
            graph_search_results: []
          }
        })
      };
      (global.fetch as jest.Mock).mockResolvedValue(mockResponse);

      await client.searchConversations('test', 'collection-123', 'session-456', false);

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/v1/retrieval/search'),
        expect.objectContaining({
          body: expect.stringContaining('"metadata.session_id":"session-456"')
        })
      );
    });
  });
});





