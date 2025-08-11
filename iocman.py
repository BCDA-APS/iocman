#!/APSshare/anaconda3/x86_64/bin/python3

import os
import re
import pwd
import sys
import copy
import glob
import time
import socket

import os.path

import configparser

from tkinter import *
from tkinter import font
import tkinter.messagebox

from epics import PV

import subprocess

master = Tk()
reload_icon = PhotoImage(data="iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAABhWlDQ1BJQ0MgcHJvZmlsZQAAKJF9kT1Iw1AUhU9bpSIVETuIiGRoO1kQFXHUKhShQqgVWnUweekfNGlIUlwcBdeCgz+LVQcXZ10dXAVB8AfEXXBSdJES70sKLWK88Hgf591zeO8+wN+oMNXsGgdUzTLSyYSQza0KwVf4MIoBRBGTmKnPiWIKnvV1T91Ud3Ge5d33Z/UpeZMBPoF4lumGRbxBPL1p6Zz3icOsJCnE58RjBl2Q+JHrsstvnIsO+3lm2Mik54nDxEKxg+UOZiVDJZ4ijiiqRvn+rMsK5y3OaqXGWvfkLwzltZVlrtMaQRKLWIIIATJqKKMCC3HaNVJMpOk84eEfdvwiuWRylcHIsYAqVEiOH/wPfs/WLExOuEmhBND9YtsfUSC4CzTrtv19bNvNEyDwDFxpbX+1Acx8kl5va5EjoH8buLhua/IecLkDDD3pkiE5UoCWv1AA3s/om3LA4C3Qu+bOrXWO0wcgQ7NK3QAHh0CsSNnrHu/u6Zzbvz2t+f0AqhtyvUx7a90AAAAGYktHRAD/AP8A/6C9p5MAAAAJcEhZcwAADdcAAA3XAUIom3gAAAAHdElNRQfpAR4RKRw9muMVAAABKklEQVQ4y6XTvS6EURAG4OdbywWIREGC+CkUGhp/N6Gg0OAClGoleu0KhcYFiAYJLReA+Alb6FiFAt9qRnLy2d1IvMnJOZkzc2be98xkfqOMAcygH194wHnsn1pgEDt4C8d6rE+8Yjd8GmIKV8gjKMdHrNR2h+mI6ciSzEex11HFPi4iaByL6EWGWyxh9YfzTjjmOAnuWVJdFrbjpJr3OBsOznU8hmMzjOA50SaHlRApx0Yhc4oeHBTEzUvoQ1t812VcFNGGOYwmooKSv+EL25jAJNZwiBdYTihstqBQRDu6YQi1KP0purAZGlZcRiX5ntN4pFQIHMA6Opu18E2i7hO2MI+FOFdDi0N0/aeVrzHWapgqoUlxmGrYKw5T1kSTfsxGj8A9zhqN8zen8GbXeKR36AAAAABJRU5ErkJggg==")
save_icon   = PhotoImage(data="R0lGODlhEAAQAMZ5ADNkpDZmpTpqp0Nwq1V4qVJ5rU96sFl5plh+r16ArlmBtWCCr2SCrGKDr2GDsmOEsoGBgWOFsl+GuGOGtWWGsmaHtWyHr2qJtWaLu2yKtWeMu2mMuW2RvnSRuY6OjnWTu5KSknSXwpOTkpOTk3mXwJSUlHmYwJWVlXqaw5eXl5mZmYicuZ2dnYWkyaGhoZGjvaSkpJimuqampqenp6ioqJyqvampqaqqqqurq6ysrK2tra6urq+vr7CwsLGxsbKysrW1ta63wq23xba2tri4uLK5w7m5ubu7u729vb6+vr++vcDAwMDBwsLCwsPDw8TExMXFxcHGzsbGxsjIyMPJ0cfJzMrKysvLy8vLzczMzMvN0c3Nzc3Nzs/Pz9HR0dPS0NbV1NbW1dbW1tjY2NXZ3dnZ2drZ2NrZ2dra2tvb293b2t3d3eDd2t/f3+Dg4OHh4eLh4OLi4uPk5eTk5OXk5OXl5ebl5eXm5ubm5v///////////////////////////yH5BAEKAH8ALAAAAAAQABAAAAe6gH+Cg4SFhRQfFwSGhRkmJC0oCYyGDCEblIJKamwvHBgrXF9MhlUWEQ8aEhMVB1oihD50ZB0KBgMCDlRmRoRLdXBRCwEACEJnaFeEYmtiYEUNBTFZXmNdNII3cWttaF5BNVhhaWVjQ4JQc21ucXh3cnZva2ltToJIW1ZTUk9NS0lIjhAhAkMQEBwpXNjQsePGjh40eOgYYZBIDhw8fPjQ4eMHDh88TghKIWMGDBYqUpQoAcKDSwiZKAUCADs=")
add_icon    = PhotoImage(data="R0lGODlhEAAQAMZsAA4TNRMZPxQaQxYbRRccSRceSxgeThshUxsiVBwjXR4lYR8lXx4lYyAmWx8nZh8naSAoaSMpWSIpbCQqZSQrYyQrZSUrYyUrZiUsZiYsaCYsaiYtaiYtayYtbCkvZSgvbicvcikvbykwcCkwcykxdCoxdSoxdioxdy0zbC0zbi00cC00dC40ci01dS41fS01gy82fi42hS83gC83gjA3gC83gy83hTA4hzU8hj1EkD1FlkJJmlRdyVVeyFVey1Zfyldfylhgy1hhy1pizVpjzFtkzlxkzl1l0F1mz15mz15m0F5m0V5n0V9nz19n0F9n0l9n02Bo0GBo0WBo0mBo02Fp0WFp0mNr02Nr1WRs1GRs1WVt1WVt1mZu1mdu1mdu12hv12hv2Gdw2Whw12px2Wtz2mxz2m103G5122923XF43XN64f///////////////////////////////////////////////////////////////////////////////yH5BAEKAH8ALAAAAAAQABAAAAeFgH+Cg38xL4SIhC8+PA+JiTY/QBCPiDVBQg6VhDNDRAybgzJFRgqPICYlJSQ6SU44IiEhHxN/LlBLTE9TUk1RVlhcXF1iCDRMTk5SUlXNV1lbW11gDX8LHRwbGjvPORgVFhYHjythYwWhgixkZATpfyplZgPvKWdoAu8ea2oA738RIjwKBAA7")
remove_icon = PhotoImage(data="R0lGODlhEAAQAMZrAMYJCbAPD8gJCccKCbMQD8cNDcQODcUODckNDb4TEtYNDcQSEtcNDdgNDcYSEb8UE74XFr8XFtQSEccXFtYTEsgXFtcTEtgTEdgTEr8aGcAaGbIgH7AhIdIYF9MYF78eHcwbGsEeHdgYF9oYF8wcGtkZGLMlJNMdHNQdHNoeHdseHdseHtUiINYiIdskItwkItcoJdgoJt0qJ9QtK781M9AxL9EyL7k5N8E3Nd4wLc80Mro6ONA1M884NtE5Nt82Mt82M+A3NL9BQMBCQNM9OtU+OuE7N+I7N8ZDQcdDQd0+Ot4+O8RFROM9OcZGRMVHRcZIReRAPOJBPcVJSORBPcdKSORDP+VDP91HRd5HRORGQuZGQuZJRedJRd1OS+ZMR95OS+dMR+dMSORPS+ZRTN5TUOBTUOBWUuJXU+ZYU+hZVP///////////////////////////////////////////////////////////////////////////////////yH5BAEKAH8ALAAAAAAQABAAAAevgH9/N0OChoZCO4Y0aWhVh4JTZ2o4fxxjYWFmUIdPZWJfZCZ/RFxaW2BOgkxeW1pdRYY9VlJRWUlIWFRSVz6QOk1GR0tKR0ZNPJCCNUFAP0BAQTbKhjM51zkzG9R/HzAy4DIxIdQZLC8u6S4vLRqQECcrKSokICrzKBGGCR0lIiMVBE0YIaKEhwd/AkiwQAGDg0MLLlCwIIHAnwINGBxQZkABAwSGBgjgBmAkt5OBAAA7")

