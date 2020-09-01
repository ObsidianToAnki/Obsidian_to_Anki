"""Script for adding cards to Anki from Obsidian."""

import re
import json
import urllib.request
import configparser
import os
import argparse
import collections


def write_safe(filename, contents):
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
            update_note = dict()
            update_note["id"] = identifier
            update_note["fields"] = note["fields"]
            update_note["audio"] = note["audio"]
            return AnkiConnect.invoke(
                "updateNoteFields", note=update_note
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

    DEFAULT_DECK = "Default"
    NOTE_DICT_TEMPLATE = {
        "deckName": DEFAULT_DECK,
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
    ID_PREFIX = "ID: "
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
        template = Note.NOTE_DICT_TEMPLATE.copy()
        template["modelName"] = self.note_type
        template["fields"] = self.fields
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
        subs = {
            note: {
                field: field + ": "
                for field in AnkiConnect.invoke(
                    "modelFieldNames", modelName=note
                )
            } for note in note_types
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

    parser = argparse.ArgumentParser(
        description="Add cards to Anki from an Obsidian markdown file."
    )
    parser.add_argument(
        "-filename", type=str, help="The file you want to add flashcards from."
    )
    parser.add_argument(
        "-update",
        action="store_true",
        help="""
            Whether you want to update the config file
            using new notes from Anki.
            Note that this does NOT open the config file for editing,
            you have to do that manually.
        """,
    )
    parser.add_argument(
        "-config",
        action="store_true",
        help="""
            Opens up config file for editing.
        """
    )

    NOTE_REGEXP = re.compile(r"(?<=START\n)[\s\S]*?(?=END\n?)")

    def anki_from_file(filename):
        print("Adding notes from", filename, "...")
        with open(filename) as f:
            file = f.read()
            updated_file = file
            position = 0
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

    def main():
        """Execute the main functionality of the script."""
        args = App.parser.parse_args()
        if args.update:
            Config.update_config()
        Config.load_config()
        if args.config:
            os.startfile(Config.CONFIG_PATH)
            return
        if args.filename:
            App.anki_from_file2(args.filename)


if __name__ == "__main__":
    if not os.path.exists(Config.CONFIG_PATH):
        Config.update_config()
    App.main()
