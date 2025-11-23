# Session Prompt: Fix Test Suite

## Objective

Fix all 19 test errors in the RA-D-PS test suite to establish a solid testing foundation for future development.

## Current State

**Test Status:**
- 15 tests collected
- 19 errors preventing execution
- Tests outdated after module reorganization

**Command to see errors:**
```bash
pytest tests/ -v
```

## Root Causes

1. **Import Errors:** Tests reference old module paths after restructuring
2. **Missing Fixtures:** Test data files not set up properly
3. **Outdated Expectations:** Tests expect old API/module structure

## Test Files to Fix

Priority order (start with easiest):

1. `tests/test_foundation_validation.py` (6 tests)
   - Import validation
   - Schema validation
   - Profile manager tests
   - Dependencies check

2. `tests/test_organization.py` (5 tests)
   - Project structure validation
   - CLI tests
   - Import tests

3. `tests/test_complete_workflow.py`
   - End-to-end workflow
   - May need sample data

4. `tests/test_document_repository.py`
   - Database integration tests
   - May need test database

5. `tests/test_excel_exporter.py`
   - Export functionality
   - May need sample data

6. GUI tests (4 files):
   - `tests/test_gui.py`
   - `tests/test_gui_integration.py`
   - `tests/test_gui_updates.py`
   - `tests/test_gui_workflow.py`

## Tasks

### Phase 1: Identify All Errors (1-2 hours)
- [ ] Run `pytest tests/ -v 2>&1 | tee test_errors.log`
- [ ] Categorize errors by type:
  - Import errors
  - Missing fixtures
  - Assertion failures
  - Other

### Phase 2: Fix Import Errors (8-10 hours)
- [ ] Update all import statements to new module structure
- [ ] Common fixes needed:
  - `from ra_d_ps.parser import X` → Check actual location
  - `from ra_d_ps.database.Y import Z` → Verify path
  - Any references to moved/renamed modules

### Phase 3: Add Test Fixtures (5-8 hours)
- [ ] Create `tests/conftest.py` with shared fixtures
- [ ] Add sample XML files in `tests/data/`
- [ ] Add sample PDF files in `tests/data/`
- [ ] Create test database fixture
- [ ] Create mock Supabase client if needed

### Phase 4: Fix Test Logic (10-12 hours)
- [ ] Update test assertions to match current API
- [ ] Fix any tests expecting old behavior
- [ ] Update GUI tests for current implementation
- [ ] Verify database tests work with current schema

### Phase 5: Verify All Green (2-3 hours)
- [ ] Run full test suite: `pytest tests/ -v`
- [ ] Check coverage: `pytest tests/ --cov=src/ra_d_ps`
- [ ] Document any skipped tests with reasons
- [ ] Update test documentation

## Success Criteria

- ✅ All 15 tests passing (or explicitly skipped with reasons)
- ✅ Zero import errors
- ✅ Test fixtures properly configured
- ✅ Tests run without manual setup
- ✅ Coverage report generated successfully

## Useful Commands

```bash
# See all errors
pytest tests/ -v

# Run single test file
pytest tests/test_foundation_validation.py -v

# Run single test
pytest tests/test_foundation_validation.py::test_imports -v

# Show more detail on failures
pytest tests/ -vv

# Stop on first failure
pytest tests/ -x

# Show print statements
pytest tests/ -s

# Generate coverage report
pytest tests/ --cov=src/ra_d_ps --cov-report=html --cov-report=term

# See which tests are collected (without running)
pytest tests/ --collect-only
```

## Example Fixture Setup

Create `tests/conftest.py`:

```python
import pytest
from pathlib import Path
import tempfile
import os

@pytest.fixture
def test_data_dir():
    """Return path to test data directory."""
    return Path(__file__).parent / "data"

@pytest.fixture
def sample_xml_file(test_data_dir):
    """Return path to sample XML file."""
    xml_file = test_data_dir / "sample.xml"
    if not xml_file.exists():
        # Create sample XML
        xml_file.parent.mkdir(exist_ok=True)
        xml_file.write_text("""<?xml version="1.0"?>
<root>
    <test>data</test>
</root>
""")
    return str(xml_file)

@pytest.fixture
def temp_output_dir():
    """Create temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def mock_db_session():
    """Mock database session for testing."""
    # Implementation depends on your DB setup
    pass
```

## Common Import Fixes

Old → New mapping:

```python
# Parser imports
from ra_d_ps.parser import parse_radiology_sample  # ✅ Correct
from XMLPARSE import parse_radiology_sample        # ❌ Old

# Database imports
from ra_d_ps.database.models import DocumentModel  # ✅ Correct
from ra_d_ps.models import DocumentModel           # ❌ Old

# Schema imports
from ra_d_ps.schemas.canonical import CanonicalDocument  # ✅ Correct
from ra_d_ps.canonical import CanonicalDocument          # ❌ Old

# Exporter imports
from ra_d_ps.exporters.excel_exporter import ExcelExporter  # ✅ Correct
from ra_d_ps.excel_exporter import ExcelExporter           # ❌ Old
```

## Reference Files

Current module structure:
```
src/ra_d_ps/
├── __init__.py
├── parser.py              # Core parsing
├── gui.py                 # GUI application
├── database.py            # Legacy database
├── api/                   # REST API
│   ├── services/         # Service layer
│   └── routers/          # API routes
├── database/              # New database layer
│   ├── models.py
│   └── repositories/
├── parsers/               # Parser implementations
├── exporters/             # Export implementations
├── schemas/               # Pydantic schemas
└── adapters/              # External integrations
```

## Expected Timeline

- **Total time:** 25-35 hours
- **Phase 1:** 1-2 hours
- **Phase 2:** 8-10 hours
- **Phase 3:** 5-8 hours
- **Phase 4:** 10-12 hours
- **Phase 5:** 2-3 hours

## Tips

1. **Start small:** Fix one test file at a time
2. **Run frequently:** After each fix, run tests to see progress
3. **Use -x flag:** Stop on first failure for faster iteration
4. **Check imports first:** Most errors are likely import issues
5. **Create fixtures:** Shared test data saves time
6. **Document skips:** If a test can't be fixed, skip it with `@pytest.mark.skip(reason="...")`

## Deliverables

When complete:
- [ ] All tests passing or explicitly skipped
- [ ] `tests/conftest.py` with shared fixtures
- [ ] `tests/data/` with sample test files
- [ ] Coverage report showing test coverage
- [ ] Updated `tests/README.md` documenting test setup

## Next Steps After Completion

Once test suite is green:
1. Set up CI to run tests on every PR
2. Add pre-commit hooks to run tests locally
3. Increase test coverage by adding new tests
4. Add API endpoint tests

---

**Start with:** `pytest tests/test_foundation_validation.py -v` and work through errors one by one.
