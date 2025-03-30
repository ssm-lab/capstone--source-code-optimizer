# Tests Directory

This directory contains all test-related files and directories for the Source Code Optimizer project. The tests are organized by component and functionality to ensure comprehensive coverage of the codebase.

## Directory Structure

### Component Tests
- `analyzers/` - Tests for code analysis components
- `refactorers/` - Tests for code refactoring implementations
- `controllers/` - Tests for controller layer components
- `smells/` - Tests for code smell detection features
- `api/` - Tests for API endpoints and interfaces

### Performance Tests
- `benchmarking/` - Performance and benchmark tests
- `measurements/` - Test metrics and measurement utilities

### Test Resources
- `input/` - Test input files and fixtures
- `temp_dir/` - Temporary directory for test file operations
- `conftest.py` - PyTest configuration and shared fixtures

## Test Development Guidelines

1. Use meaningful test names that describe the scenario
2. Keep tests independent and isolated
3. Use appropriate fixtures and mocks
4. Maintain high code coverage

## Maintenance

1. Regular test suite maintenance and updates
2. Remove obsolete tests
3. Update tests when functionality changes
