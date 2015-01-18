#! python3
'''
Anki ClozeTool
Copyright 2014 Peter Moran.
Version 0.9.0

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Additional credits:
Anki-ClozeTool is inspired by and borrows code from AnkiLPCG, by Soren Bjornstad.
Specifically, the functionality for locating Anki and automatically importing to 
Anki were written by Soren, along with much of the terminal feedback text.
'''

###################################################################
''' Options/Parameters '''
line_depth = 3                  # Number of lines per card (context + answer)
custom_initial_dir = ''         # Starting file directory in the file selector (defaults to desktop)
custom_anki_location = ''       # Location of Anki.exe if not default
anki_User = 'User 1'            # User name in Anki window title bar and/or in 'My Documents/Anki/'
saveCSV = True                  # Saves a copy of the file used to import to Anki
catch_duplicate_text = True     # Prevents duplicate cards (same front and back text) from importing
show_verse_count = True         # Front of the card will include a 'verse' count any time a context is repeated, regardless of what the answer is
show_stanza_count = True        # If cards have the same front context due to repetitions in the text, a hint will be included on repetitions 2 and on
song_leadtime = 3000            # (For audio) How much time to lead into the first lyric
ffmpegLoc = "/ffmpeg/bin/ffmpeg.exe" # Location of ffmpeg or 
###################################################################

import os
import sys
import copy
import getpass
import tempfile
import traceback
from tkinter import Tk
from subprocess import call
from tkinter.filedialog import askopenfilename
# Import pydub without ffmpeg location warning
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from pydub import AudioSegment

# Hide tkinter root window during file dialogs
root = Tk()
root.withdraw()

# Set starting file directory for finder
user = getpass.getuser()
if custom_initial_dir == '':
    custom_initial_dir = 'C:/Users/%s/Desktop' % user

# Startup
print('''Anki-ClozeTool v0.9.0
Copyright 2015 Peter Moran
---------------------------------
Please ensure Anki is open, and to the main window only''')
input("\nPress Enter when ready to select your file")

# Open audio and text/lyric files
textLoc = askopenfilename(title='Pick text or song lyric file', filetypes=[('Text or Lyric File', ('*.txt', '*.lrc'))], initialdir=custom_initial_dir)
if not textLoc: 
    sys.exit()
textInFormat = os.path.splitext(textLoc)[1][1:]

if textInFormat == 'lrc':
    AudioSegment.converter = ffmpegLoc
    audioLoc = askopenfilename(title='Pick a song', filetypes=[('Audio', ('*.mp3', '.wav', '.wma', '.m4a', 'm4p', '.aac', '.ogg', '.oga', '.flac', '.3gp')), ('All formats', ('*.*'))], initialdir=custom_initial_dir)
    if not audioLoc: 
        sys.exit()
    audioInFormat = os.path.splitext(audioLoc)[1][1:]
    audio = AudioSegment.from_file(audioLoc, format=audioInFormat)
else:
    audio = None
text = open(textLoc)

# Variables and method for reading 'ahead' of the current text/lyric
def nextContent(file):
    '''Returns the next non-blank line in the file'''
    while True:
        read = file.readline()
        if read != '\n':
            break
    return read
targetLine = nextContent(text).rstrip()
nextLine = nextContent(text).rstrip()
def pullLine():
    global targetLine
    global nextLine
    retval = targetLine
    targetLine = nextLine
    nextLine = nextContent(text).rstrip()
    return retval
def peekNextLine():
    return targetLine

# Read / set metadata
if audio:
    artist, title, offset = 'Unknown Artist', 'Unknown Title', 0
    while True:
        fileLine = pullLine()
        tag = fileLine[1:3]
        if tag == 'ar':
            artist = fileLine[5:-1]
        if tag == 'ti':
            title = fileLine[5:-1]
        if tag == 'of':
            offset = int(fileLine[9:-1])
        if any(c in peekNextLine()[1:3] for c in '0123456789'):
            break
else:
    title = os.path.splitext(textLoc)[0]

class Lyric:
    def __init__(self, line):
        if audio:
            self.milliStart = self.startTime(line[:10])
            self.lyric = line[10:]
            self.nextMilli = self.endTime()
        else:
            self.lyric = line
    def startTime(self, timeStamp):
        milli = 0
        milli += int(timeStamp[1:3]) * 60000
        milli += int(timeStamp[4:6]) * 1000
        milli += int(timeStamp[7:9]) * 10
        milli += offset
        return milli
    def endTime(self):
        if nextLine == '':
            return len(audio)
        else:
            return self.startTime(peekNextLine())
    def __str__(self):
        return self.lyric

