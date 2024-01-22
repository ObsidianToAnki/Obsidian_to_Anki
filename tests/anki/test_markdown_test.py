
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
    assert len(col.find_cards( col.build_search_string(SearchNode(deck='Default')) )) == 1

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
    assert note1.fields[0] == "<p>This note showcases a bunch of different markdown formatting.  <br />\nYou can use <em>italics</em> or <em>italics</em>.<br />\n<strong>Bold</strong> or <strong>Bold</strong><br />\nIf you want to strongly emphasise, just <strong><em>do</em></strong> <strong><em>both</em></strong></p>\n<h1 id=\"headersaresupportedtoo\">Headers are supported too</h1>\n<h2 id=\"at\">At</h2>\n<h3 id=\"varying\">Varying</h3>\n<h4 id=\"levels\">Levels</h4>\n<ol>\n<li>You can get</li>\n<li>Ordered lists</li>\n<li>By doing numbers like this</li>\n</ol>\n<ul>\n<li>Unordered lists</li>\n<li>work like this.</li>\n<li>Make sure to leave a gap between lists and other things</li>\n</ul>"
    assert note1.fields[1] == "<link href=\"https://cdn.jsdelivr.net/npm/highlightjs-themes@1.0.0/arta.css\" rel=\"stylesheet\"><p>A few more elements to see.<br />\nYou can include <a href=\"https://www.wikipedia.org/\">links</a> to websites.<br />\n<code>Code blocks</code> are supported<br />\nGithub-flavoured code blocks too, but Anki won\'t do syntax highlighting</p>\n<pre><code class=\"hljs python language-python\">    <span class=\"hljs-built_in\">print</span>(<span class=\"hljs-string\">&quot;Hello world!&quot;</span>)\n</code></pre>\n<p>Tables should hopefully work:</p>\n<table>\n<thead>\n<tr>\n<th>First Header</th>\n<th>Second Header</th>\n</tr>\n</thead>\n<tbody>\n<tr>\n<td>Content Cell</td>\n<td>Content Cell</td>\n</tr>\n<tr>\n<td>Content Cell</td>\n<td>Content Cell</td>\n</tr>\n</tbody>\n</table>"
    assert note1.has_tag('Way_too_much_info')

    assert note1.note_type()["name"] == "Basic"