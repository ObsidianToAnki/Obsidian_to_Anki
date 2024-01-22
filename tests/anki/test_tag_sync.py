
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
    'tests/test_outputs/{}/Obsidian/{}/{}.file.md'.format(test_name, test_name, test_name),
    'tests/test_outputs/{}/Obsidian/{}/{}.md'.format(test_name, test_name, test_name),
    'tests/test_outputs/{}/Obsidian/{}/{}.file.inline.md'.format(test_name, test_name, test_name),
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
    assert len(col.find_cards( col.build_search_string(SearchNode(deck='Default')) )) == 7

def test_cards_ids_from_obsidian(col: Collection):

    ID_REGEXP_STR = r'\n?(?:<!--)?(?:ID: (\d+).*)'

    obs_IDs = []
    for obsidian_test_md in test_file_paths:
        with open(obsidian_test_md) as file:
            for line in file:   
                output = re.search(ID_REGEXP_STR, line.rstrip())
                if output is not None:
                    output = output.group(1)
                    obs_IDs.append(int(output))

    anki_IDs = col.find_notes( col.build_search_string(SearchNode(deck='Default')) )

    for aid in anki_IDs:
        assert obs_IDs.index(aid) > -1

    for oid in obs_IDs:
        assert list(anki_IDs).index(oid) > -1
    
    assert len(anki_IDs) == len(obs_IDs)

def find_note_with_1st_field(field, anki_IDs, col: Collection):
    for aid in anki_IDs:
        note = col.get_note(aid)
        if note.fields[0] == field:
            return note


def test_cards_front_back_tag_type(col: Collection):

    anki_IDs = col.find_notes( col.build_search_string(SearchNode(deck='Default')) )
    
    note1 = find_note_with_1st_field("This is a test.", anki_IDs, col)
    # assert note1.fields[0] == "This is a test."
    assert note1.fields[1] == "Test successful!"
    assert note1.has_tag('Tag1')
    assert note1.has_tag('Tag2')
    assert note1.has_tag('Tag3')
    assert len(note1.tags) == 4

    note2 = find_note_with_1st_field("This is a test. This should not have any tags except default ones.<br />\nAnd the test is continuing.", anki_IDs, col)
    # assert note2.fields[0] == "This is a test. This should not have any tags except default ones.<br />\nAnd the test is continuing."
    assert note2.fields[1] == "Test successful!"
    assert note2.has_tag('Obsidian_to_Anki')
    assert len(note2.tags) == 1

    note3 = find_note_with_1st_field("This is a test. this should have meow-tag<br />\nAnd the test is continuing. ", anki_IDs, col)
    # assert note3.fields[0] == "This is a test. this should have meow-tag<br />\nAnd the test is continuing. "
    assert note3.fields[1] == "Test successful!"
    assert note3.has_tag('meow')
    assert len(note3.tags) == 2

    note4 = find_note_with_1st_field("This is a test with file tags specified in new line", anki_IDs, col)
    # assert note4.fields[0] == "This is a test with file tags specified in new line"
    assert note4.fields[1] == "Test successful!"
    assert note4.has_tag('Maths')
    assert note4.has_tag('School')
    assert note4.has_tag('Physics')
    assert len(note4.tags) == 4

    note5 = find_note_with_1st_field("This is a test 2 with file tags specified in new line<br />\nAnd the test is continuing.", anki_IDs, col)
    # assert note5.fields[0] == "This is a test 2 with file tags specified in new line<br />\nAnd the test is continuing."
    assert note5.fields[1] == "Test successful!"
    assert note5.has_tag('Maths')
    assert note5.has_tag('School')
    assert note5.has_tag('Physics')
    assert len(note5.tags) == 4

    note6 = find_note_with_1st_field("This is a test with file tags specified inline", anki_IDs, col)
    # assert note6.fields[0] == "This is a test with file tags specified inline"
    assert note6.fields[1] == "Test successful!"
    assert note6.has_tag('Maths')
    assert note6.has_tag('School')
    assert note6.has_tag('Physics')
    assert len(note6.tags) == 4

    note7 = find_note_with_1st_field("This is a test 2 with file tags specified inline<br />\nAnd the test is continuing.", anki_IDs, col)
    # assert note7.fields[0] == "This is a test 2 with file tags specified inline<br />\nAnd the test is continuing."
    assert note7.fields[1] == "Test successful!"
    assert note7.has_tag('Maths')
    assert note7.has_tag('School')
    assert note7.has_tag('Physics')
    assert len(note7.tags) == 4
