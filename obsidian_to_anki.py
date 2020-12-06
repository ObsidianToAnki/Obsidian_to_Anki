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
import argparse
import html
import time
import socket
import subprocess
try:
    import gooey
    GOOEY = True
except ModuleNotFoundError:
    print("Gooey not installed, switching to cli...")
    GOOEY = False

MEDIA = dict()

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

DATA_PATH = os.path.expanduser(
    os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "obsidian_to_anki_data.json"
    )
)

md_parser = markdown.Markdown(
    extensions=[
        'fenced_code',
        'footnotes',
        'md_in_html',
        'tables',
        'nl2br',
        'sane_lists'
    ]
)

ANKI_PORT = 8765

ANKI_CLOZE_REGEXP = re.compile(r'{{c\d+::[\s\S]+?}}')


def has_clozes(text):
    """Checks whether text actually has cloze deletions."""
    return bool(ANKI_CLOZE_REGEXP.search(text))


def note_has_clozes(note):
    """Checks whether a note has cloze deletions in any of its fields."""
    return any(has_clozes(field) for field in note["fields"].values())


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


def contained_in(span, spans):
    """Return whether span is contained in spans (+- 1 leeway)"""
    return any(
        span[0] >= start - 1 and span[1] <= end + 1
        for start, end in spans
    )


def findignore(pattern, string, ignore_spans):
    """Yield all matches for pattern in string not in ignore_spans."""
    return (
        match
        for match in pattern.finditer(string)
        if not contained_in(match.span(), ignore_spans)
    )


def wait_for_port(port, host='localhost', timeout=5.0):
    """Wait until a port starts accepting TCP connections.
    Args:
        port (int): Port number.
        host (str): Host address on which the port should exist.
        timeout (float): In seconds. How long to wait before raising errors.
    Raises:
        TimeoutError: The port isn't accepting connection after time specified
        in `timeout`.
    """
    start_time = time.perf_counter()
    while True:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                break
        except OSError as ex:
            time.sleep(0.01)
            if time.perf_counter() - start_time >= timeout:
                raise TimeoutError(
                    'Waited too long for the port {} on host {} to'
                    'start accepting connections.'.format(port, host)
                ) from ex


def load_anki():
    """Attempt to load anki in the correct profile."""
    try:
        Config.load_config()
    except Exception as e:
        print("Error when loading config:", e)
        print("Please open Anki before running script again.")
        return False
    if CONFIG_DATA["Path"] and CONFIG_DATA["Profile"]:
        print("Anki Path and Anki Profile provided.")
        print("Attempting to open Anki in selected profile...")
        subprocess.Popen(
            [CONFIG_DATA["Path"], "-p", CONFIG_DATA["Profile"]]
        )
        try:
            wait_for_port(ANKI_PORT)
        except TimeoutError:
            print("Opened Anki, but can't connect! Is AnkiConnect working?")
            return False
        else:
            print("Opened and connected to Anki successfully!")
            return True
    else:
        print(
            "Must provide both Anki Path and Anki Profile",
            "in order to open Anki automatically"
        )


