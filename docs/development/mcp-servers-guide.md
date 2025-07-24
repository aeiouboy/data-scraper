# MCP Servers Installation Guide

## Overview
This guide documents the MCP (Model Context Protocol) servers installed for the RIS Data Scraper project to enhance Claude Code's capabilities.

## Installed MCP Servers

### 1. Context7 - Library Documentation Access
- **Purpose**: Provides up-to-date code documentation for LLMs and AI code editors
- **Installation Command**: `claude mcp add --transport http context7 https://mcp.context7.com/mcp`
- **Type**: HTTP transport
- **Repository**: https://github.com/upstash/context7
- **Features**:
  - Real-time access to library documentation
  - Code examples and API references
  - Language-specific documentation

### 2. Sequential Thinking - Multi-step Reasoning
- **Purpose**: Dynamic and reflective problem-solving through structured thinking processes
- **Installation Command**: `claude mcp add sequential-thinking -- npx -y @modelcontextprotocol/server-sequential-thinking`
- **Type**: stdio transport
- **Repository**: https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking
- **Features**:
  - Break down complex problems into manageable steps
  - Structured thinking process
  - Reflective problem-solving capabilities
- **Configuration**: Set `DISABLE_THOUGHT_LOGGING=true` to disable logging

### 3. Magic - AI-generated UI Components
- **Purpose**: Create crafted UI components using AI with best design practices
- **Installation Command**: `claude mcp add magic -- npx -y @21st-dev/magic-mcp`
- **Type**: stdio transport
- **Repository**: https://github.com/21st-dev/magic-mcp
- **Features**:
  - AI-powered UI generation
  - Natural language to component conversion
  - Integration with existing projects
- **Note**: Requires API key from 21st.dev Magic Console

### 4. Browserbase - Browser Automation (Puppeteer Alternative)
- **Purpose**: Cloud browser automation for web navigation, data extraction, and testing
- **Installation Command**: `claude mcp add browserbase -- npx -y @browserbase/mcp-server-browserbase`
- **Type**: stdio transport
- **Repository**: https://github.com/browserbase/mcp-server-browserbase
- **Features**:
  - Browser control and automation
  - Web scraping and data extraction
  - Screenshot capture
  - Console monitoring
  - Form filling and interaction

## Usage

### Checking Installed Servers
```bash
claude mcp list
```

### Adding New Servers
```bash
claude mcp add [options] <name> <commandOrUrl> [args...]
```

Options:
- `-s, --scope <scope>`: Configuration scope (local, user, or project)
- `-t, --transport <transport>`: Transport type (stdio, sse, http)
- `-e, --env <env...>`: Set environment variables
- `-H, --header <header...>`: Set HTTP headers

### Removing Servers
```bash
claude mcp remove <name>
```

## Security Considerations

⚠️ **Important**: The MCP documentation warns to "use third party MCP servers at your own risk" due to potential prompt injection risks. Always:
1. Review the source code of MCP servers before installation
2. Use only trusted and well-maintained servers
3. Monitor server activity and permissions
4. Keep servers updated to latest versions

## Configuration Files

MCP server configurations are stored in:
- Local scope: `.claude/mcp.json` in the project directory
- User scope: `~/.config/claude/mcp.json`
- Project scope: Shared team configuration

## Troubleshooting

### Common Issues

1. **Server fails to start**
   - Ensure Node.js 18.0.0 or higher is installed
   - Check network connectivity for HTTP servers
   - Verify API keys are configured (for Magic server)

2. **Permission errors**
   - Ensure proper file permissions for local configurations
   - Check if the server requires additional authentication

3. **Server not responding**
   - Restart Claude Code
   - Remove and re-add the server
   - Check server logs for errors

## Benefits for the Project

1. **Context7**: Quick access to documentation while working with various libraries in the scraping project
2. **Sequential Thinking**: Better problem-solving for complex scraping logic and data processing
3. **Magic**: Rapid UI component creation for the frontend dashboard
4. **Browserbase**: Enhanced browser automation capabilities for web scraping tasks

## Next Steps

1. Configure API keys for servers that require them (e.g., Magic)
2. Test each server with relevant project tasks
3. Document any project-specific configurations
4. Share configuration with team members as needed