#!/APSshare/anaconda3/x86_64/bin/python3

import re
import sys
import socket

from subprocess import Popen, PIPE

from tkinter import *

from epics import PV

ALIVEDB = "/APSshare/bin/alivedb"


s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
my_ip = s.getsockname()[0]

my_subnet = my_ip.rsplit(sep=".", maxsplit=1)[0]
my_subnet = my_subnet.replace(".", "\.")
my_subnet = my_subnet + "\.\d+"

is_ioc = re.compile(b"(.*) \((\d+\.\d+\.\d+\.\d+)\) \d \- (Up|Down) .*")
subnet_match = re.compile(my_subnet.encode())

proc = Popen([ALIVEDB, "."], stdout=PIPE)
output = proc.communicate()[0]

ioc_list = {}


for line in output.split(b'\n'):	
	potential = is_ioc.match(line)
	
	if potential:
		same_net = subnet_match.match(potential.group(2))
		
		if same_net:
			arch_test = Popen([ALIVEDB, potential.group(1).decode() ,"-e", "ARCH"], stdout=PIPE)
			arch = arch_test.communicate()[0].decode()
			
			if "linux" in arch:
				ioc_list[potential.group(1)] = potential.group(2)
	
	
class IOCLine(Frame):
	
	def disconnect(self):
		if self.pv:
			self.pv.disconnect()
		
		self.connected = False
	
	def connect(self):
		get_prefix = Popen([ALIVEDB, self.name, "-e", "STY"], stdout=PIPE)
		prefix_info = get_prefix.communicate()[0].decode()
		
		prefix_info = prefix_info.strip()
		
		alive_pv = ""
		
		if (prefix_info):
			alive_pv = prefix_info.split(".")[1] + ":alive"
		else:
			alive_pv = self.name.replace("ioc", "", 1) + ":alive"
		
		self.pv = PV(alive_pv, connection_callback=self.connection_monitor)
			
	def connection_monitor(self, **kws):
		if kws["conn"]:
			self.connected = True
			self.host.config(text=self.pv.host)
		else:
			self.connected = False
	
	def update_visual(self):
		if self.connected:
			self.connection.config(text="Alive", fg="sea green")
		else:
			self.connection.config(text="Disconnected", fg="red")
		
		self.master.after(250, self.update_visual)
	
	def __init__(self, master, name):
		Frame.__init__(self, master)
	
		self.name = name.decode().strip()
		self.pv = None
		self.connected = False
		
		self.index = Label(self, width=25, text=self.name)
		self.index.grid(row=0, column=0, padx=(5,0), pady=(0,5))
		
		self.connection = Label(self, width=20)
		self.connection.grid(row=0, column=1, padx=(0,5), pady=(0,5))
		
		self.host = Label(self, width=40)
		self.host.grid(row=0, column=2, padx=(0,5), pady=(0,5))
		
		self.connect()
		self.update_visual()

		
		
class Application(Frame):
	def on_exit(self):
		for each in self.lines:
			each.disconnect()
			
		self.quit()
		
	def add_line(self, ioc):
		self.lines.append(IOCLine(self, ioc))
		self.next_row = self.next_row + 1
		
		self.lines[len(self.lines) - 1].grid(row=self.next_row, column=0)
		
	def __init__(self, master=None, ioc_list=[]):
		Frame.__init__(self, master)
		
		master.protocol("WM_DELETE_WINDOW", self.on_exit)
		master.title("IOC List")
		
		self.next_row = 0
		self.lines = []
		
		for ioc in ioc_list:
			self.add_line(ioc)
			
			
app = Application(master = Tk(), ioc_list=ioc_list)
app.pack()

app.mainloop()
