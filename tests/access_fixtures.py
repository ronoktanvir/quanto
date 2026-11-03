"""Explicit fixture authority for named invented stores, never production roots."""
from pathlib import Path

import pytest

from quanto.evaluation_registry import Supervisor


class SyntheticAccess:
    def __init__(self, root):
        self.allowed_parent = Path(root)
        self.session = None
        self.bind(root)

    def bind(self, root, *, synthetic=True):
        root = Path(root)
        if root != self.allowed_parent and self.allowed_parent not in root.parents:
            raise AssertionError("Fixture authority is restricted to its invented directory")
        if self.session is not None:
            self.session.__exit__(None, None, None)
        self.session = Supervisor(root, synthetic=synthetic).session()
        self.session.__enter__()
        return self.session

    def close(self):
        if self.session is not None:
            self.session.__exit__(None, None, None)


@pytest.fixture
def synthetic_access(tmp_path):
    """Opted-in modules get exactly tmp_path; other roots need explicit bind()."""
    access = SyntheticAccess(tmp_path)
    try:
        yield access
    finally:
        access.close()