COLUMN_1_WIDTH=25
COLUMN_2_WIDTH=25
COLUMN_3_WIDTH=40
COLUMN_4_WIDTH=20
COLUMN_5_WIDTH=10

MAX_INITIAL_LENGTH=15

def get_subnet():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("8.8.8.8", 80))
	my_ip = s.getsockname()[0]
	
	my_subnet = my_ip.rsplit(sep=".", maxsplit=1)[0]
	return my_subnet

def check_port(host, port):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	
	try:
		s.connect((host, port))
		return True
	except:
		return False
	

class AliveDB(object):
	_iocs = {}
	_ALIVEDB_LOC = "/APSshare/bin/alivedb"
	last_update_all = 0.0
	
	def parse(self, input, doprint=False):
		data = {}
		
		ioc = ""
		lines = ""
		
		new_ioc_match = re.compile(r"(.*) \((\d+\.\d+\.\d+\.\d+)\) \d \- (Up|Down|Conflict|Uncertain).*")
		
		for line in input:
			line_str = ""
			
			try:
				line_str = line.decode().strip()
			except:
				ioc = ""
				pass
				
			check_new_ioc = new_ioc_match.match(line_str)
			
			if check_new_ioc:
				if ioc != "":
					data[ioc] = lines
					
				ioc = check_new_ioc.group(1)
				lines = "[Info]\n"
				lines += "name = " + check_new_ioc.group(1) + "\n"
				lines += "ip = " + check_new_ioc.group(2) + "\n"
				lines += "status = " + check_new_ioc.group(3) + "\n"
				
			elif line_str.startswith("Environment Variables"):
				lines += "[Environment Variables]\n"
				
			elif line_str.endswith("Parameters"):
				lines += "[" + line_str.strip() + "]\n"
				
			elif line_str == "No Environment Variables recorded.":
				pass
				
			else:
				lines += line_str + "\n"
				
		data[ioc] = lines
				
		output = {}
		
		for ioc in data:
			config = None
			try:
				config = configparser.ConfigParser(allow_no_value=True)
				config.read_string(data[ioc])
			except:
				print(data[ioc])
				break
			
			output[ioc] = {}
				
			if "Info" in config:
				for key in config["Info"]:
					output[ioc][key] = config["Info"].get(key)
			
			if "Environment Variables" in config:
				output[ioc]["ARCH"]     = config["Environment Variables"].get("ARCH")
				output[ioc]["TOP"]      = config["Environment Variables"].get("TOP")
				output[ioc]["BASE"]     = config["Environment Variables"].get("EPICS_BASE")
				output[ioc]["SUPPORT"]  = config["Environment Variables"].get("SUPPORT")
				output[ioc]["ENGINEER"] = config["Environment Variables"].get("ENGINEER")
				output[ioc]["LOCATION"] = config["Environment Variables"].get("LOCATION")
				output[ioc]["GROUP"]    = config["Environment Variables"].get("GROUP")
				output[ioc]["STY"]      = config["Environment Variables"].get("STY")
				output[ioc]["PROCSERV"] = config["Environment Variables"].get("PROCSERV_INFO")
				output[ioc]["CONSOLE"]  = config["Environment Variables"].get("CONSOLE_INFO")
				output[ioc]["PREFIX"]   = config["Environment Variables"].get("PREFIX", config["Info"]["name"].removeprefix("ioc") + ":")
				
			if "vxWorks Boot Parameters" in config:
				for key in config["vxWorks Boot Parameters"]:
					output[ioc][key] = config["vxWorks Boot Parameters"].get(key)
			
			if "Linux Parameters" in config:
				for key in config["Linux Parameters"]:
					output[ioc][key] = config["Linux Parameters"].get(key)
						
			if "Windows Parameters" in config:
				for key in config["Windows Parameters"]:
					output[ioc][key] = config["Windows Parameters"].get(key)
					
		return output
		
	
	def update(self, ioc):
		output = subprocess.check_output([self._ALIVEDB_LOC, ioc]).splitlines()
		
		self._iocs.update(self.parse(output))
	
	def update_all(self):
		current_time = time.time()
		
		if (current_time - self.last_update_all < 120.0):
			return 
			
		self.last_update = current_time
		
		self._iocs = {}
		
		output = subprocess.check_output([self._ALIVEDB_LOC, "."]).splitlines()
		
		self._iocs.update(self.parse(output))

					
	def __getitem__(self, key):
		return self._iocs.get(key)
		
	def filter(self, subnet=None, arch=None):
		output = {}
		
		for iocname, ioc in self._iocs.items():
			add = True
			
			if arch and ioc["ARCH"] != arch:
				add = False
					
			if subnet and not ioc["ip"].startswith(subnet):
				add = False
				
			if add:
				output[iocname] = ioc
				
		return output


