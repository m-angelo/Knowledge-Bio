# -*- coding: UTF8 -*-

from __future__ import division
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.behaviors import ButtonBehavior
from kivy.animation import Animation
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.carousel import Carousel
from kivy.storage.jsonstore import JsonStore
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.graphics import Color, Ellipse, Line
from kivy.uix.textinput import TextInput
from kivy.logger 	import Logger
from kivy.config import Config
from kivy.utils import platform
from dateutil.parser import parse
from kivy.config import Config
from datetime import datetime
import webbrowser
import feedparser
import re
import random 

#Creates androidview

try:
    from jnius import autoclass
    from android.runnable import run_on_ui_thread

    android_api_version = autoclass('android.os.Build$VERSION')
    AndroidView = autoclass('android.view.View')
    AndroidPythonActivity = autoclass('org.renpy.android.PythonActivity')

    Logger.debug(
        'Application runs on Android, API level {0}'.format(
            android_api_version.SDK_INT
        )
    )
    
except ImportError:
    def run_on_ui_thread(func):
        def wrapper(*args):
            Logger.debug('{0} called on non android platform'.format(
                func.__name__
            ))
        return wrapper

#Prepares language file

def tekst(number,title=False):
	if title == True:
		return langpack[langchoice].get(number).replace(";-;", "")
	else:
		return langpack[langchoice].get(number).replace(";-;", "\n")

#Creates global variables for (w)idth, (h)eight, x,y and centerx and centery of app for later use

w = ""
h = ""
x, y = "", ""
centerx, centery = "", ""
progi=[0,4,15,30,40,50,100,150,200,250,300,350,400]
for x in range(0,87):
	progi.append(1000)

#Prepares language files

eng = JsonStore('./lang/eng.lang')
es= JsonStore('./lang/es.lang')
pl =  JsonStore('./lang/pl.lang')

#Prepares levels files

lvl=JsonStore('./levels/menu.lvl')
lvl_lib={"G":JsonStore('./levels/glycolysis.lvl') ,"K":JsonStore('./levels/krebs.lvl'),"M":JsonStore('./levels/mcznik.lvl'),"C":JsonStore('./levels/calvin.lvl')  }

#Creates selectors variable to use choose categories by given index

selectors=[lvl_lib["G"],lvl_lib["K"],lvl_lib["M"],lvl_lib["C"]]

player=JsonStore('./player/user.save') #player main save
newstand=JsonStore('./player/news.save') #saved player articles
dailys=JsonStore('./player/daily.save') #daile quest save file
pantonfo=JsonStore('./player/pantofel.save') #paramecium save file
usedsave="" #set player save file
usedscore="" #set player score file
if player["name"]["id"]!="":
	usedsave=player
	usedscore=JsonStore('./player/score.save')
if usedsave != "":
	langchoice = usedsave["lang"]["id"]
else:
	langchoice = "eng"
langpack = {"eng": eng,"pl":pl,"es":es} #langpack dict
choice = 0
allpoints = 100000 #max amount of points
allhelix = 54 #max amount of helix
alllvls = 18 #number of current levels
rscore=0 #summary score
err = 0 #amount of errors during one play
hnt = 0 #amount of hints used during one play 
stime = 0 #starting time of level
ptime = 0 #time of pause period
etime = 0 #finishing time
total = alllvls+allhelix #summary of all points summed from completed levels and collected helix

#Game variables

paus = False
game_over = False
timeend = False
loading = False	

#Lists of level names to load them by index

seq_glyco = ["G1","G2","G3","G4","G5","G6","G7","G8","G9","G10"] 
seq_krebs=["K1","K2","K3","K4","K5","K6","K7","K8"] 
seq_mcz=["M1","M2","M3","M4"]
seq_cal=["C1","C2","C3","C4","C5"]
bindlist=[]

#Whole list of levels for infinite mode

seq=seq_glyco+seq_krebs+seq_mcz+seq_cal

#rgba function to convert rgba values to 0-1 range

def rgba(r, g, b, a):
	if a == False:
		 return (float(r) / 255), (float(g) / 255), (float(b) / 255)
	else:
		return (float(r) / 255), (float(g) / 255), (float(b) / 255), a

#Addon_params class to create variable for scaling all images and widgets positioning 

class Addon_Params(object):
    def init(self):
        global w, h
        w, h = Window.size
        self.ws = float(w) / 1920
        self.hs = float(h) / 1080
        self.scale = min(self.ws, self.hs)

params = Addon_Params()

#Get information from level completion and update Daily Quests status

def Daily_checker(ge,gh,gt,gs,ga):
	nprg={}
	aprg=None
	for x in range(1,4):
		requested = dailys["choosed"]["id"][str(x)][1]
		prg = dailys["progress"]["id"][str(x)]
		t = dailys["choosed"]["id"][str(x)][0]
		if prg < requested:
			if t == 0:
				aprg = gh+prg
			if t == 1:
				aprg= ge+prg
			if t == 2:
				aprg = ga+prg
			if t ==  3:
				if gt > prg:
					aprg = gt
				else:
					aprg=prg
			if t == 4:
				if gs > prg:		
					aprg = gs
				else:
					aprg=prg
			nprg[str(x)]=aprg
		else:
			nprg[str(x)]=prg
			
	dailys.put("progress",id=nprg)

#Creates sprite from image

class UI_Sprite(Image):
    def __init__(self, a=1, **kwargs):
		super(UI_Sprite, self).__init__(allow_stretch=True, **kwargs)
		self.source = self.source
		self.a=a
		self.color = (1, 1, 1, self.a)
		w, h = self.texture_size
		self.size = (params.scale * w, params.scale *h)

#Creates imagebutton with given transparency, press image and release image

class UI_Btn(ButtonBehavior, Image):
    def __init__(self, defalt, pres,a=1, **kwargs):
        super(UI_Btn, self).__init__(**kwargs)
        self.pres = pres
        self.defalt = defalt
        self.source = defalt
        self.color=(1,1,1,a)
        w, h = self.texture_size
        if "arrow" in self.pres:
            self.size = (params.scale * 170, params.scale * 170)
        else:
            self.size = (params.scale * w, params.scale * h)

    def on_press(self):
        self.source = self.pres

    def on_release(self):
        self.source = self.defalt

#Creates Helix counter in upper-left corner

class UI_Helix_Meter(Widget):
	def __init__(self):
		super(UI_Helix_Meter, self).__init__()
		self.bg = UI_Sprite(source="./ui/icons/btnbg.png",a=0.9)
		self.bg.color=(1,1,1,0.7)
		self.bg.center = 0,Window.height
		self.sh = usedsave["helix"]["id"]
		if self.sh>999:
			self.tsh="+999"
		else:
			self.tsh=int(self.sh)
		self.count = Label(text=str(self.tsh),halign='center',size=(10,10),font_name="./fonts/CaviarDreams",font_size=50*params.scale,color=(0,0,0,1))
		self.icon = UI_Sprite(source="./ui/icons/helix.png",)
		self.icon.size=90*params.scale,90*params.scale
		self.icon.center = 0+70*params.scale,Window.height-120*params.scale
		self.count.center =  0+70*params.scale,Window.height-40*params.scale
		self.add_widget(self.bg)
		self.add_widget(self.icon)
		self.add_widget(self.count)		
		self.counter=0
	
	
	
	def update(self,*ignore):
		self.counter=self.counter+1
		self.strcounter=str(self.counter)
		Animation(color=(1,1,1,1),d=.5).start(self.bg)
		dh=(usedsave["helix"]["id"]-self.sh)
		if usedsave["helix"]["id"]>self.sh:
			dc=rgba(48, 240, 5, 1)
			dst="+"+str(usedsave["helix"]["id"]-self.sh)
		else:
			dc=rgba(240, 5, 5, 1)
			dst=str(usedsave["helix"]["id"]-self.sh)
		self.visu={}
		self.up={}
		self.visu[self.strcounter] = Label(text=dst,halign='center',size=(10,10),font_name="./fonts/CaviarDreams",font_size=80*params.scale,color=dc)
		self.visu[self.strcounter].center=0+70*params.scale,Window.height-280*params.scale
		self.up[self.strcounter] = Animation(center_y=Window.height+40*params.scale,t="in_circ",duration=.8)
		self.up[self.strcounter].bind(on_complete=self.endupdate)
		self.add_widget(self.visu[self.strcounter],index=100)
		self.up[self.strcounter].start(self.visu[self.strcounter])
	
	def endupdate(self,*ignore):
		self.visu[self.strcounter].color=0,0,0,0
		self.remove_widget(self.visu[self.strcounter])
		if usedsave["helix"]["id"]>999:
			self.count.text="+999"
		else:
			self.count.text=str(usedsave["helix"]["id"])
		self.sh=usedsave["helix"]["id"]
		Clock.schedule_once(self.alfa5,2)

	def alfa5(self,*ignore):
		Animation(color=(1,1,1,0.5),d=.5).start(self.bg)
	
#Creates levelbutton with given lvl number, state of level, group of levels, looping of whole group and amount of points on that level

class UI_Lvlbtn(Widget):
	def __init__(self,number,state,group,loop,pts,amount):
		super(UI_Lvlbtn, self).__init__()
		self.pts=pts
		if loop == "True":
			if int(number)<amount+1:
				self.nbr = str(int(number))
			elif int(number)<2*amount+1:
				self.nbr = str(int(number)-amount)
			elif int(number)<3*amount+1:
				self.nbr = str(int(number)-2*amount)
			elif int(number)<4*amount+1:
				self.nbr = str(int(number)-3*amount)
		else:
			self.nbr = number
		self.touch_move_list = []
		self.stt = state
		
		if loop == "True":
			self.center_x = (620*params.scale*int(number))-4000*params.scale
		else:
			self.center_x = (620*params.scale*int(number))+350*params.scale
		self.center_y=centery
		if state == True:
			if pts == 0:
				self.bg = UI_Sprite(source='./ui/select/nodotssh.png',a=1)
			elif pts == 1 :
				self.bg = UI_Sprite(source='./ui/select/1dotsh.png',a=1)
			elif pts == 2 :
				self.bg = UI_Sprite(source='./ui/select/2dotsh.png',a=1)
			elif pts == 3:
				self.bg = UI_Sprite(source='./ui/select/3dotsh.png',a=1)
			
			self.default = self.bg.source
			self.bg.center = self.center
			nr = int(number)
			if loop == "True":
				self.nr = UI_ToggleSett(txt=self.nbr, grup=group,row="lvlbtn",font="./fonts/CaviarDreams")
			else:	
				self.nr = UI_ToggleSett(txt=number, grup=group,row="lvlbtn",font="./fonts/CaviarDreams")
			self.score = UI_ToggleSett(txt=("Score\n"+str(pts)), grup=group,row="lvltxtbtn",font="./fonts/CaviarDreams_Bold")
		
			self.nr.center = self.bg.center_x-250*params.scale,self.bg.center_y-120*params.scale
			self.nr.bind(state=self.statecall)
			self.nr.font_size = 250*params.scale
			self.nr.size = self.bg.size
		
			self.add_widget(self.bg)
			self.add_widget(self.nr)
			self.sizer()
			
		elif state == False:
			self.bg = UI_Sprite(source='./ui/select/locked.png',a=1)
			self.bg.center=self.center	
			self.add_widget(self.bg)
			
		if state==True:	
			self.every=[self.bg,self.nr]	
			self.every0=[self.bg.center_x,self.nr.center_x,]
			self.every0y=[self.bg.center_y,self.nr.center_y,]
		else:
			self.every=[self.bg]
			self.every0=[self.bg.center_x]
			self.every0y=[self.bg.center_y]
		for x in range(0,len(self.every)):
			self.every[x].center_y = self.every[x].center_y - 2000*params.scale
			Animation(center_y=self.every0y[x],t="in_sine", duration=1).start(self.every[x])
		self.sizer()
	def statecall(self,obj,value):
		if value == "down":
			self.bg.source='./ui/select/selected.png'
		else:
			self.bg.source=self.default
			
			
	def loader(self,*ignore):
		global loading
		loading = False
		
	def sizer(self,*ignore):
		alfa = 	(0-1)/(((-150*params.scale) - centerx)**2)
		self.bg.a = alfa*(self.bg.center_x - centerx)**2+1
		self.bg.color[3] = self.bg.a
	
	def on_touch_move(self, touch):
			self.sizer()
			if loading == False:
				self.touch_move_list.append(touch.x)
				try:
					for x in range(0,len(self.every)):
						get = self.every[x]
						self.pget =  self.every[x]
						get.center_x = get.center_x+(float(self.touch_move_list[-1])-float(self.touch_move_list[-2]))
				except:
						pass
			if self.bg.x < -600*params.scale or self.bg.x > Window.width+200*params.scale:
				self.remove_widget(self.bg)
				try:	
					self.remove_widget(self.nr)
				except:
					pass
			else:
				try:
					self.add_widget(self.bg)
					self.add_widget(self.nr)
				except:
					pass
				
	def on_touch_up(self, touch):
		self.touch_move_list=[]

#Creates toggle button with given text, group, row which specify position of button and usedfont

class UI_ToggleSett(ToggleButton):
    def __init__(self, txt, grup, row="",font="" ,**kwargs):
		super(UI_ToggleSett, self).__init__(**kwargs)
		self.row = row
		self.text = txt
		self.size = (150 * params.scale, 150 * params.scale)
		self.background_color = (0, 0, 0, 0)
		if font == "":
			self.font_name = "./fonts/CaviarDreams"
		else:
			self.font_name =font
		if not grup == "":
			self.group = grup
		self.color = (rgba(124, 124, 124, 1))
		if row == "":
			pass
			
		if row == "Config":
			self.y = -515 * params.scale
			self.font_size = 150 * params.scale
		if row == "Lang":
			self.y = -910 * params.scale
			self.font_size = 70 * params.scale
			self.color = (rgba(124, 124, 124, 1))
		if row == "lvlbtn":
			self.y = -910 * params.scale
			self.font_size = 70 * params.scale
			self.color = (0, 0, 0, 1)
		if row == "lvltxtbtn":
			self.y = -910 * params.scale
			self.font_size = 70 * params.scale
			self.color = (1, 1, 1, 1)	
            
    def on_state(self, widget, value):
		if value == 'down':
			if self.row == "lvlbtn":
				self.color = (rgba(255, 255, 255, 1))
			elif self.row == "Lang" or self.row == "Config":
				self.color = (rgba(62, 253, 102, 1))
			elif self.row == "lvltxtbtn":
				self.color = (1, 1, 1, 1)	
			else:
				self.color =  (rgba(255, 255, 255, 1))
		else:
			if self.row == "lvlbtn":
				self.color = (0,0,0, 1)
			elif self.row == "lvltxtbtn":		
				self.color = (rgba(62, 253, 102, 1))	
				
			else:
				self.color = (rgba(124, 124, 124, 1))

#Main game class, stage I which covers pregame menu with whole level covered together with whole text about chemical process involved in this level

