# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this web app testing tool project.

## Project Overview

This is an automated test framework for the SoilOptix Customer Portal upload workflow. It uses Playwright + pytest to automate the complete 6-step workflow for creating fields, analyses, and uploading agricultural data files.

**Key Objectives:**
- Automate end-to-end testing of SoilOptix Customer Portal workflows
- Support multi-dataset testing with synthetic, sanitized, and real data
- Generate comprehensive test reports with screenshots and traces
- Enable parallel test execution for faster feedback
- Provide clear bug reports with full debugging context

## Quick Start Commands

### Git Operations
```bash
# Check status
git status

# Create a commit (let Claude write the message)
git add . && git commit

# View recent commits
git log --oneline -10
```

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
python -m playwright install chromium

# Run tests
python -m pytest -n auto

# Run tests with visible browser
python -m pytest --headed --slow-mo 500

# Generate test reports
python tools/summarize.py
python tools/mk_bug_packets.py
```

### Testing
```bash
# Run all tests (parallel)
python -m pytest -n auto

# Run tests (single-threaded for debugging)
python -m pytest -v

# Run smoke tests only
python -m pytest -k smoke

# View test results
cat out/summary.md
cat out/pytest.log
```

## Project Structure

```
web-app-testing-tool/
├── .claude/                  # Claude Code configuration
│   └── settings.json        # Auto-approve patterns and context settings
│
├── pages/                   # Page Object Model (POM)
│   ├── login_page.py        # Login functionality
│   ├── farm_page.py         # Field creation and management
│   ├── analysis_page.py     # Analysis creation and file uploads
│   └── upload_page.py       # Legacy (not currently used)
│
├── tests/                   # Pytest test suite
│   └── test_bulk.py         # Main test implementation
│
├── tools/                   # Post-processing scripts
│   ├── summarize.py         # Generate summary.md reports
│   └── mk_bug_packets.py    # Generate bug reports
│
├── datasets/                # Test data (gitignored for sensitive data)
│   └── soiloptix/
│       ├── lab/             # Lab CSV files
│       └── survey/          # Survey ZIP files
│
├── docs/                    # Documentation
│   ├── PRD_UPDATED.md       # Complete technical specification
│   └── WORKFLOW.md          # Step-by-step workflow guide
│
├── out/                     # Test results (gitignored)
│   ├── summary.md           # Test summary report
│   ├── results.json         # pytest-json-report output
│   ├── screenshots/         # Failure screenshots
│   └── traces/              # Playwright traces
│
├── catalog.yml              # Test matrix, selectors, timeouts
├── conftest.py              # Pytest fixtures and parametrization
├── pytest.ini               # Pytest configuration
├── requirements.txt         # Python dependencies
├── .env.example             # Credentials template
├── CLAUDE.md                # This file
└── README.md                # Main documentation
```

## Development Workflow

### Test-Driven Development
1. **Write Tests First**: For new features, start by writing tests
2. **Implement**: Write the minimal code to pass tests
3. **Refactor**: Improve code quality while keeping tests green
4. **Document**: Update docs to reflect new functionality

### Code Quality
- Run linters before committing
- Ensure all tests pass
- Maintain test coverage above [X]%
- Follow project coding standards

### Git Workflow
1. Create feature branch from `main`
2. Make changes with clear, atomic commits
3. Run tests and linting
4. Create pull request with clear description
5. Address review feedback
6. Merge when approved

## Style Guidelines

### Code Style
- [To be defined based on language/framework choice]
- Follow existing patterns in the codebase
- Prefer clarity over cleverness
- Write self-documenting code with descriptive names

### Commit Messages
- Use conventional commits format: `type(scope): description`
- Types: feat, fix, docs, style, refactor, test, chore
- Keep first line under 72 characters
- Add detailed description when needed

### Testing Style
- Use descriptive test names that explain the scenario
- Follow AAA pattern: Arrange, Act, Assert
- One assertion per test when possible
- Mock external dependencies

## Key Principles

1. **Test Coverage**: All critical paths should have tests
2. **Documentation**: Code should be self-documenting, comments explain "why"
3. **Error Handling**: Fail fast with clear error messages
4. **Maintainability**: Write code that's easy to understand and modify
5. **Performance**: Optimize only when needed, measure first

## Working with Claude Code Features

### Todo Lists
Use extensively for multi-step tasks:
- Create todos at the start of complex work
- Update them as you progress
- Mark completed only when fully done

### Planning Mode
For new features or major changes:
- Plan the implementation first
- Review and provide feedback
- Approve before proceeding

### Auto-Accept Mode (Shift+Tab)
Use for routine, safe operations:
- Running tests
- Linting and formatting
- Git status/log/diff

## Common Tasks

### Adding a New Feature
1. Create feature branch
2. Write tests for the feature
3. Implement the feature
4. Run full test suite
5. Update documentation
6. Create pull request

### Debugging
1. Reproduce the issue with a test
2. Use debugger or logging to identify root cause
3. Fix the issue
4. Verify test passes
5. Add regression test if needed

### Refactoring
1. Ensure existing tests pass
2. Make incremental changes
3. Run tests after each change
4. Keep commits small and focused

## Files to Check Before Making Changes

- `README.md` - Project overview and setup
- `package.json` / `requirements.txt` - Dependencies
- `tests/` - Existing test patterns
- `.github/workflows/` - CI/CD configuration (if present)

## Anti-Patterns to Avoid

- Don't commit code without tests for critical functionality
- Don't skip running tests before committing
- Don't write overly complex abstractions prematurely
- Don't ignore linting warnings
- Don't commit debugging code (console.log, print statements)
- Don't hardcode configuration values

## Resources

### Internal Documentation
- [Link to architecture docs - TBD]
- [Link to API docs - TBD]
- [Link to contributing guide - TBD]

### External Resources
- [Links to relevant frameworks/libraries - TBD]

## Notes

This project is currently in initial setup phase. The structure and guidelines will be refined as the project evolves based on the PRD and technical decisions made during development.
