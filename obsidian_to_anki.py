"""Script for adding cards to Anki from Obsidian."""

import re
import json
import urllib.request
import configparser
import os
import collections
import webbrowser
import markdown
import base64
import gooey
import argparse

MEDIA_PATHS = set()

ID_PREFIX = "ID: "
TAG_PREFIX = "Tags: "
TAG_SEP = " "
Note_and_id = collections.namedtuple('Note_and_id', ['note', 'id'])
NOTE_DICT_TEMPLATE = {
    "deckName": "",
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

CONFIG_PATH = os.path.expanduser(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "obsidian_to_anki_config.ini"
    )
)
CONFIG_DATA = dict()

md_parser = markdown.Markdown(
    extensions=['extra', 'nl2br', 'sane_lists'], output_format="html5"
)


def write_safe(filename, contents):
    """
    Write contents to filename while keeping a backup.

    If write fails, a backup 'filename.bak' will still exist.
    """
    with open(filename + ".tmp", "w", encoding='utf_8') as temp:
        temp.write(contents)
    os.rename(filename, filename + ".bak")
    os.rename(filename + ".tmp", filename)
    with open(filename, encoding='utf_8') as f:
        success = (f.read() == contents)
    if success:
        os.remove(filename + ".bak")


def string_insert(string, position_inserts):
    """
    Insert strings in position_inserts into string, at indices.

    position_inserts will look like:
    [(0, "hi"), (3, "hello"), (5, "beep")]
    """
    offset = 0
    position_inserts = sorted(list(position_inserts))
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


def spans(pattern, string):
    """Return a list of span-tuples for matches of pattern in string."""
    return [match.span() for match in pattern.finditer(string)]


def overlap(span, spans):
    """Determine whether span overlaps with anything in spans."""
    return any(
        start <= span[0] < end or start < span[1] <= end
        for start, end in spans
    )


