import importlib.util
from pathlib import Path
import pytest

path = Path(__file__).parent / "fixtures" / "synthetic_backup" / "build_fixture.py"
spec = importlib.util.spec_from_file_location("synthetic_fixture", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

@pytest.fixture
def backup_path(tmp_path):
    return module.build_fixture(tmp_path / "backup")
