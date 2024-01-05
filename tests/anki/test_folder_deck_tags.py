
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
    ['tests/test_outputs/{}/Obsidian/{}/{}.md'.format(test_name, test_name, test_name), 'Default'],
    ['tests/test_outputs/{}/Obsidian/{}/English/No Deck/{}.parent.md'.format(test_name, test_name, test_name),'English'],
    ['tests/test_outputs/{}/Obsidian/{}/Math meow/{}.math.md'.format(test_name, test_name, test_name),'Math'],
    ['tests/test_outputs/{}/Obsidian/{}/Science meow/{}.science.md'.format(test_name, test_name, test_name),'Science'],
]

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
    assert len(col.find_cards( col.build_search_string(SearchNode(deck='Default')) )) == 1
    assert len(col.find_cards( col.build_search_string(SearchNode(deck='English')) )) == 1
    assert len(col.find_cards( col.build_search_string(SearchNode(deck='Math')) )) == 1
    assert len(col.find_cards( col.build_search_string(SearchNode(deck='Science')) )) == 1

def test_cards_ids_from_obsidian(col: Collection):

    ID_REGEXP_STR = r'\n?(?:<!--)?(?:ID: (\d+).*)'

    for test_file, test_deck in test_file_paths:
        obs_IDs = []
        with open(test_file) as file:
            for line in file:            
                output = re.search(ID_REGEXP_STR, line.rstrip())
                if output is not None:
                    output = output.group(1)
                    obs_IDs.append(output)

        anki_IDs = col.find_notes( col.build_search_string(SearchNode(deck=test_deck)) )
        for aid, oid in zip(anki_IDs, obs_IDs):
            assert str(aid) == oid
    
def test_cards_front_back_tag_type(col: Collection):

    anki_IDs = col.find_notes( col.build_search_string(SearchNode(deck='Default')) )
    note1 = col.get_note(anki_IDs[0])
    assert note1.fields[0] == "This is a test. Should be in Default deck."
    assert note1.fields[1] == "Test successful!"
    assert note1.note_type()["name"] == "Basic"

    anki_IDs = col.find_notes( col.build_search_string(SearchNode(deck='English')) )
    note1 = col.get_note(anki_IDs[0])
    assert note1.fields[0] == "This is a test. This card should be English Deck eventhough its in No Deck folder"
    assert note1.fields[1] == "Test successful!"
    assert note1.has_tag('arts')
    assert note1.has_tag('booring')
    assert note1.note_type()["name"] == "Basic"

    anki_IDs = col.find_notes( col.build_search_string(SearchNode(deck='Math')) )
    note1 = col.get_note(anki_IDs[0])
    assert note1.fields[0] == "This is a test. Should be in Math deck."
    assert note1.fields[1] == "Test successful!"
    assert note1.has_tag('sciences')
    assert note1.has_tag('fun')
    assert note1.note_type()["name"] == "Basic"
    
    anki_IDs = col.find_notes( col.build_search_string(SearchNode(deck='Science')) )
    note1 = col.get_note(anki_IDs[0])
    assert note1.fields[0] == "This is a test. Should be in Science deck"
    assert note1.fields[1] == "Test successful!"
    assert note1.has_tag('sciences')
    assert note1.has_tag('fun')
    assert note1.note_type()["name"] == "Basic"

