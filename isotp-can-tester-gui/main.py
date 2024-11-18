import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import sys
import can
from can_isotp_sender import CanIsotpSender

class RedirectText:
    """Custom class to redirect stdout and stderr to the GUI text widget"""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.text_widget.configure(state=tk.DISABLED)

    def write(self, message):
        self.text_widget.configure(state=tk.NORMAL)
        self.text_widget.insert(tk.END, message)  # Insert message into the text widget
        self.text_widget.see(tk.END)  # Automatically scroll to the bottom
        self.text_widget.configure(state=tk.DISABLED)

    def flush(self):
        pass  # Must implement flush method to avoid errors

class PCANGUIApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PCAN GUI with Logs")

        # Main layout frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure column and row weights for responsive design
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Initialization frame
        init_frame = ttk.LabelFrame(main_frame, text="CAN Initialization", borderwidth=2, relief="solid")
        init_frame.grid(column=0, row=0, sticky=(tk.W, tk.E), pady=10)

        # Initialize button
        self.init_button = ttk.Button(init_frame, text="Initialize PCAN", command=self.initialize_pcan)
        self.init_button.grid(column=0, row=0, padx=5, pady=5)

        # Shutdown button
        self.shutdown_button = ttk.Button(init_frame, text="Shutdown PCAN", command=self.shutdown_pcan)
        self.shutdown_button.grid(column=1, row=0, padx=5, pady=5)

        # Save log button
        self.save_log_button = ttk.Button(init_frame, text="Save Log", command=self.save_log)
        self.save_log_button.grid(column=2, row=0, padx=5, pady=5)

        # Device selection dropdown menu
        self.device_var = tk.StringVar(value="PCAN_USBBUS1")
        self.device_menu = ttk.Combobox(init_frame, textvariable=self.device_var, values=["PCAN_USBBUS1", "PCAN_USBBUS2"])
        self.device_menu.grid(column=3, row=0, padx=5, pady=5)

        # Bitrate selection dropdown menu
        self.bitrate_var = tk.IntVar(value=500000)
        self.bitrate_menu = ttk.Combobox(init_frame, textvariable=self.bitrate_var, values=[500000, 1000000])
        self.bitrate_menu.grid(column=4, row=0, padx=5, pady=5)

        # ISOTP parameters frame
        isotp_frame = ttk.LabelFrame(main_frame, text="ISOTP Parameters", borderwidth=2, relief="solid")
        isotp_frame.grid(column=0, row=1, sticky=(tk.W, tk.E), pady=10)

        # RXID input
        self.rxid_var = tk.StringVar(value=format(0x7E1, 'X'))
        ttk.Label(isotp_frame, text="RX ID:").grid(column=0, row=0, padx=5, pady=5, sticky=tk.E)
        self.rxid_entry = ttk.Entry(isotp_frame, textvariable=self.rxid_var, width=10)
        self.rxid_entry.grid(column=1, row=0, padx=5, pady=5)

        # TXID input
        self.txid_var = tk.StringVar(value=format(0x7E9, 'X'))
        ttk.Label(isotp_frame, text="TX ID:").grid(column=2, row=0, padx=5, pady=5, sticky=tk.E)
        self.txid_entry = ttk.Entry(isotp_frame, textvariable=self.txid_var, width=10)
        self.txid_entry.grid(column=3, row=0, padx=5, pady=5)

        # stmin input
        self.stmin_var = tk.IntVar(value=6)
        ttk.Label(isotp_frame, text="stmin:").grid(column=0, row=1, padx=5, pady=5, sticky=tk.E)
        self.stmin_entry = ttk.Entry(isotp_frame, textvariable=self.stmin_var, width=5)
        self.stmin_entry.grid(column=1, row=1, padx=5, pady=5)

        # blocksize input
        self.blocksize_var = tk.IntVar(value=2)
        ttk.Label(isotp_frame, text="blocksize:").grid(column=2, row=1, padx=5, pady=5, sticky=tk.E)
        self.blocksize_entry = ttk.Entry(isotp_frame, textvariable=self.blocksize_var, width=5)
        self.blocksize_entry.grid(column=3, row=1, padx=5, pady=5)
        
        # Status indicator
        self.status_label = ttk.Label(init_frame, text="Status: ", anchor=tk.W)
        self.status_label.grid(column=5, row=0, padx=5)
        self.status_indicator = tk.Label(init_frame, bg="red", width=2, height=1)
        self.status_indicator.grid(column=6, row=0, padx=5)

        # CAN data send frame
        can_send_frame = ttk.Frame(main_frame)
        can_send_frame.grid(column=0, row=2, sticky=(tk.W, tk.E))

        # CAN data input
        self.can_data_var = tk.StringVar()
        ttk.Label(can_send_frame, text="Data (Hex):").grid(column=0, row=0, padx=5, pady=5, sticky=tk.E)
        self.can_data_entry = ttk.Entry(can_send_frame, textvariable=self.can_data_var, width=50)
        self.can_data_entry.grid(column=1, row=0, padx=5, pady=5)

        # DLC input
        self.dlc_var = tk.IntVar(value=8)
        ttk.Label(can_send_frame, text="DLC:").grid(column=2, row=0, padx=5, pady=5, sticky=tk.E)
        self.dlc_entry = ttk.Entry(can_send_frame, textvariable=self.dlc_var, width=5)
        self.dlc_entry.grid(column=3, row=0, padx=5, pady=5)

        # Generate data options
        self.generate_option = tk.IntVar(value=0)
        ttk.Radiobutton(can_send_frame, text="Custom Data", variable=self.generate_option, value=0).grid(column=0, row=1, padx=5, pady=5, sticky=tk.W)
        ttk.Radiobutton(can_send_frame, text="Sequential Data (0->0xFF)", variable=self.generate_option, value=1).grid(column=0, row=2, padx=5, pady=5, sticky=tk.W)
        ttk.Radiobutton(can_send_frame, text="Random Data", variable=self.generate_option, value=2).grid(column=0, row=3, padx=5, pady=5, sticky=tk.W)

        # Send button
        self.send_button = ttk.Button(can_send_frame, text="Send CAN Data", command=self.send_can_data)
        self.send_button.grid(column=1, row=1, padx=5, pady=5)

        # Log text box
        self.log_text = ScrolledText(main_frame, wrap=tk.WORD, height=15)
        self.log_text.grid(column=0, row=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)

        # Redirect standard output and error output to the log text box
        self.log_redirector = RedirectText(self.log_text)
        sys.stdout = self.log_redirector
        sys.stderr = self.log_redirector

        # CAN ISOTP sender instance
        self.can_isotp_sender = None

    def generate_sequential_data(self, length):
        return ' '.join([f'{i:02X}' for i in range(length)])

    def generate_random_data(self, length):
        return ' '.join([f'{random.randint(0, 255):02X}' for _ in range(length)])

    def initialize_pcan(self):
        """Initialize the PCAN device"""
        print("Initializing PCAN...")
        try:
            self.can_isotp_sender = CanIsotpSender(
                channel=self.device_var.get(),
                bustype="pcan",
                bitrate=self.bitrate_var.get(),
                rxid=self.rxid_var.get(),
                txid=self.txid_var.get(),
                stmin=self.stmin_var.get(),
                blocksize=self.blocksize_var.get()
            )
            self.can_isotp_sender.initialize()
            print("PCAN initialized successfully!")
            self.set_status("green")  # Change status light to green
        except Exception as e:
            print(f"Failed to initialize PCAN: {e}")
            self.set_status("red")  # Change status light to red

    def shutdown_pcan(self):
        """Shutdown the PCAN device"""
        print("Shutting down PCAN...")
        if self.can_isotp_sender:
            self.can_isotp_sender.shutdown()
            print("PCAN shutdown successfully!")
            self.can_isotp_sender = None
        else:
            print("PCAN is not initialized.")
        self.set_status("red")

    def set_status(self, color):
        """Set the status light color"""
        self.status_indicator.configure(bg=color)

    def send_can_data(self):
        """Send CAN data"""
        if self.can_isotp_sender:
            try:
                dlc = self.dlc_var.get()
                option = self.generate_option.get()

                if option == 0:  # Custom Data
                    custom_data = self.can_data_var.get().strip()
                    data_list = custom_data.split()
                    if len(data_list) < dlc:
                        data_list.extend(['00'] * (dlc - len(data_list)))
                    elif len(data_list) > dlc:
                        data_list = data_list[:dlc]
                    data = ' '.join(data_list)
                elif option == 1:  # Sequential Data
                    data = self.generate_sequential_data(dlc)
                elif option == 2:  # Random Data
                    data = self.generate_random_data(dlc)

                if data:
                    # Validate hex data
                    if all(c in '0123456789abcdefABCDEF' for c in data.replace(' ', '')) and len(data.replace(' ', '')) <= 16:
                        self.can_isotp_sender.send_data(bytearray.fromhex(data), dlc)
                    else:
                        print("Invalid hex data or data length exceeds 8 bytes.")
                else:
                    print("No data to send.")
            except Exception as e:
                print(f"Failed to send CAN data: {e}")
        else:
            print("PCAN is not initialized.")

    def save_log(self):
        """Save the log to a file"""
        from tkinter.filedialog import asksaveasfilename
        file_path = asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            with open(file_path, "w") as file:
                file.write(self.log_text.get("1.0", tk.END))
            print(f"Log saved to {file_path}")

# Main program entry point
if __name__ == "__main__":
    root = tk.Tk()
    app = PCANGUIApp(root)
    root.mainloop()