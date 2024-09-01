import customtkinter as ctk
import pyperclip
import tkinter as tk
import tkinter.messagebox as messagebox
import threading
import time
import json
import os
from PIL import Image, ImageDraw
import pystray

class ModernClipboardManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Ditto")
        self.root.geometry("550x400")
        self.root.resizable(False, False)
        
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.saved_clipboard_content = []
        self.previous_clipboard_content = ""

        self.search_entry = ctk.CTkEntry(self.root, placeholder_text="Search clipboard history...", width=400)
        self.search_entry.pack(pady=(10, 10), padx=10, fill="x")
        self.search_entry.bind("<KeyRelease>", self.search_clipboard)

        self.clipboard_display = ctk.CTkTextbox(self.root, height=250, width=580, wrap="word")
        self.clipboard_display.pack(pady=10, padx=20)

        self.clipboard_display.bind("<Button-3>", self.show_context_menu)  # Right-click event

        self.buttons_frame = ctk.CTkFrame(self.root)
        self.buttons_frame.pack(pady=10)

        self.clear_saved_button = ctk.CTkButton(self.buttons_frame, text="Clear All", command=self.clear_saved_clipboard, width=120)
        self.clear_saved_button.grid(row=0, column=0, padx=10, pady=5)

        self.clear_button = ctk.CTkButton(self.buttons_frame, text="Clear Clipboard", command=self.clear_clipboard, width=120)
        self.clear_button.grid(row=0, column=1, padx=10, pady=5)

        self.export_button = ctk.CTkButton(self.buttons_frame, text="Export History", command=self.export_history, width=120)
        self.export_button.grid(row=0, column=2, padx=10, pady=5)

        self.theme_button = ctk.CTkButton(self.buttons_frame, text="Toggle Theme", command=self.toggle_theme, width=120)
        self.theme_button.grid(row=0, column=3, padx=10, pady=5)

        self.load_clipboard_history()
        self.update_display()

        self.clipboard_thread = threading.Thread(target=self.monitor_clipboard, daemon=True)
        self.clipboard_thread.start()

        self.root.bind("<Button-1>", self.hide_context_menu)

        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Copy", command=self.copy_to_clipboard)
        self.context_menu.add_command(label="Paste", command=self.paste_from_clipboard)

        self.context_menu_shown = False

        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        self.tray_icon = self.create_tray_icon()

    def hide_context_menu(self, event):
        if self.context_menu_shown:
            self.context_menu.unpost()
            self.context_menu_shown = False

    def show_context_menu(self, event):
        if self.context_menu_shown:
            self.context_menu.unpost()
        self.context_menu.post(event.x_root, event.y_root)
        self.context_menu_shown = True

    def copy_to_clipboard(self):
        try:
            selected_text = self.clipboard_display.get("sel.first", "sel.last")
            pyperclip.copy(selected_text)
            messagebox.showinfo("Clipboard", "Copied to clipboard!")
        except tk.TclError:
            messagebox.showwarning("Clipboard", "No text selected!")

    def paste_from_clipboard(self):
        clipboard_content = pyperclip.paste()
        self.clipboard_display.insert(tk.INSERT, clipboard_content)
        messagebox.showinfo("Clipboard", "Pasted from clipboard!")

    def monitor_clipboard(self):
        while True:
            clipboard_content = pyperclip.paste()
            if clipboard_content != self.previous_clipboard_content:
                self.previous_clipboard_content = clipboard_content
                if clipboard_content.strip() and clipboard_content not in self.saved_clipboard_content:
                    self.save_to_history(clipboard_content)
            time.sleep(1)

    def save_to_history(self, content):
        if content not in self.saved_clipboard_content:
            self.saved_clipboard_content.append(content)
            self.update_display()

    def update_display(self):
        self.clipboard_display.delete(1.0, ctk.END)
        for idx, content in enumerate(self.saved_clipboard_content, start=1):
            self.clipboard_display.insert(ctk.END, f"{idx}: {content}\n\n")

    def clear_clipboard(self):
        pyperclip.copy("")
        messagebox.showinfo("Clipboard", "Current clipboard content cleared!")

    def clear_saved_clipboard(self):
        self.saved_clipboard_content.clear()
        self.update_display()
        messagebox.showinfo("Clipboard", "All saved clipboard content cleared!")

    def search_clipboard(self, event=None):
        query = self.search_entry.get().lower()
        self.clipboard_display.delete(1.0, ctk.END)
        for idx, content in enumerate(self.saved_clipboard_content, start=1):
            if query in content.lower():
                self.clipboard_display.insert(ctk.END, f"{idx}: {content}\n\n")

    def export_history(self):
        with open("clipboard_history.json", "w") as file:
            json.dump(self.saved_clipboard_content, file)
        messagebox.showinfo("Clipboard", "Clipboard history exported to clipboard_history.json")

    def toggle_theme(self):
        current_mode = ctk.get_appearance_mode()
        new_mode = "Light" if current_mode == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)

    def on_close(self):
        self.save_clipboard_history()
        self.root.quit()

    def save_clipboard_history(self):
        with open("clipboard_history.json", "w") as file:
            json.dump(self.saved_clipboard_content, file)

    def load_clipboard_history(self):
        if os.path.exists("clipboard_history.json"):
            with open("clipboard_history.json", "r") as file:
                self.saved_clipboard_content = json.load(file)

    def hide_window(self):
        self.root.withdraw()  # Hide the main window
        self.tray_icon.run()

    def create_tray_icon(self):
        image = Image.new('RGB', (64, 64), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)
        draw.rectangle([0, 0, 63, 63], fill="Grey")
        tray_icon = pystray.Icon("clipboard", image, "Ditto", menu=pystray.Menu(
            pystray.MenuItem("Show", self.show_window),
            pystray.MenuItem("Exit", self.exit_application)
        ))
        return tray_icon

    def show_window(self, icon, item):
        self.root.deiconify()  # Show the main window
        self.tray_icon.stop()

    def exit_application(self, icon, item):
        self.save_clipboard_history()
        self.tray_icon.stop()
        self.root.quit()

if __name__ == "__main__":
    root = ctk.CTk()
    clipboard_manager = ModernClipboardManager(root)
    root.mainloop()