def main():
    """Main functionality of script."""
    if not os.path.exists(CONFIG_PATH):
        Config.update_config()
    App()


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

    OBS_CODE_REGEXP = re.compile(
        r"(?<!`)`(?=[^`])[\s\S]*?`"
    )
    OBS_DISPLAY_CODE_REGEXP = re.compile(
        r"```[\s\S]*?```"
    )

    ANKI_INLINE_START = r"\("
    ANKI_INLINE_END = r"\)"

    ANKI_DISPLAY_START = r"\["
    ANKI_DISPLAY_END = r"\]"

    ANKI_MATH_REGEXP = re.compile(r"(\\\[[\s\S]*?\\\])|(\\\([\s\S]*?\\\))")

    MATH_REPLACE = "OBSTOANKIMATH"

    IMAGE_REGEXP = re.compile(r'<img alt=".*?" src="(.*?)"')
    SOUND_REGEXP = re.compile(r'\[sound:(.+)\]')
    CLOZE_REGEXP = re.compile(
        r'(?:(?<!{){(?:c?(\d+)[:|])?(?!{))((?:[^\n][\n]?)+?)(?:(?<!})}(?!}))'
    )
    URL_REGEXP = re.compile(r'https?://')

    PARA_OPEN = "<p>"
    PARA_CLOSE = "</p>"

    CLOZE_UNSET_NUM = 1

    @staticmethod
    def format_note_with_url(note, url):
        for key in note["fields"]:
            note["fields"][key] += "<br>" + "".join([
                '<a',
                ' href="{}" class="obsidian-link">Obsidian</a>'.format(url)
            ])
            break  # So only does first field

    @staticmethod
    def format_note_with_frozen_fields(note, frozen_fields_dict):
        for field in note["fields"].keys():
            note["fields"][field] += frozen_fields_dict[
                note["modelName"]
            ][field]

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
    def cloze_repl(match):
        id, content = match.group(1), match.group(2)
        if id is None:
            result = "{{{{c{!s}::{}}}}}".format(
                FormatConverter.CLOZE_UNSET_NUM,
                content
            )
            FormatConverter.CLOZE_UNSET_NUM += 1
            return result
        else:
            return "{{{{c{}::{}}}}}".format(id, content)

    @staticmethod
    def curly_to_cloze(text):
        """Change text in curly brackets to Anki-formatted cloze."""
        text = FormatConverter.CLOZE_REGEXP.sub(
            FormatConverter.cloze_repl,
            text
        )
        FormatConverter.CLOZE_UNSET_NUM = 1
        return text

    @staticmethod
    def markdown_parse(text):
        """Apply markdown conversions to text."""
        text = md_parser.reset().convert(text)
        return text

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
            path = urllib.parse.unquote(path)
            filename = os.path.basename(path)
            if filename not in App.ADDED_MEDIA and filename not in MEDIA:
                MEDIA[filename] = file_encode(path)
                # Adds the filename and data to media_names

    @staticmethod
    def get_audio(html_text):
        """Get all the audio that needs to be added"""
        for match in FormatConverter.SOUND_REGEXP.finditer(html_text):
            path = match.group(1)
            filename = os.path.basename(path)
            if filename not in App.ADDED_MEDIA and filename not in MEDIA:
                MEDIA[filename] = file_encode(path)
                # Adds the filename and data to media_names

    @staticmethod
    def path_to_filename(matchobject):
        """Replace the src in matchobject appropriately."""
        found_string, found_path = matchobject.group(0), matchobject.group(1)
        if FormatConverter.is_url(found_path):
            return found_string  # So urls should not be altered.
        found_string = found_string.replace(
            found_path, os.path.basename(urllib.parse.unquote(found_path))
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
                html.escape(math_match),
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


class Note:
    """Manages parsing notes into a dictionary formatted for AnkiConnect.

    Input must be the note text.
    Does NOT deal with finding the note in the file.
    """

    ID_REGEXP = re.compile(
        r"(?:<!--)?" + ID_PREFIX + r"(\d+)"
    )

    def __init__(self, note_text):
        """Set up useful variables."""
        self.text = note_text
        self.lines = self.text.splitlines()
        self.current_field_num = 0
        self.delete = False
        if Note.ID_REGEXP.match(self.lines[-1]):
            self.identifier = int(
                Note.ID_REGEXP.match(self.lines.pop()).group(1)
            )
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
        self.note_type = self.lines[0]
        self.field_names = App.FIELDS_DICT[self.note_type]
        self.current_field = self.field_names[0]

    def field_from_line(self, line):
        """From a given line, determine the next field to add text into.

        Then, return the stripped line, and the field."""
        for field in self.field_names:
            if line.startswith(field + ":"):
                return (line[len(field + ":"):], field)
        return (line, self.current_field)

    @property
    def fields(self):
        """Get the fields of the note into a dictionary."""
        fields = {field: "" for field in self.field_names}
        for line in self.lines[1:]:
            line, self.current_field = self.field_from_line(line)
            fields[self.current_field] += line + "\n"
        fields = {
            key: FormatConverter.format(
                value.strip(),
                cloze=(
                    self.note_type in CONFIG_DATA["Clozes"]
                    and CONFIG_DATA["CurlyCloze"]
                )
            )
            for key, value in fields.items()
        }
        return {key: value.strip() for key, value in fields.items()}

    def parse(self, deck, url=None, frozen_fields_dict=None):
        """Get a properly formatted dictionary of the note."""
        template = NOTE_DICT_TEMPLATE.copy()
        if not self.delete:
            template["modelName"] = self.note_type
            template["fields"] = self.fields
            if all([
                CONFIG_DATA["Add file link"],
                CONFIG_DATA["Vault"],
                url
            ]):
                FormatConverter.format_note_with_url(template, url)
            if frozen_fields_dict:
                FormatConverter.format_note_with_frozen_fields(
                    template, frozen_fields_dict
                )
            template["tags"] = template["tags"] + self.tags
            template["deckName"] = deck
            return Note_and_id(note=template, id=self.identifier)
        else:
            return Note_and_id(note=False, id=self.identifier)


class InlineNote(Note):

    ID_REGEXP = re.compile(r"(?:<!--)?" + ID_PREFIX + r"(\d+)")
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
        self.note_type = TYPE.group(1)
        self.text = self.text[TYPE.end():]
        self.field_names = App.FIELDS_DICT[self.note_type]
        self.current_field = self.field_names[0]

    @property
    def fields(self):
        """Get the fields of the note into a dictionary."""
        fields = {field: "" for field in self.field_names}
        for word in self.text.split(" "):
            for field in self.field_names:
                if word == field + ":":
                    self.current_field = field
                    word = ""
            fields[self.current_field] += word + " "
        fields = {
            key: FormatConverter.format(
                value,
                cloze=(
                    self.note_type in CONFIG_DATA["Clozes"]
                    and CONFIG_DATA["CurlyCloze"]
                )
            )
            for key, value in fields.items()
        }
        return {key: value.strip() for key, value in fields.items()}


class RegexNote:
    ID_REGEXP_STR = r"\n(?:<!--)?(?:" + ID_PREFIX + r"(\d+).*)"
    TAG_REGEXP_STR = r"(" + TAG_PREFIX + r".*)"

    def __init__(self, matchobject, note_type, tags=False, id=False):
        self.match = matchobject
        self.note_type = note_type
        self.groups = list(self.match.groups())
        self.group_num = len(self.groups)
        if id:
            # This means id is last group
            self.identifier = int(self.groups.pop())
        else:
            self.identifier = None
        if tags:
            # Even if id were present, tags is now last group
            self.tags = self.groups.pop()[len(TAG_PREFIX):].split(
                TAG_SEP
            )
        else:
            self.tags = list()
        self.field_names = App.FIELDS_DICT[self.note_type]

    @property
    def fields(self):
        fields = dict.fromkeys(self.field_names, "")
        for name, match in zip(self.field_names, self.groups):
            if match:
                fields[name] = match
        fields = {
            key: FormatConverter.format(
                value,
                cloze=(
                    self.note_type in CONFIG_DATA["Clozes"]
                    and CONFIG_DATA["CurlyCloze"]
                )
            )
            for key, value in fields.items()
        }
        return {key: value.strip() for key, value in fields.items()}

    def parse(self, deck, url=None, frozen_fields_dict=None):
        """Get a properly formatted dictionary of the note."""
        template = NOTE_DICT_TEMPLATE.copy()
        template["modelName"] = self.note_type
        template["fields"] = self.fields
        if all([
            CONFIG_DATA["Add file link"],
            CONFIG_DATA["Vault"],
            url
        ]):
            FormatConverter.format_note_with_url(template, url)
        if frozen_fields_dict:
            FormatConverter.format_note_with_frozen_fields(
                template, frozen_fields_dict
            )
        template["tags"] = template["tags"] + self.tags
        template["deckName"] = deck
        if self.note_type in CONFIG_DATA["Clozes"] and CONFIG_DATA[
            "CurlyCloze"
        ] and not note_has_clozes(template):
            return 1  # Like an error code
        return Note_and_id(note=template, id=self.identifier)


class Config:
    """Deals with saving and loading the configuration file."""

    @staticmethod
    def setup_syntax(config):
        """Sets up default syntax in the config object."""
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
        config["Syntax"].setdefault(
            "Frozen Fields Line", "FROZEN"
        )

    @staticmethod
    def setup_defaults(config):
        """Sets up default values in the config file, not to do with syntax."""
        config.setdefault("Obsidian", dict())
        config["Obsidian"].setdefault("Vault name", "")
        config["Obsidian"].setdefault("Add file link", "False")
        config["DEFAULT"] = dict()  # Removes DEFAULT if it's there.
        config.setdefault("Defaults", dict())
        config["Defaults"].setdefault(
            "Tag", "Obsidian_to_Anki"
        )
        config["Defaults"].setdefault(
            "Deck", "Default"
        )
        config["Defaults"].setdefault(
            "CurlyCloze", "False"
        )
        config["Defaults"].setdefault(
            "GUI", "True"
        )
        config["Defaults"].setdefault(
            "Regex", "False"
        )
        config["Defaults"].setdefault(
            "ID Comments", "True"
        )
        config["Defaults"].setdefault(
            "Anki Path", ""
        )
        config["Defaults"].setdefault(
            "Anki Profile", ""
        )

    def update_config():
        """Update config with new notes."""
        print("Updating configuration file...")
        config = configparser.ConfigParser()
        config.optionxform = str
        if os.path.exists(CONFIG_PATH):
            print("Config file exists, reading...")
            config.read(CONFIG_PATH, encoding='utf-8-sig')
        note_types = AnkiConnect.invoke("modelNames")
        config.setdefault("Cloze Note Types", dict())
        config.setdefault("Custom Regexps", dict())
        for note in note_types:
            config["Cloze Note Types"].setdefault(note, "False")
            config["Custom Regexps"].setdefault(note, "")
            if note == "Cloze":
                config["Cloze Note Types"][note] = "True"
        Config.setup_syntax(config)
        Config.setup_defaults(config)
        with open(CONFIG_PATH, "w", encoding='utf_8') as configfile:
            config.write(configfile)
        print("Configuration file updated!")

    @staticmethod
    def load_syntax(config):
        """Reads and loads syntax from the config object."""
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
        RegexFile.EMPTY_REGEXP = re.compile(
            re.escape(
                config["Syntax"]["Delete Regex Note Line"]
            ) + RegexNote.ID_REGEXP_STR
        )
        CONFIG_DATA["FROZEN_LINE"] = re.escape(
            config["Syntax"]["Frozen Fields Line"]
        )

    @staticmethod
    def load_defaults(config):
        """Loads default values not to do with syntax from config object."""
        CONFIG_DATA["Clozes"] = [
            type for type in config["Cloze Note Types"]
            if config.getboolean("Cloze Note Types", type)
        ]
        NOTE_DICT_TEMPLATE["tags"] = [config["Defaults"]["Tag"]]
        NOTE_DICT_TEMPLATE["deckName"] = config["Defaults"]["Deck"]
        CONFIG_DATA["CurlyCloze"] = config.getboolean(
            "Defaults", "CurlyCloze"
        )
        CONFIG_DATA["GUI"] = config.getboolean(
            "Defaults", "GUI"
        )
        CONFIG_DATA["Regex"] = config.getboolean(
            "Defaults", "Regex"
        )
        CONFIG_DATA["Comment"] = config.getboolean(
            "Defaults", "ID Comments"
        )
        CONFIG_DATA["Path"] = config["Defaults"]["Anki Path"]
        CONFIG_DATA["Profile"] = config["Defaults"]["Anki Profile"]
        CONFIG_DATA["Vault"] = config["Obsidian"]["Vault name"]
        CONFIG_DATA["Add file link"] = config.getboolean(
            "Obsidian", "Add file link"
        )

    def load_config():
        """Load from an existing config file (assuming it exists)."""
        print("Loading configuration file...")
        config = configparser.ConfigParser()
        config.optionxform = str  # Allows for case sensitivity
        config.read(CONFIG_PATH, encoding='utf-8-sig')
        Config.load_syntax(config)
        Config.load_defaults(config)
        CONFIG_DATA["CUSTOM_REGEXPS"] = config["Custom Regexps"]
        print("Loaded successfully!")


class Data:
    """Class for managing the data file (not meant to be changed by users.)"""

    def create_data_file():
        """Creates the data file for the script."""
        print("Creating data file...")
        with open(DATA_PATH, "w") as f:
            json.dump(list(), f)

    def update_data_file(data):
        """Updates the data file for the script with the given data."""
        print("Updating data file...")
        with open(DATA_PATH, "w") as f:
            json.dump(data, f)

    def load_data_file():
        """Loads the data file into memory"""
        with open(DATA_PATH, "r") as f:
            data = json.load(f)
        App.ADDED_MEDIA = data


class App:
    """Master class that manages the application."""

    SUPPORTED_EXTS = [".md", ".txt"]

    def __init__(self):
        """Execute the main functionality of the script."""
        try:
            Config.load_config()
        except Exception as e:
            print("Error:", e)
            print("Attempting to fix config file...")
            Config.update_config()
            Config.load_config()
        try:
            Data.load_data_file()
        except Exception as e:
            print("Error:", e)
            Data.create_data_file()
            Data.load_data_file()
        self.get_fields()
        self.get_ids()
        if CONFIG_DATA["GUI"] and GOOEY:
            self.setup_gui_parser()
        else:
            self.setup_cli_parser()
        args = self.parser.parse_args()
        if CONFIG_DATA["GUI"] and GOOEY:
            if args.directory:
                args.path = args.directory
            elif args.file:
                args.path = args.file
            else:
                args.path = False
        no_args = True
        if args.update:
            no_args = False
            Config.update_config()
            Config.load_config()
        if args.mediaupdate:
            no_args = False
            Data.create_data_file()
        self.gen_regexp()
        if args.config:
            no_args = False
            webbrowser.open(CONFIG_PATH)
            return
        if args.path:
            no_args = False
            current = os.getcwd()
            self.path = args.path
            directories = list()
            if os.path.isdir(self.path):
                os.chdir(self.path)
                if args.recurse:
                    directories = list()
                    for root, dirs, files in os.walk(os.getcwd()):
                        directories.append(
                            Directory(root, regex=args.regex)
                        )
                        for dir in dirs:
                            if dir.startswith("."):
                                dirs.remove(dir)
                                # So, ignore . folders
                else:
                    directories = [
                        Directory(
                            os.getcwd(), regex=args.regex
                        )
                    ]
                os.chdir(current)
            else:
                # Still need to get to directory of file for image resolving
                # So, go to directory where file is (hopefully)
                # But, if just file name is given (e.g. cli), don't want to
                # Break anything.
                if os.path.dirname(self.path):
                    file_dir = os.path.dirname(self.path)
                else:
                    file_dir = current
                directories = [
                    Directory(
                        file_dir, regex=args.regex, onefile=self.path
                    )
                ]
            requests = list()
            print("Getting tag list")
            requests.append(
                AnkiConnect.request(
                    "getTags"
                )
            )
            print("Adding media with these filenames...")
            print(list(MEDIA.keys()))
            requests.append(self.get_add_media())
            print("Adding directory requests...")
            for directory in directories:
                requests.append(directory.requests_1())
            result = AnkiConnect.invoke(
                "multi",
                actions=requests
            )
            App.ADDED_MEDIA = set(App.ADDED_MEDIA)
            App.ADDED_MEDIA.update(MEDIA.keys())
            App.ADDED_MEDIA = list(App.ADDED_MEDIA)
            Data.update_data_file(App.ADDED_MEDIA)
            tags = AnkiConnect.parse(result[0])
            directory_responses = result[2:]
            for directory, response in zip(directories, directory_responses):
                directory.parse_requests_1(AnkiConnect.parse(response), tags)
            requests = list()
            for directory in directories:
                requests.append(directory.requests_2())
            AnkiConnect.invoke(
                "multi",
                actions=requests
            )
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
            help="Use custom regex syntax.",
            default=CONFIG_DATA["Regex"]
        )
        self.parser.add_argument(
            "-m", "--mediaupdate",
            action="store_true",
            dest="mediaupdate",
            help="Force addition of media files."
        )
        self.parser.add_argument(
            "-R", "--recurse",
            action="store_true",
            dest="recurse",
            help="Recursively scan subfolders."
        )

    if GOOEY:
        @ gooey.Gooey(use_cmd_args=True)
        def setup_gui_parser(self):
            """Set up the GUI argument parser."""
            self.parser = gooey.GooeyParser(
                description="Add cards to Anki from a markdown or text file."
            )
            path_group = self.parser.add_mutually_exclusive_group(
                required=False
            )
            path_group.add_argument(
                "-f", "--file",
                help="Choose a file to scan.",
                dest="file",
                widget='FileChooser'
            )
            path_group.add_argument(
                "-d", "--dir",
                help="Choose a directory to scan.",
                dest="directory",
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
                        r"(?:\n|: )(.*)",
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
                        r"\n(?:<!--)?",
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
                r"^" + CONFIG_DATA["TAG_LINE"] + r"(?:\n|: )(.*)",
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
                        r"\s+(?:<!--)?" + ID_PREFIX + r".*?",
                        CONFIG_DATA["INLINE_SUFFIX"]
                    ]
                )
            )
        )
        setattr(
            App, "VAULT_PATH_REGEXP",
            re.compile(
                CONFIG_DATA["Vault"] + r".*"
            )
        )
        setattr(
            App, "FROZEN_REGEXP",
            re.compile(
                CONFIG_DATA["FROZEN_LINE"] + r" - (.*?):\n((?:[^\n][\n]?)+)"
            )
        )

    def get_add_media(self):
        """Get the AnkiConnect-formatted add_media request."""
        return AnkiConnect.request(
            "multi",
            actions=[
                AnkiConnect.request(
                    "storeMediaFile",
                    filename=key,
                    data=value
                )
                for key, value in MEDIA.items()
            ]
        )

    def get_fields(self):
        """Get the user's current note types and fields."""
        note_types = AnkiConnect.invoke("modelNames")
        fields_request = [
            AnkiConnect.request(
                "modelFieldNames", modelName=note
            )
            for note in note_types
        ]
        result = AnkiConnect.invoke(
            "multi", actions=fields_request
        )
        setattr(
            App, "FIELDS_DICT",
            {
                note_type: AnkiConnect.parse(fields)
                for note_type, fields in zip(
                    note_types,
                    result
                )
            }
        )

    def get_ids(self):
        """Get a list of the currently used card IDs."""
        setattr(App, "EXISTING_IDS", AnkiConnect.invoke("findNotes", query=""))


