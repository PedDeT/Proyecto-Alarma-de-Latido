import tkinter as tk
from tkinter import ttk
import bluetooth
import threading
import os
import time
import pygame

fuente = 'Segoe UI'

RFCOMM_PORT = os.getenv('RFCOMM_PORT', 1)
NORMAL_HEART_RATE_MIN = 70
NORMAL_HEART_RATE_MAX = 190

class BluetoothFrame(tk.Frame):
    def __init__(self, parent, main_app):
        super().__init__(parent)
        self.parent = parent
        self.main_app = main_app
        self.configure(bg="white")

        self.title_label = tk.Label(self, text="Dispositivos", font=(fuente, 20), bg="white")
        self.title_label.pack(pady=10)

        self.search_button = tk.Button(self, text="Buscar dispositivos", command=self.list_paired_devices, font=(fuente, 20), bg="white", relief="flat")
        self.search_button.pack(pady=10)

        self.devices_listbox = tk.Listbox(self, selectmode=tk.SINGLE, font=(fuente, 12), bg="white")
        self.devices_listbox.pack(pady=10, fill="both", expand=True)

        self.connect_button = tk.Button(self, text="Conectar dispositivo", command=self.connect_device, font=(fuente, 20), bg="white", relief="flat")
        self.connect_button.pack(pady=10)

        self.connection_status_label = tk.Label(self, text="", fg="green", bg="white", font=(fuente, 12), wraplength=300)
        self.connection_status_label.pack(fill="x")

    def list_paired_devices(self):
        try:
            nearby_devices = bluetooth.discover_devices(duration=10, lookup_names=True)
            self.devices_listbox.delete(0, tk.END)  # Clear the previous device list


            # Sort devices by name
            nearby_devices.sort(key=lambda device: device[1])

            for addr, name in nearby_devices:
                self.devices_listbox.insert(tk.END, f"{name} ({addr})")
        except bluetooth.btcommon.BluetoothError as e:
            self.connection_status_label.config(text="Error de Bluetooth: " + str(e), fg="red")

    def connect_device(self):
        selected_device = self.devices_listbox.get(tk.ACTIVE)
        if selected_device:
            device_address = selected_device.split(' ')[-1][1:-1]  # Extract the device's Bluetooth address
            try:
                # Attempt to connect using RFCOMM
                self.main_app.client_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                self.main_app.client_socket.connect((device_address, RFCOMM_PORT))
                self.main_app.connected = True
                self.connection_status_label.config(text="Conexión Exitosa", fg="green")
            except bluetooth.btcommon.BluetoothError as e:
                if "Connection refused" in str(e) or "Host is down" in str(e) or "No route to host" in str(e) or "Device did not respond to inquiry" in str(e):
                    self.connection_status_label.config(text="Error de conexión: No se pudo conectar al dispositivo", fg="red")
                else:
                    self.connection_status_label.config(text="Error de Bluetooth: " + str(e), fg="red")
            except OSError as e:
                self.connection_status_label.config(text="Error de conexión: " + str(e), fg="red")
        else:
            self.connection_status_label.config(text="No hay dispositivo seleccionado", fg="red")

    def receive_data(self, stop_thread):
        received_data = ""
        while not stop_thread.is_set():
            try:
                data = self.main_app.client_socket.recv(1024)
                received_data += data.decode('utf-8')  # Assuming UTF-8 encoding
                if '\n' in received_data:  # Assuming newline as delimiter
                    self.main_app.update_frame1(received_data)
                    received_data = ""  # Reset the received data
            except Exception as e:
                self.connection_status_label.config(text="Error de conexión: " + str(e), fg="red")
                self.main_app.connected = False
            time.sleep(0.01)  # Pause for 10 milliseconds