class LabelLine(Frame):
	def __init__(self, master, save_func=None, add_func=None):
		Frame.__init__(self, master)
		
		self.desc = Label(self, text="Description", width=COLUMN_1_WIDTH)
		self.desc.grid(row=0, column=0, padx=(5,0), sticky=NSEW)
		
		self.name = Label(self, text="IOC Name", width=COLUMN_2_WIDTH)
		self.name.grid(row=0, column=1, sticky=NSEW)
		
		label_font = font.Font(self.name, self.name.cget("font"))
		label_font.configure(underline=True)
		self.name.configure(font=label_font)
		self.desc.configure(font=label_font)
		
		label_font = font.Font(self.name, self.name.cget("font"))
		label_font.configure(underline=True)
		self.name.configure(font=label_font)
		
		self.host = Label(self, text="IOC Host", font=label_font, width=COLUMN_3_WIDTH)
		self.host.grid(row=0, column=3, sticky=NSEW)
		
		self.status = Label(self, text="Alive Status", font=label_font, width=COLUMN_4_WIDTH - 4)
		self.status.grid(row=0, column=4, sticky=NSEW)
		
		self.placeholder = Label(self, text="", width=COLUMN_5_WIDTH * 3 + 15)
		self.placeholder.grid(row=0, column=2, sticky=NSEW)
		
		self.saveConfig = Button(self, image=save_icon, command=save_func)
		self.saveConfig.grid(row=0, column=5, sticky=NSEW)
		
		self.addIOC = Button(self, image=add_icon, command=add_func)
		self.addIOC.grid(row=0, column=6, padx=(5,0), sticky=NSEW)
		
		
class IOCLine(Frame):
	
	def disconnect(self):
		self.destroyed = True
		self.pv.disconnect()
	
	def connect(self):		
		alive_pv = self.info["PREFIX"].strip() + "alive"
				
		self.pv = PV(alive_pv, connection_callback=self.connection_monitor)

	def info_update(self):
		self.master.iocs.update(self.info["name"])
		self.info = self.master.iocs[self.info["name"]]
		
		script_check = glob.glob(self.info["TOP"] + "/iocBoot/ioc*/softioc/" + self.info["name"].removeprefix("ioc") + ".pl")
		
		if len(script_check) == 0:
			script_check = glob.glob(self.info["TOP"] + "/iocBoot/ioc*/softioc/" + self.info["name"].removeprefix("ioc") + ".sh")
			
		if len(script_check) == 0:
			message = "Cannot find startup script (" + self.info["name"].removeprefix("ioc") + ".pl) for IOC\n\n"
			message += "Check for file system network issues\n"
			
			raise message
			
		if len(script_check) > 1:
			message = "Found multiple startup scripts ("  + self.info["name"].removeprefix("ioc") + ".pl) for IOC\n\n"
			message += "Check for file system issues"
			
			raise message
			
		self.script = script_check[0]
		self.command_file = None
		
		command_check = glob.glob(self.info["TOP"] + "/iocBoot/ioc*/softioc/" + self.info["name"] + "-command.txt")
		
		if len(command_check) > 1:
			message = "Found multiple files matching " + self.info["name"] + "-command.txt\n\n"
					
			for filepath in commands:
				message += "\t" + filepath + "\n"
						
			message += "\n"
			message += "Check IOC naming convention and folder structure."
			
			raise message
		
		if len(command_check) == 1:
			self.command_file = command_check[0]
			
			with open(self.command_file) as info:
				self.command_pid = info.readline().strip().split(":")[1]
				self.command_tcp, self.command_host, self.command_port = info.readline().strip().split(":")
				
		
	def connection_monitor(self, **kws):
		if self.pv:
			if kws["conn"]:
				self.hostname = self.pv.host
				self.connected = True
			else:
				self.hostname = ""
				self.connected = False

				
	def update_visual(self):
		if self.destroyed:
			return
		
		if self.connected:
			self.connection.config(text="Alive", fg="sea green")
			self.control.config(text="Stop", fg="red")
			self.host.config(text=self.hostname)
		else:
			self.connection.config(text="Disconnected", fg="red")
			self.control.config(text="Start", fg="sea green")
			self.host.config(text=self.hostname)
		
		self.master.after(250, self.update_visual)
		
	def console_pressed(self):
		try:
			self.info_update()
		except Exception as e:
			tkinter.messagebox.showinfo("Console", e)
			return
			
		if not self.connected:
			message = "IOC alive record not reachable\n\n"
			message += "If you believe the IOC should be starting up, you can proceed anyways."
			
			result = tkinter.messagebox.askokcancel("Console", message)
			
			if not result:
				return
		
		if not "PID" in self.info["PROCSERV"]:
			my_name = pwd.getpwuid(os.getuid()).pw_name
				
			if self.info["hostname"] != socket.gethostname() or self.info["user"] != my_name:
				ioc_userhost = self.info["user"] + "@" + self.info["hostname"]
				curr_userhost = my_name + "@" + socket.gethostname()
				
				message = "IOC running as " + ioc_userhost + "\n"
				message += "but ioc manager running as " + curr_userhost + "\n\n"
				message += "Use ssh to connect?"
				
				response = tkinter.messagebox.askokcancel("Console", message)
				
				if response:
					os.system("xterm -T '" + self.info["name"] + "console' -e ssh " + self.info["user"] + "@" + self.info["hostname"] + " '" + self.script + " console'")
				return
			
		os.system("xterm -T '" + self.info["name"] + " console' -e " + self.script + " console")
		
		
	def start_pressed(self):
		try:
			self.info_update()
		except Exception as e:
			tkinter.messagebox.showinfo("Start/Stop", e)
			return
			
		check_ok = True
			
		if not "PID" in self.info["PROCSERV"]:
			if self.connected:				
				my_name = pwd.getpwuid(os.getuid()).pw_name
				
				if self.info["hostname"] != socket.gethostname() or self.info["user"] != my_name:
					ioc_userhost = self.info["user"] + "@" + self.info["hostname"]
					curr_userhost = my_name + "@" + socket.gethostname()
					
					message = "IOC running as " + ioc_userhost + "\n"
					message += "but ioc manager running as " + curr_userhost + "\n\n"
					message += "Use ssh to connect?"
					
					response = tkinter.messagebox.askokcancel("Start/Stop", message)
					
					if response:
						os.system("xterm -T 'Stop IOC' -e ssh " + self.info["user"] + "@" + self.info["hostname"] + " '" + self.script + " stop'")
					return
		
		else:
			if not self.connected and not self.command_file:
				message = "IOC last ran using remote start, are you sure you want to start IOC without remote operation?"
			
				response = tkinter.messagebox.askokcancel("Start/Stop", message)
					
				if not response:
					return
					
				check_ok = False
					
			else:
				port_check = check_port(self.command_host, self.command_port)
			
				if not port_check:
					message = "IOC indicates a remote command console is running\n"
					message += "but cannot communicate with port.\n\n"
					message += "PID: "  + self.command_pid  + "\n"
					message += "Host: " + self.command_host + "\n"
					message += "Port: " + self.command_port + "\n\n"
					message += "Check network communications and host processes\n"
					message += "Otherwise, use 'Remote' to delete leftover file"
					
					tkinter.messagebox.showinfo("Start/Stop", message)
					return
						
		action = "start"
		
		if self.connected:
			action = "stop"
				
		if check_ok:
			message = "Are you sure you want to {} IOC?"
			response = tkinter.messagebox.askokcancel("Start/Stop", message.format(action))
			
			if response:
				os.system(self.script + " " + action)
		
			
	def remote_pressed(self):
		try:
			self.info_update()
		except Exception as e:
			tkinter.messagebox.showinfo("Remote Info", e)
			return
		
		if not self.command_file:
			if self.connected:
				if "PID" in self.info["PROCSERV"]:
					message = "IOC indicates command console should be available, but " + self.info["name"] + "-command.txt file not found\n\n"
					message += "\tIOC PROCSERV_INFO: " + self.info["PROCSERV"] + "\n\n"
					message += "Check for file system networking issues."
					
					tkinter.messagebox.showinfo("Remote Info", message)
					return
				
				else:
					message = "IOC running in screen session\n\n"
					message += "Close IOC before attempting to start remote control"
					
					tkinter.messagebox.showinfo("Remote Info", message)
					return
					
			elif self.info["status"] != "Down":
				message = "IOC states that it is running, but cannot connect to alive\n\n"
				message += "\tStatus = " + self.info["status"] + "\n"
				message += "\tIP = " + self.info["ip"] + "\n\n"
				
				message += "Check network connection or wait a bit for alive database to update (~1 min) before attempting to start remote control"
				tkinter.messagebox.showinfo("Remote Info", message)
				return
				
			elif not "rhel" in self.info["ARCH"] and not "linux" in self.info["ARCH"]:
				message = "IOC remote operation only currently enabled for linux architectures"
				tkinter.messagebox.showinfo("Remote Info", message)
				return
					
		else:
			message = "Remote control listed as\n\n"
			message += "PID: "  + self.command_pid  + "\n"
			message += "Host: " + self.command_host + "\n"
			message += "Port: " + self.command_port + "\n"
			
			message += "\n"
				
			port_check = check_port(self.command_host, self.command_port)
			
			if not port_check:
				message += "but cannot connect to listed port.\n"
				message += "Do you wish to delete command file?\n"
				message += "\tFile: " + self.command_file
				
				result = tkinter.messagebox.askokcancel("Remote Info", message)
				
				if result:
					os.system("xterm -T 'Delete file' -e rm " + self.command_file)
					
				return
					
			
			if self.connected:
				message += "Shut down IOC before disabling remote control"
				
				tkinter.messagebox.showinfo("Remote Info", message)
			else:				
				message += "\n"
		
				message += "Would you like to disable?"
				
				result = tkinter.messagebox.askokcancel("Remote Disable", message)
			
				if result:
					my_name = pwd.getpwuid(os.getuid()).pw_name
				
					if self.info["hostname"] != socket.gethostname() or self.info["user"] != my_name:
						os.system("xterm -T 'Remote Disable' -e ssh " + self.info["user"] + "@" + self.info["hostname"] + " '" + self.script + " remote disable'")
					else:
						os.system("xterm -T 'Remote Disable' -e " + self.script + " remote disable")
			return
		
		
		message = "Setup remote control of IOC?\n\n"
		message += "User: " + self.info["user"] + "\n"
		message += "Host: " + self.info["hostname"]
			
		result = tkinter.messagebox.askokcancel("Remote Control", message)
		
		if result:
			if not self.script.endswith(".pl"):
				message = "Check to make sure IOC is at least synApps 6-3 to use Remote start\n"
				
				tkinter.messagebox.showinfo("Remote Info", message)
				return
							
			my_name = pwd.getpwuid(os.getuid()).pw_name
				
			if self.info["hostname"] != socket.gethostname() or self.info["user"] != my_name:
				os.system("xterm -T 'Remote Enable' -e ssh " + self.info["user"] + "@" + self.info["hostname"] + " '" + self.script + " remote enable'")
			else:
				os.system("xterm -T 'Remote Enable' -e " + self.script + " remote enable")
				
	
	def remove_pressed(self):
		self.pv.disconnect()
		self.master.remove_line(self)
		
	def __init__(self, master, name, info, description=""):
		Frame.__init__(self, master)
	
		self.name = name.strip()
		self.info = info
		self.pv = None
		self.hostname = ""
		self.connected = False
		self.destroyed = False
		
		self.description = tkinter.StringVar()
		self.description.set(description)
		
		self.desc = Entry(self, width=COLUMN_1_WIDTH, textvariable=self.description)
		self.desc.grid(row=0, column=0, padx=(5,0), sticky=NSEW)
		
		self.index = Label(self, width=COLUMN_2_WIDTH, text=self.name)
		self.index.grid(row=0, column=1, sticky=NSEW)
		
		self.remote = Button(self, width=COLUMN_5_WIDTH, text="Remote", command=self.remote_pressed)
		self.remote.grid(row=0, column=2, padx=(0,5), sticky=NSEW)
		
		self.control = Button(self, width=COLUMN_5_WIDTH, text="Start", command=self.start_pressed, fg="sea green")
		self.control.grid(row=0, column=3, padx=(0,5), sticky=NSEW)
		
		self.console = Button(self, width=COLUMN_5_WIDTH, text="Console", command=self.console_pressed)
		self.console.grid(row=0, column=4, sticky=NSEW)
		
		self.host = Label(self, width=COLUMN_3_WIDTH)
		self.host.grid(row=0, column=5, sticky=NSEW)
		
		self.connection = Label(self, width=COLUMN_4_WIDTH, text="Disconnected", fg="red")
		self.connection.grid(row=0, column=6, sticky=NSEW)
		
		self.remove = Button(self, image=remove_icon, command=self.remove_pressed)
		self.remove.grid(row=0, column=7, padx=(10,5), sticky=NSEW)
		
		self.connect()
		self.update_visual()

		
		
class Application(Frame):
	def on_exit(self):
		for each in self.lines:
			each.disconnect()
		
		#self.save_config(pop_up=False)
			
		self.quit()
		
		
	def add_line(self, ioc, info, description=""):
		self.lines.append(IOCLine(self, ioc, info, description=description))
		self.next_row = self.next_row + 1
		
		self.lines[len(self.lines) - 1].grid(row=self.next_row, column=0, pady=(0,5), sticky=NSEW)
		
	def remove_line(self, line):
		index = self.lines.index(line)
		
		self.lines.remove(line)
		line.grid_remove()
		
	def save_config(self, pop_up=True):
		config = configparser.RawConfigParser()
		config.add_section("MAIN")
		config.set("MAIN", "NUMBER_OF_IOCS", str(len(self.lines)))
		
		i = 0
		
		for line in self.lines:
			index = "IOC_" + str(i)
			
			config.add_section(index)
			config.set(index, "NAME", line.info["name"])
			config.set(index, "DESC", line.description.get())
			
			i = i + 1
			
		with open(self.config_file, "w") as output:
			config.write(output)
			
			if pop_up:
				tkinter.messagebox.showinfo("Saved Config", "Configuration saved to: " + self.config_file)
			
	def choose_ioc(self):
		self.popup = Toplevel()
		self.popup.wm_title("Add IOC")
		
		self.iocs.update_all()
		
		ioc_list = self.iocs.filter(self.subnet)
		
		self.popup_list = Listbox(self.popup, height=10)
		
		for item in ioc_list:
			self.popup_list.insert(END, item)
		
		self.popup_list.grid(row=0, column=0, padx=(10,10), pady=(10,5))
		
		
		self.popup_add = Button(self.popup, text="Add", command=self.ioc_chosen)
		self.popup_add.grid(row=1, column=0, pady=(0,10))
		
		self.popup.grab_set()
		
	def ioc_chosen(self):
		selection = self.popup_list.curselection()
		ioc_name = self.popup_list.get(selection[0])
		
		self.add_line(ioc_name, self.iocs[ioc_name])
		
		self.popup.grab_release()
		self.popup.destroy()
		self.popup = None
		self.popup_list = None
		self.popup_add = None
		
	def __init__(self, master=None):
		Frame.__init__(self, master)
		
		self.config_folder = os.path.join(os.path.expanduser("~"), os.environ.get("XDG_CONFIG_HOME", ".config"), "iocman")
		self.subnet = get_subnet()
		self.config_file = os.path.join(self.config_folder, self.subnet.replace(".", "-") + ".ini")
		
		self.iocs = AliveDB()
		self.iocs.update_all()
		
		master.protocol("WM_DELETE_WINDOW", self.on_exit)
		master.title("IOC List")
		
		self.labels = LabelLine(self, save_func=self.save_config, add_func=self.choose_ioc)
		self.labels.grid(row=0, column=0, pady=(5,5), sticky=NSEW)
		
		self.next_row = 1
		self.lines = []
		
		ioc_list = self.iocs.filter(self.subnet)
		
		if not os.path.exists(self.config_folder):
			os.mkdir(self.config_folder)
			
		if os.path.exists(self.config_file):
			parser = configparser.RawConfigParser()
			parser.read(self.config_file)
			
			if parser.has_option("MAIN", "NUMBER_OF_IOCS"):
				for index in range(int(parser.get("MAIN", "NUMBER_OF_IOCS"))):
					ioc = parser.get("IOC_" + str(index), "NAME")
					desc = parser.get("IOC_" + str(index), "DESC")
					
					if ioc in ioc_list:
						self.add_line(ioc, ioc_list[ioc], description=desc)
					else:
						print("Could not find saved IOC: " + ioc)
		
		else:
			for ioc in ioc_list:
				if "PREFIX" in ioc_list[ioc] and ioc_list[ioc]["PREFIX"]:
					if self.next_row <= MAX_INITIAL_LENGTH:
						self.add_line(ioc, ioc_list[ioc])
					else:
						message = "More IOCs are availble, truncated results to first " + str(MAX_INITIAL_LENGTH) + "\n\n"
						message += "Create and save a configuration to allow for more IOCs"
						tkinter.messagebox.showinfo("Truncated IOCS", message)
						break


app = Application(master = master)
app.pack()

app.mainloop()