class Card:
    def __init__(self):
        titleLyrc = '' # Fake lyric for song startTime
        if audio:
            titleLyrc = Lyric('[00:00.00][Song Start] ' + title + ' - ' + artist)
            songStart = titleLyrc.nextMilli - song_leadtime
            if songStart < 0:
                songStart = 0
            titleLyrc.milliStart = songStart
        else:
            titleLyrc = '[Start] ' + title
        self.lyrics = [titleLyrc]
        self.verse = 1
    def add(self, line):
        if len(self.lyrics) < line_depth:
            self.lyrics.append(Lyric(line))
        else:
            self.lyrics = self.lyrics[1:]
            self.lyrics.append(Lyric(line))
        self.verse = 0
    def exportText(self):
        preSound, postSound = '', ''
        if audio:
            preSound = '[sound:' + self.preAudioFile() + ']<br>'
            postSound = '[sound:' + self.postAudioFile() + ']<br>'
        # Get text for front of lyrics
        frontText = ''
        for line in self.lyrics[:-2]:
            frontText += str(line) + '<br>'
        frontText += str(self.lyrics[-2])
        # Add front lyrics and then the lyrics for the back
        return preSound + frontText + '<br><b style="color:blue">['+ self.getVerse() +']</b>\t' + postSound + frontText + '<br>' + str(self.lyrics[-1])
    def __str__(self):
        text = ''
        for line in self.lyrics[:-1]:
            text += str(line)+'\n'
        text += str(self.lyrics[-1])
        return text
    def startTime(self):
        return self.lyrics[0].milliStart
    def contextEndTime(self):
        return self.lyrics[-1].milliStart
    def cardEndTime(self):
        return self.lyrics[-1].endTime()
    def preAudioFile(self):
        return artist + '_' + title + '_' + str(self.startTime()) + '-' + str(self.contextEndTime()) + '.mp3'
    def postAudioFile(self):
        return artist + '_' + title + '_' + str(self.contextEndTime()) + '-' + str(self.cardEndTime()) + '.mp3'
    def textEquals(self, card2):
        return str(self) == str(card2)
    def contextEquals(self, card2):
        selfText = ''
        otherText = ''
        for line in self.lyrics[:-1]:
            selfText += str(line)
        for line in card2.lyrics[:-1]:
            otherText += str(line)
        return selfText == otherText
    def getVerse(self):
        if self.verse == 1:
            return '...'
        else:
            return 'Verse ' + str(self.verse)
        

def locate_anki_executable():
    if custom_anki_location:
        if os.path.exists(custom_anki_location):
            return custom_anki_location
        else:
            print("*****\nError: Your custom Anki location does not exist! ")
            print("Please check the pathname and\n       try again.\n*****\n")
            return None

    if sys.platform.startswith('win32'):
        # based on whether we're using 32- or 64-bit Windows
        if 'PROGRAMFILES(X86)' in os.environ:
            anki_location = os.environ['PROGRAMFILES(X86)']
        else:
            anki_location = os.environ['PROGRAMFILES']

        anki_location = anki_location + '\Anki\\anki.exe'

    elif sys.platform.startswith('linux2'):
        anki_location = 'anki'

    elif sys.platform.startswith('darwin'):
        anki_location = '/Applications/Anki.app/Contents/MacOS/Anki'


    if os.path.exists(anki_location):
        return anki_location
    else:
        print("*****")
        print("WARNING: Anki-ClozeTool could not locate your Anki executable and will not be able to")
        print("automatically import the generated cloze deletions. To solve this problem,")
        print("please set a Custom Anki Location")
        print("*****")
        return None

def open_anki(ankipath, anki_file):
    call([ankipath, anki_file.name])

ankipath = locate_anki_executable()

# Create a file to write to
if saveCSV is True:
    if audio:
        csv = open(artist + ' - ' + title + '_ClozeToolExport' + '.txt', 'w')
    else:
        csv = open(title + '_ClozeToolExport' + '.txt', 'w')
else:
    try:
        csv = tempfile.NamedTemporaryFile('w', delete=False)
    except:
        print("*****")
        print("Could not create a temporary file. Please ensure the")
        print("permissions on your system's temporary folder are correct.")
        print("\nThe original error follows:")
        traceback.print_exc()
        print("*****")
        exit()
ankiMediaDirectory = r'C:\Users\{}\Documents\Anki\{}\collection.media\\'.format(user, anki_User)

# Read text/lyrics
card = Card()
currFileLine = pullLine()
pastCards = []
while currFileLine != '':
    card.add(currFileLine)
    for pastCard in pastCards:
        if card.contextEquals(pastCard) and show_verse_count:
            card.verse = pastCard.verse + 1
    if not any(card.textEquals(pastCard) for pastCard in pastCards) or not catch_duplicate_text:
        pastCards.append(copy.copy(card))        
        csv.write(card.exportText())
        csv.write('\n')
        if audio:
            if not os.path.isfile(ankiMediaDirectory + card.preAudioFile()):
                selection = audio[card.startTime():card.contextEndTime()]
                selection.export(ankiMediaDirectory + card.preAudioFile(), format='mp3')
            if not os.path.isfile(ankiMediaDirectory + card.postAudioFile()):
                selection = audio[card.contextEndTime():card.cardEndTime()]
                selection.export(ankiMediaDirectory + card.postAudioFile(), format='mp3')
    currFileLine = pullLine()

# Import file to Anki, if a location has been found.
if ankipath:
    open_anki(ankipath, csv)
    print("\n* Anki is importing your file. *")
    print("If Anki import does not appear, restart Anki and")
    print("try running Anki-ClozeTool again.")
else:
    print("\nDone! Now manually import the file %s into Anki.\n" % csv.name)
    print("To avoid having to do this manually in the future, consider setting the path")
    print("to Anki in the script file")
