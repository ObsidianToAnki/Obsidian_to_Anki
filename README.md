# Obsidian_to_Anki
Script to add flashcards from a text or markdown file to Anki. Run from the command line. Built with [Obsidian](https://obsidian.md/) markdown syntax in mind. Supports **user-defined custom syntax for flashcards.**  
See the [Trello](https://trello.com/b/6MXEizGg/obsidiantoanki) for planned features.

Now an Obsidian plugin!

## Getting started

Check out the [Wiki](https://github.com/Pseudonium/Obsidian_to_Anki/wiki)! It has a ton of information, including setup instructions for new users. I will include a copy of the instructions here:

## Setup

### All users
1. Install the latest version of [Python](https://www.python.org/downloads/).
2. Start up [Anki](https://apps.ankiweb.net/), and navigate to your desired profile.
3. Ensure that you've installed [AnkiConnect](https://github.com/FooSoft/anki-connect).

### Obsidian plugin users
4. Have [Obsidian](https://obsidian.md/) downloaded
5. Search the 'Community plugins' list for this plugin
6. Install the plugin.
7. In Anki, navigate to Tools->Addons->AnkiConnect->Config, and change it to look like this: ![AnkiConnect_Config](Images/AnkiConnect_ConfigREAL.png)
8. With Anki running in the background, load the plugin. This will generate the plugin settings.

You shouldn't need Anki running to load Obsidian in the future, though of course you will need it for using the plugin!

### Python script users
4. If you are a new user, download `obstoanki_setup.py` from the [releases page](https://github.com/Pseudonium/Obsidian_to_Anki/releases), and place it in the folder you want the script installed (for example your notes folder).  
5. Run `obstoanki_setup.py`, for example by double-clicking it in a file explorer. This will download the latest version of the script and required dependencies automatically. Existing users should be able to run their existing `obstoanki_setup.py` to get the latest version of the script.  
6. Check the Permissions tab below to ensure the script is able to run.
7. Run `obsidian_to_anki.py`, for example by double-clicking it in a file explorer. This will generate a config file, `obsidian_to_anki_config.ini`.

#### Permissions
The script needs to be able to:
* Make a config file in the directory the script is installed.
* Read the file in the directory the script is used.
* Make a backup file in the directory the script is used.
* Rename files in the directory the script is used.
* Remove a backup file in the directory the script is used.
* Change the current working directory temporarily (so that local image paths are resolved correctly).

## Features

Current features (check out the wiki for more details):
* **Custom note types** - You're not limited to the 6 built-in note types of Anki.
* **Updating notes from file** - Your text files are the canonical source of the notes.
* **Tags**, including **tags for an entire file**.
* **Adding to user-specified deck** on a *per-file* basis.
* **Markdown formatting**.
* **Math formatting**.
* **Embedded images**. GIFs should work too.
* **Audio**.
* **Auto-deleting notes from the file**.
* **Reading from all files in a directory automatically** - recursively too!
* **Inline Notes** - Shorter syntax for typing out notes on a single line.
* **Easy cloze formatting** - A more compact syntax to do Cloze text
* **Frozen Fields**
* **Obsidian integration** - A link to the file that made the flashcard, full link and image embed support.
* **Custom syntax** - Using **regular expressions**, add custom syntax to generate **notes that make sense for you.** Some examples:
  * RemNote single-line style. `This is how to use::Remnote single-line style`  
  ![Remnote 1](Images/Remnote_1.png)
  * Header paragraph style.
  <pre>
  # Style
  This style is suitable for having the header as the front, and the answer as the back
  </pre>  
  ![Header 1](Images/Header_1.png)
  * Question answer style.
  <pre>
  Q: How do you use this style?
  A: Just like this.
  </pre>  
  ![Question 1](Images/Question_1.png)
  * Neuracache #flashcard style.  
  <pre>
  In Neuracache style, to make a flashcard you do #flashcard
  The next lines then become the back of the flashcard
  </pre>  
  ![Neuracache 1](Images/Neuracache_1.png)
  * Ruled style  
  <pre>
  How do you use ruled style?
  ---
  You need at least three '-' between the front and back of the card.
  </pre>  
  ![Ruled 1](Images/Ruled_1.png)
  * Markdown table style  
  <pre>
  | Why might this style be useful? |
  | ------ |
  | It looks nice when rendered as HTML in a markdown editor. |
  </pre>
  ![Table 2](Images/Table_2.png)
  * Cloze paragraph style  
  <pre>
  The idea of {cloze paragraph style} is to be able to recognise any paragraphs that contain {cloze deletions}.
  </pre>
  ![Cloze 1](Images/Cloze_1.png)

Note that **all custom syntax is off by default**, and must be programmed into the script via the config file - see the Wiki for more details.
