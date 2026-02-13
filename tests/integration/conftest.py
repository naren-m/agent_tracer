"""Integration test fixtures with real TraceClient."""

import pytest
import tempfile
import shutil
from pathlib import Path

from agent_tracer import TraceClient
from agent_tracer.storage import TraceStorageBackend


@pytest.fixture
def temp_storage_dir():
    """Create temporary directory for trace storage."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def real_trace_client(temp_storage_dir):
    """Create real TraceClient with file-based storage (no database).
    
    Uses TraceStorageBackend with db_conn=None, which skips PostgreSQL
    writes but still stores full trace JSON to disk.
    """
    backend = TraceStorageBackend(db_conn=None, storage_dir=temp_storage_dir)
    client = TraceClient(backend)
    return client


@pytest.fixture
def storage_dir_path(temp_storage_dir):
    """Return Path object for storage directory inspection."""
    return Path(temp_storage_dir)
