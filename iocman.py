#!/APSshare/anaconda3/x86_64/bin/python3

import os
import re
import pwd
import glob
import time
import socket
import threading

import os.path

import configparser

import tkinter as tk
from tkinter import font
import tkinter.messagebox

from epics import PV

import subprocess

COLUMN_1_WIDTH=25
COLUMN_2_WIDTH=25
COLUMN_3_WIDTH=40
COLUMN_4_WIDTH=20
COLUMN_5_WIDTH=10

MAX_INITIAL_LENGTH=15

def get_subnet():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	try:
		s.connect(("8.8.8.8", 80))
		my_ip = s.getsockname()[0]
	finally:
		s.close()

	my_subnet = my_ip.rsplit(sep=".", maxsplit=1)[0]
	return my_subnet

def check_port(host, port):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.settimeout(3)

	try:
		s.connect((host, port))
		return True
	except OSError:
		return False
	finally:
		s.close()


class AliveDB(object):
	def __init__(self):
		self._iocs = {}
		self._ALIVEDB_LOC = "/APSshare/bin/alivedb"
		self.last_update_all = 0.0

	def parse(self, input, doprint=False, ):
		data = {}

		ioc = ""
		lines = ""

		new_ioc_match = re.compile(r"(.*) \((\d+\.\d+\.\d+\.\d+)\) \d \- (Up|Down|Conflict|Uncertain).*")

		for line in input:
			line_str = ""

			check_new_ioc = False

			try:
				line_str = line.decode().strip()
				check_new_ioc = new_ioc_match.match(line_str)

			except Exception as e:
				ioc = ""

			if check_new_ioc:
				if ioc != "":
					data[ioc] = lines

				ioc = check_new_ioc.group(1)
				lines = "[Info]\n"
				lines += "name = " + check_new_ioc.group(1) + "\n"
				lines += "ip = " + check_new_ioc.group(2) + "\n"
				lines += "status = " + check_new_ioc.group(3) + "\n"

			elif ioc != "":
				if line_str.startswith("Environment Variables"):
					lines += "[Environment Variables]\n"

				elif line_str.endswith("Parameters"):
					lines += "[" + line_str.strip() + "]\n"

				elif line_str == "No Environment Variables recorded.":
					pass

				elif line_str.startswith("Address and Port"):
					lines += "address_and_port = " + line_str.split("=", 1)[1].strip() + "\n"

				elif line_str.startswith("Incarnation") or line_str.startswith("Reply") or line_str.startswith("Status"):
					pass

				elif line_str.startswith("Boot Time"):
					lines += "boot_timestamp = " + line_str.split("=", 1)[1].strip() + "\n"

				elif line_str.startswith("Ping Timestamp"):
					lines += "ping_timestamp = " + line_str.split("=", 1)[1].strip() + "\n"
				else:
					lines += line_str + "\n"


		if ioc:
			data[ioc] = lines

		output = {}

		for ioc in data:
			config = None
			try:
				config = configparser.ConfigParser(allow_no_value=True)
				config.read_string(data[ioc])
			except Exception as e:
				continue

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
		try:
			output = subprocess.check_output([self._ALIVEDB_LOC, "-d", ioc]).splitlines()
		except FileNotFoundError:
			raise Exception("alivedb not found at " + self._ALIVEDB_LOC)
		except subprocess.CalledProcessError as e:
			raise Exception("alivedb failed for " + ioc + ": " + str(e))

		output[0] = str.encode(ioc + " (" + self._iocs[ioc]["ip"] + ") 0 - " + self._iocs[ioc]["status"] + "  \n")

		self._iocs.update(self.parse(output))

	def update_all(self):
		current_time = time.time()

		if (current_time - self.last_update_all < 120.0):
			return

		self.last_update_all = current_time

		self._iocs = {}

		try:
			output = subprocess.check_output([self._ALIVEDB_LOC, "."]).splitlines()
		except FileNotFoundError:
			raise Exception("alivedb not found at " + self._ALIVEDB_LOC)
		except subprocess.CalledProcessError as e:
			raise Exception("alivedb query failed: " + str(e))

		self._iocs.update(self.parse(output))


	def __getitem__(self, key):
		return self._iocs.get(key)

	def filter(self, subnet=None, arch=None):
		output = {}


		for iocname, ioc in self._iocs.items():
			add = True

			try:
				if arch and ioc["ARCH"] != arch:
					add = False

				if subnet and not ioc["ip"].startswith(subnet):
					add = False
			except Exception as e:
				add = False

			if add:
				output[iocname] = ioc


		return output


