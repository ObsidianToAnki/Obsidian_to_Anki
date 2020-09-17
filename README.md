# Obsidian_to_Anki
Script to add flashcards from a text or markdown file to Anki. Run from the command line. Built with [Obsidian](https://obsidian.md/) markdown syntax in mind. Supports **user-defined custom syntax for flashcards.**

## Features

Current features:
* **[Custom note types](#note-formatting)** - You're not limited to the 6 built-in note types of Anki.
* **Updating notes from file** - Your text files are the canonical source of the notes.
* **Substitutions** - see [Config](#config). Makes typing out long names easier.
* **[Tags](#tag-formatting)**, including **[tags for an entire file](#file-tag-formatting)**.
* **Adding to user-specified [decks](#deck-formatting),** on a *per-file* basis.
* **[Markdown formatting](#markdown-formatting)**, including **[math formatting](#math-formatting)**
* **[Embedded images](#image-formatting)**. GIFs should work too.
* **[Audio](#audio-formatting)**.
* **[Auto-deleting notes](#deleting-notes) from the file**.
* **Reading from all files in a directory automatically** - not recursively however.
* **[Inline Notes](#inline-note-formatting)** - Shorter syntax for typing out notes on a single line.
* **[Easy cloze formatting](#cloze-formatting)** - A more compact syntax to do Cloze text
* **[Custom syntax](regex.md)** - Using regular expressions, add custom syntax to generate **notes that make sense for you.**

## Who is this for?

It might be useful to show the motivation for me personally writing the script in the first place.  
My workflow is essentially to have notes *be* flashcards - [one of my notes](https://www.evernote.com/shard/s522/sh/672b696d-4944-4894-a641-c84529d9ce9b/230b93561681475726fa1e2188becf78) (before I discovered Obsidian). However, it got tedious to keep copy-pasting cards into Anki, so I got the idea to write a script to do it automatically.

However, you don't need to have your notes be files of flashcards to use this script! You just need to be fine with visibly embedding flashcards in your notes, and keeping them there for future reference/editing. The script will ignore anything it doesn't think is a flashcard, so you're free to add context/information not needed for Anki to your notes.

## Setup
1. Install the latest version of [Python](https://www.python.org/downloads/).
2. Start up [Anki](https://apps.ankiweb.net/), and navigate to your desired profile.
3. Ensure that you've installed [AnkiConnect](https://github.com/FooSoft/anki-connect).
4. If you are a new user, download `obstoanki_setup.py`, and place it in the folder you want the script installed (for example your notes folder).  
5. Run `obstoanki_setup.py`, for example by double-clicking it in a file explorer. This will download the latest version of the script and required dependencies automatically. Existing users should be able to run their existing `obstoanki_setup.py` to get the latest version of the script.  
6. Check the Permissions tab below to ensure the script is able to run.
7. Run `obsidian_to_anki.py`, for example by double-clicking it in a file explorer. This will generate a config file, `obsidian_to_anki_config.ini`.

See [Troubleshooting](#Troubleshooting) if you have problems.


## Permissions
The script needs to be able to:
* Make a config file in the directory the script is installed.
* Read the file in the directory the script is used.
* Make a backup file in the directory the script is used.
* Rename files in the directory the script is used.
* Remove a backup file in the directory the script is used.
* Change the current working directory temporarily (so that local image paths are resolved correctly).


## Usage

**Apart from editing the config file, all operations of the script require Anki to be running.**

The GUI of the script looks like this:  
![GUI](Images/GUI.png)

Hopefully the options and path are self-explanatory.  
Note that you can run the script over the same file twice perfectly fine - it won't add duplicate cards. 

### Command line usage
If you set 'GUI' in the config file to False, the script is then run from the command line:
* Use `-h` to see help.
* Run the script as `obsidian_to_anki.py [path]`, where `[path]` is the path to the file or folder you wish to add notes from.
* Use `-c` to open up the config file for editing (not guaranteed to work on all operating systems, if it doesn't you'll have to find and edit it manually).
* Use `-u` to update the config file. Do this when you add new note types to Anki.
* Use `-m` to force the script to add all media files detected, instead of lazy addition of media files. Useful if you've e.g. resized the image, and want the changes to be reflected in Anki.
* Use `-r` to use custom regex syntax, ignoring the default syntax of the script.

## New users

If you are a **new user**, these steps are recommended:
1. Check [Custom syntax](regex.md) to see if there is a template that works for you.
2. Then, check the information on the following topics:
 * **Adding to user-specified [decks](#deck-formatting),** on a *per-file* basis.
 * **[Markdown formatting](#markdown-formatting)**, including **[math formatting](#math-formatting)**
 * **[Embedded images](#image-formatting)**. GIFs should work too.
 * **[Auto-deleting notes](#deleting-notes) from the file**.
 * **[File tag formatting](#file-tag-formatting)**.
 * **[Easy cloze formatting](#cloze-formatting)** - A more compact syntax to do Cloze text
 * [Defaults](#default).
3. You should be good to go simply running the script with the 'Regex' option checked.

The sections below describe the default syntax of the script (with the 'Regex' option not checked).

## Config

### DEFAULT section
Allows you to change the default deck and tag of the script.  
New in v2.2.2 - allows you to enable/disable the 'CurlyCloze' option, which is explained in [Cloze formatting](#cloze-formatting)  
New in v2.4.0 - allows you to enable/disable the GUI of the script - see [Command line usage](#command-line-usage).  

### Syntax
Note that START, END, TARGET DECK, FILE TAGS and DELETE all require an **exact match** on the line - you cannot have spaces afterwards.
As of v1.2, the Config file now allows you to change the syntax of the script:
* Begin Note - The string that signals the start of a [note](#note-formatting). Defaults to START.
* End Note - The string that signals the end of a note. Defaults to END.
* Begin Inline Note - The string that signals the start of an [inline note](#inline-note-formatting). Defaults to STARTI (Start-Inline).
* End Inline Note - The string that signals the end of an inline note. Defaults to ENDI (End-Inline).
* Target Deck Line - The string that signals "the line beneath me is the name of the target deck". Defaults to TARGET DECK.
* File Tags Line - The string that signals "the line beneath me is the set of tags that should be added to all notes from this file". Defaults to FILE TAGS.
* Delete Regex Note Line - The string that signals "the line beneath me is an id string for a regex note that should be deleted." Defaults to DELETE.

### Field substitutions
The substitutions for field prefixes. For example, under the section ['Basic'], you'll see something like this:
<pre>
Front = Front:
Back = Back:
</pre>
If you edit and save this to say
<pre>
Front = Front:
Back = A:
</pre>
Then you now format your notes like this:
<pre>
START
Basic
This is a test.
A: Test successful!
END
</pre>
As an inline note:
<pre>
STARTI [Basic] This is a test. A: Test successful! ENDI
</pre>

### Note Type Substitutions
These are under the section ['Note Substitutions']. Similar to the above, you'll see something like this:
<pre>
...
Basic = Basic
Basic (and reversed card) = Basic (and reversed card)
...
</pre>
If you edit and save this to say  
<pre>
...
Basic = B
Basic (and reversed card) = Basic (and reversed card)
...
</pre>
Then you now format your notes like this:  
<pre>
START
B
This is a test.
Back: Test successful!
END
</pre>
As an inline note:
<pre>
STARTI [B] This is a test. Back: Test successful! ENDI
</pre>

### Added Media
This section is reserved for the script to keep track of what media files it has added. You can clear this by running the script with the `-m` flag.

## Deck formatting
Anywhere within the file, format the deck that you want the notes to go into as follows:
<pre>
{Target Deck Line}
{Deck name}
</pre>
For example, with the default settings:
<pre>
TARGET DECK
Mathematics
</pre>
You may place more than one target deck in the same file, but only the first instance will be read and used.

## Note formatting

In the markdown file, you must format your 'block' notes as follows (see [Inline notes](#inline-note-formatting) for notes on a single line):
<pre>
START
{Note Type}
{Note Fields}
Tags:
END
</pre>
### Markdown formatting

Standard markdown formatting is supported.
You can check [test.md](./test.md) as an example.
Card produced:
![front](/Images/Markdown_1.png)
![back](/Images/Markdown_2.png)

### Math formatting
Supports both inline mode and displayed mode:
<pre>
Inline $x = 5$
</pre>
<pre>
Displayed $$z = 10$$
</pre>

### Image formatting

Embedded images are supported if they are embedded using the standard markdown syntax: `![alt-text](path_to_image)`

v2.3 - Web-hosted images are now supported! Do `![alt-text](image_url)`. You'll want to do 'copy image address' on the image, and use that for the image url.

### Audio formatting

Embedded audio is supported if the following criteria are met:
1. The audio file is stored locally
2. It is embedded using the syntax `[sound:{path_to_file}]`. So, for example, if the filename was `record.wav` and it was in a `Media` folder, you'd write `[sound:Media/record.wav]`

### Tag formatting

For reference, the note formatting style is:

<pre>
START
{Note Type}
{Note Fields}
Tags:
END
</pre>
Note that the Tags: line is optional - if you don't want tags, you may leave out the line.

Tags should be formatted as such:
<pre>
Tags: Tag1 Tag2 Tag3
</pre>
So, **a space between the colon and the first tag**, and a space between tags.

Hence, this syntax **would not work**:
<pre>
Tags:Tag1 Tag2 Tag3
</pre>

### File tag formatting

v1.1.1 now allows you to specify 'file tags' for a file - these tags will be added to every card in the file.

To do this:
Anywhere within the file, format the file tags as follows:
<pre>
{File Tags Line}
{Tag list}
</pre>
For example, with the default settings:
<pre>
FILE TAGS
Maths School Physics
</pre>
Like with tag-line formatting, you need a space between tags - however, do not include the "Tags: " prefix.

### Field formatting

Apart from the first field, each field must have a prefix to indicate to the program when to move on to the next field. For example:

<pre>
START
Basic
This is a test.
Back: Test successful!
END
</pre>
Note that you must start new fields on a new line for non-inline notes.  
When the script successfully adds a note, it will append an ID to the Note Data. This allows you to *update existing notes by running the script again*.

Example output:
<pre>
START
Basic
This is a test.
Back: Test successful!
ID: 1566052191670
END
</pre>
### Deleting notes

The script can delete notes that *it has added* automatically. To do this:
1. Find the formatted note in your file:
<pre>
START
{Note Type}
{Note Data}
ID: {Identifier}
END
</pre>
2. Change this to read:
<pre>
START
ID: {Identifier}
END
</pre>
3. If you run the script on the file, it will interpret this as "delete the note with ID {identifier}". For convenience, it will also delete the unnecessary `START END` block from the file.

See [Deleting inline notes](#deleting-inline-notes) for how to do this with inline notes.

## Inline note formatting
*v1.2 feature*
v1.2 of the script introduces **inline notes** - notes which are entirely on a single line. They are formatted as such:  
<pre>
STARTI [{Note Type}] {Note Data} ENDI
</pre>
For example  
<pre>
STARTI [Basic] This is a test. Back: Test successful! ENDI  
</pre>
Unlike regular 'block' notes, you can put inline notes anywhere on a line - for example, you could have a bulletpointed list of inline notes.  
Also, unlike regular 'block' notes, the script identifies the note type through the string in square brackets. Hence, **note types with [ or ] in the name are not supported for inline notes.**

### Deleting inline notes

The instructions are quite similar to deleting normal notes:
1. Find the formatted note in your file:
<pre>
STARTI [{Note Type}] {Note Data} ID: {Identifier} ENDI
</pre>
2. Change this to read:
<pre>
STARTI ID: {Identifier} ENDI
</pre>
3. If you run the script on the file, it will interpret this as "delete the note with ID {identifier}". For convenience, it will also delete the unnecessary `STARTI ENDI` block from the file.

### Cloze formatting

New in v2.2.2  
In any note, you can do clozes using Anki's standard syntax:  
`This is a {{c1::cloze note}}`  
However, by enabling the 'CurlyCloze' option (see [Config](#config)), you can write the above as:  
`This is a {cloze note}`  
It'll pick up multiple clozes accordingly:  
`This is a {cloze note} with {multiple clozes}`  
Gets translated to:  
`This is a {{c1::cloze note}} with {{c2::multiple clozes}}`  
However, simultaneous clozes are NOT supported when using this syntax.  
Also, you cannot use Anki's regular syntax for clozes if the 'CurlyCloze' option is enabled.

## Default
By default, the script:
- Adds notes with the DEFAULT Tag in the config file (+ other specified tags, if applicable).  
- Adds to the DEFAULT Deck in the config file (if `{Target Deck Line}` is not specified).  
- Adds to the current profile in Anki.  

## Troubleshooting

If the script itself is not able to run, try running `python3 {PATH_TO_SCRIPT}`.

If you are unable to get `pip` to run, see this [user guide](https://pip.pypa.io/en/stable/user_guide/).

If you are getting a `KeyError`, you may have typed one of the [substitutions](#Config) wrong - double check the config file and what you actually wrote.
Examples:
* Anki actually stores "Basic (and reversed)" as "Basic (and reversed card)" - hence, without changing the config file, formatting "Basic (and reversed)" for the note type will throw a `KeyError`

The script seems to have unexpected behaviour when reading from a file for the first time, while the file is open in another program (though this doesn't always happen!).  
The script was written in Python 3.8.5, and it uses `os` module features from Python 3.6+ [This issue](https://github.com/Pseudonium/Obsidian_to_Anki/issues/6#issue-690905446) confirms that the script does not run on Python 2.

## Technical
The script doesn't need to be in the same folder as your notes - you can put it in a Scripts folder if you have the means to run it remotely. Just ensure that the config file ends up in the same folder as the script.

You may also want to prepend the following shebang to the start of the file:

`#!/usr/bin/env python`

For more information, see [this pull request](https://github.com/Pseudonium/Obsidian_to_Anki/pull/13).