def findignore(pattern, string, ignore_spans):
    """Yield all matches for pattern in string not in ignore_spans."""
    return (
        match
        for match in pattern.finditer(string)
        if not overlap(match.span(), ignore_spans)
    )


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
        return AnkiConnect.parse(response)

    def parse(response):
        """Parse the received response."""
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

    IMAGE_REGEXP = re.compile(r'<img alt="[\s\S]*?" src="([\s\S]*?)">')
    SOUND_REGEXP = re.compile(r'\[sound:(.+)\]')
    CLOZE_REGEXP = re.compile(r'{(.+?)}')
    URL_REGEXP = re.compile(r'https?://')

    PARA_OPEN = "<p>"
    PARA_CLOSE = "</p>"

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
    def cloze_repl(string, cloze_number):
        """Return a Anki-formatted cloze string."""
        return "".join(
            [
                r"{{c",
                str(cloze_number),
                r"::",
                string[1:-1],
                r"}}"
            ]
        )

    @staticmethod
    def curly_to_cloze(text):
        """Change text in curly brackets to Anki-formatted cloze."""
        for index, cloze_match in enumerate(
            FormatConverter.CLOZE_REGEXP.finditer(
                text
            ), start=1
        ):
            text = text.replace(
                cloze_match.group(0),
                FormatConverter.cloze_repl(cloze_match.group(0), index),
                1
            )
        return text

    @staticmethod
    def markdown_parse(text):
        """Apply markdown conversions to text."""
        text = md_parser.reset().convert(text)
        return text

    @staticmethod
    def format(note_text, cloze=False):
        """Apply all format conversions to note_text."""
        note_text = FormatConverter.obsidian_to_anki_math(note_text)
        # Extract the parts that are anki math
        math_matches = [
            math_match.group(0)
            for math_match in FormatConverter.ANKI_MATH_REGEXP.finditer(
                note_text
            )
        ]
        # Replace them to be later added back, so they don't interfere
        # with markdown parsing
        note_text = FormatConverter.ANKI_MATH_REGEXP.sub(
            FormatConverter.MATH_REPLACE, note_text
        )
        if cloze:
            note_text = FormatConverter.curly_to_cloze(note_text)
        note_text = FormatConverter.markdown_parse(note_text)
        # Add back the parts that are anki math
        for math_match in math_matches:
            note_text = note_text.replace(
                FormatConverter.MATH_REPLACE,
                math_match,
                1
            )
        FormatConverter.get_images(note_text)
        FormatConverter.get_audio(note_text)
        note_text = FormatConverter.fix_image_src(note_text)
        note_text = FormatConverter.fix_audio_src(note_text)
        note_text = note_text.strip()
        # Remove unnecessary paragraph tag
        if note_text.startswith(
            FormatConverter.PARA_OPEN
        ) and note_text.endswith(
            FormatConverter.PARA_CLOSE
        ):
            note_text = note_text[len(FormatConverter.PARA_OPEN):]
            note_text = note_text[:-len(FormatConverter.PARA_CLOSE)]
        return note_text

    @staticmethod
    def is_url(text):
        """Check whether text looks like a url."""
        return bool(
            FormatConverter.URL_REGEXP.match(text)
        )

    @staticmethod
    def get_images(html_text):
        """Get all the images that need to be added."""
        for match in FormatConverter.IMAGE_REGEXP.finditer(html_text):
            path = match.group(1)
            if FormatConverter.is_url(path):
                continue  # Skips over images web-hosted.
            filename = os.path.basename(path)
            if filename not in CONFIG_DATA["Added Media"].keys():
                MEDIA_PATHS.add(path)
            # ^Adds the image path (relative to cwd)

    @staticmethod
    def get_audio(html_text):
        """Get all the audio that needs to be added"""
        for match in FormatConverter.SOUND_REGEXP.finditer(html_text):
            path = match.group(1)
            filename = os.path.basename(path)
            if filename not in CONFIG_DATA["Added Media"].keys():
                MEDIA_PATHS.add(path)

    @staticmethod
    def path_to_filename(matchobject):
        """Replace the src in matchobject appropriately."""
        found_string, found_path = matchobject.group(0), matchobject.group(1)
        if FormatConverter.is_url(found_path):
            return found_string  # So urls should not be altered.
        found_string = found_string.replace(
            found_path, os.path.basename(found_path)
        )
        return found_string

    @staticmethod
    def fix_image_src(html_text):
        """Fix the src of the images so that it's relative to Anki."""
        return FormatConverter.IMAGE_REGEXP.sub(
            FormatConverter.path_to_filename,
            html_text
        )

    @staticmethod
    def fix_audio_src(html_text):
        """Fix the audio filenames so that it's relative to Anki."""
        return FormatConverter.SOUND_REGEXP.sub(
            FormatConverter.path_to_filename,
            html_text
        )


class Note:
    """Manages parsing notes into a dictionary formatted for AnkiConnect.

    Input must be the note text.
    Does NOT deal with finding the note in the file.
    """

    def __init__(self, note_text):
        """Set up useful variables."""
        self.text = note_text
        self.lines = self.text.splitlines()
        self.current_field_num = 0
        self.delete = False
        if self.lines[-1].startswith(ID_PREFIX):
            self.identifier = int(self.lines.pop()[len(ID_PREFIX):])
            # The above removes the identifier line, for convenience of parsing
        else:
            self.identifier = None
        if not self.lines:
            # This indicates a delete action.
            self.delete = True
            return
        elif self.lines[-1].startswith(TAG_PREFIX):
            self.tags = self.lines.pop()[len(TAG_PREFIX):].split(
                TAG_SEP
            )
        else:
            self.tags = list()
        self.note_type = Note.note_subs[self.lines[0]]
        self.subs = Note.field_subs[self.note_type]
        self.field_names = list(self.subs)

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
            key: FormatConverter.format(
                value.strip(),
                cloze=(self.note_type == "Cloze" and CONFIG_DATA["CurlyCloze"])
            )
            for key, value in fields.items()
        }
        return {key: value.strip() for key, value in fields.items()}

    def parse(self, deck):
        """Get a properly formatted dictionary of the note."""
        template = NOTE_DICT_TEMPLATE.copy()
        if not self.delete:
            template["modelName"] = self.note_type
            template["fields"] = self.fields
            template["tags"] = template["tags"] + self.tags
            template["deckName"] = deck
            return Note_and_id(note=template, id=self.identifier)
        else:
            return Note_and_id(note=False, id=self.identifier)