class Game(Widget):
	def __init__(self,pattern,ingred,loop,transition,bg,choice1="",choice2="",choice3="",pchoice1="",pchoice2="",pchoice3="",random=False):
		super(Game, self).__init__()
		global stance,game_over,paus,stime,ptime,etime,err,hnt,timeend
		self.random = random
		timeend = False
		err = 0
		hnt = 0
		self.chapter=1
		self.timer = 0
		self.starting = True
		self.trans = transition
		self.choice1=choice1
		self.choice2=choice2
		self.choice3=choice3
		self.product1=pchoice1
		self.product2=pchoice2
		self.product3=pchoice3
		self.producted=False
		self.choosed=[]
		self.count = 3050
		self.defs = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
		self.wirepatt={}
		self.blk50= UI_Sprite(source ="./ui/game/black50.png")
		self.add_widget(self.blk50)
		self.pattern = []
		self.wire=[]
		self.wired={}
		self.wirecount=0
		self.wiredpatt={}
		for x in pattern:
			if type(x) != int:
				self.wire.append(x)
				y = int(x[:-1])
				self.pattern.append(y)
			else:
				self.pattern.append(x)
		self.wire.sort()
		for z in range(len(self.wire)):
			a=[]
			if self.wire[z][-1] == "<":
				self.wirecount=self.wirecount+1
				a.append(int(self.wire[z][:-1]))
				smplcount = 1
				if self.wire[z+smplcount][-1] == "*":
					while self.wire[z+smplcount][-1] == "*":
						a.append(int(self.wire[z+smplcount][:-1]))
						smplcount = smplcount +1
				if self.wire[z+smplcount][-1] == ">":
					a.append(int(self.wire[z+smplcount][:-1]))
				self.wired[self.wirecount]=a
		for x in range(1,self.wirecount+1):
			self.wiredpatt[x]=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			for z in self.wired[x]:
					for y in range(len(self.pattern)):
						if z ==self.pattern[y]:
							self.wiredpatt[x][y]=1
							
		self.cntlist = self.pattern
		self.ingred = ingred
		stance = 0	
		if loop == 0:
			self.loop = False
		else:
			self.loop = True	
		self.package = {"loop":loop,"name":transition,"bg":bg,"pattern":self.pattern,"ingred":ingred,"choice1":choice1,"choice2":choice2,"choice3":choice3,"pchoice1":pchoice1,"pchoice2":pchoice2,"pchoice3":pchoice3,"random":random}
		game_over = False
		self.switcher = [False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False]
		self.amount = self.counter()
		self.patt = self.patterner()
		self.backg = UI_Sprite(source=bg)
		self.backg.allow_stretch = True
		self.backg.keep_ratio = False
		self.backg.size_hint =(None,None)
		self.backg.size=Window.size
	#	self.lbl = Label(text=tekst("Draw"), font_name="./fonts/CaviarDreams", font_size=(110 * params.scale),size=(10 * params.scale, 80 * params.scale),valign="top", halign="center", markup=True,color=(rgba(124, 124, 124, 1)))
		self.timer=Label(text=tekst("time")+": 0", font_name="./fonts/CaviarDreams", font_size=(80 * params.scale),size=(10 * params.scale, 80 * params.scale),valign="top", halign="left", markup=True,color=(rgba(28, 217, 44, 1)))
		self.drawinfo = Label(text=tekst(self.trans,title=True), font_name="./fonts/CaviarDreams_Bold", font_size=(70 * params.scale),size=(10 * params.scale, 100 * params.scale),valign="top", halign="left", markup=True,color=(rgba(28, 217, 44, 1)))
	#tekst(self.trans)
	#	self.scoreinfo = Label(text=tekst("ScoreINF"), font_name="./fonts/CaviarDreams", font_size=(110 * params.scale),size=(10 * params.scale, 100 * params.scale), halign="center", markup=True,color=(rgba(28, 217, 44, 1)))
	#	self.points = Label(text=(str(dtime)), font_name="./fonts/CaviarDreams_Bold", font_size=(110 * params.scale),size=(10 * params.scale, 100 * params.scale), halign="center", markup=True,color=(rgba(124, 124, 124, 1)))
		paus = False
		self.pause =  UI_Btn("./ui/game/paus.png","./ui/game/paus.png")
		self.paused =  Button(text=tekst("Paused"),font_name="./fonts/CaviarDreams",font_size=300*params.scale,background_color=(0,0,0,0),halign="center",color=(rgba(62, 253, 102, 1)))
		self.paused.size = 1000*params.scale,300*params.scale
		self.paused.center=centerx,centery
		self.exiter =  Button(text=tekst("Exiter"),font_name="./fonts/CaviarDreams",font_size=150*params.scale,background_color=(0,0,0,0),halign="center",color=(rgba(223, 67, 67, 1)))
		self.exiter.size = 1000*params.scale,500*params.scale
		self.exiter.center=centerx+500*params.scale,centery-420*params.scale
		if transition[0]=="G":
			if usedsave["lang"]["id"] == "pl":
				self.hintdata = JsonStore('./hints/glyco_pl.hint')
			elif  usedsave["lang"]["id"] == "eng":
				self.hintdata = JsonStore('./hints/glyco_eng.hint')
		elif transition[0]=="K":
			if usedsave["lang"]["id"] == "pl":
				self.hintdata = JsonStore('./hints/glyco_pl.hint')
			elif  usedsave["lang"]["id"] == "eng":
				self.hintdata = JsonStore('./hints/glyco_eng.hint')	
		if transition[-1]=="T":
			hintid = transition[0:-1]
		else:
			hintid = transition
		self.hintsrc = UI_Sprite(source=("./hints/"+hintid+".png"))
		try:
			self.hintbox = TextInput(text=self.hintdata.get(str(hintid)),autoindent = True,valign="top",cursor_color = (0,0,0,0),foreground_color=(1,1,1,1),background_color=(0,0,0,0),selection_color=(0,0,0,0),font_size=50*params.scale)
		except:
			self.hintbox = TextInput(text="placeholder",autoindent = True,valign="top",cursor_color = (0,0,0,0),foreground_color=(1,1,1,1),background_color=(0,0,0,0),selection_color=(0,0,0,0),font_size=50*params.scale)
		
		self.hinttab = UI_Sprite(source="./hints/dt.png")
		self.hintbox.allow_copy=False
		self.hintbox.readonly=True 
		self.hintbox.size=830*params.scale,800*params.scale
		self.hinttab.center=centerx+460*params.scale,centery+135*params.scale+820*params.scale
		self.hintbox.center=self.hinttab.center
		self.hintsrc.center=centerx-500*params.scale,centery+135*params.scale+820*params.scale
		self.hinter =  UI_Btn("./hints/dico.png","./hints/dico.png")
		self.hinter.size = 240*params.scale,180*params.scale
		self.hinter.center=centerx,centery+420*params.scale
		self.pause.pos=0,0
		self.transed =  Button(text=tekst(self.trans,title=False),font_name="./fonts/CaviarDreams",font_size=160*params.scale,background_color=(0,0,0,0),halign="center",color=(rgba(62, 253, 102, 1)))
		self.gstart=[self.transed,self.exiter]
		self.gpause=[self.paused,self.exiter]
		self.ghint=[self.hinttab,self.hintsrc,self.hintbox]
		self.timer.center = (centerx+0*params.scale,80*params.scale)
		self.drawinfo.center = (centerx+50*params.scale,Window.height-50*params.scale)
		self.blk50=UI_Sprite(source="./ui/game/black50.png")
		self.blk50.allow_stretch = True
		self.blk50.keep_ratio = False
		self.blk50.size_hint =(None,None)
		self.blk50.size=Window.size
		self.black=UI_Sprite(source="./ui/game/black25.png")
		self.fader= UI_Sprite(source="./ui/select/fader.png")
		self.fader.allow_stretch = True
		self.fader.keep_ratio = False
		self.fader.size_hint =(None,None)
		self.fader.size=Window.size
		self.black.allow_stretch = True
		self.black.keep_ratio = False
		self.black.size_hint =(None,None)
		self.black.size=Window.size
		self.yes=UI_Sprite(source="./ui/game/yes.png")
		self.yes.center=(centerx,centery)
		self.no=UI_Sprite(source="./ui/game/no.png")
		self.no.center=(centerx,centery)
		self.fg=UI_Sprite(source="./ui/game/grid.png")#grid
		self.fg.center=centerx,centery+20*params.scale
		self.paint = Game_Draw()
		self.hinter.bind(on_press=self.hint)
		self.paint.bind(on_touch_move=self.checker)
		self.paint.bind(on_touch_down=self.zero)
		self.paint.bind(on_touch_down=self.stopper)
		self.paint.bind(on_touch_up=self.summit)
		self.pause.bind(on_press=self.pauser)
		self.paused.bind(on_press=self.pauser)
		self.exiter.bind(on_press=self.exited)
		self.add_widget(self.backg)
		self.add_widget(self.fader)
		self.add_widget(self.fg)
	#	self.add_widget(self.lbl)
		self.add_widget(self.timer)
		self.add_widget(self.drawinfo)
		self.add_widget(self.pause)
		#self.add_widget(self.scoreinfo)
		#self.add_widget(self.points)
		self.starttm=0
		self.grid()
		
		if not self.trans =="":
			self.exiter.center=centerx,centery-420*params.scale
			self.transed.size = 1000*params.scale,300*params.scale
			self.transed.center=centerx,centery
			self.transed.bind(on_press=self.startgame)
			self.add_widget(self.black)
			self.add_widget(self.hinter)
			self.add_widget(self.transed)
			self.add_widget(self.exiter)
			win.bind(on_keyboard=self.softback)

			
			
		else:
			if not choice1=="" and not choice2 == "" and not choice3 =="":
				self.chooser(choice1,choice2,choice3,"Which of them is added?")
			else:
				Clock.schedule_once(self.start_mod,0.2)
				
	def startgame(self,*ignore):
		self.remove_widget(self.black)
		self.remove_widget(self.hinter)
		self.remove_widget(self.transed)
		self.remove_widget(self.exiter)
		if not self.choice1=="" and not  self.choice2 == "" and not  self.choice3 =="":
			self.chooser( self.choice1, self.choice2, self.choice3,"Which of them is added?")
		elif not self.product1=="" and not self.product2 == "" and not self.product3 =="" and self.producted==False:
				self.chooser(self.product1,self.product2,self.product3,"Choose side product")
		else:
			Clock.schedule_once(self.start_mod,0.2)
					
	def chooser(self,choice1,choice2,choice3,name):
		self.choosed=[]
		self.choose1=choice1
		self.choose2=choice2
		self.choose3=choice3
		self.adding = Label(text=name,font_name="./fonts/CaviarDreams",font_size=130*params.scale,background_color=(0,0,0,0),halign="center",color=(rgba(62, 253, 102, 1)))	
		self.frontbtn1 = Button(text=choice1.replace("*",""),font_name="./fonts/RomanBold",font_size=150*params.scale,background_color=(0,0,0,0),halign="center",color=(1,0.96,0.44,1))
		self.frontbtn2 = Button(text=choice2.replace("*",""),font_name="./fonts/RomanBold",font_size=150*params.scale,background_color=(0,0,0,0),halign="center",color=(1,0.96,0.44,1))
		self.frontbtn3 = Button(text=choice3.replace("*",""),font_name="./fonts/RomanBold",font_size=150*params.scale,background_color=(0,0,0,0),halign="center",color=(1,0.96,0.44,1))
		self.choices = [self.frontbtn1,self.frontbtn2,self.frontbtn3]
		self.adding.center=(centerx,centery+235*params.scale)
		self.frontbtn1.center=(centerx-550*params.scale,centery-35*params.scale)
		self.frontbtn2.center=(centerx+12*params.scale,centery-35*params.scale)
		self.frontbtn3.center=(centerx+580*params.scale,centery-35*params.scale)
		for x in self.choices:
			x.bind(on_press=self.choosecheck)
		self.add_widget(self.black)
		self.add_widget(self.frontbtn1)
		self.add_widget(self.frontbtn2)
		self.add_widget(self.frontbtn3)
		self.add_widget(self.adding)

	def choosecheck(self,btn): #ADDS POINTS FOR WRONG ANSWERS SCORING
		global err
		if str(btn.text) in str(self.choose1):
			if not btn.text in self.choosed:
				if "*" in self.choose1:
					self.choosed.append(btn.text)
					self.frontbtn1.color=(rgba(62, 253, 102, 1))
					Clock.schedule_once(self.goodchoice,0.5)

				else:
					self.choosed.append(btn.text)
					self.frontbtn1.color=(rgba(255, 91, 91, 1))
					err = err+1

		elif str(btn.text) in str(self.choose2):
			if not btn.text in self.choosed:
				if "*" in self.choose2:
					self.choosed.append(btn.text)
					self.frontbtn2.color=(rgba(62, 253, 102, 1))
					Clock.schedule_once(self.goodchoice,0.5)
				else:
					self.frontbtn2.color=(rgba(255, 91, 91, 1))
					self.choosed.append(btn.text)
					err = err+1
					
		elif str(btn.text) in str(self.choose3):
			if not btn.text in self.choosed:				
				if "*" in self.choose3:
					self.choosed.append(btn.text)
					self.frontbtn3.color=(rgba(62, 253, 102, 1))
					Clock.schedule_once(self.goodchoice,0.5)
				else:
					self.choosed.append(btn.text)
					self.frontbtn3.color=(rgba(255, 91, 91, 1))
					err = err+1
			
	def goodchoice(self,*ignore):
		self.remove_widget(self.black)
		self.remove_widget(self.frontbtn1)
		self.remove_widget(self.frontbtn2)
		self.remove_widget(self.frontbtn3)
		self.remove_widget(self.adding)
		if not self.product1=="" and not self.product2 == "" and not self.product3 =="" and self.producted==False:
				self.chooser(self.product1,self.product2,self.product3,"Choose side product")
		else:
			self.start_mod()
		self.producted=True

	def pauser(self,info,*ignore):
		global ptime,paus
		if paus == False  :
			st = (datetime.now())
			paus = True
			if self.chapter==1:
				try:
					self.remove_widget(self.paint)
				except:
					pass 
			try:
				self.add_widget(self.black)
				self.add_widget(self.paused)
				self.add_widget(self.exiter)
				self.add_widget(self.hinter)
			except:
				pass 
				
			
		elif paus == True :
			if self.chapter==1:
				try:
					self.add_widget(self.paint)
				except:
					pass 
			try:
				self.remove_widget(self.black)
				self.remove_widget(self.paused)
				self.remove_widget(self.exiter)
				self.remove_widget(self.hinter)
				en = (datetime.now())
				ptime = ptime + (en-st)
			except:
				pass
			paus = False
	
	def exited(self,*ignore):
		cat=lvl_lib[self.package["name"][0]]
		if self.random == False:
			self.category=Selector_Category(cat["GROUP"],cat["BG"],cat["ID"],cat["LOOP"],cat["TYPE"])
		else:
			self.category=Menu_Main()
		parent = self.exiter.parent
		for x in parent.children:
			parent.remove_widget(x)
		parent.clear_widgets()
		parent.add_widget(self.category)
	
	def softback(self,window, key, *largs):
		if key == 1001:
			win.unbind(on_keyboard=self.softback)
			cat=lvl_lib[self.package["name"][0]]
			if self.random == False:
				self.category=Selector_Category(cat["GROUP"],cat["BG"],cat["ID"],cat["LOOP"],cat["TYPE"])
			else:
				self.category=Menu_Main()
			parent = self.backg.parent
			parent.clear_widgets()
			parent.add_widget(self.category)
		
	def hint(self,*ignore):
		global hnt
		self.hinter.unbind(on_press=self.hint)
		if self.starting==True:
			part = self.gstart
		else:
			part = self.gpause
		anim = self.ghint+[self.hinter]+part
		for b in self.ghint:
			hnt = hnt+1
			self.add_widget(b)	
		for a in anim:
			ahint=Animation(center_y=(a.center_y-820*params.scale),duration=0.6,t="out_sine")
			ahint.bind(on_complete=self.hintfin)
			ahint.start(a)
	
	def unhint(self, *ignore):
		self.hinter.unbind(on_press=self.unhint)
		if self.starting==True:
			remove = self.gstart
		else:
			remove = self.gpause
		for x in remove:
			self.add_widget(x)
		anim = self.ghint+[self.hinter]+remove
		for a in anim:
			ahint=Animation(center_y=(a.center_y+820*params.scale),duration=0.6,t="out_sine")
			ahint.bind(on_complete=self.unhintfin)
			ahint.start(a)
	
	def hintfin(self, *ignore):
		self.hinter.bind(on_press=self.unhint)
		if self.starting==True:
			remove = self.gstart
		else:
			remove = self.gpause
		for x in remove:
			self.remove_widget(x)
			
	def unhintfin(self, *ignore):
		self.hinter.bind(on_press=self.hint)
		for x in self.ghint:
			self.remove_widget(x)
			
	def stopper(self,touch,*ignore):
		self.paint.unbind(on_touch_down=self.stopper)
		
	def patterner(self):
		for x in range(len(self.cntlist)):
			if self.cntlist[x] != 0:
				self.defs[x] = 1
		return self.defs
	
	def counter(self,count=0):
		for x in range(len(self.cntlist)):
			if self.cntlist[x] != 0:
				count = count+1
		return count
			
	def start_mod(self,*ignore):
		global stime
		self.starting = False
		stime = (datetime.now())
		self.timeswitch=Clock.schedule_interval(self.timeevent,1)
		self.add_widget(self.paint)
	
	def timeevent(self,*ignore):
		if paus == False  :
			self.starttm=self.starttm+1
			self.timer.text=tekst("time")+": "+str(self.starttm)
		if timeend == True:
			self.timeswitch.cancel()
			
	def grid(self):
		self.connections = []
		self.d1 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d2 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d3 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d4 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d5 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d6 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d7 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d8 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d9 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d10 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d11 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d12 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d13 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d14 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d15 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d16 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d17 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d18 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d19 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d20 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d21 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d22 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d23 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d24 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d25 = UI_Sprite(source="./ui/game/dot_off.png")
		
		self.d=[self.d1,self.d2,self.d3,self.d4,self.d5,self.d6,self.d7,self.d8,self.d9,self.d10,self.d11,self.d12,self.d13,self.d14,self.d15,self.d16,self.d17,self.d18,self.d19,self.d20,self.d21,self.d22,self.d23,self.d24,self.d25]
		for x in range(0,len(self.d)):
			self.d[x].size=self.d[x].width/1.2,self.d[x].height/1.2
			self.add_widget(self.d[x])
			
		for x in range(0,len(self.cntlist)):
			
			if self.cntlist[x] != 0:
				self.connections.append(0)
				self.connections.append(0)
		xshift=centerx-430*params.scale
		yshift=centery+340*params.scale 
		for z in range(0,len(self.d)):
			if z<5:
				self.d[z].x = (200*params.scale*(z))+xshift
				self.d[z].y = yshift
			elif z<10:
				self.d[z].x = (200*params.scale*(z-5))+xshift
				self.d[z].y = yshift-170*params.scale
			elif z<15:
				self.d[z].x = (200*params.scale*(z-10))+xshift
				self.d[z].y = yshift-2*170*params.scale
			elif z<20:
				self.d[z].x = (200*params.scale*(z-15))+xshift
				self.d[z].y = yshift-3*170*params.scale
			else:
				self.d[z].x = (200*params.scale*(z-20))+xshift
				self.d[z].y = yshift-4*170*params.scale
				
		for y in range(0,len(self.d)):
			
			if self.patt[y] == 1:
				a =self.d[y].center_x
				b =self.d[y].center_y
				self.connections[(self.cntlist[y]-1)*2]	=a
				self.connections[((self.cntlist[y]-1)*2)+1]	=b
		
	def zero(self,*ignore):
		global game_over
		self.count = 0
		game_over = False
		self.switcher = [False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False]
		
	def checker(self,touch,value):
		for x in range(0,25):
			if self.paint.dot.collide_widget(self.d[x]):
				self.d[x].source="./ui/game/dot_check.png"
				if self.patt[x] == 1:
					if self.switcher[x] == False:
						self.count = self.count +1
						self.switcher[x] = True
					
				else:
					global game_over
					game_over = True
	
	def summit(self,*ignore):
		global game_over,err
		st= str(datetime.now().time())[-11:]
		if self.count == self.amount and game_over == False:
			self.chapter=2
			self.remove_widget(self.paint)
			x=1
			for z in range(len(self.connections)):
				x=x+1
				if x%2==0:
					(self.connections[z])=(self.connections[z]-300*params.scale)
			self.wirelines = {}
			if self.wirecount != 0:
				
				for y in range(1,self.wirecount+1):
					a=[]
					
					for x in range(0,len(self.d)):
						if self.wiredpatt[y][x] ==1:
							b = self.d[x]
							a.append(float(b.center_x)-300*params.scale)
							a.append(float(b.center_y+50*params.scale))
							
					self.wirelines[y]=a
						
			Clock.schedule_once(self.remyes,1)
			self.add_widget(self.yes)
			#self.lbl.text=tekst("Place")
			for x in range(0,25):								
				if  self.ingred[x] == 0 :
				
					self.remove_widget(self.d[x])
				
					
			for x in range(0,25):				
				if self.d[x].source=="./ui/game/dot_check.png":						
					self.d[x].source="./ui/game/dot_on.png"
				
		elif self.count == 3050:
			pass
		else:
			err = err +1
			game_over = True
			self.remove_widget(self.paint)
			for x in range(0,25):
				if self.d[x].source=="./ui/game/dot_check.png":
					self.d[x].source="./ui/game/dot_go.png"
			try:
				if self.pause == False:
					self.add_widget(self.no)
				Clock.schedule_once(self.remno,1)
			except:
				pass	
		
				
	def remyes(self,*ignore):
		self.drag = Game_Drag(self.ingred,self.package)
		self.remove_widget(self.yes)
		k = 0
		Animation(center_x=self.fg.center_x-(300*params.scale),d=.2).start(self.fg)
		for g in self.d:
			k=k+1
			a = Animation(x=g.x-(300*params.scale),d=.2)
			if k<2:
				a.bind(on_complete=self.onfini)	
			a.start(g)
			
			
	def onfini(self,*ignore):
		if self.wirecount != 0:
			for g in self.wirelines:
					self.add_widget(Game_Lines(self.wirelines[g],width=6))
		self.winlines = Game_Lines(self.connections,loop=self.loop)
		self.add_widget(self.winlines)
		self.add_widget(self.drag)
		
	def remno(self,*ignore):
		if self.pause == False:
			self.remove_widget(self.no)
		self.add_widget(self.paint)
		for x in range(0,25):
				self.d[x].source="./ui/game/dot_off.png"	

