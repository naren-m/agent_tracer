# Packaging Configuration

This project uses modern Python packaging standards (PEP 517/518).

## Primary Configuration: pyproject.toml

All packaging configuration is now in `pyproject.toml`:
- Project metadata (name, version, description)
- Dependencies and optional dependencies
- Build system configuration
- Tool configurations (pytest, coverage)

## Legacy Files

- **setup.py.legacy**: Old setuptools configuration (DEPRECATED)
  - Kept for reference only
  - All configuration migrated to pyproject.toml
  - Not used by build process

## Building and Installing

### Development Installation
```bash
pip install -e .
pip install -e ".[dev]"  # Include dev dependencies
```

### Building Distribution
```bash
pip install build
python -m build
```

This creates both wheel and source distributions using pyproject.toml.

### Publishing (when ready)
```bash
pip install twine
twine upload dist/*
```

## Migration Notes

**2025-02-12**: Migrated from setup.py to pyproject.toml
- Created README.md and LICENSE files
- Updated pyproject.toml to reference README.md
- Deprecated setup.py (renamed to .legacy)
- Modern pip (>=21.3) fully supports pyproject.toml
