#!/usr/bin/env python

"""Script for adding cards to Anki from Obsidian."""

import re
import json
import urllib.request
import configparser
import os
import argparse
import collections
import webbrowser
import markdown
import base64

md_parser = markdown.Markdown(
    extensions=['extra', 'nl2br', 'sane_lists'], output_format="html5"
)


def write_safe(filename, contents):
    """
    Write contents to filename while keeping a backup.

    If write fails, a backup 'filename.bak' will still exist.
    """
    with open(filename + ".tmp", "w") as temp:
        temp.write(contents)
    os.rename(filename, filename + ".bak")
    os.rename(filename + ".tmp", filename)
    success = False
    with open(filename) as f:
        if f.read() == contents:
            success = True
    if success:
        os.remove(filename + ".bak")


def string_insert(string, position_inserts):
    """
    Insert strings in position_inserts into string, at indices.

    position_inserts will look like:
    [(0, "hi"), (3, "hello"), (5, "beep")]
    """
    offset = 0
    for position, insert_str in position_inserts:
        string = "".join(
            [
                string[:position + offset],
                insert_str,
                string[position + offset:]
            ]
        )
        offset += len(insert_str)
    return string


def file_encode(filepath):
    """Encode the file as base 64."""
    with open(filepath, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


class AnkiConnect:
    """Namespace for AnkiConnect functions."""

    def request(action, **params):
        """Format action and parameters into Ankiconnect style."""
        return {'action': action, 'params': params, 'version': 6}

    def invoke(action, **params):
        """Do the action with the specified parameters."""
        requestJson = json.dumps(
            AnkiConnect.request(action, **params)
        ).encode('utf-8')
        response = json.load(urllib.request.urlopen(
            urllib.request.Request('http://localhost:8765', requestJson)))
        if len(response) != 2:
            raise Exception('response has an unexpected number of fields')
        if 'error' not in response:
            raise Exception('response is missing required error field')
        if 'result' not in response:
            raise Exception('response is missing required result field')
        if response['error'] is not None:
            raise Exception(response['error'])
        return response['result']


class FormatConverter:
    """Converting Obsidian formatting to Anki formatting."""

    OBS_INLINE_MATH_REGEXP = re.compile(
        r"(?<!\$)\$(?=[\S])(?=[^$])[\s\S]*?\S\$"
    )
    OBS_DISPLAY_MATH_REGEXP = re.compile(r"\$\$[\s\S]*?\$\$")

    ANKI_INLINE_START = r"\("
    ANKI_INLINE_END = r"\)"

    ANKI_DISPLAY_START = r"\["
    ANKI_DISPLAY_END = r"\]"

    ANKI_MATH_REGEXP = re.compile(r"(\\\[[\s\S]*?\\\])|(\\\([\s\S]*?\\\))")

    MATH_REPLACE = "OBSTOANKIMATH"

    IMAGE_PATHS = set()
    IMAGE_REGEXP = re.compile(r'<img alt="[\s\S]*?" src="([\s\S]*?)">')

    @staticmethod
    def inline_anki_repl(matchobject):
        """Get replacement string for Obsidian-formatted inline math."""
        found_string = matchobject.group(0)
        # Strip Obsidian formatting by removing first and last characters
        found_string = found_string[1:-1]
        # Add Anki formatting
        result = FormatConverter.ANKI_INLINE_START + found_string
        result += FormatConverter.ANKI_INLINE_END
        return result

    @staticmethod
    def display_anki_repl(matchobject):
        """Get replacement string for Obsidian-formatted display math."""
        found_string = matchobject.group(0)
        # Strip Obsidian formatting by removing first two and last two chars
        found_string = found_string[2:-2]
        # Add Anki formatting
        result = FormatConverter.ANKI_DISPLAY_START + found_string
        result += FormatConverter.ANKI_DISPLAY_END
        return result

    @staticmethod
    def obsidian_to_anki_math(note_text):
        """Convert Obsidian-formatted math to Anki-formatted math."""
        return FormatConverter.OBS_INLINE_MATH_REGEXP.sub(
            FormatConverter.inline_anki_repl,
            FormatConverter.OBS_DISPLAY_MATH_REGEXP.sub(
                FormatConverter.display_anki_repl, note_text
            )
        )

    @staticmethod
    def markdown_parse(text):
        """Apply markdown conversions to text."""
        text = md_parser.reset().convert(text)
        return text

    @staticmethod
    def format(note_text):
        """Apply all format conversions to note_text."""
        note_text = FormatConverter.obsidian_to_anki_math(note_text)
        # Extract the parts that are anki math
        math_matches = [
            math_match.group(0)
            for math_match in FormatConverter.ANKI_MATH_REGEXP.finditer(
                note_text
            )
        ]
        # Replace them to be later added  back, so they don't interfere
        # With markdown parsing
        note_text = FormatConverter.ANKI_MATH_REGEXP.sub(
            FormatConverter.MATH_REPLACE, note_text
        )
        note_text = FormatConverter.markdown_parse(note_text)
        # Add back the parts that are anki math
        for math_match in math_matches:
            note_text = note_text.replace(
                FormatConverter.MATH_REPLACE,
                math_match,
                1
            )
        FormatConverter.get_images(note_text)
        note_text = FormatConverter.fix_image_src(note_text)
        return note_text

    @staticmethod
    def get_images(html_text):
        """Get all the images that need to be added."""
        for match in FormatConverter.IMAGE_REGEXP.finditer(html_text):
            FormatConverter.IMAGE_PATHS.add(match.group(1))
            # ^Adds the image path (relative to cwd)

    @staticmethod
    def fix_image_src_repl(matchobject):
        """Replace the src in matchobject appropriately."""
        found_string, found_path = matchobject.group(0), matchobject.group(1)
        found_string = found_string.replace(
            found_path, os.path.basename(found_path)
        )
        return found_string

    @staticmethod
    def fix_image_src(html_text):
        """Fix the src of the images so that it's relative to Anki."""
        return FormatConverter.IMAGE_REGEXP.sub(
            FormatConverter.fix_image_src_repl,
            html_text
        )


class Note:
    """Manages parsing notes into a dictionary formatted for AnkiConnect.

    Input must be the note text.
    Does NOT deal with finding the note in the file.
    """

    TARGET_DECK = "Default"
    ID_PREFIX = "ID: "
    TAG_PREFIX = "Tags: "
    TAG_SEP = " "
    Note_and_id = collections.namedtuple('Note_and_id', ['note', 'id'])

    def __init__(self, note_text):
        """Set up useful variables."""
        self.text = note_text
        self.lines = self.text.splitlines()
        self.current_field_num = 0
        self.delete = False
        if self.lines[-1].startswith(Note.ID_PREFIX):
            self.identifier = int(self.lines.pop()[len(Note.ID_PREFIX):])
            # The above removes the identifier line, for convenience of parsing
        else:
            self.identifier = None
        if not self.lines:
            # This indicates a delete action.
            self.delete = True
            return
        elif self.lines[-1].startswith(Note.TAG_PREFIX):
            self.tags = self.lines.pop()[len(Note.TAG_PREFIX):].split(
                Note.TAG_SEP
            )
        else:
            self.tags = None
        self.note_type = Note.note_subs[self.lines[0]]
        self.subs = Note.field_subs[self.note_type]
        self.field_names = list(self.subs)

    @property
    def NOTE_DICT_TEMPLATE(self):
        """Template for making notes."""
        return {
            "deckName": Note.TARGET_DECK,
            "modelName": "",
            "fields": dict(),
            "options": {
                "allowDuplicate": False,
                "duplicateScope": "deck"
            },
            "tags": ["Obsidian_to_Anki"],
            # ^So that you can see what was added automatically.
            "audio": list()
        }

    @property
    def current_field(self):
        """Get the field to add text to."""
        return self.field_names[self.current_field_num]

    @property
    def current_sub(self):
        """Get the prefix substitution of the current field."""
        return self.subs[self.current_field]

    @property
    def next_field(self):
        """Attempt to get the next field to add text to."""
        try:
            return self.field_names[self.current_field_num + 1]
        except IndexError:
            return ""

    @property
    def next_sub(self):
        """Attempt to get the substitution of the next field."""
        try:
            return self.subs[self.next_field]
        except KeyError:
            return ""

    @property
    def fields(self):
        """Get the fields of the note into a dictionary."""
        fields = dict.fromkeys(self.field_names, "")
        for line in self.lines[1:]:
            if self.next_sub and line.startswith(self.next_sub):
                # This means we're entering a new field.
                # So, we should format the text in the current field
                self.current_field_num += 1
                line = line[len(self.current_sub):]
            fields[self.current_field] += line + "\n"
        fields = {
            key: FormatConverter.format(value)
            for key, value in fields.items()
        }
        return {key: value.strip() for key, value in fields.items()}

    def parse(self):
        """Get a properly formatted dictionary of the note."""
        template = self.NOTE_DICT_TEMPLATE.copy()
        if not self.delete:
            template["modelName"] = self.note_type
            template["fields"] = self.fields
            if self.tags:
                template["tags"] = template["tags"] + self.tags
            return Note.Note_and_id(note=template, id=self.identifier)
        else:
            return Note.Note_and_id(note=False, id=self.identifier)


class Config:
    """Deals with saving and loading the configuration file."""

    CONFIG_PATH = os.path.expanduser(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "obsidian_to_anki_config.ini"
        )
    )

    def update_config():
        """Update config with new notes."""
        print("Updating configuration file...")
        config = configparser.ConfigParser()
        config.optionxform = str
        if os.path.exists(Config.CONFIG_PATH):
            print("Config file exists, reading...")
            config.read(Config.CONFIG_PATH)
        note_types = AnkiConnect.invoke("modelNames")
        fields_request = [
            AnkiConnect.request(
                "modelFieldNames", modelName=note
            )
            for note in note_types
        ]
        subs = {
            note: {
                field: field + ": "
                for field in fields["result"]
            }
            for note, fields in zip(
                note_types,
                AnkiConnect.invoke(
                    "multi", actions=fields_request
                )
            )
        }
        for note, note_field_subs in subs.items():
            if note not in config:
                config[note] = dict()
            for field, sub in note_field_subs.items():
                config[note].setdefault(field, sub)
                # This means that, if there's already a substitution present,
                # the 'default' substitution of field + ": " isn't added.
        if "Note Substitutions" not in config:
            config["Note Substitutions"] = dict()
        for note in note_types:
            config["Note Substitutions"].setdefault(note, note)
            # Similar to above - if there's already a substitution present,
            # it isn't overwritten
        with open(Config.CONFIG_PATH, "w") as configfile:
            config.write(configfile)
        print("Configuration file updated!")

    def load_config():
        """Load from an existing config file (assuming it exists)."""
        print("Loading configuration file...")
        config = configparser.ConfigParser()
        config.optionxform = str  # Allows for case sensitivity
        config.read(Config.CONFIG_PATH)
        note_subs = config["Note Substitutions"]
        Note.note_subs = {v: k for k, v in note_subs.items()}
        Note.field_subs = {
            note: dict(config[note]) for note in config
            if note != "Note Substitutions" and note != "DEFAULT"
        }
        print("Loaded successfully!")


