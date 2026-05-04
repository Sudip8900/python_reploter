import sys
import tkinter as tk
from digitizer.ui import DigitizerApp

if __name__ == "__main__":
    root = tk.Tk()
    app = DigitizerApp(root)
    root.mainloop()
