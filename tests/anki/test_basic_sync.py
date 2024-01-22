
import re
import pytest
from anki.errors import NotFoundError  # noqa
from anki.collection import Collection
from anki.collection import SearchNode
# from conftest import col

col_path = 'tests/test_outputs/basic_sync/Anki2/User 1/collection.anki2'
test_file_path = 'tests/test_outputs/basic_sync/Obsidian/basic_sync/basic_sync.md'

@pytest.fixture()
def col():
    col = Collection(col_path)
    yield col
    col.close()

def test_col_exists(col):
    assert not col.is_empty()

def test_deck_default_exists(col: Collection):
    assert col.decks.id_for_name('Default') is not None

def test_cards_count(col: Collection):
    assert len(col.find_cards( col.build_search_string(SearchNode(deck='Default')) )) == 3

def test_cards_ids_from_obsidian(col: Collection):

    ID_REGEXP_STR = r'\n?(?:<!--)?(?:ID: (\d+).*)'
    obsidian_test_md = test_file_path

    obs_IDs = []
    with open(obsidian_test_md) as file:
        for line in file:            
            output = re.search(ID_REGEXP_STR, line.rstrip())
            if output is not None:
                output = output.group(1)
                obs_IDs.append(output)

    anki_IDs = col.find_notes( col.build_search_string(SearchNode(deck='Default')) )
    for aid, oid in zip(anki_IDs, obs_IDs):
        assert str(aid) == oid
    
def test_cards_front_back_tag_type(col: Collection):

    anki_IDs = col.find_notes( col.build_search_string(SearchNode(deck='Default')) )
    
    note1 = col.get_note(anki_IDs[0])
    assert note1.fields[0] == "This is a test."
    assert note1.fields[1] == "Test successful!"

    note2 = col.get_note(anki_IDs[1])
    assert note2.fields[0] == "This is a test with Front specified."
    assert note2.fields[1] == "Test successful!"

    note3 = col.get_note(anki_IDs[2])
    assert note3.fields[0] == "This is a test.<br />\nAnd the test is continuing."
    assert note3.fields[1] == "Test successful!"

    assert note1.has_tag("Testing")
    assert note2.has_tag("Testing")
    assert note2.has_tag("2")

    assert note1.note_type()["name"] == "Basic"
    assert note2.note_type()["name"] == "Basic"
    assert note3.note_type()["name"] == "Basic"