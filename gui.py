"""Verbatim Playground: a small desktop window to write and run Verbatim programs.
Usage:  python gui.py        (uses tkinter, which comes with Python)"""
import os
import re
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

HERE = os.path.dirname(os.path.abspath(__file__))
EXAMPLES = os.path.join(HERE, "examples")
TIMEOUT = 5          # seconds; stops accidental infinite loops


class Playground:
    def __init__(self, root):
        self.root = root
        root.title("Verbatim Playground")
        root.geometry("1000x600")

        # ---- top bar ----
        bar = ttk.Frame(root, padding=6)
        bar.pack(fill="x")
        ttk.Label(bar, text="Example:").pack(side="left")
        names = sorted(f for f in os.listdir(EXAMPLES) if f.endswith(".vbt")) if os.path.isdir(EXAMPLES) else []
        self.example = ttk.Combobox(bar, values=names, state="readonly", width=20)
        self.example.pack(side="left", padx=4)
        self.example.bind("<<ComboboxSelected>>", self.load_example)
        ttk.Button(bar, text="Open...", command=self.open_file).pack(side="left", padx=2)
        ttk.Button(bar, text="Save as...", command=self.save_file).pack(side="left", padx=2)
        ttk.Button(bar, text="Clear output", command=self.clear_output).pack(side="right", padx=2)
        ttk.Button(bar, text="Run  \u25b6  (F5)", command=self.run).pack(side="right", padx=2)

        # ---- editor | output ----
        panes = ttk.PanedWindow(root, orient="horizontal")
        panes.pack(fill="both", expand=True, padx=6, pady=(0, 4))
        font = ("Consolas", 12)

        left = ttk.Frame(panes)
        ttk.Label(left, text="Program").pack(anchor="w")
        self.editor = tk.Text(left, font=font, undo=True, wrap="none", width=50)
        sb = ttk.Scrollbar(left, command=self.editor.yview)
        self.editor.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.editor.pack(fill="both", expand=True)
        self.editor.tag_configure("errline", background="#ffd6d6")
        panes.add(left, weight=3)

        right = ttk.Frame(panes)
        ttk.Label(right, text="Output").pack(anchor="w")
        self.output = tk.Text(right, font=font, state="disabled", wrap="word", width=40,
                              background="#f4f4f8")
        self.output.pack(fill="both", expand=True)
        self.output.tag_configure("error", foreground="#b00020")
        self.output.tag_configure("ok", foreground="#1b5e20")
        panes.add(right, weight=2)

        self.status = ttk.Label(root, text="Ready", padding=(8, 2))
        self.status.pack(fill="x")

        # ---- key bindings ----
        root.bind("<F5>", lambda e: self.run())
        root.bind("<Control-Return>", lambda e: self.run())
        self.editor.bind("<Tab>", self.on_tab)
        self.editor.bind("<Return>", self.on_return)
        self.editor.bind("<Key>", lambda e: self.editor.tag_remove("errline", "1.0", "end"))

        first = os.path.join(EXAMPLES, "factorial.vbt")
        if os.path.exists(first):
            self.example.set("factorial.vbt")
            self.load_path(first)

    # ---------- editor helpers ----------
    def on_tab(self, event):
        self.editor.insert("insert", "    ")
        return "break"

    def on_return(self, event):
        line = self.editor.get("insert linestart", "insert")
        indent = re.match(r"\s*", line).group(0)
        if line.rstrip().endswith("{"):
            indent += "    "
        self.editor.insert("insert", "\n" + indent)
        self.editor.see("insert")
        return "break"

    def load_path(self, path):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", text)
        self.editor.edit_reset()
        self.clear_output()

    def load_example(self, _event=None):
        self.load_path(os.path.join(EXAMPLES, self.example.get()))

    def open_file(self):
        path = filedialog.askopenfilename(initialdir=EXAMPLES,
                                          filetypes=[("Verbatim", "*.vbt"), ("All files", "*.*")])
        if path:
            self.load_path(path)
            self.example.set("")

    def save_file(self):
        path = filedialog.asksaveasfilename(initialdir=EXAMPLES, defaultextension=".vbt",
                                            filetypes=[("Verbatim", "*.vbt")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.editor.get("1.0", "end-1c"))
            self.status.config(text=f"Saved {os.path.basename(path)}")

    # ---------- output helpers ----------
    def clear_output(self):
        self.output.config(state="normal")
        self.output.delete("1.0", "end")
        self.output.config(state="disabled")
        self.editor.tag_remove("errline", "1.0", "end")

    def write(self, text, tag=None):
        self.output.config(state="normal")
        self.output.insert("end", text, tag)
        self.output.config(state="disabled")

    # ---------- running ----------
    def run(self):
        self.clear_output()
        source = self.editor.get("1.0", "end-1c")
        with tempfile.NamedTemporaryFile("w", suffix=".vbt", delete=False, encoding="utf-8") as f:
            f.write(source)
            path = f.name
        try:
            # Runs the exact same command as the terminal: python verbatim.py <file>
            proc = subprocess.run(
                [sys.executable, os.path.join(HERE, "verbatim.py"), path],
                capture_output=True, text=True, encoding="utf-8", timeout=TIMEOUT, cwd=HERE,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        except subprocess.TimeoutExpired:
            self.write(f"Stopped: the program ran for more than {TIMEOUT} seconds.\n"
                       "Hint: check for a while loop that never ends.\n", "error")
            self.status.config(text="Timed out")
            return
        finally:
            os.remove(path)

        if proc.returncode == 0:
            self.write(proc.stdout)
            self.write("\n(finished)\n" if proc.stdout else "(finished, no output)\n", "ok")
            self.status.config(text="Finished successfully")
        else:
            message = proc.stdout or proc.stderr
            self.write(message, "error")
            m = re.search(r"on line (\d+)", message)
            if m:
                n = int(m.group(1))
                self.editor.tag_add("errline", f"{n}.0", f"{n}.end")
                self.editor.see(f"{n}.0")
            self.status.config(text="Error (see the output panel)")


def main():
    root = tk.Tk()
    Playground(root)
    root.mainloop()


if __name__ == "__main__":
    main()