class App:
    """Master class that manages the application."""

    # Useful REGEXPs
    NOTE_REGEXP = re.compile(r"(?<=START\n)[\s\S]*?(?=END\n?)")
    DECK_REGEXP = re.compile(r"(?<=TARGET DECK\n)[\s\S]*?(?=\n)")
    EMPTY_REGEXP = re.compile(r"START\nID: [\s\S]*?\nEND")

    SUPPORTED_EXTS = [".md", ".txt"]

    def __init__(self):
        """Execute the main functionality of the script."""
        self.setup_parser()
        args = self.parser.parse_args()
        if args.update:
            Config.update_config()
        Config.load_config()
        if args.config:
            webbrowser.open(Config.CONFIG_PATH)
            return
        if args.path:
            self.path = args.path
            if os.path.isdir(self.path):
                with os.scandir(self.path) as it:
                    self.files = [
                        File(entry.path)
                        for entry in it
                        if entry.is_file() and os.path.splitext(
                            entry.path
                        )[1] in App.SUPPORTED_EXTS
                    ]
            else:
                self.files = [File(self.path)]
            for file in self.files:
                file.scan_file()
            self.parse_requests_1()
            for file in self.files:
                file.get_cards()
                file.write_ids()
                print("Removing empty notes for file", file.filename)
                file.remove_empties()
                file.write_file()
            self.requests_2()

    def setup_parser(self):
        """Set up the argument parser."""
        self.parser = argparse.ArgumentParser(
            description="Add cards to Anki from an Obsidian markdown file."
        )
        self.parser.add_argument(
            "path",
            nargs="?",
            default=False,
            help="Path to the file or directory you want to scan.",
        )
        self.parser.add_argument(
            "-c", "--config",
            action="store_true",
            dest="config",
            help="""
                Opens up config file for editing.
            """
        )
        self.parser.add_argument(
            "-u", "--update",
            action="store_true",
            dest="update",
            help="""
                Whether you want to update the config file
                using new notes from Anki.
                Note that this does NOT open the config file for editing,
                use -c for that.
            """,
        )

    def get_tags(self):
        """Get a set of currently used tags for notes to be edited."""
        self.tags = set()
        for info in self.info:
            self.tags.update(info["tags"])

    def get_add_images(self):
        """Get the AnkiConnect-formatted add_images request."""
        return AnkiConnect.request(
            "multi",
            actions=[
                AnkiConnect.request(
                    "storeMediaFile",
                    filename=imgpath.replace(
                        imgpath, os.path.basename(imgpath)
                    ),
                    data=file_encode(imgpath)
                )
                for imgpath in FormatConverter.IMAGE_PATHS
            ]
        )

    def requests_1(self):
        """Do big request 1.

        This adds images, adds notes, updates fields,
        gets note info, gets tags and removes notes.
        """
        requests = list()
        print("Adding images with these paths...")
        print(FormatConverter.IMAGE_PATHS)
        requests.append(self.get_add_images())
        print("Adding notes into Anki...")
        requests.append(
            AnkiConnect.request(
                "multi",
                actions=[
                    file.get_add_notes()
                    for file in self.files
                ]
            )
        )
        print("Updating fields of existing notes...")
        requests.append(
            AnkiConnect.request(
                "multi",
                actions=[
                    file.get_update_fields()
                    for file in self.files
                ]
            )
        )
        print("Getting card IDs of notes to be edited...")
        requests.append(
            AnkiConnect.request(
                "multi",
                actions=[
                    file.get_note_info()
                    for file in self.files
                ]
            )
        )
        print("Getting list of tags...")
        requests.append(
            AnkiConnect.request(
                "getTags"
            )
        )
        print("Removing empty notes...")
        requests.append(
            AnkiConnect.request(
                "multi",
                actions=[
                    file.get_delete_notes()
                    for file in self.files
                ]
            )
        )
        return AnkiConnect.invoke(
            "multi",
            actions=requests
        )

    def parse_requests_1(self):
        """Get relevant info from requests_1."""
        result = self.requests_1()
        notes_ids = result[1]["result"]
        cards_ids = result[3]["result"]
        tags = result[4]["result"]
        for note_ids, file in zip(notes_ids, self.files):
            file.note_ids = note_ids["result"]
        for card_ids, file in zip(cards_ids, self.files):
            file.card_ids = card_ids["result"]
        for file in self.files:
            file.tags = tags

    def requests_2(self):
        """Perform requests group 2.

        This moves cards, clears tags, adds tags.
        """
        requests = list()
        print("Moving cards to target deck...")
        requests.append(
            AnkiConnect.request(
                "multi",
                actions=[
                    file.get_change_decks()
                    for file in self.files
                ]
            )
        )
        print("Replacing tags...")
        requests.append(
            AnkiConnect.request(
                "multi",
                actions=[
                    file.get_clear_tags()
                    for file in self.files
                ]
            )
        )
        requests.append(
            AnkiConnect.request(
                "multi",
                actions=[
                    file.get_add_tags()
                    for file in self.files
                ]
            )
        )
        AnkiConnect.invoke(
            "multi",
            actions=requests
        )