#Game module which creates lines of chemical structure

class Game_Lines(Widget):

     def __init__(self, points=[],width=12,  loop=False,over=False, *args, **kwargs):
        super(Game_Lines, self).__init__(*args, **kwargs)
        self.over = over
        with self.canvas:
			if self.over == True:
				Color(0.99,0.34,0.34)
			else:
				Color(0.24,0.99,0.4)
			self.line = Line(points=points,width=width*params.scale,close=loop)

#Stage II of the game in which you need to place chemical symbols and groups to fitting spots

class Game_Drag(Widget):
	
	def __init__(self,ingred,package):
		super(Game_Drag, self).__init__()
		self.package = package
		self.ptrn = self.package["pattern"]
		self.ingred = ingred
		self.labelling = {}
		self.labels = []
		self.alfa = 0
		self.patt = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
		self.alfas = {}
		translated = []
		summed = []
		corrected =[]
		self.select = ""
		self.btn_refresh = UI_Sprite(source ="./ui/game/refresh.png")
		self.btn_check= UI_Sprite(source ="./ui/game/check.png")
		self.btn_refresh.center = centerx+680*params.scale,centery-320*params.scale
		self.btn_check.center = centerx+410*params.scale,centery-320*params.scale
		self.toucher = UI_Sprite(source="./ui/game/dot_on.png",a=0)
		self.toucher.size=35*params.scale,35*params.scale
		self.yes=UI_Sprite(source="./ui/game/yes.png")
		self.yes.center=(centerx,centery)
		self.no=UI_Sprite(source="./ui/game/no.png")
		self.no.center=(centerx,centery)
		self.dragbg=UI_Sprite(source="./ui/game/drag.png")
		self.dragbg.center=centerx+550*params.scale,centery+10*params.scale
		self.every=[self.dragbg,self.btn_check,self.btn_refresh]
		for x in self.ingred:
			if x is not 0:
				translated.append(x)
		for x in translated:
			summed =summed +x
		for z in summed:
			corrected.append(z[:-3])
		self.counter={x:corrected.count(x) for x in corrected}
		self.grid()
		self.items_creator(self.counter)
		for z in self.every:
			z.x=z.x+1200*params.scale
			self.add_widget(z)
		for z in self.every:
			Animation(x=z.x-1200*params.scale,d=.4).start(z)
		self.bind(on_touch_down=self.touch_fnc)
	
	def items_creator(self,a):
		#creates elements to add
		self.items = {}
		k = 0
		y = 0
		for key in a:
			y=y+1		
			base = "basic"+str(y)
			self.items[base]=Label(text=key, font_name="./fonts/RomanBold", font_size=(65 * params.scale),size=(70 * params.scale, 70 * params.scale), halign="center", markup=True,color=(rgba(124, 124, 124, 1)))
			if y <= 2:
				self.items[base].y = 900*params.scale
			elif y <= 4:
				self.items[base].y = 750*params.scale
			elif y <= 6:
				self.items[base].y = 600*params.scale
			elif y <= 8:
				self.items[base].y = 550*params.scale
			elif y <= 10:
				self.items[base].y = 400*params.scale
			elif y <= 12:
				self.items[base].y = 350*params.scale
			if y%2 == 0:
				self.items[base].center_x = centerx + 530*params.scale-105*params.scale
			else:
				self.items[base].center_x = centerx + 760*params.scale-105*params.scale
			self.every.append(self.items[base])

	def grid(self):
		#makes grid of dots
		self.d1 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d2 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d3 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d4 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d5 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d6 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d7 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d8 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d9 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d10 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d11 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d12 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d13 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d14 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d15 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d16 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d17 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d18 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d19 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d20 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d21 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d22 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d23 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d24 = UI_Sprite(source="./ui/game/dot_off.png")
		self.d25 = UI_Sprite(source="./ui/game/dot_off.png")
		
		self.d=[self.d1,self.d2,self.d3,self.d4,self.d5,self.d6,self.d7,self.d8,self.d9,self.d10,self.d11,self.d12,self.d13,self.d14,self.d15,self.d16,self.d17,self.d18,self.d19,self.d20,self.d21,self.d22,self.d23,self.d24,self.d25]
		xshift=centerx-430*params.scale
		yshift=centery+365*params.scale
		for z in range(0,len(self.d)):
			#self.d[z].size=80*params.scale,80*params.scale
			if z<5:
				self.d[z].center_x = (200*params.scale*(z))+xshift-(272*params.scale)
				self.d[z].center_y = yshift
			elif z<10:
				self.d[z].center_x = (200*params.scale*(z-5))+xshift-(272*params.scale)
				self.d[z].center_y = yshift-170*params.scale
			elif z<15:
				self.d[z].center_x = (200*params.scale*(z-10))+xshift-(272*params.scale)
				self.d[z].center_y = yshift-2*170*params.scale
			elif z<20:
				self.d[z].center_x = (200*params.scale*(z-15))+xshift-(272*params.scale)
				self.d[z].center_y = yshift-3*170*params.scale
			else:
				self.d[z].center_x = (200*params.scale*(z-20))+xshift-(272*params.scale)
				self.d[z].center_y = yshift-4*170*params.scale
	
		for x in range(0,25):			
				if  self.ingred == 0:
					self.remove_widget(self.d[x])
	
	def touch_fnc(self,value,touch):
		if paus == False:
			self.toucher.center = touch.pos
			if self.toucher.collide_widget(self.btn_check):
				self.btn_check.source = "./ui/game/checked.png"
				self.checker()
			elif self.toucher.collide_widget(self.btn_refresh):
				self.btn_refresh.source = "./ui/game/refreshed.png"
				self.restart()
			else:
				if self.select == "":
					for value in self.items:
						if self.toucher.collide_widget(self.items[value]):
							self.items[value].color = (rgba(62, 253, 102, 1))
							self.select = self.items[value].text		
							
				elif self.select != "" :
					for value in self.items:
						if self.toucher.collide_widget(self.items[value]):
							for keys in self.items:
								self.items[keys].color = (rgba(124, 124, 124, 1))
								
							if self.select ==  self.items[value].text:
								self.select = ""
								
							elif self.select !=  self.items[value].text:
								self.select=self.items[value].text
								self.items[value].color = (rgba(62, 253, 102, 1))
					mv=90		
					for x in range(len(self.d)):
						direction = {"c":[self.d[x].center_x, self.d[x].center_y],"u":[self.d[x].center_x, self.d[x].center_y+  mv*params.scale],"r":[self.d[x].center_x+mv*params.scale, self.d[x].center_y],"d":[self.d[x].center_x, self.d[x].center_y- mv *params.scale],"l":[self.d[x].center_x- mv *params.scale, self.d[x].center_y]}

						if self.toucher.collide_widget(self.d[x]):
							if self.patt[x]  == 0:
								lp = 0 #dlugosc wiersza 0 gdy brak
							else:
								lp = len(self.patt[x])
							if self.ingred[x] != 0:
								if len(self.ingred[x])>lp:
									for z in self.ingred[x]:
										if self.patt[x] == 0:
											rot = self.ingred[x][0][-3:] 
											
										else:
											c=len(self.patt[x])
											rot = self.ingred[x][c][-3:]
									labvar = str(self.d.index(self.d[x]))+str(lp)
									#black
									self.labelling[labvar] =Label(text=self.select, font_name="./fonts/RomanBold",halign="center",valign="center" ,font_size=(65 * params.scale),size=(200 * params.scale, 50 * params.scale), markup=True,color=(0,0,0,1))		
									if rot[0] == "u" or rot[0] == "d":
											if rot[1] == "-":
													vot = "|"
											else:
													vot = "||"
									else:
											if rot[1] == "-":
													vot = "-"
											else:
													vot = "="

									if self.patt[x] == 0:
											
											
											if rot[0] == "u":
												self.labelling[labvar].text = self.select+"\n"+vot
												
											elif rot[0] == "d" :
												self.labelling[labvar].text = vot+"\n"+self.select
											elif rot[0] == "l" :
												self.labelling[labvar].halign="left"
												self.labelling[labvar].text = self.select+""+vot
												
											elif rot[0] == "r" :
												self.labelling[labvar].halign="right"
												self.labelling[labvar].text = vot+""+self.select
												
											else:
												self.labelling[labvar].text = self.select
											self.labelling[labvar].center = direction[rot[0]][0],direction[rot[0]][1]
											self.patt[x] = [self.select+rot]
			
									else:
										
										self.patt[x].append(self.select+rot)
							
										if rot[0] != self.patt[x][-2][-3]:
											
											if rot[0] == "u":
												self.labelling[labvar].text = self.select+"\n"+vot
											elif rot[0] == "d" :
												self.labelling[labvar].text = vot+"\n"+self.select
											elif rot[0] == "l" :
												self.labelling[labvar].text = self.select+""+vot
											elif rot[0] == "r" :
												self.labelling[labvar].text = vot+""+self.select			
											self.labelling[labvar].center = direction[rot[0]][0],direction[rot[0]][1]
										else:
											addvar = str(int(str(self.d.index(self.d[x]))+str(lp))-1)
											if rot[2] == "*":
													dlt = len(self.labelling[addvar].text)
											else:
													dlt = int(rot[2])*(-1)
											if self.patt[x][-2][-3] == "u":
												if  self.labelling[addvar].text[-2:]	 == "||":
													wire=  self.labelling[addvar].text[-3:]	
												else:
													wire=  self.labelling[addvar].text[-2:]	
												modificable=self.labelling[addvar].text[:-2]	
												doneit=modificable[:dlt]+rot[1]+self.select+wire
											elif self.patt[x][-2][-3] == "r":
												modificable=self.labelling[addvar].text	
												doneit="   "+modificable[:dlt]+rot[1]+self.select
											elif self.patt[x][-2][-3] == "l":
												modificable=self.labelling[addvar].text[:-1]
												wire = 	self.labelling[addvar].text[-1]
												doneit=self.select+modificable[:dlt]+rot[1]+wire+"   "
											elif self.patt[x][-2][-3] == "d":
												if  self.labelling[addvar].text[0:2] == "||":
													wire=  self.labelling[addvar].text[0:2]	
												else:
													wire=  self.labelling[addvar].text[0:1]	
												modificable=self.labelling[addvar].text[2:-1]	
												doneit=wire+modificable[:dlt]+rot[1]+self.select
											
											self.labelling[addvar].text = doneit
												
											self.labelling[labvar].pos =  -10000, -10000
									self.add_widget(self.labelling[labvar])
									self.labels.append(self.labelling[labvar])
									
										
							
	def on_touch_up(self,touch):
		self.btn_check.source = "./ui/game/check.png"
		self.btn_refresh.source = "./ui/game/refresh.png"
		
	def checker(self,*ignore):
		global etime, err
		if self.patt == self.ingred:
			etime = datetime.now()
			self.unbind(on_touch_down=self.touch_fnc)
			self.finito = Game_Finish(self.package)
			self.add_widget(self.finito)
		else:
			err = err +1
			self.add_widget(self.no)
			self.unbind(on_touch_down=self.touch_fnc)
			self.restart()
			Clock.schedule_once(self.binder,1)
			
	def restart(self,*ignore):
		for x in self.labels:
			self.remove_widget(x)	
		self.labels = []
		self.labelling = {}
		self.pattlab = {}
		self.alfas = {}
		self.alfa = 0
		self.patt = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
		
	def binder(self,*ignore):
		global stance
		stance = 1
		self.remove_widget(self.no)
		self.bind(on_touch_down=self.touch_fnc)

#Game module which creates a canvas and possibility to draw a line across dots on a grid. Its also switch dots to on after drawing on them

class Game_Draw(Widget):
	def __init__(self):
		super(Game_Draw, self).__init__()
		self.dot = UI_Sprite(0,source="./ui/game/dot_on.png")
		self.add_widget(self.dot)
		
	def on_touch_down(self, touch):
		self.dot.center = touch.pos
		with self.canvas:
			Color(1,0.96,0.44)
			d = 6.*params.scale
			Ellipse(pos=(touch.x - d / 2, touch.y - d / 2), size=(d, d))
			touch.ud['line'] = Line(points=(touch.x, touch.y))
			touch.ud['line'].width=12*params.scale
	def on_touch_move(self, touch):
		self.dot.center=touch.pos
		try:
			touch.ud['line'].points += [touch.x, touch.y]
		except:
			pass
	def on_touch_up(self,touch):
			self.canvas.clear()

#End screen game class
	
