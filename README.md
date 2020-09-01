# Obsidian_to_Anki
Script to add flashcards from an Obsidian markdown file to Anki.

## Setup
1. Install [Python](https://www.python.org/downloads/)
2. Download the desired release.
3. Place the script "obsidian_to_anki.py" in a convenient folder. You may wish to consider placing it in a Scripts folder, and adding the folder to your PATH
4. Start up Anki, and navigate to your desired profile
5. Ensure that you've installed [AnkiConnect](https://github.com/FooSoft/anki-connect).
6. From the command line, run the script once with no arguments - `{Path to script}/obsidian_to_anki.py`
This will make a configuration file in the same directory as the script, "obsidian_to_anki_config.ini".

## Permissions
The script needs to be able to:
* Make a config file in the directory the script is installed
* Read the file in the directory the script is used
* Make a backup file in the directory the script is used
* Rename files in the directory the script is used

## Usage
For simple documentation, run the script with the `-h` flag.

To edit the config file, run `obsidian_to_anki.py -c`. This will attempt to open the config file for editing, but isn't guaranteed to work. If it doesn't work, you'll have to navigate to the config file and edit it manually. For more information, see [Config](#config)

**All other operations of the script require Anki to be running.**

To update the config file with new note types from Anki, run `obsidian_to_anki -u`

To add appropriately-formatted notes from a file, run `obsidian_to_anki -f {FILENAME}`

## Deck formatting
Anywhere within the file, format the deck that you want the notes to go into as follows:
> TARGET DECK
> {Deck name}

For example:
> TARGET DECK
> Mathematics

You may place more than one TARGET DECK, but only the first instance will be read and used.

## Note formatting

In the markdown file, you must format your notes as follows:

> START  
> {Note Type}  
> {Note Fields}  
> Tags: 
> END  

### Tag formatting

Note that the Tags: line is optional - if you don't want tags, you may leave out the line.

Tags should be formatted as such:

> Tags: Tag1 Tag2 Tag3

So, a space between the colon and the first tag, and a space between tags.

### Field formatting

Apart from the first field, each field must have a prefix to indicate to the program when to move on to the next field. For example:

> START  
> Basic  
> This is a test.  
> Back: Test successful!  
> END  

When the script successfully adds a note, it will append an ID to the Note Data. This allows you to update existing notes by running the script again.

Example output:

> START
> Basic
> This is a test.
> Back: Test successful!
> ID: 1566052191670
> END

### Default
By default, the script:
- Adds notes with the tag "Obsidian_to_Anki" (+ other specified tags, if applicable)
- Adds to the Default deck (if TARGET DECK is not specified)
- Adds to the current profile in Anki

## Config
The configuration file allows you to change two things:
1. The substitutions for field prefixes. For example, under the section ['Basic'], you'll see something like this:

> Front = Front:  
> Back = Back:  

If you edit and save this to say

> Front = Front:   
> Back = A:  

Then you now format your notes like this:

> START  
> Basic  
> This is a test.  
> A: Test successful!  
> END  


2. The substitutions for notes. These are under the section ['Note Substitutions']. Similar to the above, you'll see something like this:
> ...  
> Basic = Basic  
> Basic (and reversed) = Basic (and reversed)  
> ...  

If you edit and save this to say  
> ...  
> Basic = B  
> Basic (and reversed) = Basic (and reversed)  
> ...  

Then you now format your notes like this:  
> START  
> B  
> {Note Data}  
> END  

## Supported?

Currently supported features:
* Custom note types
* Updating notes from Obsidian
* Substitutions (see above)
* Auto-convert math formatting
* Tags
* Adding to decks other than Default

Not currently supported features:
* Media
* Markdown formatting
