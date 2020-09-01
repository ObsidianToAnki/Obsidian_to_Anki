"""Script for adding cards to Anki from Obsidian."""

import re
import json
import urllib.request
import configparser
import os
import argparse
import collections
import webbrowser


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

    def add_or_update(note_and_id):
        """Add the note if id is None, otherwise update the note."""
        note, identifier = note_and_id.note, note_and_id.id
        if identifier is None:
            return AnkiConnect.invoke(
                "addNote", note=note
            )
        else:
            AnkiConnect.note_update(note, identifier)

    def note_update(note_dict, id):
        """Update note with identifier id to match note_dict."""
        # First, update fields
        update_note = dict()
        update_note["id"] = id
        update_note["fields"] = note_dict["fields"]
        update_note["audio"] = note_dict["audio"]
        AnkiConnect.invoke(
            "updateNoteFields", note=update_note
        )
        # Next, change deck
        cards = AnkiConnect.invoke(
            "notesInfo",
            notes=[id]
        )[0]["cards"]
        AnkiConnect.invoke(
            "changeDeck",
            cards=cards,
            deck=Note.TARGET_DECK
        )


class FormatConverter:
    """Converting Obsidian formatting to Anki formatting."""

    INLINE_MATH_REGEXP = re.compile(r"(?<!\$)\$(?=[\S])(?=[^$])[\s\S]*?\S\$")
    DISPLAY_MATH_REGEXP = re.compile(r"\$\$[\s\S]*?\$\$")

    ANKI_INLINE_START = r"\("
    ANKI_INLINE_END = r"\)"

    ANKI_DISPLAY_START = r"\["
    ANKI_DISPLAY_END = r"\]"

    def inline_anki_repl(matchobject):
        """Get replacement string for Obsidian-formatted inline math."""
        found_string = matchobject.group(0)
        # Strip Obsidian formatting by removing first and last characters
        found_string = found_string[1:-1]
        # Add Anki formatting
        result = FormatConverter.ANKI_INLINE_START + found_string
        result += FormatConverter.ANKI_INLINE_END
        return result

    def display_anki_repl(matchobject):
        """Get replacement string for Obsidian-formatted display math."""
        found_string = matchobject.group(0)
        # Strip Obsidian formatting by removing first two and last two chars
        found_string = found_string[2:-2]
        # Add Anki formatting
        result = FormatConverter.ANKI_DISPLAY_START + found_string
        result += FormatConverter.ANKI_DISPLAY_END
        return result

    def obsidian_to_anki_math(note_text):
        """Convert Obsidian-formatted math to Anki-formatted math."""
        return FormatConverter.INLINE_MATH_REGEXP.sub(
            FormatConverter.inline_anki_repl,
            FormatConverter.DISPLAY_MATH_REGEXP.sub(
                FormatConverter.display_anki_repl, note_text
            )
        )

    def format(note_text):
        """Apply all format conversions to note_text."""
        note_text = FormatConverter.obsidian_to_anki_math(note_text)
        return note_text


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
        self.text = FormatConverter.format(note_text)
        self.lines = self.text.splitlines()
        self.note_type = Note.note_subs[self.lines[0]]
        self.subs = Note.field_subs[self.note_type]
        self.current_field_num = 0
        self.field_names = list(self.subs)
        if self.lines[-1].startswith(Note.ID_PREFIX):
            self.identifier = int(self.lines.pop()[len(Note.ID_PREFIX):])
            # The above removes the identifier line, for convenience of parsing
        else:
            self.identifier = None
        if self.lines[-1].startswith(Note.TAG_PREFIX):
            self.tags = self.lines.pop()[len(Note.TAG_PREFIX):].split(
                Note.TAG_SEP
            )
        else:
            self.tags = None

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
                self.current_field_num += 1
                line = line[len(self.current_sub):]
            fields[self.current_field] += line + " "
        return {key: value.rstrip() for key, value in fields.items()}

    def parse(self):
        """Get a properly formatted dictionary of the note."""
        template = self.NOTE_DICT_TEMPLATE.copy()
        template["modelName"] = self.note_type
        template["fields"] = self.fields
        if self.tags:
            template["tags"] = template["tags"] + self.tags
        return Note.Note_and_id(note=template, id=self.identifier)