class Game_Finish(Widget):
	def __init__(self,package):
		super(Game_Finish, self).__init__()	
		#global err,hnt,stime,ptime,etime
		self.package = package
		global timeend
		timeend = True
		if  self.package["name"][-1]=="T":
			id = self.package["name"][0:-1]
		else:
			id = self.package["name"]
		self.random=self.package["random"]
		self.tile=UI_Sprite(source="./ui/game/tile.png")
		self.fg=UI_Sprite(source="./ui/game/black50.png")
		self.fg.allow_stretch = True
		self.fg.keep_ratio = False
		self.fg.size_hint =(None,None)
		self.fg.size=Window.size
		self.fg.center_x = centerx
		if ptime != 0:
			diff = etime-stime-ptime
		else:
			diff = etime-stime	
		elapsed_ms = (diff.days * 86400000) + (diff.seconds * 1000) + (diff.microseconds / 1000)
		if err == 0:
			se = 2000
		else:
			se = 1/err*10000 
		if hnt == 0:
			sh = 1000
		else:
			sh = 1/hnt *5000
		scored =int( float(1/elapsed_ms) *10000000+ se + sh)
		self.win= Label(text=tekst("Win"), font_name="./fonts/CaviarDreams", font_size=(110 * params.scale),size=(10 * params.scale, 100 * params.scale), halign="center", markup=True,color=(0,0,0,1))
		self.scorelbl= Label(text=tekst("ScoreINF"), font_name="./fonts/CaviarDreams", font_size=(80 * params.scale),size=(10 * params.scale, 100 * params.scale), halign="center", markup=True,color=(rgba(85, 85, 85, 1)))
		self.helixlbl= Label(text=tekst("HelixINF"), font_name="./fonts/CaviarDreams", font_size=(80 * params.scale),size=(10 * params.scale, 100 * params.scale), halign="center", markup=True,color=(rgba(85, 85, 85, 1)))
		self.scoreinf= Label(text=(str(scored)), font_name="./fonts/CaviarDreams", font_size=(110 * params.scale),size=(10 * params.scale, 100 * params.scale), halign="center", markup=True,color=(rgba(62, 253, 102, 1)))
		self.tile.center=(centerx,-550*params.scale)
		self.win.center=(centerx,-200*params.scale)
		self.scorelbl.center=(centerx,-350*params.scale)
		self.scoreinf.center=(centerx,-450*params.scale)
		self.helixlbl.center=(centerx,-680*params.scale)
		self.restart =  Button(text=("R\nE\nS\nT\nA\nR\nT"),font_name="./fonts/CaviarDreams",font_size=70*params.scale,background_color=(0,0,0,0),halign="center")
		self.nxt =  Button(text=("N\nE\nX\nT"),font_name="./fonts/CaviarDreams",font_size=70*params.scale,background_color=(0,0,0,0),halign="center")
		self.menu =  Button(text=("M\nE\nN\nU"),font_name="./fonts/CaviarDreams",font_size=70*params.scale,background_color=(0,0,0,0),halign="center")
		self.btns = [self.restart,self.nxt,self.menu]
		self.restart.center = centerx-390*params.scale,-800*params.scale
		self.menu.center= centerx+390*params.scale,-1010*params.scale
		self.nxt.center= centerx+390*params.scale,-590*params.scale
		self.restart.bind(on_release=self.restarter)
		self.menu.bind(on_release=self.exited)
		self.nxt.bind(on_release=self.nexter)
		for x in self.btns:
			x.bind(on_press=self.colorchanger)
			x.bind(on_release=self.uncolor)
		done = [0,0,0]
		userdone = [0,0,0]
		hcount = 1
		if pantonfo["name"]["id"] != "":
			hpan=pantonfo["hint"]["id"]
			epan=pantonfo["error"]["id"]
			tpan=pantonfo["time"]["id"]
		else:
			hpan=0
			epan=0
			tpan=0
			
		if elapsed_ms<= (15000+1000*tpan):
			hcount = hcount +1
			done[0]=1
			self.h1=UI_Sprite(source='./ui/icons/time.png')
		else:
			self.h1=UI_Sprite(source='./ui/icons/notime.png')
		
		
		if hnt<(1+hpan):
			hcount = hcount +1
			done[1]=1
			self.h2=UI_Sprite(source='./ui/icons/nohint.png')
		else:
			self.h2=UI_Sprite(source='./ui/icons/hint.png')
			
		if err<(1+epan):
			hcount = hcount +1
			done[2]=1
			self.h3=UI_Sprite(source='./ui/icons/noerror.png')
		else:
			self.h3=UI_Sprite(source='./ui/icons/error.png')	
		if userdone == [1,1,1]:
			fa=1
		else:
			fa=0
		Daily_checker(done[2],done[1],(elapsed_ms/1000),scored,fa)
		hlx = usedsave["helix"]["id"]+hcount
		usedsave.put("helix",id=hlx)
		if self.random == False:
			if usedscore.exists(id):
				for x in range(len(done)):
					if usedscore[id]["awards"][x]<done[x]:
						userdone[x] = done[x]
					else:
						userdone[x] = usedscore[id]["awards"][x]
				usedscore.put(id,score=usedscore[id]["score"],awards=userdone)
				if  usedscore[id]["score"]<scored:
					usedscore.put(id,score=scored,awards=userdone)
			else:
				usedscore.put(id,score=scored,awards=done)
		else:
			global rscore
			rscore = rscore+scored
			usedscore.put("random",score=rscore)
			
		self.h=[self.h1,self.h2,self.h3]
		for x in self.h:
			x.size = 125*params.scale,125*params.scale
		self.h1.center_x = centerx-220*params.scale
		self.h2.center_x = centerx
		self.h3.center_x = centerx+220*params.scale
		tileanim = Animation(center_y=centery, t="in_out_back", duration=1.5)
		self.fg.color = (1,1,1,0)
		Animation(color=(1,1,1,1),t="in_sine", duration=1.5).start(self.fg)
		Animation(center_y=centery+350*params.scale, t="in_out_back", duration=1.5).start(self.win)
		Animation(center_y=centery-210*params.scale, t="in_out_back", duration=1.5).start(self.menu)
		Animation(center_y=centery+210*params.scale, t="in_out_back", duration=1.5).start(self.nxt)
		Animation(center_y=centery, t="in_out_back", duration=1.5).start(self.restart)
		Animation(center_y=centery+200*params.scale, t="in_out_back", duration=1.5).start(self.scorelbl)
		Animation(center_y=centery+100*params.scale, t="in_out_back", duration=1.5).start(self.scoreinf)
		Animation(center_y=centery-130*params.scale, t="in_out_back", duration=1.5).start(self.helixlbl)
		tileanim.bind(on_complete=GameApp.body.meter.update)
		tileanim.start(self.tile)
		
		self.HxAn = Animation(center_y=centery-350*params.scale, t="in_out_back", duration=1.5)	
		for x in self.h:
			x.center_y = -900*params.scale
		for x in self.h:
			self.HxAn.start(x)
		
		self.add_widget(self.fg)
		self.add_widget(self.menu)
		self.add_widget(self.nxt)
		if self.random == False:
			self.add_widget(self.restart)
		self.add_widget(self.tile)
		self.add_widget(self.h1)
		self.add_widget(self.h2)
		self.add_widget(self.h3)
		self.add_widget(self.win)
		self.add_widget(self.scorelbl)
		self.add_widget(self.scoreinf)
		self.add_widget(self.helixlbl)

	
	def exited(self,*ignore):
		self.deleter()
		if self.package["name"][0]==(lvl_lib[self.package["name"][0]]["TYPE"]):
				cat=lvl_lib[self.package["name"][0]]
		if self.random == False:
			self.category=Selector_Category(cat["GROUP"],cat["BG"],cat["ID"],cat["LOOP"],cat["TYPE"])
		else:
			self.category=Menu_Main()
		self.gop.add_widget(self.category)
				
	def deleter(self,*ignore):	
		pkg = self.package
		self.p = self.parent
		self.op = self.p.parent
		self.gop = self.op.parent
		self.gop.remove_widget(self.op)
		
	def restarter(self,*ignore):
		self.deleter()
		self.gop.add_widget(Game(self.package["pattern"],self.package["ingred"],self.package["loop"],self.package["bg"],self.package["name"],self.package["choice1"],self.package["choice2"],self.package["choice3"],self.package["pchoice1"],self.package["pchoice2"],self.package["pchoice3"]))	

	def nexter(self,*ignore):
		self.p = self.parent
		self.op = self.p.parent
		self.gop = self.op.parent
		if self.package["name"][-1]=="T":
						name = self.package["name"][0:-1]
		else:
						name = self.package["name"]
		if self.random == False:
			for f in seq:
					if str(name) == f:
						try:
							nextitem= seq[(seq.index(name)+1)]
							if nextitem[0] != name[0]:
								nextitem = None
						except IndexError:
							nextitem = None
						
						
			if nextitem == None:
				self.exited()
			else:
				params = lvl_lib[nextitem[0]][nextitem+"FULL"]
				params[0] =lvl_lib[nextitem[0]][nextitem]
				params[1] =lvl_lib[nextitem[0]][nextitem+"DRAG"]
				self.gop.remove_widget(self.op)
				self.gop.add_widget(Game(*params))
				
		else:
			randseq=[]
			for x in seq:
				if usedscore.exists(x) == True:
					if name != x:
						randseq.append(x)
			rl = random.randrange(0,(len(randseq)))
			Pparams = lvl_lib[randseq[rl][0]][randseq[rl]+"FULL"]
			Pparams[0] =lvl_lib[randseq[rl][0]][randseq[rl]]
			Pparams[1] =lvl_lib[randseq[rl][0]][randseq[rl]+"DRAG"]		
			self.gop.add_widget(Game(*Pparams,random=True))
	
	def colorchanger(self,btn,*ignore):
		btn.color = rgba(62, 253, 102, 1)
		
	def uncolor(self,btn,*ignore):
		btn.color = (1, 1, 1, 1)
 
#Category Selector main file, containing screen with all categories

class Selector_Main(Widget):
	def __init__(self):
		super(Selector_Main, self).__init__()
		self.bg = UI_Sprite(source="./ui/backgrounds/lvl3.png",a=0)
		self.bg.allow_stretch = True
		self.bg.keep_ratio = False
		self.bg.size_hint =(None,None)
		self.bg.size=Window.size
		self.bg.center_x = centerx
		self.fader = UI_Sprite(source="./ui/select/fader.png")
		self.fader.allow_stretch = True
		self.fader.keep_ratio = False
		self.fader.size_hint =(None,None)
		self.fader.size=Window.size
		self.fader.center_x = centerx
		self.actionbt =  Button(text=tekst("Exiter"),font_name="./fonts/CaviarDreams",font_size=150*params.scale,background_color=(0,0,0,0),color=(rgba(223, 67, 67, 1)))
		self.actionbt.center = centerx,centery-400*params.scale
		self.actionbt.bind(on_release=self.exiter)
		tot = 0
		done = 0
		for x in seq_glyco:
			tot = tot+1
			if usedscore.exists(x) == True:
				done = done +1
		self.glyco=Selector_Tile("square",tekst("LVL1_0"),(float(done)/float(tot)*100)) 
		self.random=Selector_Tile("random","",(usedscore["random"]["score"]),"h",(centerx,centery),(centerx-750*params.scale,centery))
		tot = 0
		done = 0
		for z in seq_krebs:
			tot = tot+1
			if usedscore.exists(z) == True:
				done = done +1
		self.random.play.bind(on_release=self.randomquest)
		self.glyco.play.bind(on_release=self.starter)
		self.krebs=Selector_Tile("circle",tekst("LVL1_1"),(float(done)/float(tot)*100),"h",(centerx,centery),(centerx+750*params.scale,centery))
		self.krebs.play.bind(on_release=self.starter)
		tot = 0
		done = 0
		for z in seq_mcz:
			tot = tot+1
			if usedscore.exists(z) == True:
				done = done +1
		self.mcz=Selector_Tile("circle",tekst("LVL1_2"),(float(done)/float(tot)*100),"v",(centerx+750*params.scale,centery),(centerx+750*params.scale,centery-800*params.scale))
		self.mcz.play.bind(on_release=self.starter)
		self.cel=Selector_Tile("circle",tekst("LVL1_3"),(float(done)/float(tot)*100),"v",(centerx+750*params.scale,centery-800*params.scale),(centerx+1650*params.scale,centery-800*params.scale))
		self.cel.play.bind(on_release=self.starter)
		Animation(color=(1, 1, 1, 1), t="in_sine", duration=0.5).start(self.bg)
		self.add_widget(self.bg)	
		self.add_widget(self.random)
		self.add_widget(self.cel)
		self.add_widget(self.mcz)
		self.add_widget(self.krebs)
		self.add_widget(self.glyco)
		self.add_widget(self.fader)
		self.add_widget(self.actionbt)
		win.bind(on_keyboard=self.softback)

	def randomquest(self,*ignore):
		global rscore
		rscore=0
		randseq=[]
		for x in seq:
			if usedscore.exists(x) == True:
				randseq.append(x)
		rl = random.randrange(0,(len(randseq)))
		Pparams = lvl_lib[randseq[rl][0]][randseq[rl]+"FULL"]
		Pparams[0] =lvl_lib[randseq[rl][0]][randseq[rl]]
		Pparams[1] =lvl_lib[randseq[rl][0]][randseq[rl]+"DRAG"]
		parent = self.parent
		parent.clear_widgets()
		parent.add_widget(Game(*Pparams,random=True))
		
	def exiter(self,value):
		parent = self.fader.parent
		parent.clear_widgets()
		parent.add_widget(Menu_Main())
	
	def softback(self,window, key, *largs):
			if key == 1001:
				win.unbind(on_keyboard=self.softback)
				self.exiter("wowimsoindependent")
			
	
	def starter(self,value):
		for x in selectors:
			if value.parent.txt==tekst(x["NID"]):
				cat=x
		self.category=Selector_Category(cat["GROUP"],cat["BG"],cat["ID"],cat["LOOP"],cat["TYPE"])
		parent = self.parent
		parent.clear_widgets()
		parent.add_widget(self.category)

#Creates Level Selector from choosed category in Category Selector

class Selector_Category(Widget):
	def __init__(self,title,background,select,loop,type):
		super(Selector_Category, self).__init__()
		self.type=type
		self.loop = loop
		self.lvlcount = int(selectors[int(select)]["NUMBER"])
		self.fader= UI_Sprite(source="./ui/select/fader.png")
		self.fader.allow_stretch = True
		self.fader.keep_ratio = False
		self.fader.size_hint =(None,None)
		self.fader.size=Window.size
		self.upper = Label(text="", font_name="./fonts/CaviarDreams",font_size=(150 * params.scale), size=(10 * params.scale, 100 * params.scale),color=(rgba(62, 253, 102, 1)))
		self.upper.center = centerx,centery+400*params.scale
		self.actionbt =  Button(text=tekst("Exiter"),font_name="./fonts/CaviarDreams",font_size=150*params.scale,background_color=(0,0,0,0),color=(rgba(223, 67, 67, 1)))
		self.actionbt.center = centerx,centery-400*params.scale
		self.score=Label(text="", font_name="./fonts/CaviarDreams",halign="center",font_size=(100 * params.scale), size=(10 * params.scale, 100 * params.scale),color=(rgba(62, 253, 102, 1)))
		self.rank=Label(text="", font_name="./fonts/CaviarDreams",halign="center",font_size=(100 * params.scale), size=(10 * params.scale, 100 * params.scale),color=(rgba(62, 253, 102, 1)))
		self.score.center=centerx-650*params.scale,centery-400*params.scale
		self.rank.center=centerx+650*params.scale,centery-400*params.scale
		self.bg = UI_Sprite(source=background, a=0)
		self.bg.allow_stretch = True
		self.bg.keep_ratio = False
		self.bg.size_hint =(None,None)
		self.bg.size=Window.size
		self.levels={}
		Animation(color=(1, 1, 1, 1), t="in_sine", duration=1).start(self.bg)
		if loop == "False":
			for x in range(1,self.lvlcount+1):
				if x == 1:
					if usedscore.exists(self.type+str(x)) == True:
						awards =0
						for y in usedscore[self.type+str(x)]["awards"]:
							awards = awards+y
					else:
						awards = 0
					state = True
					
				else:
					if usedscore.exists(self.type+str(x-1)) == False:
						state = False
						awards = 0
					else:
						state = True
						if usedscore.exists(self.type+str(x)) == True:
							awards = 0
							for y in usedscore[self.type+str(x)]["awards"]:
								awards = awards+y
						else:
							awards = 0
				self.levels[str(x)]=UI_Lvlbtn(str(x),state,title,(selectors[int(select)]["LOOP"]),awards,self.lvlcount)
		else:	
			for x in range(1,(self.lvlcount*3)+1):
				f=0
				if x == 1 :
				 f=-1
				elif x==1+self.lvlcount :
				 f=-1
				elif  x==1+self.lvlcount*2 :
				 f=-1
				elif  x==1+self.lvlcount*3 :
				 f=-1
				elif x<=self.lvlcount:
					f=x
				elif x<=self.lvlcount*2:
					f=x-self.lvlcount
				elif x<=self.lvlcount*3:
					f=x-self.lvlcount*2
				if f <0:
					if usedscore.exists(type+str(-1*f)) == True:
						awards = 0
						for y in usedscore[self.type+str(-1*f)]["awards"]:
								awards = awards+y
					else:
						awards = 0
					state = True
					
				if f >0:
					if usedscore.exists(type+str(f-1)) == False:
							state = False
							awards = 0
					else:
							state = True
							awards = 0
							if usedscore.exists(type+str(f)) == True:
								for y in usedscore[self.type+str(f)]["awards"]:
									awards = awards+y
							else:
								awards = 0
				self.levels[str(x)]=UI_Lvlbtn(str(x),state,title,(selectors[int(select)]["LOOP"]),awards,self.lvlcount)
		self.everyalfa=[]
		self.every=[]
		if loop == "False":
			for x in range(1,self.lvlcount+1):
				self.every.append(self.levels[str(x)])
		else:
			for x in range(1,(self.lvlcount*3)+1):
				self.every.append(self.levels[str(x)])
		self.every_center=[]
		self.add_widget(self.bg)
		self.add_widget(self.fader)
		for x in self.levels:
			self.add_widget(self.levels[x])
		self.add_widget(self.upper)
		self.add_widget(self.actionbt)
		self.add_widget(self.score)
		self.add_widget(self.rank)
		self.actionbt.bind(on_press=self.exit)
		win.bind(on_keyboard=self.softback)

		for x in range(0,len(self.every)):
			self.every_center.append(self.every[x].center)
			if self.every[x].stt==True:
				self.every[x].nr.bind(state=self.statecaller)
		self.changeevent = Clock.schedule_interval(self.changer,0.3)
		
	
	def changer(self,*ignore):
			
		for x in self.every:	
			self.everyalfa.append(x.bg.color[3])
		maximum = self.everyalfa.index(max(self.everyalfa))
		current= self.every[self.everyalfa.index(max(self.everyalfa))].nbr
		self.upper.text=tekst(self.type+current,title=True)
		self.everyalfa=[]

	def statecaller(self,obj,value):
		
		if value == "down":
			self.actionbt.color = (rgba(62, 253, 102, 1))
			self.actionbt.text = tekst("Play")
			self.actionbt.unbind(on_press=self.exit)
			self.actionbt.bind(on_press=self.lvlgen)
			if usedscore.exists(self.type+obj.text) == True:
					self.score.text = "Score\n"+str(usedscore[self.type+obj.text]["score"])
			else:
				self.score.text ="Score\nNone"
			self.rank.text ="Rank\nTBA"
			self.chosed=obj.text
		else:
			self.actionbt.color = (rgba(223, 67, 67, 1))
			self.actionbt.text = tekst("Exiter")
			self.actionbt.unbind(on_press=self.lvlgen)
			self.actionbt.bind(on_press=self.exit)
			self.score.text =""
			self.rank.text =""
			self.chosed=obj.text
		
	def lvlgen(self,nbr):
		parent = self.parent
		grandparent =  parent.parent
		params = lvl_lib[self.type][self.type+self.chosed+"FULL"]
		params[0] =lvl_lib[self.type][self.type+self.chosed]
		params[1] =lvl_lib[self.type][self.type+self.chosed+"DRAG"]
		i=1
		for x in params:
			i+=1
		parent.clear_widgets()
		parent.add_widget(Game(*params))	
	
	def exit(self,*ignore):
		parent = self.actionbt.parent
		parent.clear_widgets()
		self.changeevent.cancel()
		parent.add_widget(Selector_Main())

	def softback(self,window, key, *largs):
		if key == 1001:
			win.unbind(on_keyboard=self.softback)
			parent = self.actionbt.parent
			parent.clear_widgets()
			self.changeevent.cancel()
			parent.add_widget(Selector_Main())
				