class InlineNote(Note):

    ID_REGEXP = re.compile(ID_PREFIX + r"(\d+)")
    TAG_REGEXP = re.compile(TAG_PREFIX + r"(.*)")
    TYPE_REGEXP = re.compile(r"\[(.*?)\]")  # So e.g. [Basic]

    def __init__(self, note_text):
        self.text = note_text.strip()
        self.current_field_num = 0
        self.delete = False
        ID = InlineNote.ID_REGEXP.search(self.text)
        if ID is not None:
            self.identifier = int(ID.group(1))
            self.text = self.text[:ID.start()]  # Removes identifier
        else:
            self.identifier = None
        if not self.text:
            # This indicates a delete action
            self.delete = True
            return
        TAGS = InlineNote.TAG_REGEXP.search(self.text)
        if TAGS is not None:
            self.tags = TAGS.group(1).split(TAG_SEP)
            self.text = self.text[:TAGS.start()]
        else:
            self.tags = list()
        TYPE = InlineNote.TYPE_REGEXP.search(self.text)
        self.note_type = Note.note_subs[TYPE.group(1)]
        self.text = self.text[TYPE.end():]
        self.subs = Note.field_subs[self.note_type]
        self.field_names = list(self.subs)
        self.text = self.text.strip()

    @property
    def fields(self):
        """Get the fields of the note into a dictionary."""
        fields = dict.fromkeys(self.field_names, "")
        while self.next_sub:
            # So, we're expecting a new field
            end = self.text.find(self.next_sub)
            fields[self.current_field] += self.text[:end]
            self.text = self.text[end + len(self.next_sub):]
            self.current_field_num += 1
        # For last field:
        fields[self.current_field] += self.text
        fields = {
            key: FormatConverter.format(
                value,
                cloze=(self.note_type == "Cloze" and CONFIG_DATA["CurlyCloze"])
            )
            for key, value in fields.items()
        }
        return {key: value.strip() for key, value in fields.items()}


class RegexNote:
    ID_REGEXP_STR = r"\n(" + ID_PREFIX + r"\d+)"
    TAG_REGEXP_STR = r"(" + TAG_PREFIX + r".*)"

    def __init__(self, matchobject, note_type, tags=False, id=False):
        self.match = matchobject
        self.note_type = note_type
        self.groups = list(self.match.groups())
        self.group_num = len(self.groups)
        if id:
            # This means id is last group
            self.identifier = int(self.groups.pop()[len(ID_PREFIX):])
        else:
            self.identifier = None
        if tags:
            # Even if id were present, tags is now last group
            self.tags = self.groups.pop()[len(TAG_PREFIX):].split(
                TAG_SEP
            )
        else:
            self.tags = list()
        self.field_names = list(Note.field_subs[self.note_type])

    @property
    def fields(self):
        fields = dict.fromkeys(self.field_names, "")
        for name, match in zip(self.field_names, self.groups):
            if match:
                fields[name] = match
        fields = {
            key: FormatConverter.format(
                value,
                cloze=(self.note_type == "Cloze" and CONFIG_DATA["CurlyCloze"])
            )
            for key, value in fields.items()
        }
        return {key: value.strip() for key, value in fields.items()}

    def parse(self, deck):
        """Get a properly formatted dictionary of the note."""
        template = NOTE_DICT_TEMPLATE.copy()
        template["modelName"] = self.note_type
        template["fields"] = self.fields
        template["tags"] = template["tags"] + self.tags
        template["deckName"] = deck
        return Note_and_id(note=template, id=self.identifier)


