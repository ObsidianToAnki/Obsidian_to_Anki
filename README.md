# Obsidian_to_Anki
Script to add flashcards from a text or markdown file to Anki. Run from the command line. Built with [Obsidian](https://obsidian.md/) markdown syntax in mind. Supports **user-defined custom syntax for flashcards.**  
See the [Trello](https://trello.com/b/6MXEizGg/obsidiantoanki) for planned features.

## Getting started

Check out the [Wiki](https://github.com/Pseudonium/Obsidian_to_Anki/wiki)! It has a ton of information, including setup instructions for new users. I will include a copy of the instructions here:

### Setup
1. Install the latest version of [Python](https://www.python.org/downloads/).
2. Start up [Anki](https://apps.ankiweb.net/), and navigate to your desired profile.
3. Ensure that you've installed [AnkiConnect](https://github.com/FooSoft/anki-connect).
4. If you are a new user, download `obstoanki_setup.py` from the [releases page](https://github.com/Pseudonium/Obsidian_to_Anki/releases), and place it in the folder you want the script installed (for example your notes folder).  
5. Run `obstoanki_setup.py`, for example by double-clicking it in a file explorer. This will download the latest version of the script and required dependencies automatically. Existing users should be able to run their existing `obstoanki_setup.py` to get the latest version of the script.  
6. Check the Permissions tab below to ensure the script is able to run.
7. Run `obsidian_to_anki.py`, for example by double-clicking it in a file explorer. This will generate a config file, `obsidian_to_anki_config.ini`.

### Permissions
The script needs to be able to:
* Make a config file in the directory the script is installed.
* Read the file in the directory the script is used.
* Make a backup file in the directory the script is used.
* Rename files in the directory the script is used.
* Remove a backup file in the directory the script is used.
* Change the current working directory temporarily (so that local image paths are resolved correctly).

## Features

Current features:
* **[Custom note types](#note-formatting)** - You're not limited to the 6 built-in note types of Anki.
* **Updating notes from file** - Your text files are the canonical source of the notes.
* **[Tags](#tag-formatting)**, including **[tags for an entire file](#file-tag-formatting)**.
* **Adding to user-specified [decks](#deck-formatting),** on a *per-file* basis.
* **[Markdown formatting](#markdown-formatting)**, including **[math formatting](#math-formatting)**
* **[Embedded images](#image-formatting)**. GIFs should work too.
* **[Audio](#audio-formatting)**.
* **[Auto-deleting notes](#deleting-notes) from the file**.
* **Reading from all files in a directory automatically** - recursively too!
* **[Inline Notes](#inline-note-formatting)** - Shorter syntax for typing out notes on a single line.
* **[Easy cloze formatting](#cloze-formatting)** - A more compact syntax to do Cloze text
* **[Obsidian integration](#obsidian)** - Currently, this only includes a link to the file that made the flashcard, appended to the first field of your card.
* **[Custom syntax](regex.md)** - Using **regular expressions**, add custom syntax to generate **notes that make sense for you.** Some examples:
  * [RemNote single-line style](regex.md#remnote-single-line-style). `This is how to use::Remnote single-line style`  
  ![Remnote 1](Images/Remnote_1.png)
  * [Header paragraph style](regex.md#header-paragraph-style).
  <pre>
  # Style
  This style is suitable for having the header as the front, and the answer as the back
  </pre>  
  ![Header 1](Images/Header_1.png)
  * [Question answer style](regex.md#question-answer-style).
  <pre>
  Q: How do you use this style?
  A: Just like this.
  </pre>  
  ![Question 1](Images/Question_1.png)
  * [Neuracache #flashcard style](regex.md#neuracache-flashcard-style).  
  <pre>
  In Neuracache style, to make a flashcard you do #flashcard
  The next lines then become the back of the flashcard
  </pre>  
  ![Neuracache 1](Images/Neuracache_1.png)
  * [Ruled style](regex.md#ruled-style)  
  <pre>
  How do you use ruled style?
  ---
  You need at least three '-' between the front and back of the card.
  </pre>  
  ![Ruled 1](Images/Ruled_1.png)
  * [Markdown table style](regex.md#markdown-table-style)  
  <pre>
  | Why might this style be useful? |
  | ------ |
  | It looks nice when rendered as HTML in a markdown editor. |
  </pre>
  ![Table 2](Images/Table_2.png)
  * [Cloze paragraph style](regex.md#cloze-paragraph-style)  
  <pre>
  The idea of {cloze paragraph style} is to be able to recognise any paragraphs that contain {cloze deletions}.
  </pre>
  ![Cloze 1](Images/Cloze_1.png)

Note that **all custom syntax is off by default**, and must be programmed into the script via the config file - see [Custom syntax](regex.md) for instructions.