#Single selector tile look to be initiated in Selector_Main

class Selector_Tile(Widget):
		def __init__(self,shape,text,percent,dep="",prnt=(),ctr=(),**kwargs):
			super(Selector_Tile, self).__init__(**kwargs)
			self.shape=shape
			self.dep = dep
			self.prnt = prnt
			self.txt=text
			self.toucherx = []
			self.touchery = []
			self.starer = 0
			self.finish=90
			self.bg=UI_Sprite(source="./ui/map/"+self.shape.lower()+".png")
			
			if dep=="":
				self.center = centerx,centery
			else:
				self.center = ctr
				if self.dep.lower() =="h":
					self.dots = [prnt[0],prnt[1],self.center_x,prnt[1],ctr[0],ctr[1]]
				elif self.dep.lower() == "v":
					self.dots = [prnt[0],prnt[1],prnt[0],self.center_y,ctr[0],ctr[1]]
				if self.dep.lower() !="":
					self.branch = Selector_Lines(self.dots)
					
			
			self.play = UI_Btn('./ui/icons/play.png', './ui/icons/played.png')		
			self.play.size=(150*params.scale,150*params.scale)
			if self.shape=="random":
				self.prcnt = Label(text="Score\n"+str(int(percent)), font_name="./fonts/CaviarDreams",font_size=(140 * params.scale), size=(10 * params.scale, 100 * params.scale),color=(1,1,1,1))

			else:
				self.prcnt = Label(text=str(int(percent))+"%", font_name="./fonts/CaviarDreams",font_size=(140 * params.scale), size=(10 * params.scale, 100 * params.scale),color=(rgba(62, 253, 102, 1)))
			
			if self.shape=="circle":
				self.bg.size=500*params.scale,500*params.scale	
				self.play.center=self.center_x,self.center_y+80*params.scale
				self.prcnt.center=self.center_x,self.center_y-80*params.scale
			elif self.shape=="random":
				self.bg.size=400*params.scale,400*params.scale	
				self.play.center=self.center_x,self.center_y
				self.prcnt.center=self.center_x,self.center_y-320*params.scale
			else:
				self.play.center=self.center_x-145*params.scale,self.center_y
				self.prcnt.center=self.center_x+120*params.scale,self.center_y
			
			self.bg.center=self.center	
			self.lbl= Label(text=self.txt,halign="center", font_name="./fonts/CaviarDreams_Bold",font_size=(80 * params.scale), size=(10 * params.scale, 100 * params.scale),color=(rgba(62, 253, 102, 1)))
			self.lbl.center=self.bg.center	
			self.toggler = ToggleButton(text='',group="tiles")
			self.toggler.background_color=(0,0,0,0)
			self.toggler.foreground_color=(0,0,0,0)
			self.toggler.size = self.bg.size
			self.toggler.center=self.center
			self.toggler.bind(state=self.state)
			#Clock.schedule_interval(self.optimizer,0.3
			if dep!="":
				self.add_widget(self.branch)
			self.add_widget(self.bg)
			self.add_widget(self.lbl)
			self.add_widget(self.toggler)
			
		
		def state(self,widget, value):
			
		#	self.play.bind(on_release=self.game)
			if value == 'down':
				if self.shape=="random":
					self.bg.source="./ui/map//playrandom.png"
				self.add_widget(self.play)
				self.add_widget(self.prcnt)
				self.lbl.text=""
			else:
				if self.shape=="random":
					self.bg.source="./ui/map//random.png"
				self.lbl.text=self.txt
				self.starer = 0
				try:
					self.remove_widget(self.play)
					self.remove_widget(self.prcnt)
					self.raiseing
				except:
					pass
		
		'''
		def optimizer(self,*ignore):
			if self.bg.right<-300*params.scale or self.bg.top<0-300*params.scale or self.bg.x>Window.width+300*params.scale or self.bg.y>Window.height+300*params.scale:
				self.remove_widget(self.bg)
				self.remove_widget(self.lbl)
				self.remove_widget(self.toggler)
			else:
				try:
					self.add_widget(self.bg)
					self.add_widget(self.lbl)
					self.add_widget(self.toggler)
				except:
					pass
		'''
		
		def on_touch_move(self, touch):
			self.toucherx.append(touch.x)
			self.touchery.append(touch.y)
			self.lbl.center=self.center
			self.bg.center=self.center
			self.toggler.center=self.center
			try:
				if self.shape=="circle":
					self.play.center=self.center_x,self.center_y+90*params.scale
					self.prcnt.center=self.center_x,self.center_y-90*params.scale
				elif self.shape=="random":
					self.bg.size=400*params.scale,400*params.scale	
					self.play.center=self.center_x,self.center_y
					self.prcnt.center=self.center_x,self.center_y-320*params.scale
				
			
				else:
					self.play.center=self.center_x-140*params.scale,self.center_y
					self.prcnt.center=self.center_x+120*params.scale,self.center_y
			except:
				pass
			try:
				self.branch.line.points=self.branch.line.points 
			except:
				pass
			try:	
						
				self.center_x= self.center_x+(float(self.toucherx[-1])-float(self.toucherx[-2]))		
				self.center_y= self.center_y+(float(self.touchery[-1])-float(self.touchery[-2]))	
				for x in range(len(self.branch.line.points)):
					if x%2 == 0:
						self.branch.line.points[x]= self.branch.line.points[x]+(float(self.toucherx[-1])-float(self.toucherx[-2]))				
					else:
						self.branch.line.points[x] = self.branch.line.points[x]+(float(self.touchery[-1])-float(self.touchery[-2]))				
			except:
				pass
		  
			
					
		def on_touch_up(self,touch):
			self.toucherx = []
			self.touchery = []

#Selector line class look, which creates line connection between two tiles

class Selector_Lines(Widget):
	def __init__(self, points=[], *args, **kwargs):
		
		super(Selector_Lines, self).__init__(*args, **kwargs)
		self.toucherx = []
		self.touchery = [] 
		self.points = points

		with self.canvas:
			Color(1.0, 1.0, 1.0,0.5)
			self.line = Line(
					points=self.points,
					joint = "round",
					cap = "none",
					width=10)

#Main Menu class

class Menu_Main(Widget):
	def __init__(self, startup=False, fade=False):
		super(Menu_Main, self).__init__()
		self.blank = UI_Sprite(source='./ui/menus/fg75.png', a=.75)
		self.bot = UI_Sprite(source='./ui/menus/bot.png', a=1)		
		self.bot.allow_stretch = True
		self.bot.keep_ratio = False
		self.bot.size_hint =(None,None)
		self.bot.width 	= Window.width
		self.name = Label(text=tekst(lvl[choice][0]), font_name="./fonts/CaviarDreams", font_size=(200 * params.scale),size=(10 * params.scale, 100 * params.scale), halign="center", markup=True,color=(1, 1, 1, 0))
		self.carousel = Carousel(direction='right', loop=True)
		self.carousel.size = Window.size
		self.carousel.center = (centerx, centery)
		self.carousel.anim_move_duration = 0.1
		self.carousel.scroll_timeout = 0
		self.black=UI_Sprite(source="./ui/game/black25.png",a=0.3)
		self.black.allow_stretch = True
		self.black.keep_ratio = False
		self.black.size_hint =(None,None)
		self.black.size=Window.size
		for i in range(0,len(lvl)):
			image = UI_Sprite(source=lvl[i][1], a=1)
			image.allow_stretch = True
			image.keep_ratio = False
			image.size=Window.size
			self.carousel.add_widget(image)
		self.carousel.index = choice
		self.play = UI_Btn('./ui/icons/play.png', './ui/icons/played.png')
		self.play.id="game"
		self.play.bind(on_press=self.game)
		self.cfg = UI_Btn('./ui/icons/sett.png', './ui/icons/setted.png')
		self.cfg.id="config"
		self.achv = UI_Btn('./ui/icons/achieve.png', './ui/icons/achieved.png')
		self.achv.id="stats"
		self.daily= UI_Btn('./ui/icons/dailyq.png', './ui/icons/dailyq.png')
		self.pant= UI_Btn('./ui/icons/icopantofel.png', './ui/icons/icopantofel.png')
		self.pant.id="pantofel"
		self.pant.bind(on_press=self.game)
		self.daily.id="quests"
		self.daily.bind(on_press=self.game)
		self.cfg.bind(on_press=self.game)
		self.achv.bind(on_press=self.game)
		self.Larrow = UI_Btn('./ui/icons/Larrow.png', './ui/icons/LarrowED.png')
		self.Rarrow = UI_Btn('./ui/icons/Rarrow.png', './ui/icons/RarrowED.png')
		self.Rarrow.bind(on_press=self.next)
		self.Larrow.bind(on_press=self.prev)
		self.Rarrow.size=self.Rarrow.size[0]*2,self.Rarrow.size[1]*2
		self.Larrow.size = self.Rarrow.size
		self.Rarrow.center = ((Window.width - (150 * params.scale)), (670) * params.scale)
		self.Larrow.center = ((150 * params.scale)), (670) * params.scale
		
		self.play.center = (centerx, (140 - 540) * params.scale)
		self.achv.center = ((160 * params.scale), (140 - 540) * params.scale)
		self.cfg.center = ((Window.width-160*params.scale ), (140 - 540) * params.scale)
		self.pant.center= ((centerx + (150 * params.scale))/2, (140 - 540) * params.scale)
		self.daily.center= (((Window.width-((160*params.scale+centerx)/2))), (140 - 540) * params.scale)
		self.bot.center_x = centerx
		self.name.center_x = centerx
		self.name.y = 650 * params.scale
		self.bot.y = (-50 - 540) * params.scale
		self.every = [self.carousel, self.bot, self.cfg, self.play, self.achv,self.pant,self.daily, self.Larrow,self.Rarrow, self.name]
		if startup == False:
			self.start()
		elif startup == True:
			self.started()
		if fade == True:
			for x in range(len(self.carousel.slides)):
				self.carousel.slides[x].color = (1, 1, 1, 0)
				Animation(color=(1, 1, 1, 1), t="in_sine", duration=1.3).start(self.carousel.slides[x])
		
		self.add_widget(self.carousel)
		self.add_widget(self.black)
		self.add_widget(self.bot)
		self.add_widget(self.cfg)
		self.add_widget(self.play)
		self.add_widget(self.achv)
		self.add_widget(self.pant)
		self.add_widget(self.daily)
		self.add_widget(self.name)
		self.add_widget(self.Larrow)
		self.add_widget(self.Rarrow)

		
	def next(self, *ignore):
			
		self.Rarrow.unbind(on_release=self.next)
		Clock.schedule_once(self.bnd, .4)
		self.carousel.load_next(mode="next")
		global choice
		if choice < len(lvl)-1:
			choice = choice + 1
			self.name.text = tekst(lvl[choice][0])

		elif choice == len(lvl)-1:
			choice = 0
			self.name.text = tekst(lvl[choice][0])
		
				
	def prev(self, *ignore):
		self.Larrow.unbind(on_release=self.prev)
		Clock.schedule_once(self.bnd, .4)
		self.carousel.load_previous()
		global choice
		if choice > 0:
			choice = choice - 1
			self.name.text = tekst(lvl[choice][0])
		elif choice == 0:
			choice = len(lvl)-1
			self.name.text = tekst(lvl[choice][0])


	def bnd(self, value):
		if not self.Larrow.on_release == self.prev:
			self.Larrow.bind(on_release=self.prev)
		if not self.Rarrow.on_release == self.next:
			self.Rarrow.bind(on_release=self.next)

	def start(self, *ignore):
		dur = 0.5
		Animation(color=(1, 1, 1, 1), t="in_sine", duration=0.8).start(self.name)
		for x in range(1, 7):
			Animation(y=self.every[x].y + 540 * params.scale, t="in_sine", duration=dur).start(self.every[x])
		#for z in range(5, 7):
		#	Animation(y=self.every[z].y - 540 * params.scale, t="in_sine", duration=dur).start(self.every[z])
            
	def started(self, *ignore):
		self.name.color=(1, 1, 1, 1)
		for x in range(1, 7):
			self.every[x].y=self.every[x].y + 540 * params.scale
	#	for z in range(5, 7):
	#		self.every[z].y=self.every[z].y - 540 * params.scale
            
	def game(self,data):
		parent = self.parent
		data.unbind(on_press=self.game)
		if data.id == "game":
			dur = 0.6
			for x in range(1, 5):
				Animation(y=self.every[x].y - 540 * params.scale, t="in_sine", duration=dur).start(self.every[x])
			Animation(x=self.Rarrow.x + 540 * params.scale, t="in_sine", duration=dur).start(self.Rarrow)
			Animation(x=self.Larrow.x - 540 * params.scale, t="in_sine", duration=dur).start(self.Larrow)
			if choice == 0:
				#game
				self.rem()
				parent.add_widget(Selector_Main())
		
			if choice == 1:
				#news
				self.rem()
				parent.add_widget(Menu_News(usedsave["sources"]["id"]))
				
		elif data.id == "quests":
			#daily
				ndq={}
				dq ={}
				prg={"1":0,"2":0,"3":0}
				if str(datetime.now().date()) > str(dailys["date"]["id"]):
					for x in range(1,4):
						q=random.randrange(len(dailys["quest"]["id"])) #id questa
						b=random.randrange(len(dailys["values"]["id"][q])) #valindex
						v=dailys["values"]["id"][q][b] #id value
						r=(dailys["rewards"]["id"][q][b]) #id reward
										
						ndq[str(x)]=[q,v,r]
					dailys.put("date",id=str(datetime.now().date()))
					dailys.put("choosed",id=ndq)
					dailys.put("progress",id=prg)
					dq =ndq
					
				else:
					  dq = dailys["choosed"]["id"]
						
				self.rem()
				parent.add_widget(Menu_Daily(dq))
				
		elif data.id == "pantofel":
			self.rem()
			parent.add_widget(Menu_Paramecium())
		elif data.id == "stats":
			self.rem()
			self.sett = Menu_Stats()
			parent.add_widget(self.sett)
		elif data.id == "config":
			self.rem()
			self.sett = Menu_Config()
			parent.add_widget(self.sett)
			
	def rem(self,*ignore):
		parent = self.parent
		for x in self.children:
			self.remove_widget(x)
		parent.clear_widgets()

#Daily quests menu segment