class Config:
    """Deals with saving and loading the configuration file."""

    def update_config():
        """Update config with new notes."""
        print("Updating configuration file...")
        config = configparser.ConfigParser()
        config.optionxform = str
        if os.path.exists(CONFIG_PATH):
            print("Config file exists, reading...")
            config.read(CONFIG_PATH, encoding='utf-8-sig')
        # Setting up field substitutions
        note_types = AnkiConnect.invoke("modelNames")
        fields_request = [
            AnkiConnect.request(
                "modelFieldNames", modelName=note
            )
            for note in note_types
        ]
        subs = {
            note: {
                field: field + ":"
                for field in AnkiConnect.parse(fields)
            }
            for note, fields in zip(
                note_types,
                AnkiConnect.invoke(
                    "multi", actions=fields_request
                )
            )
        }
        for note, note_field_subs in subs.items():
            config.setdefault(note, dict())
            for field, sub in note_field_subs.items():
                config[note].setdefault(field, sub)
                # This means that, if there's already a substitution present,
                # the 'default' substitution of field + ":" isn't added.
        # Setting up Note Substitutions
        config.setdefault("Note Substitutions", dict())
        for note in note_types:
            config["Note Substitutions"].setdefault(note, note)
            # Similar to above - if there's already a substitution present,
            # it isn't overwritten
        # Setting up Syntax
        config.setdefault("Syntax", dict())
        config["Syntax"].setdefault(
            "Begin Note", "START"
        )
        config["Syntax"].setdefault(
            "End Note", "END"
        )
        config["Syntax"].setdefault(
            "Begin Inline Note", "STARTI"
        )
        config["Syntax"].setdefault(
            "End Inline Note", "ENDI"
        )
        config["Syntax"].setdefault(
            "Target Deck Line", "TARGET DECK"
        )
        config["Syntax"].setdefault(
            "File Tags Line", "FILE TAGS"
        )
        config["Syntax"].setdefault(
            "Delete Regex Note Line", "DELETE"
        )
        config.setdefault("DEFAULT", dict())
        config["DEFAULT"].setdefault(
            "Tag", "Obsidian_to_Anki"
        )
        config["DEFAULT"].setdefault(
            "Deck", "Default"
        )
        config["DEFAULT"].setdefault(
            "CurlyCloze", "False"
        )
        config["DEFAULT"].setdefault(
            "GUI", "True"
        )
        # Setting up Custom Regexps
        config.setdefault("Custom Regexps", dict())
        for note in note_types:
            config["Custom Regexps"].setdefault(note, "")
        # Setting up media files
        config.setdefault("Added Media", dict())
        with open(CONFIG_PATH, "w", encoding='utf_8') as configfile:
            config.write(configfile)
        print("Configuration file updated!")

    def load_config():
        """Load from an existing config file (assuming it exists)."""
        print("Loading configuration file...")
        config = configparser.ConfigParser()
        config.optionxform = str  # Allows for case sensitivity
        config.read(CONFIG_PATH, encoding='utf-8-sig')
        note_subs = config["Note Substitutions"]
        Note.note_subs = {v: k for k, v in note_subs.items()}
        Note.field_subs = {
            note: dict(config[note]) for note in config
            if note not in [
                "Note Substitutions",
                "DEFAULT",
                "Syntax",
                "Custom Regexps",
                "Added Media"
            ]
        }
        CONFIG_DATA["NOTE_PREFIX"] = re.escape(
            config["Syntax"]["Begin Note"]
        )
        CONFIG_DATA["NOTE_SUFFIX"] = re.escape(
            config["Syntax"]["End Note"]
        )
        CONFIG_DATA["INLINE_PREFIX"] = re.escape(
            config["Syntax"]["Begin Inline Note"]
        )
        CONFIG_DATA["INLINE_SUFFIX"] = re.escape(
            config["Syntax"]["End Inline Note"]
        )
        CONFIG_DATA["DECK_LINE"] = re.escape(
            config["Syntax"]["Target Deck Line"]
        )
        CONFIG_DATA["TAG_LINE"] = re.escape(
            config["Syntax"]["File Tags Line"]
        )
        CONFIG_DATA["Added Media"] = config["Added Media"]
        RegexFile.EMPTY_REGEXP = re.compile(
            re.escape(
                config["Syntax"]["Delete Regex Note Line"]
            ) + RegexNote.ID_REGEXP_STR
        )
        NOTE_DICT_TEMPLATE["tags"] = [config["DEFAULT"]["Tag"]]
        NOTE_DICT_TEMPLATE["deckName"] = config["DEFAULT"]["Deck"]
        CONFIG_DATA["CurlyCloze"] = config.getboolean(
            "DEFAULT", "CurlyCloze"
        )
        CONFIG_DATA["GUI"] = config.getboolean(
            "DEFAULT", "GUI"
        )
        Config.config = config  # Can access later if need be
        print("Loaded successfully!")


