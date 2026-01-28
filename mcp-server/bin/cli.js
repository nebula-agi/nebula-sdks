#!/usr/bin/env node
import { hideBin } from 'yargs/helpers';
import yargs from 'yargs';
import { startServer } from '../src/server.js';

const argv = yargs(hideBin(process.argv))
  .option('api-url', { type: 'string', default: process.env.NEBULA_API_URL || 'https://api.trynebula.ai', describe: 'Nebula API base URL' })
  .option('api-key', { type: 'string', default: process.env.NEBULA_API_KEY, describe: 'Nebula API key' })
  .option('stdio', { type: 'boolean', default: false, describe: 'Use stdio transport for MCP clients' })
  .strict()
  .help()
  .parse();

if (!argv.apiKey) {
  console.error('NEBULA_API_KEY is required (pass --api-key or set env NEBULA_API_KEY)');
  process.exit(1);
}

await startServer({ 
  baseUrl: argv.apiUrl, 
  apiKey: argv.apiKey, 
  transport: argv.stdio ? 'stdio' : 'sse' 
});


