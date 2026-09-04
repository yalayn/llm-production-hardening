"""Integrity of the golden dataset.

These tests check the evidence, not the implementations. The dataset is the
ground truth both versions are measured against, so it declares its own
vocabulary: if the schema in an implementation ever drifts from what is written
here, the implementation is what is wrong.
"""

import json
import pathlib

DATA = pathlib.Path(__file__).parent.parent / "data"
GOLDEN = DATA / "golden.jsonl"

CATEGORIES = {"billing", "technical", "account", "feature_request", "other", "unknown"}
URGENCIES = {"low", "medium", "high", "critical", "unknown"}

EDGE_FAMILIES = {
    "empty",
    "two_words",
    "other_language",
    "very_long",
    "ambiguous",
    "prompt_injection",
    "bogus_category",
    "markup_noise",
    "duplicate",
}


def load():
    with GOLDEN.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def test_holds_fifty_records_split_thirty_twenty():
    records = load()

    assert len(records) == 50
    assert sum(1 for r in records if r["family"] == "normal") == 30
    assert sum(1 for r in records if r["family"] != "normal") == 20


def test_every_edge_family_is_represented():
    families = {r["family"] for r in load() if r["family"] != "normal"}

    assert families == EDGE_FAMILIES


def test_every_record_is_complete_and_carries_exactly_one_ticket_source():
    for record in load():
        assert record["id"], record
        assert record["family"], record
        assert record["notes"], f"{record['id']} has no note explaining its answer"
        assert ("ticket" in record) ^ ("ticket_file" in record), record["id"]
        assert set(record["expected"]) == {"category", "urgency", "entities"}, record["id"]


def test_ids_are_unique():
    ids = [r["id"] for r in load()]

    assert len(ids) == len(set(ids))


def test_every_expected_answer_uses_the_declared_vocabulary():
    for record in load():
        assert record["expected"]["category"] in CATEGORIES, record["id"]
        assert record["expected"]["urgency"] in URGENCIES, record["id"]
        assert isinstance(record["expected"]["entities"], list), record["id"]


def test_the_duplicate_is_byte_identical_to_the_record_it_names():
    records = {r["id"]: r for r in load()}
    duplicates = [r for r in records.values() if r["family"] == "duplicate"]

    assert duplicates, "the cache case needs at least one duplicate"
    for dup in duplicates:
        original = records[dup["duplicate_of"]]
        assert dup["ticket"] == original["ticket"], dup["id"]
        assert dup["expected"] == original["expected"], dup["id"]


def test_the_long_ticket_fixture_is_at_least_ten_thousand_words():
    record = next(r for r in load() if r["family"] == "very_long")
    text = (DATA / record["ticket_file"]).read_text(encoding="utf-8")

    assert len(text.split()) >= 10_000


def test_normal_cases_span_every_category_and_urgency():
    normal = [r for r in load() if r["family"] == "normal"]

    assert {r["expected"]["category"] for r in normal} == CATEGORIES - {"unknown"}
    assert {r["expected"]["urgency"] for r in normal} == URGENCIES - {"unknown"}


def test_the_dataset_names_no_implementation():
    raw = GOLDEN.read_text(encoding="utf-8")

    assert "v1_naive" not in raw
    assert "v2_hardened" not in raw
