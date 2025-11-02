# Contributing Guidelines

We welcome contributions to **Remez**!  
We would appreciate your help, whether it's fixing a bug, adding a feature, or improving documentation.

## How to Contribute
1. Fork this repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push to your branch: `git push origin feature/my-feature`
5. Open a Pull Request

## Code Style
- Use clear commit messages
- Follow existing code patterns and conventions
- Add comprehensive tests for all new features

## Testing Requirements

### Backend Testing (`/backend/`) - **Unit Tests Required**
- **Framework:** pytest with Django integration
- **Location:** Place tests in `*/tests/` directories within each app
- **Style:** Follow existing test patterns in `users/tests/` and `analysis/tests/`
- **Database:** Use `@pytest.mark.django_db` for tests that interact with the database

### Pipeline Testing (`/pipeline/`) - **Unit Tests Required**
- **Framework:** pytest with FastAPI integration  
- **Location:** Place tests in `/pipeline/tests/` directory
- **Style:** Follow existing test patterns in the current test suite

### Frontend Testing (`/frontend/`) - **Manual Testing & Screenshots**
- **E2E Integration Testing:** Manually test complete user workflows
- **Screenshots Required:** Include before/after screenshots for UI changes
- **Browser Testing:** Test in major browsers (Chrome, Firefox, Safari)
- **Documentation:** Document test scenarios and expected behavior

### Running Tests

Before submitting your pull request:

```bash
# Backend tests (required)
cd backend && pytest

# Pipeline tests (required)  
cd pipeline && pytest

# Frontend - manual testing with screenshots in PR description
```

### Test Guidelines

**General Testing Principles:**
- **Write descriptive test names** that explain what is being tested
- **Follow Arrange-Act-Assert pattern** for test structure
- **Test both success and failure scenarios**
- **Aim for high test coverage** on new code

**pytest Framework (Backend & Pipeline):**
- **Use pytest-mock** for external dependencies to ensure tests are isolated and fast
- **Use pytest fixtures** for reusable test data, database setup, and mock objects
- **Create conftest.py files** when fixtures are shared across multiple test files
- **Leverage fixture scopes** (function, module, session) appropriately for performance
- **Ensure comprehensive test coverage** for new features
- **Follow existing test patterns** in the respective directories

## Reporting Issues
If you find a bug, please open an Issue with:
- A clear description
- Steps to reproduce
- Expected vs actual behavior