class Menu_Daily(Widget):
	def __init__(self,rdailys):
		super(Menu_Daily, self).__init__()
		self.bg=UI_Sprite(source="./ui/backgrounds/lvl99.png")
		self.bg.allow_stretch = True
		self.bg.keep_ratio = False
		self.bg.size_hint =(None,None)
		self.bg.size 	= Window.size

		self.type =  dailys["quest"]["id"]
		self.val=dailys["values"]["id"]
		self.rew=dailys["rewards"]["id"]
		self.rdailys=rdailys
		self.L = {}
		self.L[1]=Label(text="", font_name="./fonts/CaviarDreams", font_size=(70 * params.scale),height=227*params.scale,width=1492 * params.scale, halign="left", markup=True,color=(0,0,0,1))
		self.L[2]=Label(text="", font_name="./fonts/CaviarDreams", font_size=(70 * params.scale),height=227*params.scale,width=1492 * params.scale, halign="left", markup=True,color=(0,0,0,1))
		self.L[3]=Label(text="", font_name="./fonts/CaviarDreams", font_size=(70 * params.scale),height=227*params.scale,width=1492 * params.scale,halign="left", markup=True,color=(0,0,0,1))
		
		self.B={}

		for x in range(1,4):
			qid=rdailys[str(x)][0]
			prg= dailys["progress"]["id"][str(x)]
			req= rdailys[str(x)][1]
			qst= dailys["quest"]["id"][qid]
			rew=rdailys[str(x)][2]
			full=tekst(qst)+str(prg)+"/"+str(req)+"\n"+tekst("Reward")+str(rew)
			
			if dailys["quest"]["id"][qid] == "t":
				if prg<=req and rew > 0 and prg>0:
					self.B[x]=UI_Btn('./ui/daily/ready.png','./ui/daily/ready.png')
					self.B[x].bind(on_press=self.Collect)
					full=tekst(qst)+str(prg)+"/"+str(req)+"\n"+tekst("Reward")+str(rew)
					
				elif prg<=req and rew == 0 and prg>0:
					self.B[x]=UI_Btn('./ui/daily/done.png','./ui/daily/done.png')
					full=tekst(qst)+str(prg)+"/"+str(req)+"\n"+tekst("Reward")+tekst("Collected")
				else:
					self.B[x]=UI_Btn('./ui/daily/prg.png','./ui/daily/prg.png')
					full=tekst(qst)+str(prg)+"/"+str(req)+"\n"+tekst("Reward")+str(rew)
			else:
				if prg>=req and rew > 0:
					self.B[x]=UI_Btn('./ui/daily/ready.png','./ui/daily/ready.png')
					self.B[x].bind(on_press=self.Collect)
					full=tekst(qst)+str(prg)+"/"+str(req)+"\n"+tekst("Reward")+str(rew)
					
				elif prg>=req and rew == 0:
					self.B[x]=UI_Btn('./ui/daily/done.png','./ui/daily/done.png')
					full=tekst(qst)+str(prg)+"/"+str(req)+"\n"+tekst("Reward")+tekst("Collected")
				else:
					self.B[x]=UI_Btn('./ui/daily/prg.png','./ui/daily/prg.png')
					full=tekst(qst)+str(prg)+"/"+str(req)+"\n"+tekst("Reward")+str(rew)
			self.B[x].id=str(x)
			self.L[x].text= '[b]'+ (full)+'[/b]'
			
		self.L[1].center=centerx-100*params.scale,centery+320*params.scale+70*params.scale - 1200 * params.scale
		self.L[2].center=centerx-100*params.scale,centery+70*params.scale - 1200 * params.scale
		self.L[3].center=centerx-100*params.scale,centery-320*params.scale+70*params.scale - 1200 * params.scale
		for x in range(1,4):
			self.B[x].size=self.B[x].width*1.2,self.B[x].height*1.2
		self.B[1].center=centerx,self.L[1].center_y #centery+320*params.scale+50*params.scale - 1150 * params.scale
		self.B[2].center=centerx,self.L[2].center_y
		self.B[3].center=centerx,self.L[3].center_y
		
		self.FLarrow = UI_Btn('./ui/icons/Darrow.png', './ui/icons/DarrowED.png')
		self.FLarrow.size = self.FLarrow.size[0]*1.2,self.FLarrow.size[1]*1.2
		self.FLarrow.center = ((centerx)), centery-460 * params.scale- 1130 * params.scale
		self.FLarrow.bind(on_press=self.BackAnim)
		self.StartAnim()
		self.add_widget(self.bg)
		self.add_widget(self.FLarrow)
		self.add_widget(self.B[1])
		self.add_widget(self.B[2])
		self.add_widget(self.B[3])
		self.add_widget(self.L[1])
		self.add_widget(self.L[2])
		self.add_widget(self.L[3])
		win.bind(on_keyboard=self.softback)

	
	def Collect(self,item):
		item.unbind(on_press=self.Collect)
		x = item.id
		qid=self.rdailys[str(x)][0]
		prg= dailys["progress"]["id"][str(x)]
		req=self.rdailys[str(x)][1]
		qst= dailys["quest"]["id"][qid]
		self.L[int(x)].text=tekst(qst)+str(prg)+"/"+str(req)+"\n"+tekst("Reward")+tekst("Collected")
		item.pres = item.defalt = item.source = './ui/daily/done.png'
		dbody=dict(dailys["choosed"]["id"])
		hcount=dbody[str(x)][2]
		dbody[str(x)][2]=0
		dailys.put("choosed",id=dbody)
		hlx = usedsave["helix"]["id"]+hcount
		usedsave.put("helix",id=hlx)
		GameApp.body.meter.update()
	
	def StartAnim(self,*ignore):
		for k in range(1,4):
			Animation(y=self.L[k].center_y + 1000 * params.scale, t="in_sine",duration=0.5).start(self.L[k])
			Animation(y=self.B[k].center_y + 1000 * params.scale, t="in_sine",duration=0.5).start(self.B[k])
		one=Animation(y=self.FLarrow.center_y + 1000 * params.scale, t="in_sine",duration=0.5)
		one.start(self.FLarrow)
	
	def BackAnim(self,*ignore):
		
		for k in range(1,4):
			Animation(y=self.L[k].center_y - 1000 * params.scale, t="in_sine",duration=0.5).start(self.L[k])
			Animation(y=self.B[k].center_y - 1000 * params.scale, t="in_sine",duration=0.5).start(self.B[k])
		one=Animation(y=self.FLarrow.center_y - 1000 * params.scale, t="in_sine",duration=0.5)
		one.bind(on_complete=self.Back)
		one.start(self.FLarrow)
		
		
	
	def Back(self,*ignore):
		parent = self.parent
		parent = self.parent
		parent.clear_widgets()
		parent.add_widget(Menu_Main())
	
	def softback(self,window, key, *largs):
		if key == 1001:
			win.unbind(on_keyboard=self.softback)
			for k in range(1,4):
				Animation(y=self.L[k].center_y - 1000 * params.scale, t="in_sine",duration=0.5).start(self.L[k])
				Animation(y=self.B[k].center_y - 1000 * params.scale, t="in_sine",duration=0.5).start(self.B[k])
			one=Animation(y=self.FLarrow.center_y - 1000 * params.scale, t="in_sine",duration=0.5)
			one.bind(on_complete=self.Back)
			one.start(self.FLarrow)

#Paramecium - player biological charater with upgrades and perks segment

class Menu_Paramecium(Widget):
	def __init__(self):
		super(Paramecium, self).__init__()
		self.bg = UI_Sprite(source="./ui/backgrounds/lvl2.png", a=1)
		self.bg.allow_stretch = True
		self.bg.keep_ratio = False
		self.bg.size_hint =(None,None)
		self.bg.size 	= Window.size
		#if pantonfo["name"]["id"] == "":
		#	pass
		#else:
		if pantonfo["lvl"]["id"] <= 13:
			self.pantofel = UI_Sprite(source=("./paramecium/p"+str(pantonfo["lvl"]["id"])+".png"), a=1)
		else:
			self.pantofel = UI_Sprite(source=("./paramecium/p13.png"), a=1)
		self.tile=UI_Sprite(source="./ui/menus/pantile.png", a=1)		
		self.tut=UI_Sprite(source="./ui/menus/pantut.png", a=1)
		self.sbar=UI_Sprite(source="./ui/menus/startbar.png", a=1)
		self.bar=UI_Sprite(source="./ui/menus/bar.png", a=1)
		self.ebar=UI_Sprite(source="./ui/menus/endbar.png", a=1)
		self.error=UI_Btn("./ui/icons/noerror.png", "./ui/icons/noerror.png")
		self.time=UI_Btn("./ui/icons/time.png","./ui/icons/time.png" )
		self.hint=UI_Btn("./ui/icons/nohint.png","./ui/icons/nohint.png" )
		self.counterror=Label(text=str(pantonfo["error"]["id"]), font_name="./fonts/CaviarDreams", font_size=(120 * params.scale),size=(100 * params.scale, 100 * params.scale), halign="center", markup=True,color=(0,0, 0, 1))
		self.counthint=Label(text=str(pantonfo["hint"]["id"]), font_name="./fonts/CaviarDreams", font_size=(120 * params.scale),size=(100 * params.scale, 100 * params.scale), halign="center", markup=True,color=(0,0, 0, 1))
		self.counttime=Label(text=str(pantonfo["time"]["id"]), font_name="./fonts/CaviarDreams", font_size=(120 * params.scale),size=(100 * params.scale, 100 * params.scale), halign="center", markup=True,color=(0,0, 0, 1))
		self.bartext= Button(text="GIVE IT DNA", font_name="./fonts/CaviarDreams", font_size=(100 * params.scale),size=(1000 * params.scale, 100 * params.scale), color=(0,0, 0, 1),background_color=(0,0,0,0))
		self.name = Label(text=pantonfo["name"]["id"],font_name="./fonts/CaviarDreams", font_size=(120 * params.scale),size=(10 * params.scale, 100 * params.scale), halign="center", markup=True,color=(0,0, 0, 1))
		self.lvl=Label(text="lvl. "+str(pantonfo["lvl"]["id"]), font_name="./fonts/CaviarDreams", font_size=(80 * params.scale),size=(10 * params.scale, 100 * params.scale), halign="center", markup=True,color=(0,0, 0, 1))	
		self.prg=Label(text=str(pantonfo["exp"]["id"])+"/"+str(progi[pantonfo["lvl"]["id"]]), font_name="./fonts/CaviarDreams", font_size=(70 * params.scale),size=(10 * params.scale, 100 * params.scale), halign="center", markup=True,color=(0,0, 0, 1))
		self.bartext.bind(on_press=self.startcharge)
		self.bartext.bind(on_release=self.stopcharge)
		self.tile.center=(Window.width-960*params.scale),centery
		self.name.center=(Window.width-500*params.scale),centery+450*params.scale
		self.lvl.center=(Window.width-500*params.scale),centery+330*params.scale
		self.prg.center=(Window.width-500*params.scale),centery+200*params.scale
		self.bartext.center=(Window.width-550*params.scale),centery+80*params.scale
		self.tut.center=(Window.width-(960-1150)*params.scale),centery
		self.pantofel.center=centerx,centery+100*params.scale
		self.sbar.center=(Window.width-1090*params.scale),centery+80*params.scale
		if pantonfo["lvl"]["id"] ==1:
			self.bar.size=(1100*(pantonfo["exp"]["id"]/progi[pantonfo["lvl"]["id"]]))*params.scale,self.bar.height
		else:
			self.bar.size=(1100*((pantonfo["exp"]["id"]-progi[pantonfo["lvl"]["id"]-1])/(progi[pantonfo["lvl"]["id"]]-progi[pantonfo["lvl"]["id"]-1])))*params.scale,self.bar.height
		self.bar.allow_stretch = True
		self.bar.keep_ratio = False
		self.bar.size_hint =(None,None)
		self.bar.pos=self.sbar.x+self.sbar.width,self.sbar.y
		self.ebar.pos=self.bar.x+self.bar.width,self.sbar.y
		self.hint.size=self.time.size=self.error.size=(240*params.scale,240*params.scale)
		
		self.hint.center=Window.width-970*params.scale,centery-200*params.scale
		self.time.center=Window.width-620*params.scale,centery-200*params.scale
		self.error.center=Window.width-270*params.scale,centery-200*params.scale
		
		self.counthint.center=Window.width-(970+0)*params.scale,centery-(200+210)*params.scale
		self.counttime.center=Window.width-(620+0)*params.scale,centery-(200+210)*params.scale
		self.counterror.center=Window.width-(270+0)*params.scale,centery-(200+210)*params.scale
		if pantonfo["exp"]["id"]==progi[pantonfo["lvl"]["id"]]:
				self.bartext.text="CHOOSE PERK"
				self.sbar.source="./ui/menus/startbarcollect.png"
				self.bar.source="./ui/menus/barcollect.png"
				self.ebar.source="./ui/menus/endbarcollect.png"
				self.hint.id="hint"
				self.error.id="error"
				self.time.id="time"
				self.error.defalt=self.error.source="./ui/icons/acterror.png"
				self.time.defalt=self.time.source="./ui/icons/acttime.png"
				self.hint.defalt=self.hint.source="./ui/icons/acthnt.png"
				self.error.bind(on_press=self.addperk)
				self.time.bind(on_press=self.addperk)
				self.hint.bind(on_press=self.addperk)
		self.FLarrow = UI_Btn('./ui/icons/Darrow.png', './ui/icons/DarrowED.png')
		self.FLarrow.size = self.FLarrow.size[0]*1.2,self.FLarrow.size[1]*1.2
		self.FLarrow.center = ((centerx-650 * params.scale)), centery-1450*params.scale
		self.FLarrow.bind(on_press=self.back)
		self.every=[self.tile,self.tut,self.sbar,self.bar,self.ebar,self.hint,self.error,self.counterror,self.counthint,self.counttime,self.time,self.name,self.prg,self.lvl,self.bartext]
		for f in self.every:
			f.x=f.x+1500*params.scale
			Animation(x=(f.x-1500*params.scale),d=.4).start(f)
		Animation(x=((400*params.scale)-((self.pantofel.width)/2)),d=.4).start(self.pantofel)
		Animation(y=(self.FLarrow.y+1000*params.scale),d=.4).start(self.FLarrow)
		self.add_widget(self.bg)
		self.add_widget(self.tile)
		self.add_widget(self.tut)
		self.add_widget(self.pantofel)
		self.add_widget(self.sbar)
		self.add_widget(self.bar)
		self.add_widget(self.ebar)
		self.add_widget(self.hint)
		self.add_widget(self.error)
		self.add_widget(self.counterror)
		self.add_widget(self.counthint)
		self.add_widget(self.counttime)
		self.add_widget(self.time)
		self.add_widget(self.name)
		self.add_widget(self.prg)
		self.add_widget(self.lvl)
		self.add_widget(self.bartext)
		self.add_widget(self.FLarrow)
		win.bind(on_keyboard=self.softback)


	def startcharge(self,*ignore):
		self.charging = Clock.schedule_interval(self.charger,0.1)
		self.bartext.color=rgba(0, 0, 0, 1)
		
	def stopcharge(self,*ignore):
		GameApp.body.meter.update()
		self.bartext.color=(0,0,0,1)
		self.charging.cancel()
			
	
	def charger(self,*ignore):
		if usedsave["helix"]["id"] >0:
			if pantonfo["exp"]["id"]<progi[pantonfo["lvl"]["id"]]:
			
				if GameApp.body.meter.count.text!="+999":
					GameApp.body.meter.count.text=str(int(GameApp.body.meter.count.text)-1)
				newexp=pantonfo["exp"]["id"]+1
				newhlx=usedsave["helix"]["id"]-1
				pantonfo.put('exp',id=newexp)
				usedsave.put('helix',id=newhlx)
				self.prg.text=str(pantonfo["exp"]["id"])+"/"+str(progi[pantonfo["lvl"]["id"]])
				if pantonfo["lvl"]["id"] ==1:
					self.bar.size=(1100*(pantonfo["exp"]["id"]/progi[pantonfo["lvl"]["id"]]))*params.scale,self.bar.height
				else:
					self.bar.size=(1100*((pantonfo["exp"]["id"]-progi[pantonfo["lvl"]["id"]-1])/(progi[pantonfo["lvl"]["id"]]-progi[pantonfo["lvl"]["id"]-1])))*params.scale,self.bar.height

				self.bar.pos=self.sbar.x+self.sbar.width,self.sbar.y
				self.ebar.pos=self.bar.x+self.bar.width,self.sbar.y
			elif pantonfo["exp"]["id"]==progi[pantonfo["lvl"]["id"]]:
				self.stopcharge()
				self.bartext.text="CHOOSE PERK"
				self.sbar.source="./ui/startbarcollect.png"
				self.bar.source="./ui/barcollect.png"
				self.ebar.source="./ui/endbarcollect.png"
				self.hint.id="hint"
				self.error.id="error"
				self.time.id="time"
				self.error.defalt=self.error.source="./ui/icons/acterror.png"
				self.time.defalt=self.time.source="./ui/icons/acttime.png"
				self.hint.defalt=self.hint.source="./ui/icons/acthnt.png"
				self.error.bind(on_press=self.addperk)
				self.time.bind(on_press=self.addperk)
				self.hint.bind(on_press=self.addperk)
	
	def addperk(self,nfo):
		self.error.unbind(on_press=self.addperk)
		self.time.unbind(on_press=self.addperk)
		self.hint.unbind(on_press=self.addperk)
		newperk = pantonfo[nfo.id]["id"]+1
		newlvl = pantonfo["lvl"]["id"]+1
		pantonfo.put(nfo.id,id=newperk)		
		pantonfo.put("lvl",id=newlvl)
		if pantonfo["lvl"]["id"] <= 13:
			self.pantofel.source=("./paramecium/p"+str(pantonfo["lvl"]["id"])+".png")
		else:
			self.pantofel.source=("./paramecium/p13.png")
		self.counthint.text=str(pantonfo["hint"]["id"])
		self.counterror.text=str(pantonfo["error"]["id"])
		self.counttime.text=str(pantonfo["time"]["id"])
		self.sbar.source="./ui/startbar.png"
		self.bar.source="./ui/bar.png"
		self.ebar.source="./ui/endbar.png"
		self.error.defalt=self.error.source="./ui/icons/noerror.png"
		self.time.defalt=self.time.source="./ui/icons/time.png"
		self.hint.defalt=self.hint.source="./ui/icons/nohint.png"
		self.bartext.text="GIVE IT DNA"
		self.lvl.text="lvl. "+str(pantonfo["lvl"]["id"])
		self.prg.text=str(pantonfo["exp"]["id"])+"/"+str(progi[pantonfo["lvl"]["id"]])
		if pantonfo["lvl"]["id"] ==1:
			self.bar.size=(1100*(pantonfo["exp"]["id"]/progi[pantonfo["lvl"]["id"]]))*params.scale,self.bar.height
		else:
			self.bar.size=(1100*((pantonfo["exp"]["id"]-progi[pantonfo["lvl"]["id"]-1])/(progi[pantonfo["lvl"]["id"]]-progi[pantonfo["lvl"]["id"]-1])))*params.scale,self.bar.height
		self.bar.pos=self.sbar.x+self.sbar.width,self.sbar.y
		self.ebar.pos=self.bar.x+self.bar.width,self.sbar.y
		
	def back(self,*ignore):
		for f in self.every:
			Animation(x=(f.x+1500*params.scale),d=.4).start(f)
		Animation(x=((-500)-((self.pantofel.width)/2)),d=.4).start(self.pantofel)
		a=Animation(y=(self.FLarrow.y-1000*params.scale),d=.4)
		a.bind(on_complete=self.getback)
		a.start(self.FLarrow)
		
	def softback(self,window, key, *largs):
			if key == 1001:
				win.unbind(on_keyboard=self.softback)
				for f in self.every:
					Animation(x=(f.x+1500*params.scale),d=.4).start(f)
				Animation(x=((-500)-((self.pantofel.width)/2)),d=.4).start(self.pantofel)
				a=Animation(y=(self.FLarrow.y-1000*params.scale),d=.4)
				a.bind(on_complete=self.getback)
				a.start(self.FLarrow)
			
		
	def getback(self,*ignore):
		parent = self.parent
		parent = self.parent
		parent.clear_widgets()
		parent.add_widget(Menu_Main())	

