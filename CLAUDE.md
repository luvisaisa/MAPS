# CLAUDE.md - AI Assistant Guide for RA-D-PS

**Last Updated:** November 21, 2025
**Repository:** RA-D-PS (Radiology XML Data Processing System)
**Version:** 1.0.0
**Python Version:** 3.8+

---

## Table of Contents

1. [Documentation Style Requirements](#documentation-style-requirements)
2. [Project Overview](#project-overview)
3. [Repository Structure](#repository-structure)
4. [Architecture & Design](#architecture--design)
5. [Development Setup](#development-setup)
6. [Code Conventions](#code-conventions)
7. [Testing Strategy](#testing-strategy)
8. [Common Workflows](#common-workflows)
9. [Key Components Reference](#key-components-reference)
10. [AI Assistant Guidelines](#ai-assistant-guidelines)
11. [Troubleshooting](#troubleshooting)

---

## Documentation Style Requirements

All documentation generated for this project must follow the standards outlined below:

### 1. No Emojis or Decorative Glyphs

All text must remain professional, clean, and appropriate for technical documentation.

### 2. No AI-Style Phrasing or Meta-Commentary

Documentation should never include statements that reveal or imply it was produced by an automated system. Avoid expressions such as "As an AI," "This model suggests," "Here is your request," or any language that addresses the reader in a conversational or assistant-like tone.

### 3. Authoritative, Concise Writing

Documentation should be written as if authored by the project maintainer. Use clear, direct technical prose suitable for engineers, collaborators, and future contributors.

### 4. Consistent Formatting

Follow the existing structure and conventions in this repository:
- Use standard Markdown headings
- Use bullet points or numbered lists where appropriate
- Keep explanations focused, with no filler language
- Include code blocks only when necessary

### 5. No Informal or Conversational Language

Do not greet the reader, thank the reader, or reference the act of writing. Provide information, not commentary.

### 6. Self-Contained, Implementation-Focused Content

Documentation should describe:
- What a component does
- How to use it
- How it integrates with the system
- Any assumptions, constraints, or edge cases

It should not contain personal opinions, anecdotes, or speculative notes.

### 7. No Unnecessary Qualifiers

Avoid phrases like "simply," "just," "easily," and other softeners. Keep sentences neutral and technical.

### Scope of Application

These rules apply to:
- All project documentation
- Migrations and SQL comments
- Code comments
- Architecture notes
- API descriptions
- Internal developer guides

Adhering to these standards ensures consistency, professionalism, and long-term maintainability across all written materials in the project.

---

## Project Overview

### Purpose

RA-D-PS is a schema-agnostic radiology data processing system that parses, analyzes, and exports medical imaging XML data from various radiology systems. The project has evolved from a specific NYT XML parser into a flexible, profile-based data ingestion system.

### Key Capabilities

- Multi-format XML parsing (NYT, LIDC-IDRI, custom formats)
- Profile-based mapping system for schema-agnostic data ingestion
- GUI application (Tkinter) for non-technical users
- Multiple export formats (Excel, SQLite, PostgreSQL)
- Keyword extraction from XML and PDF documents
- Batch processing with progress tracking
- Database integration for analytics and reporting
- PYLIDC adapter for LIDC-IDRI dataset integration

### Current Development Status

- **Complete**: Core parsing, GUI, Excel/SQLite export
- **Complete**: Profile-based architecture implemented
- **Complete**: Database schema and models ready
- **In Progress**: Generic XML parser, REST API (FastAPI)
- **Planned**: Web interface, advanced analytics, ML integration

---

## Repository Structure

```
RA-D-PS/
├── src/ra_d_ps/              # Main source code package
│   ├── __init__.py           # Package initialization and public API
│   ├── parser.py             # Core parsing logic (legacy)
│   ├── gui.py                # Tkinter GUI application
│   ├── database.py           # SQLite database operations (legacy)
│   ├── radiology_database.py # Enhanced database with analytics
│   ├── config.py             # Configuration management
│   ├── profile_manager.py    # Profile CRUD and validation
│   ├── batch_processor.py    # Batch processing engine
│   ├── structure_detector.py # XML structure detection
│   ├── keyword_search_engine.py   # Full-text keyword search
│   ├── keyword_normalizer.py      # Keyword normalization
│   ├── pdf_keyword_extractor.py   # PDF text extraction
│   │
│   ├── parsers/              # Parser implementations
│   │   ├── base.py           # Abstract BaseParser interface
│   │   ├── xml_parser.py     # Generic profile-driven XML parser
│   │   └── legacy_radiology.py # Backward compatibility wrapper
│   │
│   ├── schemas/              # Pydantic data models
│   │   ├── canonical.py      # Canonical document schema (Pydantic v2)
│   │   └── profile.py        # Profile definition schema
│   │
│   ├── exporters/            # Export implementations
│   │   ├── base.py           # Abstract BaseExporter interface
│   │   └── excel_exporter.py # Excel export with formatting
│   │
│   ├── database/             # Database layer
│   │   ├── models.py         # SQLAlchemy ORM models
│   │   ├── db_config.py      # Database configuration
│   │   ├── keyword_models.py # Keyword-specific models
│   │   ├── keyword_repository.py     # Keyword data access
│   │   ├── parse_case_repository.py  # Parse case data access
│   │   └── migrations/       # Database migrations
│   │
│   ├── adapters/             # External system adapters
│   │   └── pylidc_adapter.py # LIDC-IDRI dataset integration
│   │
│   ├── validation/           # Data validation modules
│   │   └── data_validator.py # Validation utilities (placeholder)
│   │
│   └── profiles/             # Profile storage directory
│
├── tests/                    # Test suite
│   ├── test_organization.py
│   ├── test_complete_workflow.py
│   ├── test_excel_exporter.py
│   ├── test_pylidc_adapter.py
│   ├── test_gui.py
│   └── ... (20+ test files)
│
├── docs/                     # Documentation
│   ├── README.md
│   ├── IMPLEMENTATION_GUIDE_SCHEMA_AGNOSTIC.md
│   ├── SCHEMA_AGNOSTIC_SUMMARY.md
│   ├── API_REFERENCE.md
│   ├── DEVELOPER_GUIDE.md
│   └── ... (40+ documentation files)
│
├── examples/                 # Usage examples
│   ├── basic_parsing.py
│   ├── batch_processing.py
│   ├── keyword_search_engine_examples.py
│   └── ... (10+ examples)
│
├── scripts/                  # Utility scripts
│   ├── launch_gui.py
│   ├── setup_database.py
│   ├── test_detection.py
│   └── ... (15+ scripts)
│
├── migrations/               # PostgreSQL migrations
│   └── 001_initial_schema.sql
│
├── configs/                  # Configuration templates
│   ├── .env.example
│   └── config_template.json
│
├── data/                     # Sample/test data
├── validation_results/       # Validation output
├── backup/                   # Backup directory
│
├── .github/
│   └── workflows/
│       └── python-package.yml  # CI/CD workflow
│
├── .vscode/                  # VS Code settings
├── pyproject.toml            # Project metadata and dependencies
├── requirements.txt          # Python dependencies
├── setup.cfg                 # Tool configurations (pytest, flake8, mypy)
├── .pylintrc                 # Pylint configuration
├── Makefile                  # Development automation
├── Dockerfile                # Docker image definition
├── docker-compose.yml        # Multi-container setup
├── README.md                 # Project documentation
└── CLAUDE.md                 # This file
```

---

## Architecture & Design

### Architectural Principles

1. **Schema-Agnostic Design**: Profile-based mapping system allows parsing any XML/JSON structure without code changes
2. **Modular Components**: Parsers, exporters, and repositories follow abstract interfaces
3. **Backward Compatibility**: Legacy code preserved through wrapper classes
4. **Type Safety**: Pydantic v2 models with strict validation
5. **Separation of Concerns**: GUI, parsing, database, and export layers are independent

### Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Data Ingestion Flow                         │
└─────────────────────────────────────────────────────────────────┘

Source Files (XML/PDF/CSV)
        ↓
Profile Manager (selects appropriate profile)
        ↓
Parser Factory (instantiates correct parser)
        ↓
Generic Parser (profile-driven extraction)
        ↓
Canonical Schema (Pydantic validation)
        ↓
Repository Layer (data persistence)
        ├─→ PostgreSQL (JSONB + full-text search)
        ├─→ SQLite (analytics + local storage)
        └─→ Excel (formatted reports)
        ↓
Export/Query Layer
        ├─→ REST API (FastAPI - planned)
        ├─→ GUI (Tkinter - current)
        └─→ CLI tools
```

### Core Design Patterns

1. **Abstract Factory**: `ParserFactory` creates appropriate parser instances
2. **Strategy Pattern**: Different parsers (XML, LIDC, legacy) implement `BaseParser`
3. **Repository Pattern**: Data access abstracted through repository classes
4. **Builder Pattern**: Complex objects (canonical documents) built incrementally
5. **Adapter Pattern**: `PylidcAdapter` adapts LIDC-IDRI API to canonical schema

### Profile System

Profiles define how to map source data to canonical schema:

```python
{
  "profile_name": "lidc_idri_standard",
  "file_type": "XML",
  "description": "LIDC-IDRI radiology format",
  "mappings": [
    {
      "source_path": "/ResponseHeader/StudyInstanceUID",
      "target_path": "study_instance_uid",
      "data_type": "string",
      "required": true
    },
    # ... more mappings
  ],
  "validation_rules": {
    "required_fields": ["study_instance_uid"],
    "field_constraints": {...}
  },
  "transformations": {...}
}
```

---

## Development Setup

### Prerequisites

- **Python**: 3.8+ (tested on 3.8, 3.9, 3.10, 3.11, 3.12)
- **Docker**: For PostgreSQL and pgAdmin (optional but recommended)
- **Git**: Version control
- **PostgreSQL**: 16+ (via Docker or local installation)

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/luvisaisa/RA-D-PS.git
cd RA-D-PS

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Install package in editable mode
pip install -e .

# 5. Run tests to verify setup
pytest -q

# 6. (Optional) Start PostgreSQL via Docker
docker-compose up -d postgres

# 7. (Optional) Apply database migrations
make db-migrate

# 8. Launch GUI
python -m src.ra_d_ps.gui
# OR
make gui
```

### Development Tools Setup

```bash
# Install development dependencies
pip install pytest pytest-cov black flake8 mypy

# Format code
make fmt
# OR
black src/ tests/ --line-length 100

# Run linters
make lint
# OR
flake8 src/ tests/ --max-line-length 100
mypy src/ra_d_ps/

# Run tests with coverage
make test-coverage
# OR
pytest --cov=src/ra_d_ps --cov-report=html --cov-report=term
```

### Docker Setup

```bash
# Start PostgreSQL only
make db-up

# Start all services (including pgAdmin)
make docker-up

# View logs
make docker-logs

# Stop services
make docker-down

# Reset database (WARNING: deletes all data)
make db-reset
```

### Database Access

**PostgreSQL** (via Docker):
- Host: `localhost`
- Port: `5432`
- Database: `ra_d_ps_db`
- User: `ra_d_ps_user`
- Password: `changeme`

**pgAdmin** (optional UI):
- URL: `http://localhost:5050`
- Email: `admin@ra-d-ps.local`
- Password: `admin`

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Database
DATABASE_URL=postgresql://ra_d_ps_user:changeme@localhost:5432/ra_d_ps_db

# Paths
PROFILE_DIR=./profiles
DATA_DIR=./data

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/ra_d_ps.log
```

---

## Code Conventions

### Python Style

- **Style Guide**: PEP 8 with modifications (see `setup.cfg`)
- **Line Length**: 100 characters (not strict, see `.pylintrc`)
- **Formatter**: Black with `--line-length 100`
- **Type Hints**: Required for public APIs (`mypy` enforced)
- **Docstrings**: Google style for modules, classes, and public functions

### Naming Conventions

```python
# Modules: lowercase with underscores
# Files: snake_case.py
xml_parser.py
radiology_database.py

# Classes: PascalCase
class XMLParser(BaseParser):
    pass

class RadiologyCanonicalDocument(CanonicalDocument):
    pass

# Functions/Methods: snake_case
def parse_radiology_sample(xml_file: str) -> dict:
    pass

def export_to_excel(data: pd.DataFrame, output_path: str) -> None:
    pass

# Constants: UPPER_SNAKE_CASE
DEFAULT_BATCH_SIZE = 1000
MAX_RETRIES = 3

# Private members: leading underscore
class Parser:
    def __init__(self):
        self._cache = {}

    def _internal_parse(self) -> None:
        pass
```

### Import Organization

```python
# Standard library imports
import os
import sys
from typing import Optional, Dict, List
from pathlib import Path

# Third-party imports
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field
from sqlalchemy import Column, String

# Local imports (absolute from src root)
from ra_d_ps.parsers.base import BaseParser
from ra_d_ps.schemas.canonical import RadiologyCanonicalDocument
from ra_d_ps.database.models import DocumentModel
```

### Error Handling

```python
# Use specific exceptions
from ra_d_ps.exceptions import ParsingError, ValidationError

# Provide context in error messages
try:
    result = parse_xml(file_path)
except ElementTree.ParseError as e:
    raise ParsingError(f"Failed to parse XML file {file_path}: {e}") from e

# Log errors before raising
logger.error(f"Parsing failed for {file_path}", exc_info=True)
raise ParsingError(f"Parsing failed for {file_path}")
```

### Logging

```python
import logging

# Use module-level logger
logger = logging.getLogger(__name__)

# Log levels:
# DEBUG: Detailed diagnostic information
# INFO: General informational messages
# WARNING: Something unexpected but handled
# ERROR: Serious problem, operation failed
# CRITICAL: System-level failure

logger.debug(f"Processing file: {file_path}")
logger.info(f"Successfully parsed {len(results)} records")
logger.warning(f"Missing required field 'study_uid' in {file_path}")
logger.error(f"Failed to connect to database: {e}")
```

### Type Hints

```python
from typing import Optional, List, Dict, Union, Tuple, Any
from pathlib import Path

# Function signatures
def parse_xml_file(
    file_path: Union[str, Path],
    profile_name: str,
    validate: bool = True
) -> Optional[RadiologyCanonicalDocument]:
    """Parse XML file using specified profile.

    Args:
        file_path: Path to XML file
        profile_name: Name of parsing profile to use
        validate: Whether to validate against schema

    Returns:
        Parsed canonical document or None if parsing failed

    Raises:
        ParsingError: If XML is malformed
        ValidationError: If data fails schema validation
    """
    pass

# Class attributes
class Parser:
    config: Dict[str, Any]
    profiles: List[Profile]
    _cache: Dict[str, Any]
```

### Pydantic Models

```python
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class DocumentMetadata(BaseModel):
    """Document metadata schema."""

    title: str = Field(..., description="Document title")
    date: datetime = Field(..., description="Document date")
    source: Optional[str] = Field(None, description="Data source")

    @validator('title')
    def title_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v

    class Config:
        # Pydantic v2 uses ConfigDict
        json_schema_extra = {
            "example": {
                "title": "Radiology Report",
                "date": "2025-11-21T10:00:00Z",
                "source": "LIDC-IDRI"
            }
        }
```

---

## Testing Strategy

### Test Structure

```
tests/
├── test_organization.py          # Repository organization tests
├── test_complete_workflow.py     # End-to-end workflow tests
├── test_excel_exporter.py        # Excel export functionality
├── test_pylidc_adapter.py        # LIDC adapter tests
├── test_gui.py                   # GUI component tests
├── test_foundation_validation.py # Core validation tests
├── test_type_safety.py           # Type checking tests
└── integration/                  # Integration tests (planned)
```

### Test Categories

1. **Unit Tests**: Test individual functions and classes
2. **Integration Tests**: Test component interactions
3. **End-to-End Tests**: Test complete workflows
4. **GUI Tests**: Test GUI components (mocked)
5. **Regression Tests**: Ensure backward compatibility

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_excel_exporter.py

# Run specific test function
pytest tests/test_excel_exporter.py::test_export_to_excel

# Run tests matching pattern
pytest -k "keyword"

# Run with coverage
pytest --cov=src/ra_d_ps --cov-report=html

# Run only unit tests (exclude integration)
pytest tests/ -k "not integration"
```

### Writing Tests

```python
import pytest
from pathlib import Path
from ra_d_ps.parsers.xml_parser import XMLParser
from ra_d_ps.schemas.canonical import RadiologyCanonicalDocument

class TestXMLParser:
    """Test suite for XMLParser."""

    @pytest.fixture
    def sample_xml_path(self, tmp_path):
        """Create temporary XML file for testing."""
        xml_content = """<?xml version="1.0"?>
        <root><title>Test</title></root>
        """
        xml_file = tmp_path / "test.xml"
        xml_file.write_text(xml_content)
        return xml_file

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return XMLParser(profile_name="test_profile")

    def test_parse_xml_success(self, parser, sample_xml_path):
        """Test successful XML parsing."""
        result = parser.parse(sample_xml_path)
        assert result is not None
        assert isinstance(result, RadiologyCanonicalDocument)

    def test_parse_xml_invalid_file(self, parser):
        """Test parsing with non-existent file."""
        with pytest.raises(FileNotFoundError):
            parser.parse("nonexistent.xml")

    @pytest.mark.parametrize("file_name,expected", [
        ("valid.xml", True),
        ("invalid.txt", False),
    ])
    def test_file_validation(self, parser, file_name, expected):
        """Test file validation with multiple inputs."""
        result = parser.is_valid_file(file_name)
        assert result == expected
```

### Test Fixtures

Common fixtures are available in `conftest.py` (if exists):

```python
# conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def test_data_dir():
    """Path to test data directory."""
    return Path(__file__).parent / "data"

@pytest.fixture
def sample_profile():
    """Sample profile for testing."""
    return {
        "profile_name": "test",
        "file_type": "XML",
        "mappings": [...]
    }
```

---

## Common Workflows

### 1. Adding a New Parser

```bash
# 1. Create parser class in src/ra_d_ps/parsers/
cat > src/ra_d_ps/parsers/json_parser.py << 'EOF'
from .base import BaseParser
from ra_d_ps.schemas.canonical import CanonicalDocument

class JSONParser(BaseParser):
    """JSON document parser."""

    def parse(self, file_path: str) -> CanonicalDocument:
        # Implementation
        pass
EOF

# 2. Update parsers/__init__.py
# Add: from .json_parser import JSONParser
# Add to __all__

# 3. Create tests
cat > tests/test_json_parser.py << 'EOF'
from ra_d_ps.parsers.json_parser import JSONParser

def test_json_parser():
    # Test implementation
    pass
EOF

# 4. Run tests
pytest tests/test_json_parser.py -v

# 5. Update documentation
# Add parser to README.md and API_REFERENCE.md
```

### 2. Creating a New Profile

```bash
# 1. Create profile JSON
cat > profiles/my_custom_format.json << 'EOF'
{
  "profile_name": "my_custom_format",
  "file_type": "XML",
  "description": "Custom XML format parser",
  "mappings": [
    {
      "source_path": "/root/field",
      "target_path": "canonical_field",
      "data_type": "string",
      "required": true
    }
  ],
  "validation_rules": {
    "required_fields": ["canonical_field"]
  }
}
EOF

# 2. Validate profile
python -c "
from ra_d_ps.profile_manager import get_profile_manager
manager = get_profile_manager()
profile = manager.import_profile('profiles/my_custom_format.json')
is_valid, errors = manager.validate_profile(profile)
print(f'Valid: {is_valid}')
print(f'Errors: {errors}')
"

# 3. Test with sample data
python -c "
from ra_d_ps.parsers.xml_parser import XMLParser
parser = XMLParser(profile_name='my_custom_format')
result = parser.parse('path/to/sample.xml')
print(result)
"
```

### 3. Running the GUI Application

```bash
# Method 1: Using make
make gui

# Method 2: Using Python module
python -m src.ra_d_ps.gui

# Method 3: Using launch script
python scripts/launch_gui.py

# Method 4: Direct import
python -c "from ra_d_ps import NYTXMLGuiApp; NYTXMLGuiApp().run()"
```

### 4. Batch Processing XML Files

```bash
# Using Python API
python << 'EOF'
from ra_d_ps import parse_multiple
from pathlib import Path

xml_files = list(Path("data/xml").glob("*.xml"))
results = parse_multiple(
    xml_files,
    batch_size=100,
    progress_callback=lambda i, total: print(f"{i}/{total}")
)
print(f"Processed {len(results)} files")
EOF

# Using batch processor
python << 'EOF'
from ra_d_ps.batch_processor import BatchProcessor

processor = BatchProcessor(profile_name="lidc_idri_standard")
results = processor.process_directory("data/xml", recursive=True)
processor.export_results("output.xlsx", format="excel")
EOF
```

### 5. Database Operations

```bash
# Start database
make db-up

# Apply migrations
make db-migrate

# Check database status
make db-status

# Open database shell
make db-shell

# Reset database (WARNING: deletes all data)
make db-reset
```

### 6. Exporting Data

```bash
# Export to Excel (template format)
python << 'EOF'
from ra_d_ps import export_excel
import pandas as pd

df = pd.read_csv("parsed_data.csv")
export_excel(df, "output.xlsx", format="template")
EOF

# Export to SQLite
python << 'EOF'
from ra_d_ps.database import RadiologyDatabase

db = RadiologyDatabase("output.db")
db.insert_batch(parsed_data)
db.export_to_excel("analytics.xlsx")
EOF

# Export to PostgreSQL
python << 'EOF'
from ra_d_ps.database.models import DocumentModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("postgresql://ra_d_ps_user:changeme@localhost/ra_d_ps_db")
Session = sessionmaker(bind=engine)
session = Session()

# Insert documents
for doc in canonical_documents:
    model = DocumentModel.from_canonical(doc)
    session.add(model)
session.commit()
EOF
```

### 7. Running Code Quality Checks

```bash
# Format code
make fmt

# Run all linters
make lint

# Individual linters
flake8 src/ tests/
mypy src/ra_d_ps/
pylint src/ra_d_ps/

# Check for security issues (if bandit installed)
bandit -r src/

# Check for unused imports (if autoflake installed)
autoflake --remove-all-unused-imports --check src/
```

### 8. Git Workflow

```bash
# Work directly on the designated branch (provided in task context)
# DO NOT create new feature branches

# Make changes and commit with clear, descriptive messages
git add .
git commit -m "feat: add JSON parser implementation"

# Force push to the designated branch when needed
git push -f -u origin <designated-branch-name>

# Note: The designated branch is specified in the task context
# For Claude Code sessions, this will be a branch starting with 'claude/'
```

---

## Key Components Reference

### Core Parser (`src/ra_d_ps/parser.py`)

**Purpose**: Legacy parsing logic, still used by GUI and examples

**Key Functions**:
- `parse_radiology_sample(xml_file)`: Parse single XML file
- `parse_multiple(files, batch_size)`: Batch processing
- `detect_parse_case(xml_root)`: Detect XML structure type
- `export_excel(df, output_path)`: Export to Excel

**Parse Cases**:
- `Complete_Attributes`: Full radiologist data
- `With_Reason_Partial`: Partial attributes with reason
- `Core_Attributes_Only`: Essential attributes
- `LIDC_Single_Session`: Single LIDC reading
- `LIDC_Multi_Session_X`: Multiple LIDC sessions (2-4 radiologists)

### Profile Manager (`src/ra_d_ps/profile_manager.py`)

**Purpose**: Manage parsing profiles (CRUD operations)

**Key Methods**:
```python
manager = get_profile_manager()

# Load profile
profile = manager.load_profile("lidc_idri_standard")

# List all profiles
profiles = manager.list_profiles()

# Validate profile
is_valid, errors = manager.validate_profile(profile)

# Import/export
manager.import_profile("path/to/profile.json")
manager.export_profile("profile_name", "output.json")
```

### Canonical Schema (`src/ra_d_ps/schemas/canonical.py`)

**Purpose**: Define standardized data models (Pydantic v2)

**Key Classes**:
- `CanonicalDocument`: Base class for all documents
- `RadiologyCanonicalDocument`: Radiology-specific document
- `DocumentMetadata`: Document metadata (title, date, source)
- `EntityExtraction`: Entity extraction results

### XML Parser (`src/ra_d_ps/parsers/xml_parser.py`)

**Purpose**: Generic profile-driven XML parsing

**Usage**:
```python
from ra_d_ps.parsers.xml_parser import XMLParser

parser = XMLParser(profile_name="lidc_idri_standard")
document = parser.parse("data/sample.xml")
print(document.model_dump_json(indent=2))
```

### Batch Processor (`src/ra_d_ps/batch_processor.py`)

**Purpose**: Process large batches of files efficiently

**Features**:
- Memory-efficient processing
- Progress tracking
- Error handling and retry logic
- Structure detection and optimization

### Database Models (`src/ra_d_ps/database/models.py`)

**Purpose**: SQLAlchemy ORM models for PostgreSQL

**Tables**:
- `documents`: Main document metadata
- `document_content`: JSONB content storage
- `profiles`: Profile definitions
- `ingestion_logs`: Processing audit logs
- `keywords`: Extracted keywords (with full-text search)

### GUI Application (`src/ra_d_ps/gui.py`)

**Purpose**: Tkinter GUI for non-technical users

**Features**:
- File/folder selection
- Batch processing with progress bar
- Export to Excel/SQLite
- Real-time logging
- Error handling and user feedback

### Excel Exporter (`src/ra_d_ps/exporters/excel_exporter.py`)

**Purpose**: Export data to formatted Excel files

**Formats**:
- **Standard**: Separate sheets by parse case
- **Template**: Radiologist 1-4 column structure
- **Multi-folder**: Combined and per-folder sheets

### PYLIDC Adapter (`src/ra_d_ps/adapters/pylidc_adapter.py`)

**Purpose**: Integrate with LIDC-IDRI dataset

**Usage**:
```python
from ra_d_ps.adapters.pylidc_adapter import PylidcAdapter

adapter = PylidcAdapter()
scans = adapter.get_scans()
for scan in scans:
    canonical_doc = adapter.convert_to_canonical(scan)
```

### Keyword Search Engine (`src/ra_d_ps/keyword_search_engine.py`)

**Purpose**: Full-text keyword search across documents

**Features**:
- Multi-field search (title, content, metadata)
- Fuzzy matching and normalization
- Relevance scoring
- PostgreSQL full-text search integration

---

## AI Assistant Guidelines

### When Working on This Codebase

1. **Always Read First**: Before making changes, read relevant files using the `Read` tool
2. **Preserve Backward Compatibility**: Legacy code (`parser.py`, `gui.py`) must continue working
3. **Use Type Hints**: All new code should include type hints
4. **Write Tests**: Add tests for new functionality
5. **Update Documentation**: Update relevant .md files when changing functionality
6. **Follow Existing Patterns**: Match existing code style and structure

### File Organization Principles

- **Core logic**: `src/ra_d_ps/` package
- **Abstract interfaces**: `parsers/base.py`, `exporters/base.py`
- **Implementations**: Subfolders (`parsers/`, `exporters/`, `database/`)
- **Configuration**: `configs/` directory
- **Documentation**: `docs/` directory
- **Examples**: `examples/` directory
- **Scripts**: One-off utilities in `scripts/`

### Common Pitfalls to Avoid

1. **Breaking imports**: The package uses absolute imports from `src.ra_d_ps`
2. **Removing legacy code**: Wrap it with new interfaces instead
3. **Hardcoded paths**: Use `Path` objects and configuration
4. **Skipping validation**: Always validate user inputs and external data
5. **Ignoring errors**: Proper error handling and logging required
6. **Modifying Pydantic models carelessly**: Schema changes affect database

### Making Changes Safely

```python
# Good: Add new functionality alongside old
class XMLParser(BaseParser):
    def parse(self, file_path: str) -> CanonicalDocument:
        # New implementation
        pass

class LegacyRadiologyParser(BaseParser):
    """Wrapper for backward compatibility."""
    def parse(self, file_path: str) -> CanonicalDocument:
        # Call old parse_radiology_sample()
        legacy_result = parse_radiology_sample(file_path)
        return self._convert_to_canonical(legacy_result)

# Bad: Replace existing functionality directly
# Do not modify parse_radiology_sample() directly
```

### Testing Guidelines for AI

- **Before committing**: Run `pytest -q` to ensure tests pass
- **After adding features**: Add corresponding tests
- **For bug fixes**: Add regression test first
- **For refactoring**: Ensure all existing tests still pass

### Documentation Requirements

When adding new features:
1. Update `README.md` with user-facing changes
2. Update `docs/API_REFERENCE.md` for API changes
3. Add examples to `examples/` directory
4. Update this `CLAUDE.md` file for structural changes

### Database Migration Guidelines

```bash
# 1. Create new migration file
cat > migrations/002_add_new_feature.sql << 'EOF'
-- Migration: Add new feature
-- Date: 2025-11-21

BEGIN;

-- Your SQL changes here
ALTER TABLE documents ADD COLUMN new_field TEXT;

-- Update version
INSERT INTO schema_migrations (version, applied_at)
VALUES ('002', NOW());

COMMIT;
EOF

# 2. Test migration on clean database
make db-reset
make db-migrate

# 3. Verify changes
make db-shell
\d documents
```

### Profile Creation Guidelines

When creating new profiles:
1. Analyze source XML/JSON structure
2. Map fields to canonical schema
3. Define validation rules
4. Test with sample data
5. Document in profile description

### Code Review Checklist

Before submitting changes:
- [ ] Code follows PEP 8 and project conventions
- [ ] Type hints added for public APIs
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] No hardcoded paths or credentials
- [ ] Error handling implemented
- [ ] Logging added for debugging
- [ ] Backward compatibility maintained

---

## Troubleshooting

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'ra_d_ps'`

**Solution**:
```bash
# Ensure package is installed
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/RA-D-PS/src"
```

**Problem**: `ImportError: cannot import name 'parse_radiology_sample'`

**Solution**: Check import path - should be `from ra_d_ps.parser import parse_radiology_sample`

### Database Connection Issues

**Problem**: `psycopg2.OperationalError: could not connect to server`

**Solution**:
```bash
# Check if PostgreSQL is running
docker-compose ps

# Restart PostgreSQL
make db-down
make db-up

# Verify connection
psql -h localhost -U ra_d_ps_user -d ra_d_ps_db
```

### Test Failures

**Problem**: Tests fail after changes

**Solution**:
```bash
# Run with verbose output to see details
pytest -v

# Run specific failing test
pytest tests/test_name.py::test_function -v

# Check for import issues
python -c "from ra_d_ps import parser"

# Clear pytest cache
rm -rf .pytest_cache
pytest --cache-clear
```

### GUI Freezing

**Problem**: GUI freezes during processing

**Solution**: Ensure long operations run in background threads (see `src/ra_d_ps/gui.py` for patterns)

### Memory Issues

**Problem**: Out of memory during batch processing

**Solution**:
```python
# Reduce batch size
from ra_d_ps import parse_multiple
results = parse_multiple(files, batch_size=50)  # Reduce from default 1000

# Or use streaming
from ra_d_ps.batch_processor import BatchProcessor
processor = BatchProcessor(profile_name="lidc_idri_standard")
processor.process_directory("data/", streaming=True)
```

### Profile Validation Errors

**Problem**: Profile fails validation

**Solution**:
```python
from ra_d_ps.profile_manager import get_profile_manager

manager = get_profile_manager()
profile = manager.load_profile("my_profile")
is_valid, errors = manager.validate_profile(profile)

if not is_valid:
    for error in errors:
        print(f"Error: {error}")
        # Fix issues in profile JSON
```

---

## Additional Resources

### Documentation Files

- **README.md**: Project overview and quick start
- **QUICKSTART_SCHEMA_AGNOSTIC.md**: Schema-agnostic system setup
- **docs/IMPLEMENTATION_GUIDE_SCHEMA_AGNOSTIC.md**: Detailed implementation phases
- **docs/SCHEMA_AGNOSTIC_SUMMARY.md**: Architecture overview
- **docs/API_REFERENCE.md**: Complete API documentation
- **docs/DEVELOPER_GUIDE.md**: Developer onboarding

### Example Scripts

- **examples/basic_parsing.py**: Simple XML parsing example
- **examples/batch_processing.py**: Batch processing example
- **examples/database_integration.py**: Database integration example
- **examples/keyword_search_engine_examples.py**: Keyword search usage
- **examples/pylidc_integration.py**: LIDC-IDRI integration example

### Utility Scripts

- **scripts/launch_gui.py**: Launch GUI application
- **scripts/setup_database.py**: Database setup automation
- **scripts/test_detection.py**: Test XML structure detection
- **scripts/validate_xml_comprehensive_dataset.py**: Validate XML dataset

### External References

- **LIDC-IDRI Dataset**: https://wiki.cancerimagingarchive.net/display/Public/LIDC-IDRI
- **Pydantic Documentation**: https://docs.pydantic.dev/latest/
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/

---

## Quick Command Reference

```bash
# Setup
make setup              # Install dependencies
make install            # Install package in editable mode

# Database
make db-up              # Start PostgreSQL
make db-down            # Stop PostgreSQL
make db-migrate         # Apply migrations
make db-reset           # Reset database (WARNING: deletes data)
make db-shell           # Open PostgreSQL shell
make pgadmin            # Start pgAdmin UI

# Development
make test               # Run all tests
make test-coverage      # Run tests with coverage
make fmt                # Format code with black
make lint               # Run linters
make clean              # Remove build artifacts

# Running
make gui                # Launch GUI
make api                # Start FastAPI server (when implemented)

# Docker
make docker-build       # Build Docker image
make docker-up          # Start all services
make docker-down        # Stop all services
make docker-logs        # View container logs
```

---

## Changelog

### Version 1.0.0 (November 2025)
- Repository organization complete
- Schema-agnostic foundation implemented
- PostgreSQL integration ready
- Profile system operational
- Canonical schema defined
- CI/CD pipeline configured
- Comprehensive documentation added

### Previous Milestones
- Core XML parsing engine
- GUI application (Tkinter)
- Excel/SQLite export
- Multi-folder processing
- PYLIDC adapter
- Keyword extraction system

---

## Contributing

**For AI Assistants**: When making contributions:
1. Work directly on the designated branch specified in task context (DO NOT create new feature branches)
2. Make changes following this guide
3. Run tests: `pytest -q`
4. Run linters: `make lint`
5. Update documentation
6. Commit with clear, descriptive messages
7. Force push to the designated branch when complete: `git push -f -u origin <branch-name>`

---

## License

This project is licensed under the MIT License.

---

## Authors

- **Isa Lucia Schlichting** - Original author and maintainer
- **RA-D-PS Team** - Development team

---

**Last Updated**: November 21, 2025
**Document Version**: 1.0.0
**For Questions**: Refer to documentation in `docs/` or create an issue on GitHub

---

This document serves as a reference for AI assistants to understand the codebase structure, conventions, and workflows.