class File:
    """Class for performing script operations at the file-level."""

    def __init__(self, filepath):
        """Perform initial file reading and attribute setting."""
        self.filename = filepath
        with open(self.filename) as f:
            self.file = f.read()
        self.target_deck = App.DECK_REGEXP.search(self.file)
        if self.target_deck is not None:
            Note.TARGET_DECK = self.target_deck.group(0)
        print(
            "Identified target deck for", self.filename,
            "as", Note.TARGET_DECK
        )

    def scan_file(self):
        """Sort notes from file into adding vs editing."""
        print("Scanning file", self.filename, " for notes...")
        self.notes_to_add = list()
        self.id_indexes = list()
        self.notes_to_edit = list()
        self.notes_to_delete = list()
        for note_match in App.NOTE_REGEXP.finditer(self.file):
            note, position = note_match.group(0), note_match.end()
            parsed = Note(note).parse()
            if parsed.id is None:
                self.notes_to_add.append(parsed.note)
                self.id_indexes.append(position)
            elif not parsed.note:
                # This indicates a delete action
                self.notes_to_delete.append(parsed.id)
            else:
                self.notes_to_edit.append(parsed)

    @staticmethod
    def id_to_str(id):
        """Get the string repr of id."""
        return "ID: " + str(id) + "\n"

    def write_ids(self):
        """Write the identifiers to self.file."""
        print("Writing new note IDs to file,", self.filename, "...")
        self.file = string_insert(
            self.file, zip(
                self.id_indexes, map(
                    self.id_to_str, self.note_ids
                )
            )
        )

    def remove_empties(self):
        """Remove empty notes from self.file."""
        self.file = App.EMPTY_REGEXP.sub(
            "", self.file
        )

    def write_file(self):
        """Write to the actual os file"""
        write_safe(self.filename, self.file)

    def get_add_notes(self):
        """Get the AnkiConnect-formatted request to add notes."""
        return AnkiConnect.request(
            "addNotes",
            notes=self.notes_to_add
        )

    def get_delete_notes(self):
        """Get the AnkiConnect-formatted request to delete a note."""
        return AnkiConnect.request(
            "deleteNotes",
            notes=self.notes_to_delete
        )

    def get_update_fields(self):
        """Get the AnkiConnect-formatted request to update fields."""
        return AnkiConnect.request(
            "multi",
            actions=[
                AnkiConnect.request(
                    "updateNoteFields", note={
                        "id": parsed.id,
                        "fields": parsed.note["fields"],
                        "audio": parsed.note["audio"]
                    }
                )
                for parsed in self.notes_to_edit
            ]
        )

    def get_note_info(self):
        """Get the AnkiConnect-formatted request to get note info."""
        return AnkiConnect.request(
            "notesInfo",
            notes=[
                parsed.id for parsed in self.notes_to_edit
            ]
        )

    def get_cards(self):
        """Get the card IDs for all notes that need to be edited."""
        print("Getting card IDs")
        self.cards = list()
        for info in self.card_ids:
            self.cards += info["cards"]

    def get_change_decks(self):
        """Get the AnkiConnect-formatted request to change decks."""
        return AnkiConnect.request(
            "changeDeck",
            cards=self.cards,
            deck=Note.TARGET_DECK
        )

    def get_clear_tags(self):
        """Get the AnkiConnect-formatted request to clear tags."""
        return AnkiConnect.request(
            "removeTags",
            notes=[parsed.id for parsed in self.notes_to_edit],
            tags=" ".join(self.tags)
        )

    def get_add_tags(self):
        """Get the AnkiConnect-formatted request to add tags."""
        return AnkiConnect.request(
            "multi",
            actions=[
                AnkiConnect.request(
                    "addTags",
                    notes=[parsed.id],
                    tags=" ".join(parsed.note["tags"])
                )
                for parsed in self.notes_to_edit
                if parsed.note["tags"]
            ]
        )


if __name__ == "__main__":
    if not os.path.exists(Config.CONFIG_PATH):
        Config.update_config()
    App()
