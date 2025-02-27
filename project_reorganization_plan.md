# Cool Squad Project Reorganization Plan

## Current Issues

The current project structure has several issues:

1. Inconsistent naming conventions
2. Overlapping functionality between different components
3. Unclear separation between backend services and frontend clients
4. Multiple client interfaces with different capabilities
5. Confusing organization of code

## Reorganization Plan

### 1. Unified CLI Interface (Completed)

- [x] Merge the functionality of cli.py and board_client.py into a single unified CLI tool
- [x] Implement subcommands for different functions (explore, chat, board)
- [x] Update documentation to reflect the new CLI structure

### 2. Consistent Module Structure

- [ ] Reorganize the cool_squad package into logical submodules:
  ```
  cool_squad/
  ├── api/              # API-related code
  │   ├── __init__.py
  │   ├── routes.py     # FastAPI routes
  │   └── models.py     # Pydantic models
  ├── core/             # Core data models and utilities
  │   ├── __init__.py
  │   ├── models.py     # Data models (Message, Channel, Board, Thread)
  │   └── config.py     # Configuration utilities
  ├── storage/          # Storage-related code
  │   ├── __init__.py
  │   └── storage.py    # Storage implementation
  ├── bots/             # Bot-related code
  │   ├── __init__.py
  │   ├── base.py       # Base bot class
  │   ├── tools.py      # Bot tools
  │   └── personalities/# Bot personalities
  │       ├── __init__.py
  │       ├── curator.py
  │       └── ...
  ├── server/           # Server implementations
  │   ├── __init__.py
  │   ├── chat.py       # Chat server
  │   └── board.py      # Board server
  ├── clients/          # Client implementations
  │   ├── __init__.py
  │   ├── cli.py        # CLI client
  │   └── web/          # Web client
  ├── utils/            # Utility functions
  │   ├── __init__.py
  │   ├── logging.py    # Logging utilities
  │   └── token_budget.py # Token budget tracking
  ├── __init__.py
  └── main.py           # Main entry point
  ```

### 3. Consistent Naming Conventions

- [ ] Rename files and classes to follow consistent naming conventions:
  - Use snake_case for module and function names
  - Use CamelCase for class names
  - Use consistent prefixes/suffixes (e.g., all servers end with "Server")

### 4. Clear Separation of Concerns

- [ ] Separate backend services from frontend clients
- [ ] Create clear interfaces between components
- [ ] Implement proper dependency injection
- [ ] Use consistent patterns for async code

### 5. Documentation Updates

- [ ] Update all documentation to reflect the new structure
- [ ] Create architecture diagrams
- [ ] Document the relationships between components
- [ ] Provide clear examples for common use cases

### 6. Testing Improvements

- [ ] Reorganize tests to match the new structure
- [ ] Ensure all components have appropriate tests
- [ ] Implement integration tests for the entire system

## Implementation Plan

1. **Phase 1: Unified CLI (Completed)**
   - [x] Merge cli.py and board_client.py
   - [x] Implement subcommands
   - [x] Update documentation

2. **Phase 2: Module Reorganization**
   - [ ] Create the new directory structure
   - [ ] Move existing code to the new locations
   - [ ] Update imports and references
   - [ ] Ensure all tests pass

3. **Phase 3: Interface Cleanup**
   - [ ] Define clear interfaces between components
   - [ ] Implement proper dependency injection
   - [ ] Remove duplicate code

4. **Phase 4: Documentation and Testing**
   - [ ] Update all documentation
   - [ ] Create architecture diagrams
   - [ ] Ensure comprehensive test coverage

## Benefits

1. **Improved Developer Experience**
   - Easier to understand the codebase
   - Consistent patterns and conventions
   - Clear separation of concerns

2. **Better Maintainability**
   - Modular design makes changes easier
   - Clear interfaces between components
   - Comprehensive tests ensure stability

3. **Easier Onboarding**
   - Well-documented architecture
   - Consistent patterns and conventions
   - Clear examples for common use cases

4. **Future-Proofing**
   - Modular design makes it easier to add new features
   - Clear interfaces make it easier to replace components
   - Consistent patterns make it easier to understand the codebase 