class Tooltip:
	def __init__(self, widget, text_func):
		self.widget = widget
		self.text_func = text_func
		self.tip = None
		widget.bind("<Enter>", self.show)
		widget.bind("<Leave>", self.hide)

	def show(self, event):
		text = self.text_func()
		if not text:
			return
		x, y = event.x_root + 10, event.y_root + 10
		self.tip = tk.Toplevel(self.widget)
		self.tip.wm_overrideredirect(True)
		self.tip.wm_geometry("+{}+{}".format(x, y))
		label = tk.Label(self.tip, text=text, background="#ffffe0",
			relief="solid", borderwidth=1, justify=tk.LEFT)
		label.pack()

	def hide(self, event):
		if self.tip:
			self.tip.destroy()
			self.tip = None


class LabelLine(tk.Frame):
	def __init__(self, master, save_func=None, add_func=None):
		tk.Frame.__init__(self, master)

		self.desc = tk.Label(self, text="Description", width=COLUMN_1_WIDTH)
		self.desc.grid(row=0, column=0, padx=(5,0), sticky=tk.NSEW)

		self.name = tk.Label(self, text="IOC Name", width=COLUMN_2_WIDTH)
		self.name.grid(row=0, column=1, sticky=tk.NSEW)

		self.label_font = font.Font(self.name, self.name.cget("font"))
		self.label_font.configure(underline=True)
		self.name.configure(font=self.label_font)
		self.desc.configure(font=self.label_font)

		self.placeholder = tk.Label(self, text="", width=COLUMN_5_WIDTH * 3 + 15)
		self.placeholder.grid(row=0, column=2, sticky=tk.NSEW)

		self.host = tk.Label(self, text="IOC Host", font=self.label_font, width=COLUMN_3_WIDTH)
		self.host.grid(row=0, column=3, sticky=tk.NSEW)
		self.grid_columnconfigure(3, weight=1)

		self.status = tk.Label(self, text="Alive Status", font=self.label_font, width=COLUMN_4_WIDTH - 4)
		self.status.grid(row=0, column=4, sticky=tk.NSEW)

		self.saveConfig = tk.Button(self, image=save_icon, command=save_func)
		self.saveConfig.grid(row=0, column=5, sticky=tk.NSEW)

		self.addIOC = tk.Button(self, image=add_icon, command=add_func)
		self.addIOC.grid(row=0, column=6, padx=(5,5), sticky=tk.NSEW)


