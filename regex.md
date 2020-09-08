# Table of contents
This page lists templates for custom syntax. In each case, copy-paste the regex line into the desired note type in the config file to use the template.

* [Remnote single-line style](#remnote-single-line-style)
* [Header paragraph style)(#header-paragraph-style)

## Remnote single line style

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
![remnote_1](Images/Remnote_1.png)  
![remnote_2](Images/Remnote_2.png)

## Header paragraph style

Regex line: `^#+(.+)\n+((?:[^\n#][\n]?)+)`

Example usage:
1. Create a file called `test.md`
2. Paste the following contents into the file:
<pre>
# Style  
This style is suitable for having the header as the front, and the answer as the back
# Overall heading  
## Subheading 1  
You're allowed to nest headers within each other
## Subheading 2
It'll take the deepest level for the question
## Subheading 3
   
   
   
It'll even  
Span over  
Multiple lines, and ignore preceding whitespace  
</pre>
3. Run `obsidian_to_anki.py -c` to open up the config file
4. Navigate to the "Custom Regexps" section
5. Change the line
> Basic =  

to  

> Basic = `^#+(.+)\n+((?:[^\n#][\n]?)+)`
6. Save the config file
7. Run `obsidian_to_anki.py --regex test.md`
8. You should see these cards in Anki:  
![header_1](Images/Header_1.png)  
![header_2](Images/Header_2.png)  
![header_3](Images/Header_3.png)  
![header_4](Images/Header_4.png)  
