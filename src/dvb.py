import curses
import re
import os

deb=open('debug.log','w')
ch = '.mplayer/channels.conf' # channels for mplayer below ~
command = 'mplayer -ao pulse -vf pp=fd dvb://' 

class Nav(object):
    
    li = []
    start = stop = high = 0
    scrn = None
    
    def __init__(self, li, scrn):
        self.li = li
        self.scrn = scrn
        return

    def home(self):
        self.high = self.start = 0
        self.stop = min(curses.LINES, len(self.li))
        self.present()
    
    def end(self):
        t = len(self.li)
        self.high = t-1
        self.start = t - curses.LINES
        self.stop = t
        self.present()  
        
    def arrow(self, c1, c2, d):
        if c1:
            self.high += d
            self.present()
        else:
            if c2:
                self.high += d
                self.stop += d
                self.start += d
        
    def uparrow(self, pres=True):
        c1 = self.high > self.start
        c2 = self.high > 0
        self.arrow(c1, c2, -1) 
        if pres: self.present()          
        
    def downarrow(self, pres=True):             
        c1 = self.high < (self.stop-1)
        c2 = self.high < (len(self.li)-1)
        self.arrow(c1, c2, +1)
        if pres: self.present()        
        
    def pgdn(self):
        for k in range(curses.LINES):
            self.downarrow(False)
        self.present()
            
    def pgup(self):
        for k in range(curses.LINES):
            self.uparrow(False)
        self.present()
        
    def supr(self):
        ex = '(\d+)\t.*'
        co = re.compile(ex)
        self.scrn.getch()
        deb.write(co.search(self.li[self.high]).group(1))
        deb.write('\n')
        deb.flush()
              
    def subebaja(self, c, start, stop, high):
        d = {65:'uparrow', 66:'downarrow', 72:'home', 53:'pgup', 54:'pgdn', 70:'end', 51:'supr'}
        self.start = start
        self.stop = stop
        self.high = high
        c = self.scrn.getch()
        if c == 91:
            c = self.scrn.getch()
            if c in d.keys():
                getattr(self, d[c])()
            else:
                deb.write('27+91+'+c+'\n')
                deb.flush()
        else:
            deb.write('27+'+c+'\n')
            deb.flush()
        return self.start, self.stop, self.high                
    
    def present(self):
        self.scrn.clear()
        k = 0
        for ln in self.li[self.start:self.stop]:
            self.scrn.addstr(k,0,ln)
            k += 1
        self.scrn.addstr(self.high-self.start,0,self.li[self.high],curses.A_STANDOUT) 
        self.scrn.refresh()  

class Dvb(object):
    
    start = stop = high = 0
    scrn = None 
    nav = None 
    li = []
    co = None  
    
    def initCurses(self):
        self.scrn = curses.initscr()       
        curses.noecho()
        curses.cbreak()
                
    def getList(self):        
        return [str(k+1)+'\t'+self.co.search(i).group() for k,i in enumerate(self.li)]
    
    def ic(self, first, second):
        return cmp(first[0].lower(),second[0].lower())
    
    def sort(self):
        k = [(self.co.search(i).group(), str(j+1)) for j,i in enumerate(self.li)]
        k = sorted(k, self.ic)
        k = [i[1]+'\t'+i[0] for i in k]
        self.nav = Nav(k, self.scrn)
        self.nav.home()
        self.high,self.start,self.stop = self.nav.high, self.nav.start, self.nav.stop        
    
    def unsort(self):
        self.nav = Nav(self.getList(), self.scrn)
        self.nav.home()
        self.high,self.start,self.stop = self.nav.high, self.nav.start, self.nav.stop
        
    def search(self):
        c = self.scrn.getch()
        deb.write('searching for :'+str(c)+'\n')
        deb.flush()
    
    def processInput(self):
        while True:
            c = self.scrn.getch()
            if c == 113:    #'q' quit
                break
            elif c == 27:   #3 byte sequence for navigation, arrows, PgDn, etc.
                self.start, self.stop, self.high = self.nav.subebaja(c, self.start, self.stop, self.high)
            elif c == 10:   #Enter, play selected
                ex = '\d+\t(.*)'
                co = re.compile(ex)
                st = command+'"'+co.search(self.nav.li[self.nav.high]).group(1)+'" >> debug.log 2>&1'
                deb.write(st+'\n')
                deb.flush()
                self.scrn.clear()
                self.scrn.refresh()
                #curses.endwin()                
                os.system(st)              
                self.unsort()
            elif c == 115:  #'s' sort
                self.sort()
            elif c == 117:  #'u' unsort
                self.unsort()
            elif c == 47:   #'/' search
                self.search()
            else:
                deb.write('Command: '+str(c)+'\n')
                deb.flush()
    
    def initstep1(self):
        ex = '[^:]+'
        self.co = re.compile(ex)
        f = open(os.environ['HOME']+"/" + ch, "r")
        self.li = f.readlines()
        f.close()
            
    def __init__(self):    
        self.initCurses()
        self.initstep1()
        self.unsort()
        self.processInput()
        curses.nocbreak()
        curses.echo()
        curses.endwin()
        
if __name__ =='__main__':
        Dvb()