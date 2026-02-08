"""Shared fixtures and import helpers for blender-orchestrator tests.

The blender_addon package imports bpy/bmesh at the package level, so we
can't simply ``import blender_addon.handlers.foo``.  Instead we use
importlib to load individual handler *files* directly, after stubbing
the Blender-only modules they need.
"""

import importlib.util
import json
import os
import sys
import types

import pytest


# ---------------------------------------------------------------------------
# Blender stubs — enough to let the handler files parse without error
# ---------------------------------------------------------------------------

def _ensure_stub(name):
    if name not in sys.modules:
        sys.modules[name] = types.ModuleType(name)


class _Vector(list):
    """Minimal mathutils.Vector stand-in."""
    def __init__(self, vals=(0, 0, 0)):
        super().__init__(vals)

    @property
    def x(self): return self[0]
    @property
    def y(self): return self[1]
    @property
    def z(self): return self[2]

    def __sub__(self, other):
        return _Vector([a - b for a, b in zip(self, other)])
    def __add__(self, other):
        return _Vector([a + b for a, b in zip(self, other)])
    def __mul__(self, scalar):
        return _Vector([v * scalar for v in self])
    def __rmul__(self, scalar):
        return self.__mul__(scalar)
    def __truediv__(self, scalar):
        return _Vector([v / scalar for v in self])
    def __matmul__(self, other):
        return other
    def __neg__(self):
        return _Vector([-v for v in self])
    @property
    def length(self):
        return sum(v**2 for v in self) ** 0.5
    def normalized(self):
        l = self.length
        return _Vector([v / l for v in self]) if l else _Vector(self)
    def dot(self, other):
        return sum(a * b for a, b in zip(self, other))
    def copy(self):
        return _Vector(list(self))


class _Euler:
    def __init__(self, vals=(0, 0, 0)):
        self._v = list(vals)
    @property
    def x(self): return self._v[0]
    @property
    def y(self): return self._v[1]
    @property
    def z(self): return self._v[2]
    def copy(self): return _Euler(list(self._v))
    def __iter__(self): return iter(self._v)


# Install stubs
for mod in ("bpy", "bmesh", "mathutils", "gpu", "gpu_extras", "bl_math",
            "blender_addon", "blender_addon.utils",
            "blender_addon.utils.serializers"):
    _ensure_stub(mod)

sys.modules["mathutils"].Vector = _Vector
sys.modules["mathutils"].Euler = _Euler
# serialize_object stub
sys.modules["blender_addon.utils.serializers"].serialize_object = lambda *a, **kw: {}


def load_handler_module(filename: str):
    """Import a single handler .py file from blender_addon/handlers/ by filename."""
    base = os.path.join(os.path.dirname(__file__), "..", "blender_addon", "handlers")
    path = os.path.join(base, filename)
    spec = importlib.util.spec_from_file_location(f"_handler_{filename}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def dimensions_db():
    """Load the object dimensions database for testing."""
    data_path = os.path.join(
        os.path.dirname(__file__), "..", "mcp_server", "data", "object_dimensions.json",
    )
    with open(data_path) as f:
        return json.load(f)
