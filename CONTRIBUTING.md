# Contributing to Nebula SDKs

Thank you for your interest in contributing to Nebula SDKs! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## How to Contribute

### Reporting Bugs

If you find a bug:

1. Check if the issue already exists in [GitHub Issues](https://github.com/nebula-cloud/nebula-sdks/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - SDK version and environment details
   - Code samples if applicable

### Suggesting Features

We welcome feature suggestions! Please:

1. Check existing issues and discussions
2. Create a new issue with the `enhancement` label
3. Describe the use case and proposed solution
4. Include code examples if relevant

### Pull Requests

1. **Fork the repository** and create a branch from `main`
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**

   For JavaScript:
   ```bash
   cd javascript
   npm install
   npm test
   npm run type-check
   npm run lint
   ```

   For Python:
   ```bash
   cd python
   pip install -e ".[dev]"
   pytest
   ruff check .
   mypy nebula_client/
   ```

4. **Commit with clear messages**
   ```bash
   git commit -m "feat: add new search filter option"
   ```

   Use conventional commit format:
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `test:` - Test changes
   - `refactor:` - Code refactoring
   - `chore:` - Maintenance tasks

5. **Push and create a pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **PR Guidelines**
   - Link related issues
   - Describe what changed and why
   - Include screenshots/examples if relevant
   - Ensure CI passes

## Development Setup

### JavaScript SDK

```bash
cd javascript
npm install
npm run dev        # Watch mode for development
npm test           # Run tests
npm run build      # Build the package
```

### Python SDK

```bash
cd python
pip install -e ".[dev]"
pytest                    # Run tests
pytest --cov             # Run tests with coverage
ruff check .             # Lint
ruff format .            # Format code
```

## Code Style

### JavaScript/TypeScript

- Use TypeScript for all new code
- Follow existing patterns in the codebase
- Use ESLint configuration provided
- Add JSDoc comments for public APIs

### Python

- Follow PEP 8 style guide
- Use type hints for function signatures
- Use ruff for linting and formatting
- Add docstrings for public APIs

## Testing

- Write tests for all new features
- Maintain or improve code coverage
- Test edge cases and error conditions
- Use meaningful test names

### JavaScript Tests

```typescript
describe('NebulaClient', () => {
  it('should create a collection', async () => {
    // Test implementation
  });
});
```

### Python Tests

```python
def test_create_collection():
    """Test that collections can be created"""
    # Test implementation
```

## Documentation

- Update README.md if changing public APIs
- Add examples for new features
- Update API documentation
- Include code comments for complex logic

## Release Process

Maintainers handle releases:

1. Update version in `package.json` or `pyproject.toml`
2. Update CHANGELOG.md
3. Create and push version tag:
   - JavaScript: `git tag js-v0.0.35`
   - Python: `git tag py-v0.1.10`
4. GitHub Actions automatically publishes to npm/PyPI

## Questions?

- Open a [GitHub Discussion](https://github.com/nebula-cloud/nebula-sdks/discussions)
- Join our [Discord](https://discord.gg/nebula)
- Email: support@trynebula.ai

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
