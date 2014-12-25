'''
Created on Dec 24, 2014

@author: Peter Moran
To-do:
- File selector (audio + lyrics)
- Automatically send music files to collections.media
- Automatically open Anki to import
- Intelligently read header
- Add more audio file support
- Fix timing of target and next line, in conjunction with nextTime
'''
from pydub import AudioSegment
AudioSegment.converter = "/ffmpeg/bin/ffmpeg.exe"

LINE_DEPTH = 3
extension = '.mp3'

# Open lyric files
lrc = open('Aquarius.lrc')
# Open audio file
audio = AudioSegment.from_mp3('Aquarius.mp3')

targetLine = lrc.readline()
nextLine = lrc.readline()
def getTargetLine():
    global targetLine
    global nextLine
    retval = targetLine
    targetLine = nextLine
    nextLine = lrc.readline()
    return retval

# Read title, album, and artist
artist, title, album = ['']*3
fileLine = getTargetLine()
for i in range(5):
    if i == 0:
        artist = fileLine[5:-2]
    if i == 1:
        title = fileLine[5:-2]
    if i == 2:
        album = fileLine[5:-2]
    fileLine = getTargetLine()

class StampLyrc:
    """A simple class for storing a line of lyrics and 
    the time stamp it starts and ends"""
    def readTime(self, timeStamp):
        milli = 0
        milli += int(timeStamp[1:3])*60000
        milli += int(timeStamp[4:6])*1000
        milli += int(timeStamp[7:9])*10
        return milli
    def nextTime(self):
        if nextLine == '':
            return len(audio)
        else:
            return self.readTime(targetLine) # TODO: Fix flow so this is nextLine. This is just a strange workaround for now.
    def __init__(self, line):
        """Reads a .lcr formatted string to pull out the millisecond time
        stamp and the line of lyrics associated with it"""
        self.milli = self.readTime(line[:10])
        self.lyric = line[10:]
        self.nextMilli = self.nextTime()
    def __str__(self):
        return self.lyric

class Card:
    def __init__(self):
        titleLryc = StampLyrc('[00:00.00][Song Start] '+title+' - '+album) # Fake lyric for song start
        songStart = titleLryc.nextMilli-3000
        if songStart < 0:
            songStart = 0
        titleLryc.milli = songStart
        self.card = [titleLryc]
    def add(self, line):
        if len(self.card) < LINE_DEPTH:
            self.card.append(StampLyrc(line[:-1]))
        else:
            self.card = self.card[1:]
            self.card.append(StampLyrc(line[:-1]))
    def start(self):
        return self.card[0].milli
    def end(self):
        return self.card[-1].milli
    def audioFileName(self):
        return album+'_'+title+'_'+str(self.start())+'-'+str(self.end())+extension
    def __str__(self):
        preSound = '[sound:'+self.audioFileName()+']'
        retval = preSound+'<br>'
        for line in self.card[:-2]:
            retval += str(line)+'<br>'
        retval += str(self.card[-2])+'\t'
        retval += str(self.card[-1])
        return retval

# Create a file to write to
csv = open(title + '.txt', 'w')

# Read lyrics
card = Card()
currFileLine = getTargetLine()
while currFileLine != '':
    card.add(currFileLine)
    csv.write(str(card))
    csv.write('\n')
    selection = audio[card.start():card.end()]
    selection.export('audio/'+card.audioFileName(), format='mp3')
    currFileLine = getTargetLine()