
import re
import os
import pytest
from anki.errors import NotFoundError  # noqa
from anki.collection import Collection
from anki.collection import SearchNode
# from conftest import col

test_name = os.path.basename(__file__)[5:-3]
col_path = 'tests/test_outputs/{}/Anki2/User 1/collection.anki2'.format(test_name)
test_file_paths = [
    ['tests/test_outputs/{}/Obsidian/{}/{}.md'.format(test_name, test_name, test_name), 'MathematicsInNextLine'],
    ['tests/test_outputs/{}/Obsidian/{}/{}.sameline.md'.format(test_name, test_name, test_name), 'MathematicsInSameLine'],
]

@pytest.fixture()
def col():
    col = Collection(col_path)
    yield col
    col.close()

def test_col_exists(col):
    assert not col.is_empty()

def test_deck_default_exists(col: Collection):
    assert col.decks.id_for_name('MathematicsInNextLine') is not None
    assert col.decks.id_for_name('MathematicsInSameLine') is not None

def test_cards_count(col: Collection):
    assert len(col.find_cards( col.build_search_string(SearchNode(deck='MathematicsInNextLine')) )) == 1
    assert len(col.find_cards( col.build_search_string(SearchNode(deck='MathematicsInSameLine')) )) == 1

def test_cards_ids_from_obsidian(col: Collection):

    ID_REGEXP_STR = r'\n?(?:<!--)?(?:ID: (\d+).*)'

    for obsidian_test_md, deck_name in test_file_paths:
        obs_IDs = []
        with open(obsidian_test_md) as file:
            for line in file:            
                output = re.search(ID_REGEXP_STR, line.rstrip())
                if output is not None:
                    output = output.group(1)
                    obs_IDs.append(output)

        anki_IDs = col.find_notes( col.build_search_string(SearchNode(deck=deck_name)) )
        for aid, oid in zip(anki_IDs, obs_IDs):
            assert str(aid) == oid
    
def test_cards_front_back_tag_type(col: Collection):

    anki_IDs = col.find_notes( col.build_search_string(SearchNode(deck='MathematicsInNextLine')) )
    
    note1 = col.get_note(anki_IDs[0])
    assert note1.fields[0] == "This is a test with target deck in a seperate line."
    assert note1.fields[1] == "Test successful!"
    assert note1.note_type()["name"] == "Basic"

    anki_IDs = col.find_notes( col.build_search_string(SearchNode(deck='MathematicsInSameLine')) )
    
    note1 = col.get_note(anki_IDs[0])
    assert note1.fields[0] == "This is a test with target deck in a same line."
    assert note1.fields[1] == "Test successful!"
    assert note1.note_type()["name"] == "Basic"