class IOCLine(tk.Frame):

	def disconnect(self):
		self.destroyed = True
		if self.pv:
			self.pv.disconnect()

	def is_remote(self):
		my_name = pwd.getpwuid(os.getuid()).pw_name
		return self.info["hostname"] != socket.gethostname() or self.info["user"] != my_name

	def run_command(self, title, *args, interactive=True):
		if self.is_remote():
			userhost = self.info["user"] + "@" + self.info["hostname"]
			remote_cmd = self.script + " " + " ".join(args)
			subprocess.Popen(["xterm", "-T", title, "-e",
				"ssh", "-o", "ConnectTimeout=5", userhost, remote_cmd])
		elif interactive:
			subprocess.Popen(["xterm", "-T", title, "-e",
				self.script] + list(args))
		else:
			subprocess.Popen([self.script] + list(args))

	def _check_remote_thread(self):
		try:
			if not self.info or not self.info.get("TOP"):
				self.remote_status = "none"
				return

			command_check = glob.glob(self.info["TOP"] + "/iocBoot/ioc*/softioc/" + self.info["name"] + "-command.txt")

			if len(command_check) != 1:
				self.command_file = None
				self.remote_status = "none"
				return

			self.command_file = command_check[0]

			with open(self.command_file) as info:
				self.command_pid = info.readline().strip().split(":")[1]
				parts = info.readline().strip().split(":")
				self.command_tcp, self.command_host = parts[0], parts[1]
				self.command_port = int(parts[2])

			if check_port(self.command_host, self.command_port):
				self.remote_status = "active"
			else:
				self.remote_status = "stale"
		except Exception:
			self.remote_status = "none"
		finally:
			self._remote_check_running = False

	def update_remote_status(self):
		if self._remote_check_running:
			return

		self._remote_check_running = True
		t = threading.Thread(target=self._check_remote_thread, daemon=True)
		t.start()

	def remote_tooltip_text(self):
		if self.remote_status == "none":
			return "No remote control configured"
		elif self.remote_status == "active":
			return "Remote active\nPID: {}\nHost: {}\nPort: {}".format(
				self.command_pid, self.command_host, str(self.command_port))
		else:
			return "Remote control stale\nPID: {}\nHost: {}\nPort: {}".format(
				self.command_pid, self.command_host, str(self.command_port))

	def connect(self):
		alive_pv = self.info["PREFIX"].strip() + "alive"

		self.pv = PV(alive_pv, connection_callback=self.connection_monitor)

	def info_update(self):
		self.app.iocs.update(self.info["name"])
		self.info = self.app.iocs[self.info["name"]]

		if not self.info or not self.info.get("TOP"):
			raise Exception("No TOP directory information available for " + (self.info or {}).get("name", "unknown IOC"))

		script_check = glob.glob(self.info["TOP"] + "/iocBoot/ioc*/softioc/" + self.info["name"].removeprefix("ioc") + ".pl")

		if len(script_check) == 0:
			script_check = glob.glob(self.info["TOP"] + "/iocBoot/ioc*/softioc/" + self.info["name"].removeprefix("ioc") + ".sh")

		if len(script_check) == 0:
			message = "Cannot find startup script (" + self.info["name"].removeprefix("ioc") + ".pl) for IOC\n\n"
			message += "Check for file system network issues\n"

			raise Exception(message)

		if len(script_check) > 1:
			message = "Found multiple startup scripts ("  + self.info["name"].removeprefix("ioc") + ".pl) for IOC\n\n"
			message += "Check for file system issues"

			raise Exception(message)

		self.script = script_check[0]
		self.command_file = None

		command_check = glob.glob(self.info["TOP"] + "/iocBoot/ioc*/softioc/" + self.info["name"] + "-command.txt")

		if len(command_check) > 1:
			message = "Found multiple files matching " + self.info["name"] + "-command.txt\n\n"

			for filepath in command_check:
				message += "\t" + filepath + "\n"

			message += "\n"
			message += "Check IOC naming convention and folder structure."

			raise Exception(message)

		if len(command_check) == 1:
			self.command_file = command_check[0]

			with open(self.command_file) as info:
				self.command_pid = info.readline().strip().split(":")[1]
				parts = info.readline().strip().split(":")
				self.command_tcp, self.command_host = parts[0], parts[1]
				self.command_port = int(parts[2])


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
			ping_ts = self.info.get("ping_timestamp", "")
			boot_ts = self.info.get("boot_timestamp", "")

			pretty = "Disconnected"

			if ping_ts and not ping_ts.startswith("1969-12-31"):
			    pretty = "Last seen: " + ping_ts.split()[0]
			if boot_ts and not boot_ts.startswith("1969-12-31"):
			    pretty = "Last seen: " + boot_ts.split()[0]

			self.connection.config(text=pretty, fg="red")

			self.control.config(text="Start", fg="sea green")
			self.host.config(text=self.hostname)

		self.visual_cycle += 1
		if self.visual_cycle >= 20:
			self.visual_cycle = 0
			self.update_remote_status()

		if self.remote_status == "active":
			self.remote.config(fg="sea green")
		elif self.remote_status == "stale":
			self.remote.config(fg="orange")
		else:
			self.remote.config(fg="black")

		self.app.after(250, self.update_visual)

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
			if self.is_remote():
				ioc_userhost = self.info["user"] + "@" + self.info["hostname"]
				curr_userhost = pwd.getpwuid(os.getuid()).pw_name + "@" + socket.gethostname()

				message = "IOC running as " + ioc_userhost + "\n"
				message += "but ioc manager running as " + curr_userhost + "\n\n"
				message += "Use ssh to connect?"

				response = tkinter.messagebox.askokcancel("Console", message)

				if response:
					self.run_command(self.info["name"] + " console", "console")
				return

		self.run_command(self.info["name"] + " console", "console")


	def start_pressed(self):
		try:
			self.info_update()
		except Exception as e:
			tkinter.messagebox.showinfo("Start/Stop", e)
			return

		check_ok = True

		if not "PID" in self.info["PROCSERV"]:
			if self.connected:
				if self.is_remote():
					ioc_userhost = self.info["user"] + "@" + self.info["hostname"]
					curr_userhost = pwd.getpwuid(os.getuid()).pw_name + "@" + socket.gethostname()

					message = "IOC running as " + ioc_userhost + "\n"
					message += "but ioc manager running as " + curr_userhost + "\n\n"
					message += "Use ssh to connect?"

					response = tkinter.messagebox.askokcancel("Start/Stop", message)

					if response:
						self.run_command("Stop IOC", "stop")
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
					message += "Port: " + str(self.command_port) + "\n\n"
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
				self.run_command("Start/Stop IOC", action, interactive=False)


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
			message += "Port: " + str(self.command_port) + "\n"

			message += "\n"

			port_check = check_port(self.command_host, self.command_port)

			if not port_check:
				message += "but cannot connect to listed port.\n"
				message += "Do you wish to delete command file?\n"
				message += "\tFile: " + self.command_file

				result = tkinter.messagebox.askokcancel("Remote Info", message)

				if result:
					try:
						os.remove(self.command_file)
						tkinter.messagebox.showinfo("Remote Info", "Deleted: " + self.command_file)
					except OSError as e:
						tkinter.messagebox.showinfo("Remote Info", "Failed to delete file: " + str(e))

				return


			if self.connected:
				message += "Shut down IOC before disabling remote control"

				tkinter.messagebox.showinfo("Remote Info", message)
			else:
				message += "\n"

				message += "Would you like to disable?"

				result = tkinter.messagebox.askokcancel("Remote Disable", message)

				if result:
					self.run_command("Remote Disable", "remote", "disable")
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

			self.run_command("Remote Enable", "remote", "enable")


	def remove_pressed(self):
		self.disconnect()
		self.app.remove_line(self)

	def __init__(self, master, app, name, info, description=""):
		tk.Frame.__init__(self, master)

		self.app = app
		self.name = name.strip()
		self.info = info
		self.pv = None
		self.hostname = ""
		self.connected = False
		self.destroyed = False
		self.remote_status = "none"
		self._remote_check_running = False
		self.visual_cycle = 0

		self.description = tk.StringVar()
		self.description.set(description)

		self.desc = tk.Entry(self, width=COLUMN_1_WIDTH, textvariable=self.description)
		self.desc.grid(row=0, column=0, padx=(5,0), sticky=tk.NSEW)

		self.index = tk.Label(self, width=COLUMN_2_WIDTH, text=self.name, cursor="fleur")
		self.index.grid(row=0, column=1, sticky=tk.NSEW)
		self.index.bind("<ButtonPress-1>", self.app._drag_start)
		self.index.bind("<B1-Motion>", self.app._drag_motion)
		self.index.bind("<ButtonRelease-1>", self.app._drag_end)

		self.remote = tk.Button(self, width=COLUMN_5_WIDTH, text="Remote", command=self.remote_pressed)
		self.remote.grid(row=0, column=2, padx=(0,5), sticky=tk.NSEW)
		Tooltip(self.remote, self.remote_tooltip_text)

		self.control = tk.Button(self, width=COLUMN_5_WIDTH, text="Start", command=self.start_pressed, fg="sea green")
		self.control.grid(row=0, column=3, padx=(0,5), sticky=tk.NSEW)

		self.console = tk.Button(self, width=COLUMN_5_WIDTH, text="Console", command=self.console_pressed)
		self.console.grid(row=0, column=4, sticky=tk.NSEW)

		self.host = tk.Label(self, width=COLUMN_3_WIDTH)
		self.host.grid(row=0, column=5, sticky=tk.NSEW)
		self.grid_columnconfigure(5, weight=1)

		self.connection = tk.Label(self, width=COLUMN_4_WIDTH, text="Disconnected", fg="red")
		self.connection.grid(row=0, column=6, sticky=tk.NSEW)

		self.remove = tk.Button(self, image=remove_icon, command=self.remove_pressed)
		self.remove.grid(row=0, column=7, padx=(10,5), sticky=tk.NSEW)

		try:
			self.info_update()
		except Exception:
			pass

		self.update_remote_status()
		self.connect()
		self.update_visual()



class Application(tk.Frame):
	def on_exit(self):
		self.unbind_all("<Button-4>")
		self.unbind_all("<Button-5>")

		for each in self.lines:
			each.disconnect()

		#self.save_config(pop_up=False)

		self.quit()

	def _on_canvas_configure(self, event):
		self.canvas.itemconfig(self.canvas_window, width=event.width)
		self._on_frame_configure()

	def _on_frame_configure(self, event=None):
		bbox = self.canvas.bbox("all")
		if bbox:
			self.canvas.configure(scrollregion=(0, 0, bbox[2], bbox[3]))
		else:
			self.canvas.configure(scrollregion=(0, 0, 0, 0))

		if self.inner_frame.winfo_reqheight() > self.canvas.winfo_height():
			self.scrollbar.grid(row=1, column=1, sticky="ns")
		else:
			self.scrollbar.grid_remove()
			self.canvas.yview_moveto(0)
		self.update_idletasks()

	def _on_mousewheel(self, event):
		if self.inner_frame.winfo_reqheight() <= self.canvas.winfo_height():
			return
		if event.num == 4:
			self.canvas.yview_scroll(-1, "units")
		elif event.num == 5:
			self.canvas.yview_scroll(1, "units")

	def _set_line_bg(self, line, color):
		default_bg = self.inner_frame.cget("bg") if not color else color
		bg = default_bg if not color else color
		line.configure(bg=bg)
		for child in line.winfo_children():
			if isinstance(child, tk.Entry):
				continue
			try:
				child.configure(bg=bg)
			except tk.TclError:
				pass

	def _drag_start(self, event):
		source = event.widget.master
		if source in self.lines:
			self._drag_source = source
			self._drag_index = self.lines.index(source)
			self._drag_target_index = self._drag_index

	def _drag_motion(self, event):
		if self._drag_source is None:
			return

		canvas_top = self.canvas.winfo_rooty()
		canvas_bottom = canvas_top + self.canvas.winfo_height()
		edge_zone = 30

		if event.y_root < canvas_top + edge_zone:
			self._auto_scroll(-1)
		elif event.y_root > canvas_bottom - edge_zone:
			self._auto_scroll(1)
		else:
			self._cancel_auto_scroll()

		canvas_y = self.canvas.canvasy(event.y_root - canvas_top)

		target_index = self._drag_index
		for i, line in enumerate(self.lines):
			line_y = line.winfo_y()
			line_h = line.winfo_height()
			if line_y <= canvas_y <= line_y + line_h:
				target_index = i
				break

		if self._drag_target_index is not None and self._drag_target_index < len(self.lines):
			self._set_line_bg(self.lines[self._drag_target_index], "")

		self._drag_target_index = target_index

		if self._drag_target_index != self._drag_index:
			self._set_line_bg(self.lines[self._drag_target_index], "light blue")

	def _drag_end(self, event):
		if self._drag_source is None:
			return

		self._cancel_auto_scroll()

		for line in self.lines:
			self._set_line_bg(line, "")

		if self._drag_target_index != self._drag_index:
			line = self.lines.pop(self._drag_index)
			self.lines.insert(self._drag_target_index, line)
			self._regrid_lines()

		self._drag_source = None
		self._drag_index = None
		self._drag_target_index = None

	def _regrid_lines(self):
		for i, line in enumerate(self.lines):
			line.grid_forget()
			line.grid(row=i, column=0, pady=(0,5), sticky=tk.NSEW)
		self.next_row = len(self.lines)

	def _auto_scroll(self, direction):
		self._cancel_auto_scroll()
		if self.inner_frame.winfo_reqheight() <= self.canvas.winfo_height():
			return
		top, bottom = self.canvas.yview()
		if direction < 0 and top <= 0:
			return
		if direction > 0 and bottom >= 1.0:
			return
		self.canvas.yview_scroll(direction, "units")
		self._drag_scroll_id = self.after(50, self._auto_scroll, direction)

	def _cancel_auto_scroll(self):
		if self._drag_scroll_id:
			self.after_cancel(self._drag_scroll_id)
			self._drag_scroll_id = None

	def _update_canvas_height(self):
		self.update_idletasks()
		if self.lines:
			row_height = self.lines[0].winfo_reqheight() + 5
			max_visible = min(len(self.lines), MAX_INITIAL_LENGTH)
			self.canvas.configure(height=row_height * max_visible)
		else:
			self.canvas.configure(height=0)
		self.update_idletasks()
		self._on_frame_configure()

	def add_line(self, ioc, info, description=""):
		self.lines.append(IOCLine(self.inner_frame, self, ioc, info, description=description))
		self.next_row = self.next_row + 1

		self.lines[len(self.lines) - 1].grid(row=self.next_row, column=0, pady=(0,5), sticky=tk.NSEW)
		self._update_canvas_height()

	def remove_line(self, line):
		index = self.lines.index(line)

		self.lines.remove(line)
		line.grid_remove()
		self._update_canvas_height()

	def save_config(self, pop_up=True):
		config = configparser.RawConfigParser()
		config.add_section("MAIN")
		config.set("MAIN", "NUMBER_OF_IOCS", str(len(self.lines)))
		config.set("MAIN", "WINDOW_WIDTH", str(self.winfo_toplevel().winfo_width()))
		config.set("MAIN", "WINDOW_HEIGHT", str(self.winfo_toplevel().winfo_height()))

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

	def filter_ioc_list(self, *args):
		filter_text = self.popup_filter_var.get().lower()

		self.popup_list.delete(0, tk.END)

		for name in sorted(self.popup_ioc_list.keys()):
			if filter_text in name.lower():
				self.popup_list.insert(tk.END, name)

	def choose_ioc(self):
		if self.popup:
			return

		self.popup = tk.Toplevel()
		self.popup.wm_title("Add IOC")

		self.iocs.update_all()

		self.popup_ioc_list = self.iocs.filter(self.subnet)

		self.popup_filter_var = tk.StringVar()
		self.popup_filter_var.trace_add("write", self.filter_ioc_list)

		self.popup_filter = tk.Entry(self.popup, textvariable=self.popup_filter_var)
		self.popup_filter.grid(row=0, column=0, padx=(10,10), pady=(10,5), sticky=tk.NSEW)

		self.popup_list = tk.Listbox(self.popup, height=10)

		for item in sorted(self.popup_ioc_list.keys()):
			self.popup_list.insert(tk.END, item)

		self.popup_list.grid(row=1, column=0, padx=(10,10), pady=(0,5), sticky=tk.NSEW)
		self.popup_list.bind("<Double-1>", lambda e: self.ioc_chosen())

		self.popup_add = tk.Button(self.popup, text="Add", command=self.ioc_chosen)
		self.popup_add.grid(row=2, column=0, pady=(0,10))

		self.popup_filter.focus_set()
		self.popup.bind("<Return>", lambda e: self.ioc_chosen())
		self.popup.bind("<Escape>", lambda e: self._close_popup())
		self.popup.grab_set()

	def _close_popup(self):
		if not self.popup:
			return

		self.popup.grab_release()
		self.popup.destroy()
		self.popup = None
		self.popup_list = None
		self.popup_add = None
		self.popup_filter = None
		self.popup_filter_var = None
		self.popup_ioc_list = None

	def ioc_chosen(self):
		selection = self.popup_list.curselection()

		if not selection:
			return

		ioc_name = self.popup_list.get(selection[0])

		self.add_line(ioc_name, self.popup_ioc_list[ioc_name])
		self._close_popup()

	def __init__(self, master=None):
		tk.Frame.__init__(self, master)

		config_home = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
		self.config_folder = os.path.join(config_home, "iocman")
		self.subnet = get_subnet()
		self.config_file = os.path.join(self.config_folder, self.subnet.replace(".", "-") + ".ini")

		self.iocs = AliveDB()
		self.iocs.update_all()

		master.protocol("WM_DELETE_WINDOW", self.on_exit)
		master.title("IOC List")

		self.labels = LabelLine(self, save_func=self.save_config, add_func=self.choose_ioc)
		self.labels.grid(row=0, column=0, pady=(5,5), sticky=tk.NSEW)

		self.canvas = tk.Canvas(self, highlightthickness=0)
		self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
		self.canvas.configure(yscrollcommand=self.scrollbar.set)

		self.inner_frame = tk.Frame(self.canvas)
		self.inner_frame.grid_columnconfigure(0, weight=1)
		self.canvas_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

		self.canvas.grid(row=1, column=0, padx=(0,5), sticky=tk.NSEW)
		self.grid_rowconfigure(1, weight=1)
		self.grid_columnconfigure(0, weight=1)

		self.canvas.bind("<Configure>", self._on_canvas_configure)
		self.inner_frame.bind("<Configure>", self._on_frame_configure)
		self.bind_all("<Button-4>", self._on_mousewheel)
		self.bind_all("<Button-5>", self._on_mousewheel)
		master.bind_all("<Control-s>", lambda e: self.save_config())
		master.bind_all("<Control-n>", lambda e: self.choose_ioc())

		self.next_row = 0
		self.lines = []
		self.popup = None
		self._drag_source = None
		self._drag_index = None
		self._drag_target_index = None
		self._drag_scroll_id = None

		ioc_list = self.iocs.filter(self.subnet)

		saved_width = None
		saved_height = None

		if not os.path.exists(self.config_folder):
			os.mkdir(self.config_folder)

		if os.path.exists(self.config_file):
			parser = configparser.RawConfigParser()
			parser.read(self.config_file)

			if parser.has_option("MAIN", "NUMBER_OF_IOCS"):
				for index in range(int(parser.get("MAIN", "NUMBER_OF_IOCS"))):
					ioc = parser.get("IOC_" + str(index), "NAME")
					desc = parser.get("IOC_" + str(index), "DESC", fallback="")

					if ioc in ioc_list:
						self.add_line(ioc, ioc_list[ioc], description=desc)
					else:
						print("Could not find saved IOC: " + ioc)

			saved_width = parser.get("MAIN", "WINDOW_WIDTH", fallback=None)
			saved_height = parser.get("MAIN", "WINDOW_HEIGHT", fallback=None)

		else:
			for ioc in ioc_list:
				if "PREFIX" in ioc_list[ioc] and ioc_list[ioc]["PREFIX"]:
					if self.next_row <= MAX_INITIAL_LENGTH:
						self.add_line(ioc, ioc_list[ioc])
					else:
						message = f"Displaying {min(len(ioc_list), MAX_INITIAL_LENGTH)} of {len(ioc_list)} IOCs\n\n"
						message += "Create and save a configuration to allow for more IOCs"
						tkinter.messagebox.showinfo("Truncated IOCS", message)
						break

		self.update_idletasks()
		min_width = self.winfo_reqwidth()
		header_height = self.labels.winfo_reqheight() + 10
		if self.lines:
			row_height = self.lines[0].winfo_reqheight() + 5
			min_height = header_height + row_height * min(len(self.lines), 5)
		else:
			min_height = header_height
		master.minsize(width=min_width, height=min_height)

		if saved_width and saved_height:
			master.geometry("{}x{}".format(saved_width, saved_height))


