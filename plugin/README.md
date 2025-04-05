# VS Code Plugin Directory

This directory contains the Visual Studio Code plugin implementation for the Source Code Optimizer project, providing integration with the VS Code IDE.

## Directory Structure

### Main Plugin Directory
- `capstone--sco-vs-code-plugin/` - VS Code extension implementation

## Plugin Features

1. Code Analysis Integration
   - Real-time code smell detection
   - Toggle automatic smell detection on/off

2. Refactoring Tools
   - Automated code refactoring
   - Refactor one smell of a type
   - Refactor all smells of a type

3. User Interface
   - Custom VS Code views
   - Command palette integration
   - Status bar indicators

4. Configuration
   - Plugin settings
   - Rule customization
   - Ignore certain smells

## Development

1. Setup Development Environment:
   ```bash
   cd capstone--sco-vs-code-plugin
   npm install
   ```

2. Build the Plugin:
   ```bash
   npm run build
   ```

3. Debug the Plugin:
   - Press F5 in VS Code
   - Select "Run Extension"

## Installation

1. From VS Code Marketplace:
   - Search for "Source Code Optimizer"
   - Click Install
