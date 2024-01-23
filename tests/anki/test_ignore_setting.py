import re
import pytest
from anki.errors import NotFoundError  # noqa
from anki.collection import Collection
from anki.collection import SearchNode

# from conftest import col

test_name = "ignore_setting"
col_path = "tests/test_outputs/{}/Anki2/User 1/collection.anki2".format(test_name)
included_file_path = "tests/test_outputs/{}/Obsidian/{}/{}.md".format(
    test_name, test_name, test_name + "_included"
)

ignored_file_path = "tests/test_outputs/{}/Obsidian/{}/{}.md".format(
    test_name, test_name, test_name + "_ignored"
)


@pytest.fixture()
def col():
    col = Collection(col_path)
    yield col
    col.close()


def test_should_only_add_included(col: Collection):
    assert len(col.find_cards(col.build_search_string(SearchNode(deck="Default")))) == 4


def test_included_cards_added(col: Collection):
    ID_REGEXP_STR = r"\n?(?:<!--)?(?:ID: (\d+).*)"
    obsidian_test_md = included_file_path

    obs_IDs = []
    with open(obsidian_test_md) as file:
        for line in file:
            output = re.search(ID_REGEXP_STR, line.rstrip())
            if output is not None:
                output = output.group(1)
                obs_IDs.append(output)

    anki_IDs = col.find_notes(col.build_search_string(SearchNode(deck="Default")))
    for aid, oid in zip(anki_IDs, obs_IDs):
        assert str(aid) == oid