class File:
    """Class for performing script operations at the file-level."""

    def __init__(self, filepath):
        """Perform initial file reading and attribute setting."""
        self.filename = filepath
        self.path = os.path.abspath(filepath)
        if CONFIG_DATA["Vault"] and App.VAULT_PATH_REGEXP.search(self.path):
            self.url = "obsidian://vault/{}".format(
                App.VAULT_PATH_REGEXP.search(self.path).group()
            ).replace("\\", "/")
        else:
            self.url = ""
        with open(self.filename, encoding='utf_8') as f:
            self.file = f.read()
            self.original_file = self.file
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
        self.setup_frozen_fields_dict()

    def setup_frozen_fields_dict(self):
        self.frozen_fields_dict = {
            note_type: dict.fromkeys(fields, "")
            for note_type, fields in App.FIELDS_DICT.items()
        }
        for match in App.FROZEN_REGEXP.finditer(self.file):
            note_type, fields = match.group(1), match.group(2)
            virtual_note = note_type + "\n" + fields
            parsed_fields = Note(virtual_note).fields
            self.frozen_fields_dict[note_type] = parsed_fields

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
            parsed = Note(note).parse(
                self.target_deck,
                url=self.url,
                frozen_fields_dict=self.frozen_fields_dict
            )
            if parsed.id is None:
                # Need to make sure global_tags get added.
                parsed.note["tags"] += self.global_tags.split(TAG_SEP)
                self.notes_to_add.append(parsed.note)
                self.id_indexes.append(position)
            elif not parsed.note:
                # This indicates a delete action
                self.notes_to_delete.append(parsed.id)
            elif parsed.id not in App.EXISTING_IDS:
                print(
                    "Warning! Note with id ",
                    parsed.id,
                    " in file ",
                    self.filename,
                    " does not exist in Anki!"
                )
            else:
                self.notes_to_edit.append(parsed)
        for inline_note_match in App.INLINE_REGEXP.finditer(self.file):
            note = inline_note_match.group(1)
            position = inline_note_match.end(1)
            parsed = InlineNote(note).parse(
                self.target_deck,
                url=self.url,
                frozen_fields_dict=self.frozen_fields_dict
            )
            if parsed.id is None:
                # Need to make sure global_tags get added.
                parsed.note["tags"] += self.global_tags.split(TAG_SEP)
                self.inline_notes_to_add.append(parsed.note)
                self.inline_id_indexes.append(position)
            elif not parsed.note:
                # This indicates a delete action
                self.notes_to_delete.append(parsed.id)
            elif parsed.id not in App.EXISTING_IDS:
                print(
                    "Warning! Note with id ",
                    parsed.id,
                    " in file ",
                    self.filename,
                    " does not exist in Anki!"
                )
            else:
                self.notes_to_edit.append(parsed)

    @ staticmethod
    def id_to_str(id, inline=False, comment=False):
        """Get the string repr of id."""
        result = ID_PREFIX + str(id)
        if comment:
            result = "<!--" + result + "-->"
        if inline:
            result += " "
        else:
            result += "\n"
        return result

    def write_ids(self):
        """Write the identifiers to self.file."""
        print("Writing new note IDs to file,", self.filename, "...")
        self.file = string_insert(
            self.file, list(
                zip(
                    self.id_indexes, [
                        self.id_to_str(id, comment=CONFIG_DATA["Comment"])
                        for id in self.note_ids[:len(self.notes_to_add)]
                        if id is not None
                    ]
                )
            ) + list(
                zip(
                    self.inline_id_indexes, [
                        self.id_to_str(
                            id, inline=True,
                            comment=CONFIG_DATA["Comment"]
                        )
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
        if self.file != self.original_file:
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

    def add_spans_to_ignore(self):
        """Mark sections of the file as places not to expect a note."""
        self.ignore_spans += spans(App.NOTE_REGEXP, self.file)
        self.ignore_spans += spans(App.INLINE_REGEXP, self.file)
        self.ignore_spans += spans(
            FormatConverter.OBS_INLINE_MATH_REGEXP, self.file
        )
        self.ignore_spans += spans(
            FormatConverter.OBS_DISPLAY_MATH_REGEXP, self.file
        )
        self.ignore_spans += spans(
            FormatConverter.OBS_CODE_REGEXP, self.file
        )
        self.ignore_spans += spans(
            FormatConverter.OBS_DISPLAY_CODE_REGEXP, self.file
        )

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
        self.add_spans_to_ignore()
        for note_type, regexp in CONFIG_DATA["CUSTOM_REGEXPS"].items():
            if regexp:
                self.search(note_type, regexp)
        # Finally, scan for deleting notes
        for match in RegexFile.EMPTY_REGEXP.finditer(self.file):
            self.notes_to_delete.append(
                int(match.group(1))
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
            parsed = RegexNote(match, note_type, tags=True, id=True).parse(
                self.target_deck,
                url=self.url,
                frozen_fields_dict=self.frozen_fields_dict
            )
            if parsed.id not in App.EXISTING_IDS:
                print(
                    "Warning! Note with id ",
                    parsed.id,
                    " in file ",
                    self.filename,
                    " does not exist in Anki!"
                )
            else:
                self.notes_to_edit.append(parsed)
        for match in findignore(regexp_id, self.file, self.ignore_spans):
            # This note has id, so we update it
            self.ignore_spans.append(match.span())
            parsed = RegexNote(match, note_type, tags=False, id=True).parse(
                self.target_deck,
                url=self.url,
                frozen_fields_dict=self.frozen_fields_dict
            )
            if parsed.id not in App.EXISTING_IDS:
                print(
                    "Warning! Note with id ",
                    parsed.id,
                    " in file ",
                    self.filename,
                    " does not exist in Anki!"
                )
            else:
                self.notes_to_edit.append(parsed)
        for match in findignore(regexp_tags, self.file, self.ignore_spans):
            # This note has no id, so we add it
            self.ignore_spans.append(match.span())
            parsed = RegexNote(match, note_type, tags=True, id=False).parse(
                self.target_deck,
                url=self.url,
                frozen_fields_dict=self.frozen_fields_dict
            )
            if parsed == 1:
                # Error code
                continue
            parsed.note["tags"] += self.global_tags.split(TAG_SEP)
            self.notes_to_add.append(
                parsed.note
            )
            self.id_indexes.append(match.end())
        for match in findignore(regexp, self.file, self.ignore_spans):
            # This note has no id, so we update it
            self.ignore_spans.append(match.span())
            parsed = RegexNote(match, note_type, tags=False, id=False).parse(
                self.target_deck,
                url=self.url,
                frozen_fields_dict=self.frozen_fields_dict
            )
            if parsed == 1:
                # Error code
                continue
            parsed.note["tags"] += self.global_tags.split(TAG_SEP)
            self.notes_to_add.append(
                parsed.note
            )
            self.id_indexes.append(match.end())

    def fix_newline_ids(self):
        """Removes double newline then ids from self.file."""
        double_regexp = re.compile(
            r"(\r\n|\r|\n){2}(?:<!--)?" + ID_PREFIX + r"\d+"
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
                    "\n" + File.id_to_str(id, comment=CONFIG_DATA["Comment"])
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


class Directory:
    """Class for managing a directory of files at a time."""

    def __init__(self, abspath, regex=False, onefile=None):
        """Scan directory for files."""
        self.path = abspath
        self.parent = os.getcwd()
        if regex:
            self.file_class = RegexFile
        else:
            self.file_class = File
        os.chdir(self.path)
        if onefile:
            # Hence, just one file to do
            self.files = [self.file_class(onefile)]
        else:
            with os.scandir() as it:
                self.files = sorted(
                    [
                        self.file_class(entry.path)
                        for entry in it
                        if entry.is_file() and os.path.splitext(
                            entry.path
                        )[1] in App.SUPPORTED_EXTS
                    ], key=lambda file: [
                        int(part) if part.isdigit() else part.lower()
                        for part in re.split(r'(\d+)', file.filename)]
                )
        for file in self.files:
            file.scan_file()
        os.chdir(self.parent)

    def requests_1(self):
        """Get the 1st HTTP request for this directory."""
        print("Forming request 1 for directory", self.path)
        requests = list()
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
        return AnkiConnect.request(
            "multi",
            actions=requests
        )

    def parse_requests_1(self, requests_1_response, tags):
        response = requests_1_response
        notes_ids = AnkiConnect.parse(response[0])
        cards_ids = AnkiConnect.parse(response[2])
        for note_ids, file in zip(notes_ids, self.files):
            file.note_ids = AnkiConnect.parse(note_ids)
        for card_ids, file in zip(cards_ids, self.files):
            file.card_ids = AnkiConnect.parse(card_ids)
        for file in self.files:
            file.tags = tags
        os.chdir(self.path)
        for file in self.files:
            file.get_cards()
            file.write_ids()
            print("Removing empty notes for file", file.filename)
            file.remove_empties()
            file.write_file()
        os.chdir(self.parent)

    def requests_2(self):
        """Get 2nd big request."""
        print("Forming request 2 for directory", self.path)
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
        return AnkiConnect.request(
            "multi",
            actions=requests
        )


if __name__ == "__main__":
    print("Attempting to connect to Anki...")
    try:
        wait_for_port(ANKI_PORT)
    except TimeoutError:
        print("Couldn't connect to Anki, attempting to open Anki...")
        if load_anki():
            main()
    else:
        print("Connected!")
        main()
