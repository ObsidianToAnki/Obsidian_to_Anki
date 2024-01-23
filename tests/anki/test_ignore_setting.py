import re
import pytest
from anki.errors import NotFoundError  # noqa
from anki.collection import Collection
from anki.collection import SearchNode

# from conftest import col

test_name = "ignore_setting"
col_path = "tests/test_outputs/{}/Anki2/User 1/collection.anki2".format(test_name)

test_file_paths = [
    "tests/test_outputs/{}/Obsidian/{}/scan_dir/included_file.md".format(
        test_name, test_name
    ),
    "tests/test_outputs/{}/Obsidian/{}/scan_dir/some/other/subdir/also_included_file.md".format(
        test_name, test_name
    ),
]

test_file_no_cards_paths = [
    "tests/test_outputs/{}/Obsidian/{}/outside_of_scandir/not_supposed_to_be_scanned.md".format(
        test_name, test_name
    ),
    "tests/test_outputs/{}/Obsidian/{}/scan_dir/ignored_by_setting_ignored/not_supposed_to_be_scanned.md".format(
        test_name, test_name
    ),
    "tests/test_outputs/{}/Obsidian/{}/scan_dir/ignored_by_setting_ignored/some/other/subdir/not_supposed_to_be_scanned.md".format(
        test_name, test_name
    ),
]


@pytest.fixture()
def col():
    col = Collection(col_path)
    yield col
    col.close()


def test_col_exists(col):
    assert not col.is_empty()


def test_deck_default_exists(col: Collection):
    assert col.decks.id_for_name("Default") is not None


def test_cards_count(col: Collection):
    assert len(col.find_cards(col.build_search_string(SearchNode(deck="Default")))) == 6


def test_cards_ids_from_obsidian(col: Collection):
    ID_REGEXP_STR = r"\n?(?:<!--)?(?:ID: (\d+).*)"

    obs_IDs = []
    for obsidian_test_md in test_file_paths:
        with open(obsidian_test_md) as file:
            for line in file:
                output = re.search(ID_REGEXP_STR, line.rstrip())
                if output is not None:
                    output = output.group(1)
                    obs_IDs.append(output)

    anki_IDs = col.find_notes(col.build_search_string(SearchNode(deck="Default")))
    for aid, oid in zip(anki_IDs, obs_IDs):
        assert str(aid) == oid


def test_no_cards_added_from_ignored_paths(col: Collection):
    ID_REGEXP_STR = r"\n?(?:<!--)?(?:ID: (\d+).*)"

    for obsidian_test_md in test_file_no_cards_paths:
        obs_IDs = []
        with open(obsidian_test_md) as file:
            for line in file:
                output = re.search(ID_REGEXP_STR, line.rstrip())
                if output is not None:
                    output = output.group(1)
                    obs_IDs.append(output)

    assert len(obs_IDs) == 0