#News segment, which get titles and articles generated while clicking menu button (they are scrapped from science-oriented websites) and load it to 

class Menu_News(Widget):
	#tile : 0index,1top,2body,3bot,4title,5article
	def __init__(self,sources):
		super(Menu_News, self).__init__()
		self.touch_move_list=[]
		self.tile={}
		self.title = "News"
		self.FLarrow = UI_Btn('./ui/icons/Larrow.png', './ui/icons/LarrowED.png')
		self.FLarrow.size = self.FLarrow.size[0]*2,self.FLarrow.size[1]*2
		self.FLarrow.center = ((centerx-890 * params.scale)), centery
		self.FLarrow.bind(on_press=self.back)
		self.sources = Label(text="", font_name="./fonts/CaviarDreams", font_size=(150 * params.scale),width=800 * params.scale, halign="center", markup=True,color=(1,1,1,1))
		lines = 1
		for x in sources:
			lines = lines +1
			self.sources.text = self.sources.text + x +"\n"
		self.sources.size_hint_y= None
		self.sources.text_size= self.sources.width, None
		self.sources.height= self.height*lines
		self.sources.center_x = centerx 
		self.sources.y=Window.height-self.sources.height-1460*params.scale
		self.bg = UI_Sprite(source="./ui/backgrounds/news.png", a=1)
		self.bg.allow_stretch = True
		self.bg.keep_ratio = False
		self.bg.size_hint =(None,None)
		self.loading = Label(text="", font_name="./fonts/CaviarDreams", font_size=(150 * params.scale),width=800 * params.scale, halign="center", markup=True,color=(1,1,1,1))
		self.loading.center = centerx,centery
		self.loading.text=tekst("nloader")
		self.bg.size=Window.size
		self.every=[self.sources]
		self.outputs=[]
		self.hypertext=[]		
		self.add_widget(self.bg)
		self.add_widget(self.FLarrow)
		self.add_widget(self.sources)
		self.add_widget(self.loading)
		win.bind(on_keyboard=self.softback)

		titles=[]
		self.articles=[]
		self.links=[]
		try:
			feed = feedparser.parse("http://feeds.feedburner.com/AllDiscovermagazinecomContent")
			feed_title = feed['feed']['title']
			feed_entries = feed.entries
			dt = parse(feed["updated"][5:16])
			clean = re.compile('<.*?>')
			x=0			
			for entry in feed.entries:
					x=x+1
					article_title = entry.title
					article_detail = entry.summary_detail["value"]
					formated= (article_detail).replace("\n","")
					titles.append(entry.title)
					article = re.sub(clean, '', formated) + "..."
					lnk=entry.links[0]['href']
					self.articles.append(article)
					self.links.append(lnk)
			
			self.remove_widget(self.loading)
			self.ttl = titles
		except:
			self.loading.text=tekst("timeout")
			
		if self.loading.text!=tekst("timeout"):
			if str(dt.date())>str(newstand["date"]["id"]):
				newstand.put('date',id=str(dt.date()))
				newstand.put('unews',id=[])
				
			if titles != []:
				for x in range(len(titles)):
					
						self.tile[titles[x]]=[x+1,UI_Sprite(source="./news/ntop.png"),UI_Sprite(source="./news/nbody.png"),
						UI_Sprite(source="./news/nbot.png"),
						Label(text=titles[x],color=(0,0,0,1),halign="center",width=UI_Sprite(source="./news/ntop.png").width-100*params.scale,max_lines=1),
						TextInput(text=self.articles[x],autoindent = True,valign="top",cursor_color = (0,0,0,0),foreground_color=(0,0,0,1),background_color=(0,0,0,0),selection_color=(0,0,0,0),font_size=45*params.scale),
						Button(text=self.links[x],color=(0,0,0,1),background_color=(0,0,0,0),font_size=30*params.scale)]
						top =self.tile[titles[x]][1]
						body = self.tile[titles[x]][2]
						bot = self.tile[titles[x]][3]
						label = self.tile[titles[x]][4]
						text = self.tile[titles[x]][5]
						link =  self.tile[titles[x]][6]
						text.size_hint=(None,None)
						text.readonly = True
						body.allow_stretch = True
						body.keep_ratio = False
						body.size_hint =(None,None)
						text.width=	body.width
						text.height=400*params.scale
						body.height=text.height
						
						if x == 0 :
							top.y = Window.height-top.height-self.sources.height+130*params.scale-1460*params.scale
						else:
							top.y = old1-(180*params.scale)
						body.center_x=centerx	
						self.every.append(top)
						self.every.append(body)
						self.every.append(bot)
						self.every.append(label)
						self.every.append(text)
						self.every.append(link)
						self.outputs.append(text)
						self.hypertext.append(link)
						top.x = body.x
						label.size=top.size
						bot.x=body.x
						body.y=top.y-body.height
						bot.y=body.y-bot.height
						old1=bot.y
						label.pos=top.pos
						text.pos=body.pos
						text.width=body.width	
						link.size=bot.size
						link.pos=bot.pos
						if not titles[x] in newstand["unews"]["id"]:
							text.text = ""
							link.text=""
							buybtn=UI_Btn('./ui/icons/helix.png','./ui/icons/helixed.png')
							buybtn.ntitle = titles[x]
							buybtn.nr = x
							buybtn.center = body.center_x,body.center_y-30*params.scale
							buybtn.bind(on_press=self.unlock)
							self.every.append(buybtn)
						z=1
						while z<7:
							self.add_widget(self.tile[titles[x]][z])
							z=z+1
							
						if not titles[x] in newstand["unews"]["id"]:
							self.add_widget(buybtn)
							
						for x in range(len(self.every)):
							wget = self.every[x]
							Animation(y=wget.y + 1460 * params.scale, t="in_sine",duration=1).start(wget)
					
	def unlock(self,obj):
		if usedsave["helix"]["id"] >= 1:
			obj.unbind(on_press=self.unlock)
			hlx = usedsave["helix"]["id"] -1
			newnews = newstand["unews"]["id"]
			newnews.append(self.ttl[obj.nr])
			newstand.put('unews',id=newnews)
			usedsave.put('helix',id=hlx)
			self.outputs[obj.nr].text = self.articles[obj.nr]
			self.hypertext[obj.nr].text = self.links[obj.nr]
			GameApp.body.meter.update()
			self.remove_widget(obj)
			
	def back(self,*ignore):
		parent = self.parent
		parent = self.parent
		parent.clear_widgets()
		parent.add_widget(Menu_Main())
	
	def softback(self,window, key, *largs):
			if key == 1001:
				win.unbind(on_keyboard=self.back)
				parent = self.parent
				parent = self.parent
				parent.clear_widgets()
				parent.add_widget(Menu_Main())
			
	def on_touch_move(self, touch):
			self.touch_move_list.append(touch.y)
			try:
				for x in range(len(self.every)):
					self.every[x].center_y = self.every[x].center_y+(float(self.touch_move_list[-1])-float(self.touch_move_list[-2]))
			except:
					pass
					
	def on_touch_up(self,touch):
		self.touch_move_list=[]

#Segment covering stats and level completion, can also display ranks and connect to google play services (to be added)
       				
class Menu_Stats(Widget):
		def __init__(self):
			super(Menu_Stats, self).__init__()

			self.bg = UI_Sprite(source='./ui/menus/bgstats.png', a=1)
			self.bg.center = (centerx, (540 - 1080) * params.scale)
			self.fg = UI_Sprite(source='./ui/menus/fgstats.png', a=1)
			self.fg.allow_stretch = True
			self.fg.keep_ratio = False
			self.fg.size_hint =(None,None)
			self.fg.size 	= Window.size
			self.bg.allow_stretch = True
			self.bg.keep_ratio = False
			self.bg.size_hint =(None,None)
			self.bg.size 	= Window.size
			self.fg.center = (centerx, (540 - 1080) * params.scale)
			

			self.darrow = UI_Btn('./ui/icons/Darrow.png', './ui/icons/DarrowED.png')
			self.mainlbl = Button(text=usedsave["name"]["id"], font_name="./fonts/CaviarDreams", font_size=(180 * params.scale),
								 size=(10 * params.scale, 100 * params.scale), halign="center", markup=True,
								 color=(rgba(62, 253, 102, 1)),background_color=(0,0,0,0))
			self.mainlbl.bind(on_press=self.user)
			self.darrow.center = (centerx + 15 * params.scale, (100 - 1080) * params.scale)
			self.darrow.bind(on_press=self.back)
			self.mainlbl.center = (centerx, (970 - 1080) * params.scale)
			self.ach = Label(text=tekst("Achv"), font_name="./fonts/CaviarDreams", font_size=(120 * params.scale),
							 size=(10 * params.scale, 100 * params.scale), halign="center", markup=True,
							 color=(rgba(62, 253, 102, 1)))
			self.rank = Label(text=tekst("Rank"), font_name="./fonts/CaviarDreams", font_size=(80 * params.scale),
							  size=(10 * params.scale, 100 * params.scale), halign="center", markup=True,
							  color=(rgba(62, 253, 102, 1)))
			self.aws = Label(text=tekst("Aws"), font_name="./fonts/CaviarDreams", font_size=(80 * params.scale),
							 size=(10 * params.scale, 100 * params.scale), halign="center", markup=True,
							 color=(rgba(62, 253, 102, 1)))
			self.ach.center = (centerx + 480 * params.scale, (710 - 1080) * params.scale)
			self.cico = UI_Sprite(source='./ui/icons/games.png', a=1)
			self.connect = Label(text=tekst("PlayGames"), font_name="./fonts/CaviarDreams", font_size=(80 * params.scale),
								 size=(10 * params.scale, 100 * params.scale), halign="center", markup=True,
								 color=(rgba(62, 253, 102, 1)))
			self.connect.center = (centerx + 520 * params.scale, (570 - 1080) * params.scale)
			self.cback = UI_Btn('./ui/icons/acvbg.png', './ui/icons/acvbgp.png')
			self.cback.center = (centerx + 480 * params.scale, (570 - 1080) * params.scale)
			self.cico.center = (centerx + 240 * params.scale, self.connect.center_y)
			self.cico.size = (130 * params.scale, 150 * params.scale)	
			self.rank.center = (centerx + 480 * params.scale, (170 - 1080) * params.scale)
			self.rback = UI_Btn('./ui/icons/acvbg.png', './ui/icons/acvbgp.png')
			self.rico = UI_Sprite(source='./ui/icons/rank.png', a=1)
			self.rico.center = (centerx + 230 * params.scale, self.rank.center_y)
			self.rback.center = self.rank.center

			self.aws.center = (centerx + 480 * params.scale, (370 - 1080) * params.scale)
			self.aback = UI_Btn('./ui/icons/acvbg.png', './ui/icons/acvbgp.png')
			self.aico = UI_Sprite(source='./ui/icons/award.png', a=1)
			self.aback.center = self.aws.center
			self.aico.center = (centerx + 230 * params.scale, self.aws.center_y)
			self.details()
			self.every = [self.bg,  self.fg,self.pbar, self.prgbar, self.hbar, self.lbar,self.cover, self.mainlbl,
						  self.darrow, self.prg, self.rank, self.connect, self.aws, self.ach, self.pcount, self.hcount,
						  self.lcount, self.ach, self.rback, self.aback, self.cback, self.cico, self.aico, self.rico,]
			for x in (self.every):
				self.introanim(x)
				try:
					self.add_widget(x)
				except:
					pass
			win.bind(on_keyboard=self.softback)

		def user(self,*ignore):
			self.skillbg = UI_Sprite(source='./ui/menus/skillui.png', a=1)
		
		def details(self,*ignore):
			
			seqlvl  = seq_glyco+seq_krebs
			lvlcount = 0
			helixcount = 0
			pointscount = 0
			for x in seqlvl:
				if usedscore.exists(x) == True:
					helixcount = helixcount + usedscore[x]["awards"][0]+usedscore[x]["awards"][1]+usedscore[x]["awards"][2]
					lvlcount = lvlcount +1
					
			completion = lvlcount + helixcount
			self.completed = int((float(completion) / (float(total))) * 100)
			self.helixed = float(helixcount) / (float(allhelix))
			self.pointed = float(helixcount) / (float(alllvls)*3)
			self.lvled = float(lvlcount) / float(alllvls)		
			self.cover = UI_Sprite(source='./ui/menus/detailed.png')
			self.prg = Label(text=(tekst("Prg") + ":" + (str(self.completed) + "%")), font_name="./fonts/CaviarDreams",font_size=(120 * params.scale), size=(10 * params.scale, 100 * params.scale), halign="center", markup=True, color=(rgba(62, 253, 102, 1)))
			self.hcount = Label(text="Levels: " + (str(pantonfo["lvl"]["id"]) + "/" + str(15)), font_name="./fonts/CaviarDreams", font_size=(80 * params.scale), size=(10 * params.scale, 100 * params.scale),halign="center", markup=True, color=(rgba(62, 253, 102, 1)))
			self.pcount = Label(text=tekst("Pts") + (str(helixcount))+"/"+str((alllvls)*3), font_name="./fonts/CaviarDreams",font_size=(80 * params.scale), size=(10 * params.scale, 100 * params.scale),  halign="center", markup=True, color=(rgba(62, 253, 102, 1)))
			self.lcount = Label(text=(tekst("Lvls") + ":" + (str(lvlcount) + "/" + str(alllvls))),font_name="./fonts/CaviarDreams", font_size=(80 * params.scale),size=(10 * params.scale, 100 * params.scale), halign="center", markup=True, color=(rgba(62, 253, 102, 1)))
			self.pbar =UI_Sprite(source='./ui/menus/scorebar.png', a=1)
			self.prgbar = UI_Sprite(source='./ui/menus/scorebar.png', a=1)
			self.hbar = UI_Sprite(source='./ui/menus/scorebar.png', a=1)
			self.lbar = UI_Sprite(source='./ui/menus/scorebar.png', a=1)
			self.bars=[self.pbar,self.prgbar,self.hbar,self.lbar]
			for f in self.bars:
				f.allow_stretch = True
				f.keep_ratio = False
				f.size_hint =(None,None)
				f.size=(43*params.scale,43*params.scale)
			self.cover.center = (centerx - 500 * params.scale, (380 - 1080) * params.scale)
			self.prg.center = (centerx - 480 * params.scale, (710 - 1080) * params.scale)
			self.pcount.center = (centerx - 470 * params.scale, (340 - 1080) * params.scale)
			self.lcount.center = (centerx - 470 * params.scale, (500 - 1080) * params.scale)
			self.hcount.center = (centerx - 470 * params.scale, (180 - 1080) * params.scale)
			self.pbar.center = (centerx - 820 * params.scale, (270 - 1080) * params.scale)
			self.prgbar.center = (centerx - 820 * params.scale, (590 - 1080) * params.scale)
			self.hbar.center = (centerx - 820 * params.scale, (100 - 1080) * params.scale)
			self.lbar.center = (centerx - 820 * params.scale, (430 - 1080) * params.scale)
			self.apbar = Animation(width=(709 * self.pointed) * params.scale, t="in_sine",duration=1).start(self.pbar)
			self.aprgbar = Animation(width=(((709 * (float(self.completed))) / 100) * params.scale),t="in_sine", duration=1).start(self.prgbar)
			self.ahbar = Animation(width= ((709 *(pantonfo["lvl"]["id"]/15)) * params.scale), t="in_sine",duration=1).start(self.hbar)
			self.albar = Animation(width=((709 * self.lvled) * params.scale), t="in_sine",duration=1).start(self.lbar)
		
		def back(self, *ignore):
			self.darrow.unbind(on_release=self.back)
			parent = self.parent
			parent.add_widget(Menu_Main(startup=True), index=100)
			for x in range(len(self.every)):
				self.delanim(self.every[x])
			Clock.schedule_once(self.delme, .4)
			
		def softback(self,window, key, *largs):
			if key == 1001:
				win.unbind(on_keyboard=self.softback)
				self.darrow.unbind(on_release=self.back)
				parent = self.parent
				parent.add_widget(Menu_Main(), index=100)
				for x in range(len(self.every)):
					self.delanim(self.every[x])
				Clock.schedule_once(self.delme, .3)
				
		def introanim(self,obj):
			Animation(center_y=obj.center_y + 1080 * params.scale, t="in_sine", duration=.15).start(obj)
			
		def delanim(self, obj):
			Animation(center_y=obj.center_y - 1080 * params.scale, t="in_sine", duration=.3).start(obj)

		def delme(self, *ignore):
			parent = self.parent
			parent.remove_widget(self)

