
import re
import os
import pytest
from anki.errors import NotFoundError  # noqa
from anki.collection import Collection
from anki.collection import SearchNode
# from conftest import col

test_name = os.path.basename(__file__)[5:-3]
col_path = 'tests/test_outputs/{}/Anki2/User 1/collection.anki2'.format(test_name)
test_file_path = 'tests/test_outputs/{}/Obsidian/{}/{}.md'.format(test_name, test_name, test_name)

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
    assert len(col.find_cards( col.build_search_string(SearchNode(deck='Default')) )) == 16

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
    assert note1.fields[0] == "This is a {{c1::cloze note}}"

    note2 = col.get_note(anki_IDs[1])
    assert note2.fields[0] == "This is a {{c1::cloze}} note with {{c2::two clozes}}"

    note3 = col.get_note(anki_IDs[2])
    assert note3.fields[0] == "This is a {{c2::cloze}} note with {{c1::id syntax}}"

    note4 = col.get_note(anki_IDs[3])
    assert note4.fields[0] == "This is a {{c2::cloze}} {{c3::note}} with {{c1::alternate id syntax}}"

    note5 = col.get_note(anki_IDs[4])
    assert note5.fields[0] == "This is a {{c1::cloze}} note with {{c2::another}} type of {{c3::id syntax}}"

    note6 = col.get_note(anki_IDs[5])
    assert note6.fields[0] == "This is a {{c1::cloze}} note with {{c2::yet another}} type of {{c3::id syntax}}"

    note7 = col.get_note(anki_IDs[6])
    assert note7.fields[0] == "This is a {{c1::cloze}} note with {{c2::multiple}} non-id clozes, as well as {{c2::some clozes}} with {{c1::other styles}}"

    assert note1.note_type()["name"] == "Cloze"
    assert note2.note_type()["name"] == "Cloze"
    assert note3.note_type()["name"] == "Cloze"
    assert note4.note_type()["name"] == "Cloze"
    assert note5.note_type()["name"] == "Cloze"
    assert note6.note_type()["name"] == "Cloze"
    assert note7.note_type()["name"] == "Cloze"