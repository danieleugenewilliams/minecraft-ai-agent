# AGENTS.md - Agent Guidelines for minecraft-ai

## Project Overview
This is a Minecraft AI agent project for Bedrock Edition using Python. The project is in early development with minimal existing code structure.

## Commands
No build/lint/test commands configured yet. Common Python commands:
- `python -m pytest` - Run tests (when configured)
- `python -m flake8` - Lint code (when configured)
- `python -m black .` - Format code (when configured)

## Code Style Guidelines
- **Language**: Python (as per requirements.md)
- **Dependencies**: pygame/PyOpenGL, minecraft/mcpi, selenium/AutoIt, TensorFlow/PyTorch
- **Naming**: Use snake_case for functions and variables, PascalCase for classes
- **Imports**: Group standard library, third-party, then local imports with blank lines
- **Types**: Use type hints where possible
- **Error Handling**: Use try/except blocks for API calls and automation tasks
- **Comments**: Add docstrings for functions and classes, inline comments for complex logic
- **Testing**: Write unit tests for core AI logic and integration tests for Minecraft interactions

## Development Notes
- Project focuses on automating Minecraft gameplay through iPhone mirroring on macOS
- Use virtual environments for dependency management
- Implement incremental testing starting with simple tasks
- Include comprehensive logging for debugging complex interactions

## Local Memory

Proactively use local-memory MCP to store, retrieve, update, and analyze memories to maintain context and build expertise over time. Store key insights including lessons learned, architectural decisions, development strategies, and project outcomes. Use semantic search and relationship mapping to find relevant memories across all projects and sessions. For non-MCP agents, you access memories here: http://localhost:3002/api/v1