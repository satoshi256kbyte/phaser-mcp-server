# Technology Stack & Build System

## Core Technologies

- **Language**: Python 3.14+
- **Framework**: Model Context Protocol (MCP)
- **Package Manager**: uv
- **Distribution**: PyPI + uvx

## Dependencies

### Core Dependencies

- `mcp[cli]>=1.11.0` - MCP framework
- `httpx>=0.28.0` - HTTP client for API requests
- `beautifulsoup4>=4.13.0` - HTML parsing
- `markdownify>=1.2.0` - HTML to Markdown conversion
- `pydantic>=2.11.0` - Data validation
- `loguru>=0.8.0` - Logging

### Development Dependencies

- `pytest>=8.0.0` - Testing framework
- `pytest-asyncio>=0.27.0` - Async testing support
- `pytest-cov>=5.0.0` - Coverage reporting
- `pytest-mock>=3.12.0` - Mock utilities
- `ruff>=0.10.0` - Linting and formatting
- `pyright>=1.2.0` - Type checking
- `pre-commit>=4.2.0` - Git hooks
- `commitizen>=4.3.0` - Conventional commits

## Deployment & Distribution

### uvx Installation

```bash
uvx phaser-mcp-server@latest
```

### Docker Support

```dockerfile
FROM python:3.14-slim
# Container setup for MCP server
```

### MCP Client Configuration

#### uvx Installation

```json
{
  "mcpServers": {
    "phaser-mcp-server": {
      "command": "uvx",
      "args": ["phaser-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

#### Docker Installation

```json
{
  "mcpServers": {
    "phaser-mcp-server": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "--interactive",
        "--env",
        "FASTMCP_LOG_LEVEL=ERROR",
        "phaser-mcp-server:latest"
      ],
      "env": {},
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## Build System

- **Build Backend**: hatchling
- **Package Structure**: Standard Python package with entry points
- **Entry Point**: `phaser-mcp-server = phaser_mcp_server.server:main`
- **Distribution**: PyPI package compatible with uvx

## Code Quality

- **Linting**: Ruff with Google docstring convention
- **Type Checking**: Pyright with strict mode
- **Testing**: pytest with asyncio and coverage support
- **Pre-commit Hooks**: Automated code quality checks
- **Conventional Commits**: Standardized commit messages
