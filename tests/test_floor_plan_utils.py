"""Tests for pure utility functions in blender_addon/handlers/floor_plan.py."""

from tests._helpers import load_handler_module

fp = load_handler_module("floor_plan.py")

_classify_object = fp._classify_object
_get_abbreviation = fp._get_abbreviation
_render_view = fp._render_view
VIEW_DEFS = fp.VIEW_DEFS


# ---------------------------------------------------------------------------
# _classify_object
# ---------------------------------------------------------------------------

class TestClassifyObject:
    def test_wall_names(self):
        assert _classify_object("Wall_Back") == "W"
        assert _classify_object("wall_left") == "W"
        assert _classify_object("boundary_north") == "W"

    def test_floor(self):
        assert _classify_object("Floor") == "#"
        assert _classify_object("floor_main") == "#"

    def test_door(self):
        assert _classify_object("Door_Entry") == "D"
        assert _classify_object("door") == "D"

    def test_unknown_returns_none(self):
        assert _classify_object("Sofa") is None
        assert _classify_object("Lamp_01") is None
        assert _classify_object("Table") is None


# ---------------------------------------------------------------------------
# _get_abbreviation
# ---------------------------------------------------------------------------

class TestGetAbbreviation:
    def test_single_char_when_available(self):
        used = {}
        assert _get_abbreviation("Sofa", used) == "S"

    def test_avoids_conflict(self):
        used = {"S": "Shelf"}
        abbr = _get_abbreviation("Sofa", used)
        assert abbr.startswith("S")
        assert len(abbr) == 2
        assert abbr not in used

    def test_multiple_conflicts(self):
        used = {"S": "Shelf", "So": "Something", "Sf": "Stuff"}
        abbr = _get_abbreviation("Sofa", used)
        assert abbr not in used

    def test_numeric_fallback(self):
        used = {"A": "x", "Ab": "x", "AB": "x"}
        abbr = _get_abbreviation("AB", used)
        assert abbr not in used


# ---------------------------------------------------------------------------
# _render_view
# ---------------------------------------------------------------------------

class TestRenderView:
    def _objs(self):
        return [
            {"name": "Wall_Back", "min": (0, 0, 0), "max": (4, 0.15, 2.7)},
            {"name": "Sofa", "min": (1, 0.5, 0), "max": (3, 1.5, 0.9)},
        ]

    def test_top_view_has_legend(self):
        out = _render_view("top", self._objs(), 0.5, True, 60)
        assert "Legend:" in out
        assert "W=Wall_Back" in out

    def test_no_labels_omits_legend(self):
        out = _render_view("top", self._objs(), 0.5, False, 60)
        assert "Legend:" not in out

    def test_view_header(self):
        out = _render_view("front", self._objs(), 0.5, True, 60)
        assert "Front" in out

    def test_all_views_render(self):
        for name in VIEW_DEFS:
            out = _render_view(name, self._objs(), 0.5, False, 40)
            assert len(out) > 0

    def test_grid_contains_wall_char(self):
        out = _render_view("top", self._objs(), 0.5, False, 60)
        grid = "".join(l for l in out.split("\n") if l and not l.startswith("-") and not l.startswith("Axes"))
        assert "W" in grid

    def test_finer_grid_more_rows(self):
        coarse = _render_view("top", self._objs(), 1.0, False, 200)
        fine = _render_view("top", self._objs(), 0.25, False, 200)
        def grid_rows(s):
            return [l for l in s.split("\n") if l and not l.startswith("-") and not l.startswith("Axes") and not l.startswith("Legend")]
        assert len(grid_rows(fine)) >= len(grid_rows(coarse))

    def test_max_grid_caps(self):
        objs = [{"name": "BigFloor", "min": (0, 0, 0), "max": (100, 100, 0.1)}]
        out = _render_view("top", objs, 0.1, False, 20)
        grid = [l for l in out.split("\n") if l and not l.startswith("-") and not l.startswith("Axes")]
        assert len(grid) <= 20
