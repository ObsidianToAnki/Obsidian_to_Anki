This page lists templates for custom syntax. In each case, copy-paste the regex line into the desired note type in the config file to use the template.

## Remnote single-line style

Regex line: `^(.*[^\n:]{1}):{2}([^\n:]{1}.*)`

Example usage:
1. Create a file called `test.md`
2. Paste the following contents into the file:
> This is how to use::Remnote single-line style  
> The script won't see things outside of it.  
> You can have::multiple notes in the same file  
3. Run `obsidian_to_anki.py -c` to open up the config file
4. Navigate to the "Custom Regexps" section
5. Change the line
> Basic =  

to  

> Basic = `^(.*[^\n:]{1}):{2}([^\n:]{1}.*)`
6. Save the config file
7. Run `obsidian_to_anki.py --regex test.md`
8. You should see these cards in Anki:
