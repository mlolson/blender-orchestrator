"""Tests for _parse_position_instruction in blender_addon/handlers/spatial.py."""

from tests._helpers import load_handler_module

spatial = load_handler_module("spatial.py")
_parse_position_instruction = spatial._parse_position_instruction


class TestParsePositionInstruction:
    def test_place_on(self):
        r = _parse_position_instruction("place on the desk")
        assert r["action"] == "place"
        assert r["relation"] == "on"
        assert "desk" in r["reference_object"]

    def test_put_on_table(self):
        r = _parse_position_instruction("put it on the table")
        assert r["action"] == "place"
        assert r["relation"] == "on"
        assert "table" in r["reference_object"]

    def test_next_to(self):
        r = _parse_position_instruction("move next to the chair")
        assert r["action"] == "place"
        assert r["relation"] == "next_to"
        assert "chair" in r["reference_object"]

    def test_left_of(self):
        r = _parse_position_instruction("put it to the left of the bookshelf")
        assert r["relation"] == "left_of"
        assert "bookshelf" in r["reference_object"]

    def test_right_of(self):
        r = _parse_position_instruction("set to the right of the lamp")
        assert r["relation"] == "right_of"
        assert "lamp" in r["reference_object"]

    def test_in_front_of(self):
        r = _parse_position_instruction("place in front of the sofa")
        assert r["relation"] == "in_front_of"
        assert "sofa" in r["reference_object"]

    def test_behind(self):
        r = _parse_position_instruction("move behind the couch")
        assert r["relation"] == "behind"
        assert "couch" in r["reference_object"]

    def test_above(self):
        r = _parse_position_instruction("place above the counter")
        assert r["relation"] == "above"

    def test_below(self):
        r = _parse_position_instruction("put under the desk")
        assert r["relation"] == "below"

    def test_move_meters_left(self):
        r = _parse_position_instruction("move 2 meters left")
        assert r["action"] == "move_relative"
        assert r["distance"] == 2.0
        assert r["direction"] == "left"

    def test_move_fractional(self):
        r = _parse_position_instruction("move 0.5m right")
        assert r["action"] == "move_relative"
        assert r["distance"] == 0.5
        assert r["direction"] == "right"

    def test_move_direction_only_defaults_1m(self):
        r = _parse_position_instruction("move up")
        assert r["action"] == "move_relative"
        assert r["direction"] == "up"
        assert r["distance"] == 1.0

    def test_move_backward_normalised(self):
        r = _parse_position_instruction("move 3 meters backward")
        assert r["action"] == "move_relative"
        assert r["direction"] == "back"

    def test_near(self):
        r = _parse_position_instruction("place near the window")
        assert r["relation"] == "near"

    def test_center(self):
        r = _parse_position_instruction("place at the center of the room")
        assert r["relation"] == "center"
        assert "room" in r["reference_object"]

    def test_left_corner_modifier(self):
        # The "corner" pattern is listed after "on", so "on" matches first
        # for this phrasing. The corner pattern needs "place on the left corner of X"
        # but "on" pattern greedily matches. This documents current behavior.
        r = _parse_position_instruction("place on the left corner of the table")
        assert r["action"] == "place"
        assert r["relation"] == "on"

    def test_unparseable(self):
        r = _parse_position_instruction("fjdkslfjdsk")
        assert r["action"] is None
