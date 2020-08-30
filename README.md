# Obsidian_to_Anki
Script to add flashcards from an Obsidian markdown file to Anki.

## Setup
Download the script from the repository. You may wish to consider placing it in a Scripts folder, and adding the script to your PATH.
You'll need to ensure that Anki is running on your desired profile, and that you've installed [AnkiConnect](https://github.com/FooSoft/anki-connect).

Once you've placed the script in the desired directory, run it once with no arguments:
`obsidian_to_anki.py`

This will make a configuration file, `obsidian_to_anki_config.ini`.

## Usage
For simple documentation, run the script with the `-h` flag.

Note that you need to have Anki running when using the script.

In the markdown file, you must format your notes as follows:

START  
{Note Type}  
{Note Data}  
END  

Apart from the first field, each field must have a prefix to indicate to the program when to move on to the next field. For example:

START  
Basic  
This is a test.  
Back: Test successful!  
END  

The configuration file allows you to change two things:
1. The substitutions for field prefixes. For example, under the section ['Basic'], you'll see something like this:

Front = Front:  
Back = Back:  

If you edit and save this to say

Front = Front:   
Back = A:  

Then you now format your notes like this:

START  
Basic  
This is a test.  
A: Test successful!  
END  


2. The substitutions for notes. These are under the section ['Note Substitutions']. Similar to the above, you'll see something like this:
...  
Basic = Basic  
Basic (and reversed) = Basic (and reversed)  
...  

If you edit and save this to say  
...  
Basic = B  
Basic (and reversed) = Basic (and reversed)  
...  

Then you now format your notes like this:  
START  
B  
{Note Data}  
END  
