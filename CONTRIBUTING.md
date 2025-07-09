# Contributing to ProjectClocktower

Thank you for your interest in contributing to the Blood on the Clocktower AI Storyteller! This document provides guidelines for contributing to the project.

## 🎯 Ways to Contribute

### 🐛 Bug Reports
- Use the [Issues](https://github.com/yourusername/ProjectClocktower/issues) page
- Check existing issues before creating new ones
- Include detailed reproduction steps
- Provide system information and log files

### 💡 Feature Requests
- Open an issue with the "enhancement" label
- Clearly describe the proposed feature
- Explain the use case and benefits
- Consider implementation complexity

### 🔧 Code Contributions
- Fork the repository
- Create a feature branch
- Follow coding standards
- Add tests for new functionality
- Update documentation

### 📚 Documentation
- Improve existing documentation
- Add examples and tutorials
- Fix typos and clarify explanations
- Translate documentation

## 🛠️ Development Setup

### Prerequisites
- Python 3.11 or higher
- Git
- Virtual environment tool (venv/conda)

### Setup Steps
```bash
# Fork and clone the repository
git clone https://github.com/yourusername/ProjectClocktower.git
cd ProjectClocktower

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Download AI models
python setup.py

# Run tests
pytest
```

## 📋 Coding Standards

### Python Style Guide
- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write descriptive docstrings
- Keep functions focused and small

### Code Formatting
```bash
# Format code with black
black src/ tests/

# Check with flake8
flake8 src/ tests/

# Sort imports
isort src/ tests/
```

### Naming Conventions
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`

## 🧪 Testing Guidelines

### Writing Tests
- Write tests for all new functionality
- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies

### Test Structure
```python
def test_feature_should_do_something_when_condition():
    # Arrange
    setup_test_data()
    
    # Act
    result = function_under_test()
    
    # Assert
    assert result == expected_value
```

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_storyteller_ai.py

# Run with coverage
pytest --cov=src tests/
```

## 📝 Pull Request Process

### Before Submitting
1. Ensure all tests pass
2. Update documentation if needed
3. Add entry to CHANGELOG.md
4. Check code formatting
5. Write clear commit messages

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
- [ ] Tests pass locally
- [ ] Added new tests for changes
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings introduced
```

### Review Process
1. Automated checks must pass
2. At least one maintainer review required
3. Address feedback promptly
4. Squash commits before merge

## 🎮 Character Implementation Guidelines

When adding new Blood on the Clocktower characters:

### Character Data Structure
```python
"CharacterName": {
    "team": "good/evil",
    "type": "townsfolk/outsider/minion/demon",
    "ability": "ability_type",
    "learns": "what_they_learn",
    "targets": number_of_targets,
    "special_rules": ["list", "of", "special", "cases"]
}
```

### Implementation Checklist
- [ ] Add character to character_data.py
- [ ] Implement ability handler
- [ ] Add to night order (if applicable)
- [ ] Create decision logic in AI engine
- [ ] Write comprehensive tests
- [ ] Update documentation
- [ ] Test edge cases and interactions

## 🔧 AI Decision Guidelines

### Decision Making Principles
1. **Game Balance**: Consider current team performance
2. **Player Experience**: Prioritize fun and engagement
3. **Rule Accuracy**: Follow official game rules
4. **Dramatic Timing**: Optimize for storytelling

### Adding New Decisions
```python
def decide_new_ability(self, player: Player, context: Dict) -> Any:
    """
    Decide outcome for new character ability.
    
    Args:
        player: The player using the ability
        context: Game state and relevant information
        
    Returns:
        Decision result appropriate for the ability
    """
    # 1. Get actual game state
    actual_result = self._calculate_true_result(context)
    
    # 2. Apply drunk/poisoned effects
    if player.is_drunk or player.is_poisoned:
        result = self._modify_for_malfunction(actual_result)
    else:
        result = actual_result
        
    # 3. Consider game balance
    result = self._apply_balance_considerations(result, context)
    
    # 4. Log decision
    self._log_decision("ability_name", confidence, reasoning, data)
    
    return result
```

## 🌐 Platform Integration Guidelines

### Adding New Platforms
1. Create platform-specific API client
2. Implement required WebSocket events
3. Handle platform-specific data formats
4. Add configuration options
5. Test connection and functionality
6. Document platform-specific features

### API Client Structure
```python
class NewPlatformAPI(ClockTowerAPI):
    def __init__(self, base_url: str, room_code: str):
        super().__init__(base_url, room_code)
        self.platform = "new_platform"
        
    async def connect(self) -> bool:
        # Platform-specific connection logic
        pass
        
    async def send_storyteller_action(self, action_type: str, data: Dict) -> bool:
        # Platform-specific action sending
        pass
```

## 📖 Documentation Standards

### Docstring Format
```python
def function_name(param1: type, param2: type) -> return_type:
    """
    Brief description of what the function does.
    
    Longer description if needed, explaining the purpose,
    algorithm, or important details.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter
        
    Returns:
        Description of return value
        
    Raises:
        ExceptionType: When this exception is raised
        
    Example:
        >>> result = function_name("value1", 42)
        >>> print(result)
        "expected output"
    """
```

### README Updates
- Keep feature lists current
- Update installation instructions
- Add new platform support
- Update system requirements

## 🚨 Security Guidelines

### Sensitive Information
- Never commit API keys or secrets
- Use environment variables for configuration
- Sanitize user inputs
- Validate all external data

### Voice Data Privacy
- Process audio locally only
- Never store or transmit voice data
- Clear audio buffers after processing
- Respect user privacy preferences

## 🎯 Release Process

### Version Numbering
- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Update version in setup.py and __init__.py
- Tag releases in git

### Release Checklist
- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version numbers incremented
- [ ] Windows executable builds
- [ ] Release notes written
- [ ] GitHub release created

## 🤝 Community Guidelines

### Code of Conduct
- Be respectful and inclusive
- Help others learn and grow
- Give constructive feedback
- Credit others' contributions

### Communication
- Use clear, professional language
- Be patient with new contributors
- Provide helpful explanations
- Celebrate successes

## ❓ Getting Help

### Resources
- [GitHub Issues](https://github.com/yourusername/ProjectClocktower/issues)
- [Documentation](docs/)
- [Discord Community](https://discord.gg/your-invite)
- [Blood on the Clocktower Rules](https://bloodontheclocktower.com/rules)

### Mentorship
New contributors are welcome! Maintainers are happy to:
- Review your first pull request
- Explain codebase architecture
- Suggest good first issues
- Provide development guidance

## 📜 Legal Considerations

### Intellectual Property
- Respect Blood on the Clocktower copyrights
- Don't reproduce game content directly
- Focus on tools and enhancement
- Credit original creators

### Platform Terms
- Follow platform terms of service
- Don't abuse API rate limits
- Respect user privacy
- Report security issues responsibly

---

Thank you for contributing to ProjectClocktower! Your efforts help make Blood on the Clocktower more accessible and enjoyable for everyone. 🎭