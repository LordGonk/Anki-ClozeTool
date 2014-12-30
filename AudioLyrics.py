'''
Anki Clozed Audio Generator
Copyright 2014 Peter Moran.
Version 0.8.0

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

Additional credits
AnkiLPCG
'''

###################################################################
''' Options/Parameters '''
line_depth = 3              # Number of lines to include on a full card
initial_Dir = ''            # Optional override for starting file directory in the file selector (defaults to desktop)
custom_anki_location = ''
anki_User = 'User 1'        # User name in Anki window title bar and/or in 'My Documents/Anki/'
ffmpegLoc = "/ffmpeg/bin/ffmpeg.exe"
saveCSV = True              # Option to save a copy of the text file imported to Anki
###################################################################

import os
import sys
import getpass
import tempfile
import traceback
from tkinter import Tk
from subprocess import call
from pydub import AudioSegment
from tkinter.filedialog import askopenfilename

# Hide tkinter root window during file dialogs
root = Tk()
root.withdraw()

# Set starting file directory for finder
user = getpass.getuser()
if initial_Dir == '':
    initial_Dir = 'C:/Users/%s/Desktop' % user

# Open audio and lyric files
AudioSegment.converter = ffmpegLoc
audioLoc = askopenfilename(title='Pick a song', filetypes=[('Audio', ('*.mp3', '.wav', '.wma', '.m4a', 'm4p', '.aac', '.ogg', '.oga', '.flac', '.3gp')), ('All formats', ('*.*'))], initialdir=initial_Dir)
if not audioLoc: 
    sys.exit()
lrcLoc = askopenfilename(title='Pick song lyrics', filetypes=[('Lyric File', '*.lrc'), ('Text File', ('*.txt'))], initialdir=initial_Dir)
if not lrcLoc: 
    sys.exit()
audioInFormat = os.path.splitext(audioLoc)[1][1:]
audio = AudioSegment.from_file(audioLoc, format=audioInFormat)
lrc = open(lrcLoc)
    
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
        print("WARNING: LPCG could not locate your Anki executable and will not be able to")
        print("automatically import the generated cloze deletions. To solve this problem,")
        print("please see the \"Setting a Custom Anki Location\" section in the README.")
        print("*****")
        return None

def open_anki(ankipath, anki_file):
    call([ankipath, anki_file.name])

# Variables and method for reading 'ahead' of the current lyric
def nextContent(file):
    '''Returns the next non-blank line in the file'''
    while True:
        read = file.readline()
        if read != '\n':
            break
    return read
targetLine = nextContent(lrc).rstrip()
nextLine = nextContent(lrc).rstrip()
def pullLine():
    global targetLine
    global nextLine
    retval = targetLine
    targetLine = nextLine
    nextLine = nextContent(lrc).rstrip()
    return retval
def peekNextLine():
    return targetLine

# Read title, album, and artist
artist, title, album, offset = 'Unknown Artist', 'Unknown Title', 'Unknown Album', 0
while True:
    fileLine = pullLine()
    tag = fileLine[1:3]
    if tag == 'ar':
        artist = fileLine[5:-1]
    if tag == 'ti':
        title = fileLine[5:-1]
    if tag == 'al':
        album = fileLine[5:-1]
    if tag == 'of':
        offset = int(fileLine[9:-1])
    if any(c in peekNextLine()[1:3] for c in '0123456789'):
        break

class StampLyrc:
    """A simple class for storing a line of lyrics and 
    the time stamp it starts and ends"""
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
    def __init__(self, line):
        """Reads a .lcr formatted string to pull out the millisecond time
        stamp and the line of lyrics associated with it"""
        self.milli = self.startTime(line[:10])
        self.lyric = line[10:]
        self.nextMilli = self.endTime()
    def __str__(self):
        return self.lyric

class Card:
    def __init__(self):
        titleLryc = StampLyrc('[00:00.00][Song Start] ' + title + ' - ' + album)  # Fake lyric for song start
        songStart = titleLryc.nextMilli - 3000
        if songStart < 0:
            songStart = 0
        titleLryc.milli = songStart
        self.card = [titleLryc]
    def add(self, line):
        if len(self.card) < line_depth:
            self.card.append(StampLyrc(line))
        else:
            self.card = self.card[1:]
            self.card.append(StampLyrc(line))
    def start(self):
        return self.card[0].milli
    def preEnd(self):
        return self.card[-1].milli
    def end(self):
        return self.card[-1].endTime()
    def preAudioFile(self):
        return album + '_' + title + '_' + str(self.start()) + '-' + str(self.preEnd()) + '.mp3'
    def postAudioFile(self):
        return album + '_' + title + '_' + str(self.preEnd()) + '-' + str(self.end()) + '.mp3'
    def __str__(self):
        preSound = '[sound:' + self.preAudioFile() + ']'
        postSound = '[sound:' + self.postAudioFile() + ']'
        # Get lyrics for front of card
        frontText = ''
        for line in self.card[:-2]:
            frontText += str(line) + '<br>'
        frontText += str(self.card[-2])
        # Add front text and then the text for the back
        return preSound + frontText + '<br><b style="color:blue">[...]</b>\t' + postSound + frontText + '<br>' + str(self.card[-1])

ankipath = locate_anki_executable()

# Create a file to write to
if saveCSV is True:
    csv = open(album + ' - ' + title + '.txt', 'w')
else:
    try:
        csv = tempfile.NamedTemporaryFile('w', delete=False)
    except:
        print("*****")
        print("Could not create a temporary file. Please ensure:")
        print("- the permissions on your system's temporary folder are correct.")
        print("\nThe original error follows:")
        traceback.print_exc()
        print("*****")
        exit()
ankiMediaDirectory = r'C:\Users\{}\Documents\Anki\{}\collection.media\\'.format(user, anki_User)

# Read lyrics
card = Card()
currFileLine = pullLine()
while currFileLine != '':
    card.add(currFileLine)
    csv.write(str(card))
    csv.write('\n')
    if not os.path.isfile(ankiMediaDirectory + card.preAudioFile()):
        selection = audio[card.start():card.preEnd()]
        selection.export(ankiMediaDirectory + card.preAudioFile(), format='mp3')
    if not os.path.isfile(ankiMediaDirectory + card.postAudioFile()):
        selection = audio[card.preEnd():card.end()]
        selection.export(ankiMediaDirectory + card.postAudioFile(), format='mp3')
    currFileLine = pullLine()

# Import file to Anki, if a location has been found.
if ankipath:
    open_anki(ankipath, csv)
    print("\n* Anki is importing your file. *")
    print("If Anki does not appear, please start Anki and open your profile if")
    print("necessary, then try running LPCG again.")
else:
    print("\nDone! Now import the file %s into Anki.\n" % csv.name)
    print("To avoid having to do this manually in the future, consider setting the path")
    print("to Anki in the script file, as described in the \"Setting a Custom Anki Location\"")
    print("section of the README.\n")
