#!/usr/bin/env node
import { hideBin } from 'yargs/helpers';
import yargs from 'yargs';
import { writeFileSync, mkdirSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { homedir } from 'os';

const argv = yargs(hideBin(process.argv))
  .option('client', { 
    type: 'string', 
    choices: ['claude', 'cursor', 'cline', 'roo-cline', 'windsurf', 'vscode'], 
    describe: 'MCP client to configure' 
  })
  .option('api-key', { type: 'string', describe: 'Nebula API key' })
  .option('api-url', { type: 'string', default: 'https://api.trynebula.ai', describe: 'Nebula API base URL' })
  .option('global', { type: 'boolean', default: false, describe: 'Install globally (for Cursor)' })
  .strict()
  .help()
  .parse();

if (!argv.client) {
  console.error('--client is required');
  process.exit(1);
}

if (!argv.apiKey) {
  console.error('--api-key is required');
  process.exit(1);
}

const configs = {
  claude: {
    path: join(homedir(), 'Library', 'Application Support', 'Claude', 'claude_desktop_config.json'),
    content: {
      mcpServers: {
        nebula: {
          command: 'npx',
          args: ['-y', '@nebula-ai/mcp-server', '--stdio'],
          env: {
            NEBULA_API_KEY: argv.apiKey,
            NEBULA_API_URL: argv.apiUrl
          }
        }
      }
    }
  },
  cursor: {
    path: argv.global 
      ? join(homedir(), '.cursor', 'mcp.json')
      : join(process.cwd(), '.cursor', 'mcp.json'),
    content: {
      mcpServers: {
        nebula: {
          command: 'npx',
          args: ['-y', '@nebula-ai/mcp-server', '--stdio'],
          env: {
            NEBULA_API_KEY: argv.apiKey,
            NEBULA_API_URL: argv.apiUrl
          }
        }
      }
    }
  },
  cline: {
    path: join(homedir(), '.cline', 'mcp.json'),
    content: {
      servers: {
        nebula: {
          command: 'npx',
          args: ['-y', '@nebula-ai/mcp-server', '--stdio'],
          env: {
            NEBULA_API_KEY: argv.apiKey,
            NEBULA_API_URL: argv.apiUrl
          }
        }
      }
    }
  },
  'roo-cline': {
    path: join(homedir(), '.roo-cline', 'mcp.json'),
    content: {
      servers: {
        nebula: {
          command: 'npx',
          args: ['-y', '@nebula-ai/mcp-server', '--stdio'],
          env: {
            NEBULA_API_KEY: argv.apiKey,
            NEBULA_API_URL: argv.apiUrl
          }
        }
      }
    }
  },
  windsurf: {
    path: join(homedir(), '.windsurf', 'mcp.json'),
    content: {
      servers: {
        nebula: {
          command: 'npx',
          args: ['-y', '@nebula-ai/mcp-server', '--stdio'],
          env: {
            NEBULA_API_KEY: argv.apiKey,
            NEBULA_API_URL: argv.apiUrl
          }
        }
      }
    }
  },
  vscode: {
    path: join(homedir(), '.vscode', 'mcp.json'),
    content: {
      servers: {
        nebula: {
          command: 'npx',
          args: ['-y', '@nebula-ai/mcp-server', '--stdio'],
          env: {
            NEBULA_API_KEY: argv.apiKey,
            NEBULA_API_URL: argv.apiUrl
          }
        }
      }
    }
  }
};

const config = configs[argv.client];
if (!config) {
  console.error(`Unknown client: ${argv.client}`);
  process.exit(1);
}

// Ensure directory exists
const configDir = dirname(config.path);
if (!existsSync(configDir)) {
  mkdirSync(configDir, { recursive: true });
}

// Read existing config if it exists
let existingConfig = {};
if (existsSync(config.path)) {
  try {
    const existingContent = await import('fs').then(fs => fs.readFileSync(config.path, 'utf8'));
    existingConfig = JSON.parse(existingContent);
  } catch (err) {
    console.warn(`Warning: Could not read existing config at ${config.path}`);
  }
}

// Merge with existing config
const mergedConfig = {
  ...existingConfig,
  ...config.content
};

// Write config
writeFileSync(config.path, JSON.stringify(mergedConfig, null, 2));

console.log(`✅ Successfully configured ${argv.client} MCP client`);
console.log(`📁 Config written to: ${config.path}`);
console.log(`🔄 Please restart ${argv.client} to load the MCP server`);
console.log(`🔑 API Key: ${argv.apiKey.substring(0, 8)}...`);
console.log(`🌐 API URL: ${argv.apiUrl}`);


