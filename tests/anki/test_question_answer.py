
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
    assert len(col.find_cards( col.build_search_string(SearchNode(deck='Default')) )) == 5

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
    assert note1.fields[0] == "How do you use this style?"
    assert note1.fields[1] == "Just like this."

    note2 = col.get_note(anki_IDs[1])
    assert note2.fields[0] == "Can the question<br />\nrun over multiple lines?"
    assert note2.fields[1] == "Yes, and<br />\nSo can the answer"

    note3 = col.get_note(anki_IDs[2])
    assert note3.fields[0] == "Does the answer need to be immediately after the question?"
    assert note3.fields[1] == "No, and preceding whitespace will be ignored."

    note4 = col.get_note(anki_IDs[3])
    assert note4.fields[0] == "How is this possible?"
    assert note4.fields[1] == "The 'magic' of regular expressions!"

    note5 = col.get_note(anki_IDs[4])
    assert note5.fields[0] == "How is this possible? "
    assert note5.fields[1] == "The 'magic' of regular expressions! "
    assert note5.has_tag('tag2')
    assert note5.has_tag('tag1')

    assert note1.note_type()["name"] == "Basic"
    assert note2.note_type()["name"] == "Basic"
    assert note3.note_type()["name"] == "Basic"
    assert note4.note_type()["name"] == "Basic"
    assert note5.note_type()["name"] == "Basic"