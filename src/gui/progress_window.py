import tkinter as tk
from tkinter import ttk

from src.gui.theme import Theme


class ProgressWindow(tk.Toplevel):
    def __init__(self, parent: tk.Tk, total_runs: int = 1):
        super().__init__(parent)
        self.parent = parent
        self.total_runs = total_runs
        self.is_complete = False

        self.theme = Theme()
        self.bg_color = self.theme.COLORS["bg_primary"]
        self.text_color = self.theme.COLORS["text_primary"]
        self.button_color = self.theme.COLORS["accent_secondary"]
        self.success_color = self.theme.COLORS["success"]

        self._setup_window()
        self._create_progress_ui()

    def _setup_window(self):
        self.title("Simulation Running...")
        self.geometry("600x300")
        self.configure(bg=self.bg_color)
        self.resizable(False, False)

        self.transient(self.parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_close_attempt)

        self.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - 500) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - 280) // 2
        self.geometry(f"+{x}+{y}")

    def _create_progress_ui(self):
        self.main_frame = tk.Frame(self, bg=self.bg_color)
        self.main_frame.pack(expand=True, fill=tk.BOTH, padx=30, pady=30)

        self.status_label = tk.Label(
            self.main_frame,
            text="Preparing simulation...",
            bg=self.bg_color,
            fg=self.text_color,
            font=("Arial", 14),
        )
        self.status_label.pack(pady=(0, 20))

        style = ttk.Style()
        style.configure(
            "Simulation.Horizontal.TProgressbar",
            thickness=25,
            troughcolor=self.theme.COLORS["bg_secondary"],
            background=self.theme.COLORS["accent_primary"],
        )
        self.progress_bar = ttk.Progressbar(
            self.main_frame,
            length=400,
            mode="determinate",
            maximum=self.total_runs,
            style="Simulation.Horizontal.TProgressbar",
        )
        self.progress_bar.pack(pady=10)

        self.progress_text = tk.Label(
            self.main_frame,
            text=f"0/{self.total_runs} runs",
            bg=self.bg_color,
            fg=self.theme.COLORS["text_secondary"],
            font=("Arial", 10),
        )
        self.progress_text.pack(pady=(5, 0))

        self.ok_button = tk.Button(
            self.main_frame,
            text="OK",
            command=self._on_ok_clicked,
            bg=self.button_color,
            fg=self.text_color,
            font=("Arial", 11),
            width=10,
            cursor="hand2",
        )

    def _on_close_attempt(self):
        if self.is_complete:
            self.destroy()

    def _on_ok_clicked(self):
        self.destroy()

    def update_progress(self, current_run: int, total_runs: int):
        self.progress_bar["value"] = current_run
        self.progress_text.config(text=f"{current_run}/{total_runs} runs")
        self.status_label.config(text=f"Running simulation {current_run}/{total_runs}...")

    def show_completion(self, summary_text: str | None = None):
        self.is_complete = True
        self.title("Simulation Complete")

        if summary_text:
            self.status_label.config(
                text=summary_text,
                fg=self.text_color,
                font=("Arial", 12),
            )
        else:
            self.status_label.config(
                text="✓ Simulation Complete",
                fg=self.text_color,
                font=("Arial", 14),
            )

        self.progress_bar["value"] = self.total_runs
        self.progress_text.config(text=f"{self.total_runs}/{self.total_runs} runs completed")
        self.ok_button.pack(pady=(20, 0))
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def show_error(self, error_message: str):
        self.is_complete = True
        self.title("Simulation Failed")

        self.status_label.config(
            text="✗ Simulation Failed",
            fg=self.theme.COLORS["danger"],
            font=("Arial", 16, "bold"),
        )

        error_label = tk.Label(
            self.main_frame,
            text=error_message[:200] + "..." if len(error_message) > 200 else error_message,
            bg=self.bg_color,
            fg=self.theme.COLORS["danger"],
            font=("Arial", 10),
            wraplength=400,
        )
        error_label.pack(pady=10)

        self.progress_bar.pack_forget()
        self.progress_text.pack_forget()
        self.ok_button.pack(pady=(20, 0))
        self.protocol("WM_DELETE_WINDOW", self.destroy)