class MainApp(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)

        pygame.mixer.init()

        self.title("Alarma Latido")
        self.geometry("390x694+550+50")
        self.resizable(False, False)

        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)

        self.frame1 = tk.Frame(self.container, bg="white")
        self.frame2 = BluetoothFrame(self.container, self)

        self.current_frame = None
        self.show_frame(self.frame1)

        self.bottom_nav = tk.Frame(self)
        self.bottom_nav.pack(side="bottom", fill="x")

        self.button1 = tk.Button(self.bottom_nav, text="Inicio", font=(fuente, 15), command=self.show_frame1, bg="white", relief="flat")
        self.button2 = tk.Button(self.bottom_nav, text="Dispositivos", font=(fuente, 15), command=self.show_frame2, bg="white", relief="flat")

        self.button1.pack(side="left", fill="both", expand=True)
        self.button2.pack(side="right", fill="both", expand=True)

        self.connected = False
        self.client_socket = None

        self.title_label = tk.Label(self.frame1, text="Alarma Latido", font=(fuente, 20), bg="white")
        self.title_label.pack(pady=10)

        self.frame1_received_data_label = tk.Label(self.frame1, text="", bg="white", font=(fuente, 30))
        self.frame1_received_data_label.pack(pady=10)

        self.normal_heartbeat_label = tk.Label(self.frame1, text="", bg="white", font=(fuente, 20))
        self.normal_heartbeat_label.pack(pady=10)

        self.start_night_button = tk.Button(self.frame1, text="COMENZAR", command=self.toggle_night, bg="white", font=(fuente, 12), relief="flat")
        self.start_night_button.pack(pady=200, fill="x")

        self.connection_status_label = tk.Label(self.frame1, text="", font=(fuente, 12), bg="white")
        self.connection_status_label.config(pady=10)

        self.night_mode_active = False  # Track whether night mode is active

    def show_frame(self, frame):
        if self.current_frame:
            self.current_frame.pack_forget()
        self.current_frame = frame
        frame.pack(fill="both", expand=True)

    def show_frame1(self):
        self.show_frame(self.frame1)

    def show_frame2(self):
        self.show_frame(self.frame2)

    def toggle_night(self):
        if not self.connected:
            self.connection_status_label.config(text="No hay dispositivo Bluetooth conectado", fg="red")
        else:
            if not self.night_mode_active:
                self.start_night()
            else:
                self.stop_night()

    def start_night(self):
        if not hasattr(self, "data_thread") or not self.data_thread or not self.data_thread.is_alive():
            self.frame1_received_data_label.config(text="")
            self.connection_status_label.config(text="")
            # Create a new thread for data reception
            self.stop_thread = threading.Event()
            self.data_thread = threading.Thread(target=self.frame2.receive_data, args=(self.stop_thread,))
            self.data_thread.start()
            # Change the button text
            self.start_night_button.config(text="TERMINAR")
            self.night_mode_active = True
        else:
            self.connection_status_label.config(text="La recepción de datos ya está en curso", fg="red")

    def stop_night(self):
        if self.data_thread and self.data_thread.is_alive():
            # Signal the thread to stop
            self.stop_thread.set()
            self.data_thread.join()
            self.data_thread = None
            # Change the button text
            self.start_night_button.config(text="Comenzar noche")
            self.night_mode_active = False
            # Clear the label
            self.frame1_received_data_label.config(text="")
            self.normal_heartbeat_label.config(text="")


    def update_frame1(self, data):
        try:
            data_as_int = int(data)
            self.frame1_received_data_label.config(text=str(data_as_int))

            if NORMAL_HEART_RATE_MIN <= data_as_int <= NORMAL_HEART_RATE_MAX:
                self.normal_heartbeat_label.config(text="Latidos normales", fg="green")
            else:
                self.normal_heartbeat_label.config(text="Latidos Anormales", fg="red")
                # Play alarm sound for abnormal heart rate
                pygame.mixer.music.load("alarm.mp3")  # Provide the path to your alarm sound file
                pygame.mixer.music.play()

        except ValueError:
            self.frame1_received_data_label.config(text="Received data is not a valid integer")
            self.normal_heartbeat_label.config(text="")

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()