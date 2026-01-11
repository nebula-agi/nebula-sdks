import * as fs from 'fs/promises';
import * as path from 'path';
import {
    FileContentPart
} from './types';

const MIME_TYPES: Record<string, string> = {
    // Images
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".heic": "image/heic",
    ".bmp": "image/bmp",
    ".tiff": "image/tiff",
    // Audio
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/m4a",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
    ".aac": "audio/aac",
    ".webm": "audio/webm",
    // Documents
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".txt": "text/plain",
    ".csv": "text/csv",
    ".rtf": "application/rtf",
    ".epub": "application/epub+zip",
};

/**
 * Utility for creating multimodal content from files.
 * Note: These methods only work in Node.js environments.
 */
export class NebulaContent {
    /**
     * Create a FileContentPart from a file path.
     * Automatically deduces media_type and the backend 'type' (image, audio, document).
     */
    static async fromFile(filePath: string, mediaType?: string): Promise<FileContentPart> {
        const absolutePath = path.resolve(filePath);
        const fileName = path.basename(absolutePath);
        const ext = path.extname(absolutePath).toLowerCase();

        const detectedMime = mediaType || MIME_TYPES[ext] || "application/octet-stream";

        const buffer = await fs.readFile(absolutePath);
        const data = buffer.toString('base64');

        return {
            data,
            media_type: detectedMime,
            filename: fileName
        };
    }
}