#Settings segment, where you can choose your language, turn on/off sounds and see credits

class Menu_Config(Widget):
		def __init__(self):
			super(Menu_Config, self).__init__()
			
			self.bg = UI_Sprite(source='./ui/menus/bgsett.png', a=1)
			self.bg.allow_stretch = True
			self.bg.keep_ratio = False
			self.bg.size_hint =(None,None)
			self.bg.size=Window.size
			self.bg.center_x = centerx
			self.bg.y = -1080 * params.scale
			self.mainlbl = Label(text=tekst("Sett"), font_name="./fonts/CaviarDreams", font_size=(180 * params.scale),
									size=(10 * params.scale, 100 * params.scale), halign="center", markup=True,
									color=(rgba(62, 253, 102, 1)))
			self.langlbl = Label(text=tekst("Lang"), font_name="./fonts/CaviarDreams", font_size=(100 * params.scale),
									size=(10 * params.scale, 100 * params.scale), halign="center", markup=True,
									color=(rgba(62, 253, 102, 1)))
			self.darrow = UI_Btn('./ui/icons/Darrow.png', './ui/icons/DarrowED.png')
			self.sfx = UI_ToggleSett(tekst("SFX"), "", "Config")
			self.music = UI_ToggleSett(tekst("MUSIC"), "", "Config")
			self.vib = UI_ToggleSett(tekst("VIB"), "", "Config")
			self.music.size = (450 * params.scale, 150 * params.scale)
			self.vib.size = (650 * params.scale, 150 * params.scale)
			self.sfx.center_x = centerx - 650 * params.scale
			self.music.center_x = centerx + 650 * params.scale
			self.vib.center_x = centerx - 50 * params.scale
			self.ru = UI_ToggleSett("Pусский", "Lang", "Lang")
			self.pl = UI_ToggleSett("Polski", "Lang", "Lang")
			self.en = UI_ToggleSett("English", "Lang", "Lang")
			self.fr = UI_ToggleSett("Français", "Lang", "Lang")
			self.de = UI_ToggleSett("Deutsch", "Lang", "Lang")
			self.es = UI_ToggleSett("Español", "Lang", "Lang")

			if langchoice == "ru":
				self.ru.state = "down"
			elif langchoice == "eng":
				self.en.state = "down"
			elif langchoice == "pl":
				self.pl.state = "down"
			elif langchoice == "fr":
				self.fr.state = "down"
			elif langchoice == "de":
				self.de.state = "down"
			elif langchoice == "es":
				self.es.state = "down"

			self.ru.center_x = centerx - 780 * params.scale
			self.pl.center_x = centerx - 500 * params.scale
			self.en.center_x = centerx - 190 * params.scale
			self.fr.center_x = centerx + 170 * params.scale
			self.de.center_x = centerx + 490 * params.scale
			self.es.center_x = centerx + 800 * params.scale

			self.darrow.center = (centerx, -290 * params.scale)
			self.langlbl.center = (centerx, -750 * params.scale)
			self.mainlbl.center = (centerx, -130 * params.scale)
			self.darrow.bind(on_release=self.back)

			self.delanim = Animation(y=-1080 * params.scale, t="in_sine", duration=.3)
			self.introbg = Animation(y=0, t="in_sine", duration=.15)
			self.introlang = Animation(center_y=170 * params.scale, t="in_sine", duration=.15)
			self.introcfg = Animation(center_y=565 * params.scale, t="in_sine", duration=.15)
			self.introlanglbl = Animation(center_y=330 * params.scale, t="in_sine", duration=.15)
			self.intromainlbl = Animation(center_y=950 * params.scale, t="in_sine", duration=.15)
			self.introarrow = Animation(center_y=790 * params.scale, t="in_sine", duration=.15)

			self.add_widget(self.bg)
			self.add_widget(self.mainlbl)
			self.add_widget(self.langlbl)
			self.add_widget(self.darrow)
			self.add_widget(self.sfx)
			self.add_widget(self.music)
			self.add_widget(self.vib)
			self.add_widget(self.ru)
			self.add_widget(self.pl)
			self.add_widget(self.en)
			self.add_widget(self.fr)
			self.add_widget(self.de)
			self.add_widget(self.es)

			self.lang = [self.es, self.de, self.fr, self.en, self.pl, self.ru]
			self.cfg = [self.vib, self.music, self.sfx]
			self.every = [self.es, self.de, self.fr, self.en, self.pl, self.ru, self.vib, self.music, self.sfx, self.darrow,
						  self.mainlbl, self.langlbl, self.bg]

			for x in range(len(self.lang)):
				self.introlang.start(self.lang[x])
				self.lang[x].bind(on_press=self.langchange)

			for y in range(len(self.cfg)):
				self.introcfg.start(self.cfg[y])
			self.introlanglbl.start(self.langlbl)
			self.intromainlbl.start(self.mainlbl)
			self.introarrow.start(self.darrow)
			self.introbg.start(self.bg)
			win.bind(on_keyboard=self.softback)

		def langchange(self, value):
			global langchoice
			
			if value.text == "Pусский":
				langchoice = "ru"
			elif value.text == "English":
				langchoice = "eng"
				usedsave.put('lang',id=langchoice)
			elif value.text == "Polski":
				langchoice = "pl"
				usedsave.put('lang',id=langchoice)
			elif value.text == "Français":
				langchoice = "fr"
			elif value.text == "Español":
				langchoice = "es"
				usedsave.put('lang',id=langchoice)
			elif value.text == "Deutsch":
				langchoice == "de"
			else:
				pass
			if langchoice=="pl" or langchoice=="eng" or langchoice=="es":
				self.mainlbl.text=tekst("Sett")
				self.langlbl.text=tekst("Lang")
				self.sfx.text=tekst("SFX")
				self.music.text=tekst("MUSIC")
				self.vib.text=tekst("VIB")

		def back(self, *ignore):
			self.darrow.unbind(on_release=self.back)
			parent = self.parent
			parent.add_widget(Menu_Main(), index=100)
			for x in range(len(self.every)):
				self.delanim.start(self.every[x])
			Clock.schedule_once(self.delme, .3)
		
		def softback(self,window, key, *largs):
			if key == 1001:
				win.unbind(on_keyboard=self.softback)
				self.darrow.unbind(on_release=self.back)
				parent = self.parent
				parent.add_widget(Menu_Main(), index=100)
				for x in range(len(self.every)):
					self.delanim.start(self.every[x])
				Clock.schedule_once(self.delme, .3)
			
		def delme(self, *ignore):
			parent = self.parent
			parent.remove_widget(self)

#Greeting tab where player set their name and choos save file
	
class Creator(Widget):
	def __init__(self):

		super(Creator, self).__init__()
		self.choosed = ""
		self.bg = UI_Sprite(source='./ui/backgrounds/lvl1.png', a=1)
		self.bg.allow_stretch = True
		self.bg.keep_ratio = False
		self.bg.size_hint =(None,None)
		self.bg.size=Window.size
		self.bg.center_x = centerx
		self.black=UI_Sprite(source="./ui/game/black25.png",a=0.1)
		self.black.allow_stretch = True
		self.black.keep_ratio = False
		self.black.size_hint =(None,None)
		self.black.size=Window.size
		self.black.center_x = centerx
		self.tile1=[UI_Sprite(source='./news/ntop.png', a=1),UI_Sprite(source='./news/nbody.png', a=1),UI_Sprite(source='./news/nbot.png', a=1)]
		self.tile2=[UI_Sprite(source='./news/ntop.png', a=1),UI_Sprite(source='./news/nbody.png', a=1),UI_Sprite(source='./news/nbot.png', a=1)]
	#	self.tile1.center=centerx,centery
	#	self.tile2.center=centerx+Window.width,centery
		self.tiles = [self.tile1,self.tile2]

		self.add_widget(self.bg)
		self.add_widget(self.black)
		
			
		for a in self.tiles:
			a[1].allow_stretch = True
			a[1].keep_ratio = False
			a[1].size_hint =(None,None)
			a[1].height = 400*params.scale
			a[1].center = centerx,centery
			a[2].y = a[1].y-a[2].height
			a[0].y= a[1].top
			a[2].x=a[0].x=a[1].x
			
		for c in self.tile2:
			c.x=c.x+Window.width
		for a in self.tiles:	
			for y in a:
				self.add_widget(y)
	#	self.add_widget(self.tile1)
	#	self.add_widget(self.tile2)
		self.name()
	
	def name(self):
		self.student = Label(text="Hello fellow student!", font_name="./fonts/CaviarDreams", font_size=(160 * params.scale),size=(800 * params.scale, 100 * params.scale), halign="center", markup=True,color=(0,0,0,1))		
		self.box =TextInput(hint_text ="Enter your Nickname",multiline=False, font_name="./fonts/CaviarDreams",cursor_color = rgba(0, 0, 0, 0),font_size=130*params.scale,background_color = (1,1,1,0),foreground_color=(0,0,0,1))
		self.Rarrow = UI_Btn('./ui/icons/Rarrow.png', './ui/icons/RarrowED.png')
		self.Rarrow.bind(on_release=self.next)
		self.Rarrow.size=self.Rarrow.size[0]*2,self.Rarrow.size[1]*2
		self.Rarrow.center = ((centerx+ (890 * params.scale)), centery)
		self.student.center = (centerx,centery+150*params.scale)
		self.box.size=1200*params.scale,500*params.scale
		self.box.center=centerx+10*params.scale,centery-250*params.scale
		self.aname=[self.box,self.Rarrow,self.student]
		self.add_widget(self.box)
		self.add_widget(self.student)
		self.add_widget(self.Rarrow)
	
	
	def fnext(self,*ignore):
		self.box.text =""
		for a in self.aname:
			self.remove_widget(a)
	
	def fprev(self,*ignore):
		for a in self.wel:
			self.remove_widget(a)
	
	def next(self,*ignore):
		if self.box.text == "":
			self.box.hint_text="Name not entered"
		else:
			player.put('name',id=self.box.text)
			self.welcome()
			self.st = self.aname+self.tile1+self.tile2+self.wel
			for a in self.st:
				nexsec= Animation(x=a.x-Window.width,duration=0.6,t="out_sine") 
				nexsec.bind(on_complete=self.fnext)
				nexsec.start(a)
					
	def prev(self,*ignore):
		player.put('name',id="")
		for a in range(len(self.aname)):
			self.aname[a].x=self.aname[a].x
			self.add_widget(self.aname[a])
		self.atname = self.aname+self.tile1+self.tile2+self.wel
		for a in self.atname:
			nexsec= Animation(x=a.x+Window.width,duration=0.6,t="out_sine") 
			nexsec.bind(on_complete=self.fprev)
			nexsec.start(a)
		
		
	def fade(self,*ignore):
		usedsave = player
		self.fader=UI_Sprite(source="./ui/game/black100.png",a=0)
		self.fader.allow_stretch = True
		self.fader.keep_ratio = False
		self.fader.size_hint =(None,None)
		self.fader.size=Window.size
		self.add_widget(self.fader)
		fade = Animation(color=[1,1,1,1],duration=0.4,t="out_sine")
		fade.bind(on_complete=self.openmenu)
		fade.start(self.fader)
		parent = self.parent
	
	def openmenu(self,*ignore):
		base = Menu_Main()
		prime=self.parent
		self.parent.clear_widgets()
		prime.add_widget(base)
		
		
	def welcome(self,*ignore):
		self.wlab = Label(text="Welcome in \nKnow|Edge Bio\n", font_name="./fonts/CaviarDreams", font_size=(170 * params.scale),size=(800 * params.scale, 100 * params.scale), halign="center", markup=True,color=(0,0,0,1))
		self.nick = Label(text=player["name"]["id"], font_name="./fonts/CaviarDreams", font_size=(170 * params.scale),size=(800 * params.scale, 100 * params.scale), halign="center", markup=True,color=(rgba(100, 100, 100, 1)))
		
		self.wlab.center = ((centerx+Window.width)), centery+10*params.scale 
		self.nick.center = ((centerx+Window.width)), centery-170*params.scale 
		self.start=Button(text="START",background_color=(0, 0, 0,0),color=(1, 1, 1, 1),font_name="./fonts/CaviarDreams",font_size=250*params.scale)
		self.FLarrow = UI_Btn('./ui/icons/Larrow.png', './ui/icons/LarrowED.png')
		self.FLarrow.size = self.FLarrow.size[0]*2,self.FLarrow.size[1]*2
		self.FLarrow.center = ((centerx-890 * params.scale+Window.width)), centery
		self.start.center=centerx+Window.width,centery-420*params.scale
		self.wel=[self.FLarrow,self.wlab,self.start,self.nick]
		self.FLarrow.bind(on_press=self.prev)
		self.start.bind(on_press=self.fade)
		self.add_widget(self.FLarrow)
		self.add_widget(self.start)
		self.add_widget(self.nick)
		self.add_widget(self.wlab)

#Class which adds fade while opening app
			
class Intro(Widget):
	def __init__(self):
		super(Intro, self).__init__()
		#if config.exists("res") == False:
		#	Clock.schedule_once(self.builder,5)
		#else:
		#	Window.size=config["res"]["id"]
		self.builder()
		
	def builder(self,*ignore):
		self.wdh = win.width
		global x, y, centerx, centery
		x, y = win.size
	#	if config.exists("res") == False:
		#	config.put("res",id=Window.size)
		centerx = (int(x) / 2)
		centery = (int(y) / 2)
		params.init()
		debug = False
		ct = "M"
		lv = "1"
		self.base =Widget()
		
		if debug == True:
			Pparams = lvl_lib[ct][ct+lv+"FULL"]
			Pparams[0] =lvl_lib[ct][ct+lv]
			Pparams[1] =lvl_lib[ct][ct+lv+"DRAG"]
			self.mainwin = Game(*Pparams)
		
		else:
			if usedsave == ""  :
				self.mainwin = Creator()
			else:
				self.mainwin =Menu_Main()
		
		self.meter = UI_Helix_Meter()
		self.base.add_widget(self.mainwin)
		self.add_widget(self.base)
		self.add_widget(self.meter)

#Main app class, which sets windowsize while in production, changes android back button functionality and starts whole app
		
class Bio(App):
	
	def build(self):
		if platform != 'android':
			self.debug("S")
		self.bind(on_start=self.post_build_init)
		self.head = Widget()
		self.body=Intro()
		self.head.add_widget(self.body)
		return self.head

	def post_build_init(self, *args):
		if platform == 'android':
			import android
			android.map_key(android.KEYCODE_BACK, 1001)
		win.bind(on_keyboard=self.callbacker)
		
	def callbacker(self,window, key, *largs):
		pass
			
	def debug(self,sze):
		if sze== "XXS":
			Window.size = (320, 180)
		elif sze== "XS":
			Window.size = (640, 360)
		elif sze== "WRDF":
			Window.size = (1100, 720)
		elif sze== "S":
			Window.size = (854, 480)
		elif sze == "WS":
			Window.size = (960, 480)	
		elif sze == "M":
			Window.size = (1280, 720)
		elif sze == "WM":
			Window.size = (1440, 720)
		elif sze == "L":
			Window.size = (1920, 1080)
		elif sze == "WL":
			Window.size = (2160, 1080)	
		elif sze == "laptop":
			Window.size = (1366, 768)	


			
Config.set('kivy','exit_on_escape', '0')
Config.write()
win = Window
if platform == 'android':
	win.maxfps=60
	win.borderless=True
GameApp = Bio()
GameApp.run()


