#!/usr/bin/env python3
"""
entry point for running MAPS gui as a module
usage: python -m src.maps
"""
import tkinter as tk
from .gui import MAPSGuiApp


def main():
    """launch the gui application"""
    root = tk.Tk()
    app = MAPSGuiApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