class Config:
    """Deals with saving and loading the configuration file."""

    CONFIG_PATH = os.path.dirname(__file__) + "/obsidian_to_anki_config.ini"

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

    @staticmethod
    def anki_from_file(filename):
        """Add to or update notes from Anki, from filename."""
        print("Adding notes from", filename, "...")
        with open(filename) as f:
            file = f.read()
            updated_file = file
            position = 0
        target_deck = App.DECK_REGEXP.search(file)
        if target_deck is not None:
            Note.TARGET_DECK = target_deck.group(0)
        match = App.NOTE_REGEXP.search(updated_file, position)
        while match:
            note = match.group(0)
            parsed = Note(note).parse()
            result = AnkiConnect.add_or_update(parsed)
            position = match.end()
            if result is not None and parsed.id is None:
                # This indicates a new note was added successfully:

                # Result being None means either error or the result is
                # an identifier.

                # parsed.id being None means that there was
                # No ID to begin with.

                # So, we need to insert the note ID as a line.
                print(
                    "Successfully added note with ID",
                    result
                )
                updated_file = "".join([
                    updated_file[:match.end()],
                    Note.ID_PREFIX + str(result) + "\n",
                    updated_file[match.end():]
                ])
                position += len(Note.ID_PREFIX + str(result) + "\n")
            else:
                print("Successfully updated note with ID", parsed.id)
            match = App.NOTE_REGEXP.search(updated_file, position)
        print("All notes from", filename, "added, now writing new IDs.")
        write_safe(filename, updated_file)

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
        if args.filename:
            self.filename = args.filename
            print("Reading file into memory...")
            with open(args.filename) as f:
                self.file = f.read()
            self.target_deck = App.DECK_REGEXP.search(self.file).group(0)
            if self.target_deck is not None:
                Note.TARGET_DECK = self.target_deck
            print("Identified target deck as", Note.TARGET_DECK)
            self.scan_file()
            self.add_notes()
            self.write_ids()
            self.update_fields()
            self.get_info()
            self.get_cards()
            self.move_cards()
            self.get_tags()
            # App.anki_from_file(args.filename)

    def setup_parser(self):
        """Set up the argument parser."""
        self.parser = argparse.ArgumentParser(
            description="Add cards to Anki from an Obsidian markdown file."
        )
        self.parser.add_argument(
            "-f",
            type=str,
            help="The file you want to add flashcards from.",
            dest="filename"
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

    def scan_file(self):
        """Sort notes from file into adding vs editing."""
        print("Scanning file for notes...")
        self.notes_to_add = list()
        self.id_indexes = list()
        self.notes_to_edit = list()
        for note_match in App.NOTE_REGEXP.finditer(self.file):
            note, position = note_match.group(0), note_match.end()
            parsed = Note(note).parse()
            if parsed.id is None:
                self.notes_to_add.append(parsed.note)
                self.id_indexes.append(position)
            else:
                self.notes_to_edit.append(parsed)

    @staticmethod
    def id_to_str(id):
        """Get the string repr of id."""
        return "ID: " + str(id) + "\n"

    def add_notes(self):
        """Add notes to Anki."""
        print("Adding notes into Anki...")
        self.identifiers = map(
            App.id_to_str, AnkiConnect.invoke(
                "addNotes",
                notes=self.notes_to_add
            )
        )

    def write_ids(self):
        """Write the identifiers to the file."""
        print("Writing new note IDs to file...")
        self.file = string_insert(
            self.file, zip(
                self.id_indexes, self.identifiers
            )
        )
        write_safe(self.filename, self.file)

    def update_fields(self):
        """Update the fields of current notes."""
        print("Updating fields of existing notes...")
        AnkiConnect.invoke(
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

    def get_info(self):
        """Get info on all notes to be edited."""
        print("Getting info on notes to be edited...")
        self.info = AnkiConnect.invoke(
            "notesInfo",
            notes=[
                parsed.id for parsed in self.notes_to_edit
            ]
        )

    def get_cards(self):
        """Get the card IDs for all notes that need to be edited."""
        print("Getting card IDs")
        self.cards = list()
        for info in self.info:
            self.cards += info["cards"]

    def move_cards(self):
        """Move all cards to target deck."""
        print("Moving cards to target deck...")
        AnkiConnect.invoke(
            "changeDeck",
            cards=self.cards,
            deck=self.target_deck
        )

    def get_tags(self):
        """Get a set of currently used tags for notes to be edited."""
        self.tags = set()
        for info in self.info:
            self.tags.update(info["tags"])

    def clear_tags(self):
        """Remove all currently used tags from notes to be edited."""
        AnkiConnect.invoke(
            "removeTags",
            notes=[parsed.id for parsed in self.notes_to_edit],
            tags="".join(self.tags)
        )


if __name__ == "__main__":
    if not os.path.exists(Config.CONFIG_PATH):
        Config.update_config()
    App()
