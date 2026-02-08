"""Tests for dimensions database and handler functions."""

import pytest
from tests._helpers import load_handler_module

dims = load_handler_module("dimensions.py")
_load_db = dims._load_db
get_object_dimensions = dims.get_object_dimensions
list_known_objects = dims.list_known_objects
get_placement_rules = dims.get_placement_rules


class TestLoadDb:
    def test_loads_successfully(self):
        db = _load_db()
        assert "objects" in db
        assert "metadata" in db

    def test_has_objects(self):
        db = _load_db()
        assert len(db["objects"]) > 0

    def test_object_structure(self):
        db = _load_db()
        obj = next(iter(db["objects"].values()))
        assert "category" in obj
        dims_data = obj["dimensions"]
        for axis in ("width", "depth", "height"):
            assert len(dims_data[axis]) == 2
            assert dims_data[axis][0] <= dims_data[axis][1]


class TestGetObjectDimensions:
    def test_known_object(self):
        result = get_object_dimensions({"object_type": "dining_chair"})
        assert result["object_type"] == "dining_chair"
        assert result["category"] == "seating"

    def test_unknown_object_raises(self):
        with pytest.raises(ValueError, match="not found"):
            get_object_dimensions({"object_type": "flying_carpet"})

    def test_partial_match_suggestion(self):
        with pytest.raises(ValueError, match="Did you mean"):
            get_object_dimensions({"object_type": "chair"})


class TestListKnownObjects:
    def test_list_all(self):
        result = list_known_objects({})
        assert result["total"] > 0

    def test_filter_by_category(self):
        result = list_known_objects({"category": "seating"})
        assert "seating" in result["categories"]
        assert len(result["categories"]) == 1

    def test_invalid_category_raises(self):
        with pytest.raises(ValueError, match="No objects in category"):
            list_known_objects({"category": "nonexistent"})


class TestGetPlacementRules:
    def test_known_object(self):
        result = get_placement_rules({"object_type": "bookshelf"})
        p = result["placement"]
        assert "against_wall" in p
        assert "typical_groupings" in p

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="not found"):
            get_placement_rules({"object_type": "unicorn_stand"})


class TestDataIntegrity:
    def test_all_dimensions_valid(self):
        db = _load_db()
        for name, obj in db["objects"].items():
            for axis in ("width", "depth", "height"):
                d = obj["dimensions"][axis]
                assert d[0] > 0 and d[0] <= d[1], f"{name} {axis}"

    def test_all_placements_valid(self):
        db = _load_db()
        for name, obj in db["objects"].items():
            p = obj["placement"]
            assert isinstance(p["against_wall"], bool)
            assert p["floor_clearance"] >= 0
            assert isinstance(p["typical_groupings"], list)
