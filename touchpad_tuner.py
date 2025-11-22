import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import re
import os
import xml.etree.ElementTree as ET
import sys
import threading
from PIL import Image, ImageDraw
import pystray
import json

class TouchpadTuner:
    def __init__(self, root):
        self.root = root
        self.root.title("Touchpad Tuner (터치패드 정밀 조정)")
        self.root.geometry("500x650")
        
        # Handle window close to minimize to tray
        self.root.protocol('WM_DELETE_WINDOW', self.minimize_to_tray)
        
        self.device_id = self.get_touchpad_id()
        if not self.device_id:
            messagebox.showerror("Error", "Touchpad device not found!")
            self.root.destroy()
            return

        self.config_dir = os.path.expanduser("~/.config/touchpad_tuner")
        self.config_path = os.path.join(self.config_dir, "config.json")
        self.touchegg_conf_path = os.path.expanduser("~/.config/touchegg/touchegg.conf")
        self.autostart_path = os.path.expanduser("~/.config/autostart/touchpad_tuner.desktop")
        
        # Load config or defaults
        self.load_config()
        
        # Get current system state for speed (gsettings persists) and touchegg (file persists)
        self.current_speed = self.get_gsettings_speed()
        self.current_threshold, self.current_delay = self.get_touchegg_settings()

        self.create_widgets()
        
        # Create persistent tray icon
        self.create_tray_icon()
        
        # Apply loaded settings to system (in case of reboot)
        self.apply_stored_settings()
        
        # Check if started minimized
        if "--minimized" in sys.argv:
            self.minimize_to_tray()
            if self.daemon_enabled:
                self.start_daemon()
        elif self.daemon_enabled:
            self.start_daemon()

    def load_config(self):
        # Defaults
        self.current_profile = 'adaptive'
        self.current_normal_ctm = 1.0
        self.current_gesture_ctm = 0.4
        self.daemon_enabled = True
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.current_profile = config.get('profile', 'adaptive')
                    self.current_normal_ctm = config.get('normal_ctm', 1.0)
                    self.current_gesture_ctm = config.get('gesture_ctm', 0.4)
                    self.daemon_enabled = config.get('daemon_enabled', True)
                print("Config loaded.")
            except Exception as e:
                print(f"Error loading config: {e}")
    
    def save_config(self):
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        
        # Only save if widgets are initialized
        if not hasattr(self, 'profile_var') or \
           not hasattr(self, 'ctm_scale') or \
           not hasattr(self, 'gesture_ctm_scale') or \
           not hasattr(self, 'daemon_var'):
            return

        config = {
            'profile': self.profile_var.get(),
            'normal_ctm': self.ctm_scale.get(),
            'gesture_ctm': self.gesture_ctm_scale.get(),
            'daemon_enabled': self.daemon_var.get()
        }
        
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
            print("Config saved.")
        except Exception as e:
            print(f"Error saving config: {e}")

    def apply_stored_settings(self):
        # Apply Profile
        self.set_profile(save=False)
        # Apply CTM
        self.set_ctm(self.current_normal_ctm, save=False)
        # Daemon is handled by start_daemon logic in __init__

    # ... (create_tray_icon, minimize_to_tray, show_window, quit_app, toggle_autostart, create/remove autostart, get_touchpad_id, get_gsettings_speed, get_xinput_profile REMOVED/UNUSED?, get_touchegg_settings, set_speed) ...
    
    # We need to modify set_profile and set_ctm to support saving
    
    def set_profile(self, save=True):
        profile = self.profile_var.get()
        val = "1, 0" if profile == 'adaptive' else "0, 1"
        try:
            subprocess.run(
                ['xinput', 'set-prop', self.device_id, 'libinput Accel Profile Enabled', val.split(',')[0], val.split(',')[1]],
                check=True
            )
            print(f"Set profile to {profile}")
            if save: self.save_config()
        except Exception as e:
            # messagebox.showerror("Error", f"Failed to set profile: {e}") 
            # Suppress error on startup if device not ready, but print it
            print(f"Failed to set profile: {e}")

    # ... (save_touchegg_settings) ...

    def set_ctm(self, val, save=True):
        multiplier = float(val)
        self.ctm_label.config(text=f"Multiplier: {multiplier:.2f}")
        self.current_normal_ctm = multiplier
        
        if hasattr(self, 'daemon_process') and self.daemon_process:
            self.restart_daemon()
        else:
            self.apply_ctm_direct(multiplier)
            
        if save: self.save_config()

    # ... (apply_ctm_direct) ...

    def toggle_daemon(self):
        if self.daemon_var.get():
            self.start_daemon()
        else:
            self.stop_daemon()
        self.save_config()

    def start_daemon(self):
        self.stop_daemon() # Ensure clean start
        
        normal = self.ctm_scale.get()
        gesture = self.gesture_ctm_scale.get()
        
        cmd = [
            'python3', '-u', '/home/hirameki/dev/antigravity_project/touchpad/gesture_daemon.py',
            '--device', self.device_id,
            '--normal', str(normal),
            '--gesture', str(gesture)
        ]
        
        print(f"Starting daemon: {' '.join(cmd)}")
        try:
            self.daemon_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.status_label.config(text="Daemon Status: Running", foreground="green")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start daemon: {e}")
            self.daemon_var.set(False)

    # ... (stop_daemon, restart_daemon) ...

    def create_widgets(self):
        # ...
        
        # Profile Control
        # ...
        self.profile_var = tk.StringVar(value=self.current_profile) # Use loaded value
        # ...
        
        # CTM Control
        # ...
        self.ctm_scale.set(self.current_normal_ctm) # Use loaded value
        # ...
        
        # Daemon
        # ...
        self.daemon_var = tk.BooleanVar(value=self.daemon_enabled) # Use loaded value
        # ...
        self.gesture_ctm_scale.set(self.current_gesture_ctm) # Use loaded value
        # ...
        
    def on_gesture_scale_change(self, val):
        if hasattr(self, 'status_label'):
            self.restart_daemon()
            self.save_config()

    def create_tray_icon(self):
        # Try to load icon from file
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
        if os.path.exists(icon_path):
            try:
                image = Image.open(icon_path)
            except Exception as e:
                print(f"Failed to load icon: {e}")
                image = self.create_default_icon()
        else:
            image = self.create_default_icon()
        
        menu = pystray.Menu(
            pystray.MenuItem('Show', self.show_window),
            pystray.MenuItem('Quit', self.quit_app)
        )
        
        self.icon = pystray.Icon("touchpad_tuner", image, "Touchpad Tuner", menu)
        
        # Run icon in separate thread to not block tkinter
        threading.Thread(target=self.icon.run, daemon=True).start()

    def create_default_icon(self):
        # Create a simple icon image as fallback
        image = Image.new('RGB', (64, 64), color=(73, 109, 137))
        d = ImageDraw.Draw(image)
        d.rectangle((16, 16, 48, 48), fill=(255, 255, 255))
        return image

    def minimize_to_tray(self):
        self.root.withdraw()
        # Icon is already running

    def show_window(self, icon, item):
        # Schedule GUI update on main thread
        self.root.after(0, self.root.deiconify)

    def quit_app(self, icon, item):
        # Schedule exit on main thread
        self.root.after(0, self.perform_exit)

    def perform_exit(self):
        if hasattr(self, 'icon'):
            self.icon.stop()
        self.stop_daemon()
        self.root.quit()
        self.root.destroy()

    def toggle_autostart(self):
        if self.autostart_var.get():
            self.create_autostart_entry()
        else:
            self.remove_autostart_entry()

    def create_autostart_entry(self):
        if not os.path.exists(os.path.dirname(self.autostart_path)):
            os.makedirs(os.path.dirname(self.autostart_path))
            
        # Get absolute path of current script
        script_path = os.path.abspath(__file__)
        
        content = f"""[Desktop Entry]
Type=Application
Exec=python3 {script_path} --minimized
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=Touchpad Tuner
Comment=Touchpad sensitivity and gesture tuner
"""
        try:
            with open(self.autostart_path, 'w') as f:
                f.write(content)
            print("Autostart entry created.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create autostart entry: {e}")
            self.autostart_var.set(False)

    def remove_autostart_entry(self):
        if os.path.exists(self.autostart_path):
            try:
                os.remove(self.autostart_path)
                print("Autostart entry removed.")
            except Exception as e:
                print(f"Failed to remove autostart entry: {e}")

    def get_touchpad_id(self):
        try:
            output = subprocess.check_output(['xinput', 'list'], text=True)
            for line in output.splitlines():
                if 'Touchpad' in line:
                    match = re.search(r'id=(\d+)', line)
                    if match:
                        return match.group(1)
        except Exception as e:
            print(f"Error finding touchpad: {e}")
        return None

    def get_gsettings_speed(self):
        try:
            output = subprocess.check_output(
                ['gsettings', 'get', 'org.gnome.desktop.peripherals.touchpad', 'speed'],
                text=True
            ).strip()
            return float(output)
        except:
            return 0.0

    def get_xinput_profile(self):
        try:
            output = subprocess.check_output(
                ['xinput', 'list-props', self.device_id],
                text=True
            )
            for line in output.splitlines():
                if 'libinput Accel Profile Enabled (' in line:
                    parts = line.split(':')[1].strip().split(',')
                    if parts[0].strip() == '1':
                        return 'adaptive'
                    elif parts[1].strip() == '1':
                        return 'flat'
        except Exception as e:
            print(f"Error reading profile: {e}")
        return 'adaptive'

    def get_touchegg_settings(self):
        # Default values
        threshold = 20
        delay = 150
        
        if not os.path.exists(self.touchegg_conf_path):
            return threshold, delay

        try:
            tree = ET.parse(self.touchegg_conf_path)
            root = tree.getroot()
            settings = root.find('settings')
            if settings is not None:
                for prop in settings.findall('property'):
                    name = prop.get('name')
                    if name == 'action_execute_threshold':
                        threshold = int(prop.text)
                    elif name == 'animation_delay':
                        delay = int(prop.text)
        except ET.ParseError:
            print("XML Parse Error detected. Attempting to read raw file...")
            # Fallback: Read file manually if XML is broken
            try:
                with open(self.touchegg_conf_path, 'r') as f:
                    content = f.read()
                    # Simple regex to find values
                    t_match = re.search(r'<property name="action_execute_threshold">(\d+)</property>', content)
                    if t_match:
                        threshold = int(t_match.group(1))
                    d_match = re.search(r'<property name="animation_delay">(\d+)</property>', content)
                    if d_match:
                        delay = int(d_match.group(1))
            except Exception as e:
                print(f"Error reading raw file: {e}")
        except Exception as e:
            print(f"Error reading touchegg conf: {e}")
        
        return threshold, delay

    def set_speed(self, val):
        speed = float(val)
        try:
            subprocess.run(
                ['gsettings', 'set', 'org.gnome.desktop.peripherals.touchpad', 'speed', str(speed)],
                check=True
            )
            self.speed_label.config(text=f"Speed: {speed:.2f}")
        except Exception as e:
            print(f"Error setting speed: {e}")

    def save_touchegg_settings(self):
        threshold = int(self.threshold_scale.get())
        delay = int(self.delay_scale.get())
        
        print(f"Saving settings: Threshold={threshold}, Delay={delay}")

        try:
            if not os.path.exists(self.touchegg_conf_path):
                messagebox.showerror("Error", "Touchegg config file not found!")
                return

            # Read existing content first to preserve other settings
            try:
                tree = ET.parse(self.touchegg_conf_path)
                root = tree.getroot()
            except ET.ParseError:
                print("Broken XML detected. Re-creating minimal valid config with existing content preservation is complex.")
                print("Backing up broken config and creating new one with current settings.")
                
                # Backup
                subprocess.run(['cp', self.touchegg_conf_path, self.touchegg_conf_path + '.bak'])
                
                # Create new minimal valid XML
                root = ET.Element('touchégg')
                settings = ET.SubElement(root, 'settings')
                
                # We might lose other app-specific gestures if we just overwrite.
                # Let's try to fix the file content string instead.
                with open(self.touchegg_conf_path, 'r') as f:
                    content = f.read()
                
                # Fix common issues
                # 1. Fix closing tag
                content = content.replace('</touch&#233;gg>', '</touchégg>')
                # 2. Remove duplicate lines if any (simple approach)
                
                # Write fixed content to temp file and parse
                with open(self.touchegg_conf_path + '.fixed', 'w') as f:
                    f.write(content)
                
                try:
                    tree = ET.parse(self.touchegg_conf_path + '.fixed')
                    root = tree.getroot()
                except:
                    # If still broken, use the new root
                    tree = ET.ElementTree(root)

            settings = root.find('settings')
            if settings is None:
                settings = ET.SubElement(root, 'settings')
            
            # Update or create properties
            props = {
                'action_execute_threshold': str(threshold),
                'animation_delay': str(delay)
            }
            
            for key, val in props.items():
                found = False
                for prop in settings.findall('property'):
                    if prop.get('name') == key:
                        prop.text = val
                        found = True
                        break
                if not found:
                    new_prop = ET.SubElement(settings, 'property', name=key)
                    new_prop.text = val
            
            # Write with explicit encoding
            tree.write(self.touchegg_conf_path, encoding='UTF-8', xml_declaration=True)
            print("Config file written successfully.")

            # Restart touchegg
            print("Restarting touchegg...")
            subprocess.run(['killall', 'touchegg'], stderr=subprocess.DEVNULL)
            import time
            time.sleep(0.5) 
            subprocess.Popen(['touchegg'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("Touchegg restarted.")
            
            messagebox.showinfo("Success", "Gesture settings saved and Touchegg restarted!")
            
        except Exception as e:
            print(f"Exception in save_touchegg_settings: {e}")
            messagebox.showerror("Error", f"Failed to save touchegg settings: {e}")

    def apply_ctm_direct(self, multiplier):
        try:
            subprocess.run(
                ['xinput', 'set-prop', self.device_id, 'Coordinate Transformation Matrix', 
                 str(multiplier), '0', '0', '0', str(multiplier), '0', '0', '0', '1'],
                check=True
            )
        except Exception as e:
            print(f"Error setting CTM: {e}")

    def stop_daemon(self):
        if hasattr(self, 'daemon_process') and self.daemon_process:
            print("Stopping daemon...")
            self.daemon_process.terminate()
            self.daemon_process = None
            self.status_label.config(text="Daemon Status: Stopped", foreground="red")
            # Restore normal CTM
            self.apply_ctm_direct(self.ctm_scale.get())

    def restart_daemon(self):
        if self.daemon_var.get():
            self.start_daemon()

    def create_widgets(self):
        # Initialize status label first to avoid AttributeError
        frame_daemon_dummy = ttk.Frame(self.root) # Temporary holder if needed, but better to just create the label later?
        # Actually, let's just create the variable and label at the end, 
        # but ensure callbacks don't run until everything is ready.
        
        # Speed Control
        frame_speed = ttk.LabelFrame(self.root, text="Pointer Speed (기본 마우스 감도)")
        frame_speed.pack(pady=5, padx=10, fill="x")

        self.speed_label = ttk.Label(frame_speed, text=f"Speed: {self.current_speed:.2f}")
        self.speed_label.pack()

        self.speed_scale = ttk.Scale(
            frame_speed, from_=-1.0, to=1.0, orient='horizontal',
            command=self.set_speed
        )
        self.speed_scale.set(self.current_speed)
        self.speed_scale.pack(fill="x", padx=10, pady=2)

        # Profile Control
        frame_profile = ttk.LabelFrame(self.root, text="Acceleration Profile (가속도)")
        frame_profile.pack(pady=5, padx=10, fill="x")

        self.profile_var = tk.StringVar(value=self.current_profile)
        
        rb_adaptive = ttk.Radiobutton(
            frame_profile, text="Adaptive", 
            variable=self.profile_var, value='adaptive', command=self.set_profile
        )
        rb_adaptive.pack(anchor='w', padx=10)

        rb_flat = ttk.Radiobutton(
            frame_profile, text="Flat", 
            variable=self.profile_var, value='flat', command=self.set_profile
        )
        rb_flat.pack(anchor='w', padx=10)

        # CTM Control (Global Sensitivity)
        frame_ctm = ttk.LabelFrame(self.root, text="1-Finger Sensitivity (기본 감도 배율)")
        frame_ctm.pack(pady=5, padx=10, fill="x")
        
        self.ctm_label = ttk.Label(frame_ctm, text="Multiplier: 1.00")
        self.ctm_label.pack()
        
        self.ctm_scale = ttk.Scale(
            frame_ctm, from_=0.1, to=3.0, orient='horizontal',
            command=self.set_ctm
        )
        self.ctm_scale.set(self.current_normal_ctm)
        self.ctm_scale.pack(fill="x", padx=10, pady=2)

        # Dynamic Sensitivity Daemon
        frame_daemon = ttk.LabelFrame(self.root, text="Dynamic 3-Finger Sensitivity (3손가락 감도 분리)")
        frame_daemon.pack(pady=5, padx=10, fill="x")
        
        # Create status label FIRST in this frame
        self.status_label = ttk.Label(frame_daemon, text="Daemon Status: Stopped", foreground="red")
        self.status_label.pack(side='bottom', pady=2)

        self.daemon_var = tk.BooleanVar(value=self.daemon_enabled)
        chk_daemon = ttk.Checkbutton(frame_daemon, text="Enable Dynamic Adjustment (동적 조정 활성화)", 
                                     variable=self.daemon_var, command=self.toggle_daemon)
        chk_daemon.pack(anchor='w', padx=10, pady=2)
        
        lbl_g_ctm = ttk.Label(frame_daemon, text="3-Finger Multiplier (3손가락 시 배율)")
        lbl_g_ctm.pack(anchor='w', padx=10)
        
        # Use a wrapper for command to check if initialization is done
        self.gesture_ctm_scale = ttk.Scale(frame_daemon, from_=0.1, to=2.0, orient='horizontal', 
                                           command=lambda v: self.on_gesture_scale_change(v))
        self.gesture_ctm_scale.set(self.current_gesture_ctm)
        self.gesture_ctm_scale.pack(fill="x", padx=10, pady=2)
        
        # Autostart
        self.autostart_var = tk.BooleanVar(value=os.path.exists(self.autostart_path))
        chk_autostart = ttk.Checkbutton(frame_daemon, text="Start on Login (로그인 시 자동 시작)", 
                                        variable=self.autostart_var, command=self.toggle_autostart)
        chk_autostart.pack(anchor='w', padx=10, pady=5)

        # Info
        lbl_info = ttk.Label(self.root, text="Note: Daemon requires sudo (passwordless or cached).", font=("Arial", 8), foreground="gray")
        lbl_info.pack(side="bottom", pady=2)

    def on_gesture_scale_change(self, val):
        # Only restart if fully initialized
        if hasattr(self, 'status_label'):
            self.restart_daemon()

if __name__ == "__main__":
    root = tk.Tk()
    app = TouchpadTuner(root)
    root.mainloop()
