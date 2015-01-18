Anki ClozeTool is a Python scrip that creates Anki notecards for memorizing sequential information. (For more information about Anki, see [their website](http://ankisrs.net/)) ClozeTool specializes in learning lyrics to songs by accompanying audio clips allong with the text of the song, but it is also designed for learning any type of text or document, such as poems, script lines, or any set of information you need to remember in order.

Each notecard contains a context clue and an answer. The context clue will be a certain number of sequential lines from the text, by default two, and the answer is the next line in the text. This way you can start at any point in the text, and with just two lines know what comes next.

## Quick Start
This is the easy, no-nonsense, way to run ClozeTool. It assumes you have installed all the dependencies to their default locations and with default options. If it does not work, try editing the settings at the top of Anki_ClozeTool.py with any text editor to suit your setup.

**First**: download and install all of the dependencies, found below

#####Text only cards

1. Create a .txt file containing the text you would like to memorize, broken down line by line
- Open Anki to the main screen 
- Run Anki_ClozeTool.py, selecting the .txt file you made
- On import, select the Raw card type, select "Import even if existing note has same first field" in the drop down, and check "Allow HTML in fields." Also, make sure to select what deck you would like to put them in. The rest of the options should be correctly set automatically.

#####Audio/Lyric cards
1. Create a lyric/karaoke file (file extension .lrc), which will contain the timestamps of the song and the text of the lyrics. Most audio files are supported by ClozeTool.
 * I recommend you use [LRCgenerator.com](http://www.lrcgenerator.com) or [MiniLyrics](http://www.crintsoft.com/) to do this. I find that MiniLyrics allows for more control (which is good for faster paced content) but LRCgenerator is good in a pinch.
- Open Anki to the main screen 
- Run Anki_ClozeTool.py, selecting the .lrc file you made and the corresponding audio file
- On import, select the Raw card type, select "Import even if existing note has same first field" in the drop down, and check "Allow HTML in fields." Also, make sure to select what deck you would like to put them in. The rest of the options should be correctly set automatically.

## Dependencies
####Python 3
Download and install [Python 3](https://www.python.org/downloads/). I recommend you install to the default directory and with default settings.

####Pydub
The easiest way to install Pydub is through a terminal. On Windows this means opening Command Prompt and typing:

```
pip install pydub
```

Other systems will use the same command.

If you have any troubles, my recommendation is to make sure you have Python installed to the default (top) directory, and that you select Python to be in your system's PATH variable. Note: pip is included with python.

To learn more about the Pydub project, check out [their website](http://pydub.com/) 

####FFmpeg or Libav
Pydub itself requires either FFmpeg or Libav as multimedia processors in order to work. 

For Windows, my recomendation is to just [download the latest 32-bit static build of ffmpeg](http://ffmpeg.zeranoe.com/builds/win32/static/ffmpeg-latest-win32-static.7z). Unzip it to your top directory in a folder named "ffmpeg". ClozeTool assumes this as a default.

Otherwise, install / unzip either program to your top directory and change the setting in Anki_ClozeTool.py with the location you installed it to.

##Customization
ClozeTool offers different setting to help you suit it to your own needs and to adapt to different computer setups.  

To change the settings, open Anki_ClozeTool.py with any text editor and change the values found at the top.

## Problems/Warnings
#####System Compatibility
ClozeTool has only been tested on Windows

#####Audio Compatibility
ClozeTool supports most audio files, and technically supports any file FFMpeg or Libav supports. ClozeTool's file chooser by default only shows common audio types, but also allows you to try any file format by changing the dropdown file selector to "All Formats." For an exhaustive list of supported file types, see the FFMpeg or Libav websites.

## License
Copyright (c) 2015 Peter Moran.

Permission is granted to copy, distribute and/or modify this document under the terms of the GNU Free Documentation License, Version 1.3 or any later version published by the Free Software Foundation; with no Invariant Sections, no Front-Cover Texts, and no Back-Cover Texts. A copy of the license can be found in the COPYING file or at http://www.gnu.org/copyleft/fdl.html.

## Attributions
#####AnkiLPCG
Anki-ClozeTool is inspired by and borrows code from [AnkiLPCG](https://github.com/sobjornstad/AnkiLPCG), by Soren Bjornstad. Specifically, the functionality for locating Anki and automatically importing to Anki were written by Soren, along with much of the terminal feedback text. I thank him for making his hard work open source.
