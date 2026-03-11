// Main Client
export { Nebula } from './client';
export { Nebula as default } from './client';

// Content Helper (Legacy/Internal)
export { NebulaContent } from './content';

// Import Types to Merge/Re-export
import { NebulaContent } from './content';
import { Memory as MemoryType } from './types';

// 1. Export Memory Factory Function (Value) - Acts like Python's class constructor
// Using Object.assign pattern to avoid @typescript-eslint/no-namespace error

type MemoryFactory = {
    (data: MemoryType): MemoryType;
    File: typeof NebulaContent.fromFile;
    fromFile: (
        filePath: string,
        collection_id: string,
        metadata?: Record<string, unknown>,
        role?: string
    ) => Promise<MemoryType>;
};

const MemoryBase = (data: MemoryType): MemoryType => data;

export const Memory: MemoryFactory = Object.assign(MemoryBase, {
    /**
     * Helper to create a file content part from a file path.
     * Alias for NebulaContent.fromFile().
     */
    File: NebulaContent.fromFile,

    /**
     * Helper to create a complete Memory object from a single file.
     */
    async fromFile(
        filePath: string,
        collection_id: string,
        metadata?: Record<string, unknown>,
        role?: string
    ): Promise<MemoryType> {
        const path = await import('path');
        const filename = path.basename(filePath);
        return {
            collection_id,
            content: [await NebulaContent.fromFile(filePath)],
            metadata: { filename, ...metadata },
            role
        };
    }
});

// 3. Export Memory Interface (Type) - Merged with Value
export type Memory = MemoryType;

// 4. Re-export all other types explicitly (excluding Memory to avoid conflict)
export {
    GraphSearchResultType,
    Chunk,
    StructuredChunk,
    MemoryResponse,
    TextContentPart,
    FileContentPart,
    S3FileReferencePart,
    MultimodalContentPart,
    // Memory is exported above
    Collection,
    SearchResult,
    GraphEntityResult,
    GraphRelationshipResult,
    GraphCommunityResult,
    SearchOptions,
    ActivatedEntity,
    ActivatedSemantic,
    ActivatedProcedure,
    ActivatedEpisode,
    ActivatedFacet,
    GroundedSource,
    NebulaClientConfig,
    NebulaException,
    NebulaClientException,
    NebulaAuthenticationException,
    NebulaRateLimitException,
    NebulaValidationException,
    NebulaCollectionNotFoundException,
    NebulaNotFoundException
} from './types';