if __name__ == "__main__":
	master = tk.Tk()

	reload_icon = tk.PhotoImage(data="iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAABhWlDQ1BJQ0MgcHJvZmlsZQAAKJF9kT1Iw1AUhU9bpSIVETuIiGRoO1kQFXHUKhShQqgVWnUweekfNGlIUlwcBdeCgz+LVQcXZ10dXAVB8AfEXXBSdJES70sKLWK88Hgf591zeO8+wN+oMNXsGgdUzTLSyYSQza0KwVf4MIoBRBGTmKnPiWIKnvV1T91Ud3Ge5d33Z/UpeZMBPoF4lumGRbxBPL1p6Zz3icOsJCnE58RjBl2Q+JHrsstvnIsO+3lm2Mik54nDxEKxg+UOZiVDJZ4ijiiqRvn+rMsK5y3OaqXGWvfkLwzltZVlrtMaQRKLWIIIATJqKKMCC3HaNVJMpOk84eEfdvwiuWRylcHIsYAqVEiOH/wPfs/WLExOuEmhBND9YtsfUSC4CzTrtv19bNvNEyDwDFxpbX+1Acx8kl5va5EjoH8buLhua/IecLkDDD3pkiE5UoCWv1AA3s/om3LA4C3Qu+bOrXWO0wcgQ7NK3QAHh0CsSNnrHu/u6Zzbvz2t+f0AqhtyvUx7a90AAAAGYktHRAD/AP8A/6C9p5MAAAAJcEhZcwAADdcAAA3XAUIom3gAAAAHdElNRQfpAR4RKRw9muMVAAABKklEQVQ4y6XTvS6EURAG4OdbywWIREGC+CkUGhp/N6Gg0OAClGoleu0KhcYFiAYJLReA+Alb6FiFAt9qRnLy2d1IvMnJOZkzc2be98xkfqOMAcygH194wHnsn1pgEDt4C8d6rE+8Yjd8GmIKV8gjKMdHrNR2h+mI6ciSzEex11HFPi4iaByL6EWGWyxh9YfzTjjmOAnuWVJdFrbjpJr3OBsOznU8hmMzjOA50SaHlRApx0Yhc4oeHBTEzUvoQ1t812VcFNGGOYwmooKSv+EL25jAJNZwiBdYTihstqBQRDu6YQi1KP0purAZGlZcRiX5ntN4pFQIHMA6Opu18E2i7hO2MI+FOFdDi0N0/aeVrzHWapgqoUlxmGrYKw5T1kSTfsxGj8A9zhqN8zen8GbXeKR36AAAAABJRU5ErkJggg==")
	save_icon   = tk.PhotoImage(data="R0lGODlhEAAQAMZ5ADNkpDZmpTpqp0Nwq1V4qVJ5rU96sFl5plh+r16ArlmBtWCCr2SCrGKDr2GDsmOEsoGBgWOFsl+GuGOGtWWGsmaHtWyHr2qJtWaLu2yKtWeMu2mMuW2RvnSRuY6OjnWTu5KSknSXwpOTkpOTk3mXwJSUlHmYwJWVlXqaw5eXl5mZmYicuZ2dnYWkyaGhoZGjvaSkpJimuqampqenp6ioqJyqvampqaqqqqurq6ysrK2tra6urq+vr7CwsLGxsbKysrW1ta63wq23xba2tri4uLK5w7m5ubu7u729vb6+vr++vcDAwMDBwsLCwsPDw8TExMXFxcHGzsbGxsjIyMPJ0cfJzMrKysvLy8vLzczMzMvN0c3Nzc3Nzs/Pz9HR0dPS0NbV1NbW1dbW1tjY2NXZ3dnZ2drZ2NrZ2dra2tvb293b2t3d3eDd2t/f3+Dg4OHh4eLh4OLi4uPk5eTk5OXk5OXl5ebl5eXm5ubm5v///////////////////////////yH5BAEKAH8ALAAAAAAQABAAAAe6gH+Cg4SFhRQfFwSGhRkmJC0oCYyGDCEblIJKamwvHBgrXF9MhlUWEQ8aEhMVB1oihD50ZB0KBgMCDlRmRoRLdXBRCwEACEJnaFeEYmtiYEUNBTFZXmNdNII3cWttaF5BNVhhaWVjQ4JQc21ucXh3cnZva2ltToJIW1ZTUk9NS0lIjhAhAkMQEBwpXNjQsePGjh40eOgYYZBIDhw8fPjQ4eMHDh88TghKIWMGDBYqUpQoAcKDSwiZKAUCADs=")
	add_icon    = tk.PhotoImage(data="R0lGODlhEAAQAMZsAA4TNRMZPxQaQxYbRRccSRceSxgeThshUxsiVBwjXR4lYR8lXx4lYyAmWx8nZh8naSAoaSMpWSIpbCQqZSQrYyQrZSUrYyUrZiUsZiYsaCYsaiYtaiYtayYtbCkvZSgvbicvcikvbykwcCkwcykxdCoxdSoxdioxdy0zbC0zbi00cC00dC40ci01dS41fS01gy82fi42hS83gC83gjA3gC83gy83hTA4hzU8hj1EkD1FlkJJmlRdyVVeyFVey1Zfyldfylhgy1hhy1pizVpjzFtkzlxkzl1l0F1mz15mz15m0F5m0V5n0V9nz19n0F9n0l9n02Bo0GBo0WBo0mBo02Fp0WFp0mNr02Nr1WRs1GRs1WVt1WVt1mZu1mdu1mdu12hv12hv2Gdw2Whw12px2Wtz2mxz2m103G5122923XF43XN64f///////////////////////////////////////////////////////////////////////////////yH5BAEKAH8ALAAAAAAQABAAAAeFgH+Cg38xL4SIhC8+PA+JiTY/QBCPiDVBQg6VhDNDRAybgzJFRgqPICYlJSQ6SU44IiEhHxN/LlBLTE9TUk1RVlhcXF1iCDRMTk5SUlXNV1lbW11gDX8LHRwbGjvPORgVFhYHjythYwWhgixkZATpfyplZgPvKWdoAu8ea2oA738RIjwKBAA7")
	remove_icon = tk.PhotoImage(data="R0lGODlhEAAQAMZrAMYJCbAPD8gJCccKCbMQD8cNDcQODcUODckNDb4TEtYNDcQSEtcNDdgNDcYSEb8UE74XFr8XFtQSEccXFtYTEsgXFtcTEtgTEdgTEr8aGcAaGbIgH7AhIdIYF9MYF78eHcwbGsEeHdgYF9oYF8wcGtkZGLMlJNMdHNQdHNoeHdseHdseHtUiINYiIdskItwkItcoJdgoJt0qJ9QtK781M9AxL9EyL7k5N8E3Nd4wLc80Mro6ONA1M884NtE5Nt82Mt82M+A3NL9BQMBCQNM9OtU+OuE7N+I7N8ZDQcdDQd0+Ot4+O8RFROM9OcZGRMVHRcZIReRAPOJBPcVJSORBPcdKSORDP+VDP91HRd5HRORGQuZGQuZJRedJRd1OS+ZMR95OS+dMR+dMSORPS+ZRTN5TUOBTUOBWUuJXU+ZYU+hZVP///////////////////////////////////////////////////////////////////////////////////yH5BAEKAH8ALAAAAAAQABAAAAevgH9/N0OChoZCO4Y0aWhVh4JTZ2o4fxxjYWFmUIdPZWJfZCZ/RFxaW2BOgkxeW1pdRYY9VlJRWUlIWFRSVz6QOk1GR0tKR0ZNPJCCNUFAP0BAQTbKhjM51zkzG9R/HzAy4DIxIdQZLC8u6S4vLRqQECcrKSokICrzKBGGCR0lIiMVBE0YIaKEhwd/AkiwQAGDg0MLLlCwIIHAnwINGBxQZkABAwSGBgjgBmAkt5OBAAA7")

	app = Application(master=master)
	app.pack(fill=tk.BOTH, expand=True)
	app.mainloop()

