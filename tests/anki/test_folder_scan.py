
import re
import pytest
from anki.errors import NotFoundError  # noqa
from anki.collection import Collection
from anki.collection import SearchNode
# from conftest import col

test_name = 'folder_scan'
col_path = 'tests/test_outputs/{}/Anki2/User 1/collection.anki2'.format(test_name)

test_file_paths = [
    'tests/test_outputs/{}/Obsidian/{}/scan_dir/{}.md'.format(test_name, test_name, test_name),
    'tests/test_outputs/{}/Obsidian/{}/scan_dir/also_scan/folder_scan_subdir.md'.format(test_name, test_name),
]

test_file_no_cards_paths = [
    'tests/test_outputs/{}/Obsidian/{}/should_not_scan_dir/should_not_scan.md'.format(test_name, test_name),
    'tests/test_outputs/{}/Obsidian/{}/{}.md'.format(test_name, test_name, test_name),
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
    assert len(col.find_cards( col.build_search_string(SearchNode(deck='Default')) )) == 8

def test_cards_ids_from_obsidian(col: Collection):

    ID_REGEXP_STR = r'\n?(?:<!--)?(?:ID: (\d+).*)'

    for obsidian_test_md in test_file_paths:
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

def test_no_cards_added_from_obsidian(col: Collection):

    ID_REGEXP_STR = r'\n?(?:<!--)?(?:ID: (\d+).*)'

    for obsidian_test_md in test_file_no_cards_paths:
        obs_IDs = []
        with open(obsidian_test_md) as file:
            for line in file:            
                output = re.search(ID_REGEXP_STR, line.rstrip())
                if output is not None:
                    output = output.group(1)
                    obs_IDs.append(output)

    assert len(obs_IDs) == 0

def test_cards_front_back_tag_type(col: Collection):

    anki_IDs = col.find_notes( col.build_search_string(SearchNode(deck='Default')) )

    # assert that should_not_add_notes weren't added
    assert len(anki_IDs) == 8
    
    note1 = col.get_note(anki_IDs[0])
    assert note1.fields[0] == "Style Subdir"
    assert note1.fields[1] == "This style is suitable for having the header as the front, and the answer as the back"

    note2 = col.get_note(anki_IDs[1])
    assert note2.fields[0] == "Subheading 1 Subdir"
    assert note2.fields[1] == "You're allowed to nest headers within each other"

    note3 = col.get_note(anki_IDs[2])
    assert note3.fields[0] == "Subheading 2 Subdir"
    assert note3.fields[1] == "It'll take the deepest level for the question"

    note4 = col.get_note(anki_IDs[3])
    assert note4.fields[0] == "Subheading 3 Subdir"
    assert note4.fields[1] == "It'll even<br />\nSpan over<br />\nMultiple lines, and ignore preceding whitespace"


    note5 = col.get_note(anki_IDs[4])
    assert note5.fields[0] == "Style"
    assert note5.fields[1] == "This style is suitable for having the header as the front, and the answer as the back"

    note6 = col.get_note(anki_IDs[5])
    assert note6.fields[0] == "Subheading 1"
    assert note6.fields[1] == "You're allowed to nest headers within each other"

    note7 = col.get_note(anki_IDs[6])
    assert note7.fields[0] == "Subheading 2"
    assert note7.fields[1] == "It'll take the deepest level for the question"

    note8 = col.get_note(anki_IDs[7])
    assert note8.fields[0] == "Subheading 3"
    assert note8.fields[1] == "It'll even<br />\nSpan over<br />\nMultiple lines, and ignore preceding whitespace"

    assert note1.note_type()["name"] == "Basic"
    assert note2.note_type()["name"] == "Basic"
    assert note3.note_type()["name"] == "Basic"
    assert note4.note_type()["name"] == "Basic"

    assert note5.note_type()["name"] == "Basic"
    assert note6.note_type()["name"] == "Basic"
    assert note7.note_type()["name"] == "Basic"
    assert note8.note_type()["name"] == "Basic"
