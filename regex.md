# Table of contents
This page lists templates for custom syntax. In each case, copy-paste the regex line into the desired note type in the config file to use the template.

* [Remnote single-line style](#remnote-single-line-style)
* [Header paragraph style](#header-paragraph-style)
* [Question answer style](#question-answer-style)
* [Neuracache #flashcard style](#neuracache-flashcard-style)
* [Ruled style](#ruled-style)

## Remnote single line #style

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

## Question answer style

Regex line: `^Q: ((?:[^\n][\n]?)+)\n+A: ((?:[^\n][\n]?)+)`

Example usage:
1. Create a file called `test.md`
2. Paste the following contents into the file:
<pre>
Q: How do you use this style?
A: Just like this.

Q: Can the question
run over multiple lines?
A: Yes, and
So can the answer

Q: Does the answer need to be immediately after the question?


A: No, and preceding whitespace will be ignored.

Q: How is this possible?
A: The 'magic' of regular expressions!
</pre>
3. Run `obsidian_to_anki.py -c` to open up the config file
4. Navigate to the "Custom Regexps" section
5. Change the line
> Basic =  

to  

> Basic = `^Q: ((?:[^\n][\n]?)+)\n+A: ((?:[^\n][\n]?)+)`
6. Save the config file
7. Run `obsidian_to_anki.py --regex test.md`
8. You should see these cards in Anki:  
![question_1](Images/Question_1.png)  
![question_2](Images/Question_2.png)  
![question_3](Images/Question_3.png)  
![question_4](Images/Question_4.png)  

## Neuracache #flashcard style

Regex line: `((?:[^\n][\n]?)+) #flashcard\n+((?:[^\n][\n]?)+)`

Example usage:
1. Create a file called `test.md`
2. Paste the following contents into the file:
<pre>
In Neuracache style, to make a flashcard you do #flashcard
The next lines then become the back of the flashcard

If you want, it's certainly possible to
do a multi-line question #flashcard
You just need to make sure both
the question and answer are one paragraph.

And, of course #flashcard


Whitespace is ignored!

</pre>
3. Run `obsidian_to_anki.py -c` to open up the config file
4. Navigate to the "Custom Regexps" section
5. Change the line
> Basic =  

to  

> Basic = `((?:[^\n][\n]?)+) #flashcard\n+((?:[^\n][\n]?)+)`
6. Save the config file
7. Run `obsidian_to_anki.py --regex test.md`
8. You should see these cards in Anki:  
![neuracache_1](Images/Neuracache_1.png)  
![neuracache_2](Images/Neuracache_2.png)  
![neuracache_3](Images/Neuracache_3.png)  

## Ruled style

Regex line: `((?:[^\n][\n]?)+\n)-{3,}\n((?:[^\n][\n]?)+)`

Example usage:
1. Create a file called `test.md`
2. Paste the following contents into the file:
<pre>
How do you use ruled style?
---
You need at least three '-' between the front and back of the card.


Are paragraphs
supported?
---------
Yes, but you need the front and back
directly before and after the ruler.
</pre>
3. Run `obsidian_to_anki.py -c` to open up the config file
4. Navigate to the "Custom Regexps" section
5. Change the line
> Basic =  

to  

> Basic = `((?:[^\n][\n]?)+\n)-{3,}\n((?:[^\n][\n]?)+)`
6. Save the config file
7. Run `obsidian_to_anki.py --regex test.md`
8. You should see these cards in Anki:  

