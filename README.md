# Minecraft AI Agent

A Python-based AI agent for automating Minecraft: Bedrock Edition gameplay through iPhone mirroring on macOS.

## Features

- **Screen Capture**: Real-time capture of Minecraft gameplay via iPhone mirroring
- **Computer Vision**: Image processing and environment analysis using OpenCV
- **Input Automation**: macOS-native mouse and keyboard control
- **AI Decision Making**: Rule-based and neural network-based agents
- **Modular Architecture**: Extensible design for different AI approaches
- **Safety Features**: Dry-run mode and safety bounds for testing

## Quick Start

### 1. Setup Environment

```bash
# Clone and enter project directory
cd minecraft-ai

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install dependencies
python setup.py
```

### 2. Configure Minecraft

1. Start Minecraft: Bedrock Edition on your iPhone
2. Enable iPhone Mirroring on your macOS device
3. Ensure Minecraft is visible on your screen

### 3. Run the Agent

```bash
# Test run (no actual input actions)
python main.py --dry-run --debug

# Live run (requires Minecraft to be active)
python main.py

# Custom configuration
python main.py --config config/custom.yaml
```

## Project Structure

```
minecraft-ai/
├── src/minecraft_ai/          # Main package
│   ├── core/                  # Core utilities (config, logging)
│   ├── automation/            # Input control (mouse, keyboard)
│   ├── vision/                # Screen capture and image processing
│   └── ai/                    # AI agents and decision making
├── config/                    # Configuration files
├── logs/                      # Log files
├── tests/                     # Unit tests
├── main.py                    # Main entry point
├── setup.py                   # Setup script
└── requirements.txt           # Python dependencies
```

## Development

The project follows modular design principles:

- **Core**: Configuration management and logging
- **Automation**: Platform-specific input control
- **Vision**: Screen capture and image analysis
- **AI**: Agent logic and decision making

## Requirements

- macOS (for iPhone mirroring support)
- Python 3.8+
- iPhone with Minecraft: Bedrock Edition
- Virtual environment recommended

## Safety Notes

- Always test with `--dry-run` flag first
- Use safety bounds to prevent runaway automation
- Monitor the agent during initial runs
- Keep Minecraft in a safe environment (creative mode recommended for testing)