class App:
    """Master class that manages the application."""

    SUPPORTED_EXTS = [".md", ".txt"]

    def __init__(self):
        """Execute the main functionality of the script."""
        try:
            Config.load_config()
        except configparser.Error as e:
            print("Error:", e)
            print("Attempting to fix config file...")
            Config.update_config()
            Config.load_config()
        if CONFIG_DATA["GUI"]:
            self.setup_gui_parser()
        else:
            self.setup_cli_parser()
        args = self.parser.parse_args()
        if CONFIG_DATA["GUI"] and args.dirpath:
            args.path = args.dirpath
        no_args = True
        if args.update:
            no_args = False
            Config.update_config()
            Config.load_config()
        if args.mediaupdate:
            no_args = False
            CONFIG_DATA["Added Media"].clear()
        self.gen_regexp()
        if args.config:
            no_args = False
            webbrowser.open(CONFIG_PATH)
            return
        if args.path:
            no_args = False
            if args.path == "False":
                return
            current = os.getcwd()
            self.path = args.path
            if os.path.isdir(self.path):
                try:
                    os.chdir(self.path)
                except Exception:
                    print("Could not move to path directory.")
                    return
                with os.scandir() as it:
                    if args.regex:
                        self.files = [
                            RegexFile(entry.path)
                            for entry in it
                            if entry.is_file() and os.path.splitext(
                                entry.path
                            )[1] in App.SUPPORTED_EXTS
                        ]
                    else:
                        self.files = [
                            File(entry.path)
                            for entry in it
                            if entry.is_file() and os.path.splitext(
                                entry.path
                            )[1] in App.SUPPORTED_EXTS
                        ]
            else:
                if args.regex:
                    self.files = [RegexFile(self.path)]
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
            os.chdir(current)
        if no_args:
            self.parser.print_help()

    def setup_parser_optionals(self):
        """Set up optional arguments for the parser."""
        self.parser.add_argument(
            "-c", "--config",
            action="store_true",
            dest="config",
            help="Open up config file for editing."
        )
        self.parser.add_argument(
            "-u", "--update",
            action="store_true",
            dest="update",
            help="Update config file."
        )
        self.parser.add_argument(
            "-r", "--regex",
            action="store_true",
            dest="regex",
            help="Use custom regex syntax."
        )
        self.parser.add_argument(
            "-m", "--mediaupdate",
            action="store_true",
            dest="mediaupdate",
            help="Force addition of media files."
        )

    @gooey.Gooey(use_cmd_args=True)
    def setup_gui_parser(self):
        """Set up the GUI argument parser."""
        self.parser = gooey.GooeyParser(
            description="Add cards to Anki from a markdown or text file."
        )
        path_group = self.parser.add_mutually_exclusive_group(required=False)
        path_group.add_argument(
            "-f", "--file",
            help="Choose a file to scan.",
            dest="path",
            widget='FileChooser'
        )
        path_group.add_argument(
            "-d", "--dir",
            help="Choose a directory to scan.",
            dest="dirpath",
            widget='DirChooser'
        )
        self.setup_parser_optionals()

    def setup_cli_parser(self):
        """Setup the command-line argument parser."""
        self.parser = argparse.ArgumentParser(
            description="Add cards to Anki from a markdown or text file."
        )
        self.parser.add_argument(
            "path",
            default=False,
            nargs="?",
            help="Path to the file or directory you want to scan."
        )
        self.setup_parser_optionals()

    def gen_regexp(self):
        """Generate the regular expressions used by the app."""
        setattr(
            App, "NOTE_REGEXP",
            re.compile(
                r"".join(
                    [
                        r"^",
                        CONFIG_DATA["NOTE_PREFIX"],
                        r"\n([\s\S]*?\n)",
                        CONFIG_DATA["NOTE_SUFFIX"],
                        r"\n?"
                    ]
                ), flags=re.MULTILINE
            )
        )
        setattr(
            App, "DECK_REGEXP",
            re.compile(
                "".join(
                    [
                        r"^",
                        CONFIG_DATA["DECK_LINE"],
                        r"\n(.*)",
                    ]
                ), flags=re.MULTILINE
            )
        )
        setattr(
            App, "EMPTY_REGEXP",
            re.compile(
                "".join(
                    [
                        r"^",
                        CONFIG_DATA["NOTE_PREFIX"],
                        r"\n",
                        ID_PREFIX,
                        r"[\s\S]*?\n",
                        CONFIG_DATA["NOTE_SUFFIX"]
                    ]
                ), flags=re.MULTILINE
            )
        )
        setattr(
            App, "TAG_REGEXP",
            re.compile(
                r"^" + CONFIG_DATA["TAG_LINE"] + r"\n(.*)\n",
                flags=re.MULTILINE
            )
        )
        setattr(
            App, "INLINE_REGEXP",
            re.compile(
                "".join(
                    [
                        CONFIG_DATA["INLINE_PREFIX"],
                        r"(.*?)",
                        CONFIG_DATA["INLINE_SUFFIX"]
                    ]
                )
            )
        )
        setattr(
            App, "INLINE_EMPTY_REGEXP",
            re.compile(
                "".join(
                    [
                        CONFIG_DATA["INLINE_PREFIX"],
                        r"\s+" + ID_PREFIX + r".*?",
                        CONFIG_DATA["INLINE_SUFFIX"]
                    ]
                )
            )
        )

    def get_tags(self):
        """Get a set of currently used tags for notes to be edited."""
        self.tags = set()
        for info in self.info:
            self.tags.update(info["tags"])

    def get_add_media(self):
        """Get the AnkiConnect-formatted add_media request."""
        return AnkiConnect.request(
            "multi",
            actions=[
                AnkiConnect.request(
                    "storeMediaFile",
                    filename=path.replace(
                        path, os.path.basename(path)
                    ),
                    data=file_encode(path)
                )
                for path in MEDIA_PATHS
            ]
        )

    def requests_1(self):
        """Do big request 1.

        This adds images, adds notes, updates fields,
        gets note info, gets tags and removes notes.
        """
        requests = list()
        print("Adding media with these paths...")
        print(MEDIA_PATHS)
        requests.append(self.get_add_media())
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
        notes_ids = AnkiConnect.parse(result[1])
        cards_ids = AnkiConnect.parse(result[3])
        tags = AnkiConnect.parse(result[4])
        for note_ids, file in zip(notes_ids, self.files):
            file.note_ids = AnkiConnect.parse(note_ids)
        for card_ids, file in zip(cards_ids, self.files):
            file.card_ids = AnkiConnect.parse(card_ids)
        for file in self.files:
            file.tags = tags
        for imgpath in MEDIA_PATHS:
            CONFIG_DATA["Added Media"].setdefault(
                os.path.basename(imgpath),
                "True"
            )
        with open(CONFIG_PATH, "w", encoding='utf_8') as configfile:
            Config.config.write(configfile)

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
        with open(self.filename, encoding='utf_8') as f:
            self.file = f.read()
            self.file += "\n"  # Adds empty line, useful for ID
        self.target_deck = App.DECK_REGEXP.search(self.file)
        if self.target_deck is not None:
            self.target_deck = self.target_deck.group(1)
        else:
            self.target_deck = NOTE_DICT_TEMPLATE["deckName"]
        print(
            "Identified target deck for", self.filename,
            "as", self.target_deck
        )
        self.global_tags = App.TAG_REGEXP.search(self.file)
        if self.global_tags is not None:
            self.global_tags = self.global_tags.group(1)
        else:
            self.global_tags = ""

    def scan_file(self):
        """Sort notes from file into adding vs editing."""
        print("Scanning file", self.filename, " for notes...")
        self.notes_to_add = list()
        self.id_indexes = list()
        self.notes_to_edit = list()
        self.notes_to_delete = list()
        self.inline_notes_to_add = list()
        self.inline_id_indexes = list()
        for note_match in App.NOTE_REGEXP.finditer(self.file):
            note, position = note_match.group(1), note_match.end(1)
            parsed = Note(note).parse(self.target_deck)
            if parsed.id is None:
                # Need to make sure global_tags get added.
                parsed.note["tags"] += self.global_tags.split(TAG_SEP)
                self.notes_to_add.append(parsed.note)
                self.id_indexes.append(position)
            elif not parsed.note:
                # This indicates a delete action
                self.notes_to_delete.append(parsed.id)
            else:
                self.notes_to_edit.append(parsed)
        for inline_note_match in App.INLINE_REGEXP.finditer(self.file):
            note = inline_note_match.group(1)
            position = inline_note_match.end(1)
            parsed = InlineNote(note).parse(self.target_deck)
            if parsed.id is None:
                # Need to make sure global_tags get added.
                parsed.note["tags"] += self.global_tags.split(TAG_SEP)
                self.inline_notes_to_add.append(parsed.note)
                self.inline_id_indexes.append(position)
            elif not parsed.note:
                # This indicates a delete action
                self.notes_to_delete.append(parsed.id)
            else:
                self.notes_to_edit.append(parsed)

    @staticmethod
    def id_to_str(id, inline=False):
        """Get the string repr of id."""
        if inline:
            return ID_PREFIX + str(id) + " "
        else:
            return ID_PREFIX + str(id) + "\n"

    def write_ids(self):
        """Write the identifiers to self.file."""
        print("Writing new note IDs to file,", self.filename, "...")
        self.file = string_insert(
            self.file, list(
                zip(
                    self.id_indexes, [
                        self.id_to_str(id)
                        for id in self.note_ids[:len(self.notes_to_add)]
                        if id is not None
                    ]
                )
            ) + list(
                zip(
                    self.inline_id_indexes, [
                        self.id_to_str(id, inline=True)
                        for id in self.note_ids[len(self.notes_to_add):]
                        if id is not None
                    ]
                )
            )
        )

    def remove_empties(self):
        """Remove empty notes from self.file."""
        self.file = App.EMPTY_REGEXP.sub(
            "", self.file
        )
        self.file = App.INLINE_EMPTY_REGEXP.sub(
            "", self.file
        )

    def write_file(self):
        """Write to the actual os file"""
        self.file = self.file[:-1]  # Remove newline added
        write_safe(self.filename, self.file)

    def get_add_notes(self):
        """Get the AnkiConnect-formatted request to add notes."""
        return AnkiConnect.request(
            "addNotes",
            notes=self.notes_to_add + self.inline_notes_to_add
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
            deck=self.target_deck
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
                    tags=" ".join(parsed.note["tags"]) + " " + self.global_tags
                )
                for parsed in self.notes_to_edit
            ]
        )


