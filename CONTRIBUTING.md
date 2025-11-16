# Contribution Guidelines

Thank you for considering contributing to WhatsApp Bot Service! This document outlines the process and guidelines for contributing.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the behavior
- **Expected behavior** vs actual behavior
- **Environment details** (OS, Python version, deployment method)
- **Logs** if applicable

### Suggesting Enhancements

Enhancement suggestions are welcome! Please provide:

- **Clear use case** for the enhancement
- **Expected behavior** of the feature
- **Alternative solutions** you've considered
- **Impact** on existing functionality

### Creating New Bots

Want to add a new bot? Great! Follow these steps:

1. Create a new file in `bots/` directory
2. Inherit from `BotBase`
3. Implement required methods
4. Add docstrings and type hints
5. Test thoroughly
6. Submit a pull request

See [README.md](README.md#creating-custom-bots) for bot development guide.

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/whatslang.git
   cd whatslang
   ```

3. Create virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -e ".[dev]"  # Development dependencies
   ```

5. Create a branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Code Style

We use:
- **Black** for code formatting
- **Ruff** for linting
- **MyPy** for type checking

Before submitting:

```bash
# Format code
black .

# Check linting
ruff check .

# Type checking
mypy .
```

### Code Standards

- Use type hints for function parameters and return values
- Add docstrings for classes and public methods
- Follow PEP 8 style guide
- Keep functions focused and small
- Write self-documenting code with clear variable names

## Testing

Currently, we don't have extensive tests. If you're adding tests (much appreciated!):

```bash
pytest
pytest --cov  # With coverage
```

## Pull Request Process

1. **Update documentation** if you're adding features
2. **Follow code style** guidelines
3. **Test your changes** thoroughly
4. **Update CHANGELOG.md** with your changes
5. **One feature per PR** - keep PRs focused

### PR Title Format

Use conventional commits format:

- `feat: Add new translation language support`
- `fix: Resolve database connection timeout`
- `docs: Update deployment guide`
- `refactor: Simplify bot initialization`
- `chore: Update dependencies`

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How has this been tested?

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings generated
```

## Commit Messages

Use clear, descriptive commit messages:

```bash
# Good
git commit -m "feat: Add health check endpoint for container orchestration"
git commit -m "fix: Resolve race condition in bot initialization"

# Bad
git commit -m "update"
git commit -m "fix bug"
```

## Adding Dependencies

If you need to add a new dependency:

1. Add to `requirements.txt` with version pinning
2. Update `pyproject.toml` if it's a core dependency
3. Explain why the dependency is needed in your PR
4. Ensure it's compatible with Python 3.10+

## Documentation

When adding features:

- Update `README.md` if it affects usage
- Update `QUICKSTART.md` if it affects setup
- Update `DEPLOYMENT.md` if it affects deployment
- Add inline code comments for complex logic
- Update docstrings

## Community

- Be respectful and constructive
- Help others when possible
- Share knowledge and experience
- Celebrate successes together

## Questions?

Feel free to:
- Open an issue for questions
- Start a discussion in GitHub Discussions
- Ask for clarification in your PR

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🎉