class RegexFile(File):

    def scan_file(self):
        """Sort notes from file into adding vs editing."""
        print("Scanning file", self.filename, " for notes...")
        self.ignore_spans = list()
        # The above ensures that the script won't match a RegexNote inside
        # a Note or InlineNote
        self.notes_to_add = list()
        self.id_indexes = list()
        self.notes_to_edit = list()
        self.notes_to_delete = list()
        self.inline_notes_to_add = list()  # To avoid overriding get_add_notes
        self.ignore_spans += spans(App.NOTE_REGEXP, self.file)
        self.ignore_spans += spans(App.INLINE_REGEXP, self.file)
        for note_type, regexp in Config.config["Custom Regexps"].items():
            if regexp:
                self.search(note_type, regexp)
        # Finally, scan for deleting notes
        for match in RegexFile.EMPTY_REGEXP.finditer(self.file):
            self.notes_to_delete.append(
                int(match.group(1)[len(ID_PREFIX):])
            )

    def search(self, note_type, regexp):
        """
        Search the file for regex matches of this type,
        ignoring matches inside ignore_spans,
        and adding any matches to ignore_spans.
        """
        regexp_tags_id = re.compile(
            "".join(
                [
                    regexp,
                    RegexNote.TAG_REGEXP_STR,
                    RegexNote.ID_REGEXP_STR
                ]
            ), flags=re.MULTILINE
        )
        regexp_id = re.compile(
            regexp + RegexNote.ID_REGEXP_STR, flags=re.MULTILINE
        )
        regexp_tags = re.compile(
            regexp + RegexNote.TAG_REGEXP_STR, flags=re.MULTILINE
        )
        regexp = re.compile(
            regexp, flags=re.MULTILINE
        )
        for match in findignore(regexp_tags_id, self.file, self.ignore_spans):
            # This note has id, so we update it
            self.ignore_spans.append(match.span())
            self.notes_to_edit.append(
                RegexNote(match, note_type, tags=True, id=True).parse(
                    self.target_deck
                )
            )
        for match in findignore(regexp_id, self.file, self.ignore_spans):
            # This note has id, so we update it
            self.ignore_spans.append(match.span())
            self.notes_to_edit.append(
                RegexNote(match, note_type, tags=False, id=True).parse(
                    self.target_deck
                )
            )
        for match in findignore(regexp_tags, self.file, self.ignore_spans):
            # This note has no id, so we update it
            self.ignore_spans.append(match.span())
            parsed = RegexNote(match, note_type, tags=True, id=False).parse(
                self.target_deck
            )
            parsed.note["tags"] += self.global_tags.split(TAG_SEP)
            self.notes_to_add.append(
                parsed.note
            )
            self.id_indexes.append(match.end())
        for match in findignore(regexp, self.file, self.ignore_spans):
            # This note has no id, so we update it
            self.ignore_spans.append(match.span())
            parsed = RegexNote(match, note_type, tags=False, id=False).parse(
                self.target_deck
            )
            parsed.note["tags"] += self.global_tags.split(TAG_SEP)
            self.notes_to_add.append(
                parsed.note
            )
            self.id_indexes.append(match.end())

    def fix_newline_ids(self):
        """Removes double newline then ids from self.file."""
        double_regexp = re.compile(
            r"(\r\n|\r|\n){2}" + ID_PREFIX + r"\d+"
        )
        self.file = double_regexp.sub(
            lambda x: x.group()[1:],
            self.file
        )

    def write_ids(self):
        """Write the identifiers to self.file."""
        print("Writing new note IDs to file,", self.filename, "...")
        self.file = string_insert(
            self.file, zip(
                self.id_indexes, [
                    "\n" + ID_PREFIX + str(id) + "\n"
                    for id in self.note_ids
                    if id is not None
                ]
            )
        )
        self.fix_newline_ids()

    def remove_empties(self):
        """Remove empty notes from self.file."""
        self.file = RegexFile.EMPTY_REGEXP.sub(
            "", self.file
        )


if __name__ == "__main__":
    if not os.path.exists(CONFIG_PATH):
        Config.update_config()
    App()
