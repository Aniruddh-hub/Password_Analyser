import threading
import customtkinter as ctk
from analyzer import analyze_password

class PasswordAnalyzerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Password Analyzer")
        self.geometry("600x700")
        self.resizable(False, False)
        
        self.grid_columnconfigure(0, weight=1)
        
        # Debounce timer
        self.analyze_timer = None
        self.current_thread = None
        
        self._build_ui()
        
    def _build_ui(self):
        # Header
        header = ctk.CTkLabel(self, text="Password Analyzer", font=ctk.CTkFont(size=28, weight="bold"))
        header.grid(row=0, column=0, pady=(30, 10))
        
        subtitle = ctk.CTkLabel(self, text="Check strength, find breaches, and get recommendations", text_color="gray")
        subtitle.grid(row=1, column=0, pady=(0, 30))
        
        # Input Frame
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.grid(row=2, column=0, padx=40, sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)
        
        self.password_var = ctk.StringVar()
        self.password_var.trace_add("write", self._on_password_change)
        
        self.pwd_entry = ctk.CTkEntry(
            input_frame, 
            textvariable=self.password_var,
            placeholder_text="Enter a password to analyze...",
            width=400,
            height=45,
            font=ctk.CTkFont(size=16),
            show="*"
        )
        self.pwd_entry.grid(row=0, column=0, sticky="ew")
        
        self.show_pwd_btn = ctk.CTkButton(
            input_frame,
            text="Show",
            width=60,
            height=45,
            command=self._toggle_password_visibility
        )
        self.show_pwd_btn.grid(row=0, column=1, padx=(10, 0))
        
        # Strength Meter
        self.meter_progress = ctk.CTkProgressBar(self, width=520, height=10)
        self.meter_progress.set(0)
        self.meter_progress.grid(row=3, column=0, pady=(30, 10), padx=40)
        
        self.strength_label = ctk.CTkLabel(self, text="Strength: None", font=ctk.CTkFont(size=14, weight="bold"))
        self.strength_label.grid(row=4, column=0)
        
        # Results Card
        self.results_card = ctk.CTkFrame(self, corner_radius=15)
        self.results_card.grid(row=5, column=0, padx=40, pady=20, sticky="nsew")
        self.grid_rowconfigure(5, weight=1)
        self.results_card.grid_columnconfigure(0, weight=1)
        
        # Crack time
        self.crack_time_label = ctk.CTkLabel(self.results_card, text="Time to Crack: -", font=ctk.CTkFont(size=14))
        self.crack_time_label.grid(row=0, column=0, pady=(20, 5), padx=20, sticky="w")
        
        # Pwned count
        self.pwned_label = ctk.CTkLabel(self.results_card, text="Breaches Found: -", font=ctk.CTkFont(size=14))
        self.pwned_label.grid(row=1, column=0, pady=5, padx=20, sticky="w")
        
        # Warnings & Suggestions
        self.warning_label = ctk.CTkLabel(self.results_card, text="", text_color="#FF6B6B", font=ctk.CTkFont(size=14, weight="bold"))
        self.warning_label.grid(row=2, column=0, pady=5, padx=20, sticky="w")
        
        self.suggestions_textbox = ctk.CTkTextbox(self.results_card, width=480, height=120, fg_color="transparent")
        self.suggestions_textbox.grid(row=3, column=0, pady=(5, 20), padx=20, sticky="nsew")
        self.suggestions_textbox.configure(state="disabled")

    def _toggle_password_visibility(self):
        current_show = self.pwd_entry.cget("show")
        if current_show == "*":
            self.pwd_entry.configure(show="")
            self.show_pwd_btn.configure(text="Hide")
        else:
            self.pwd_entry.configure(show="*")
            self.show_pwd_btn.configure(text="Show")

    def _on_password_change(self, *args):
        password = self.password_var.get()
        if self.analyze_timer:
            self.after_cancel(self.analyze_timer)
        
        # Set a loading state if length > 0
        if len(password) > 0:
            self.strength_label.configure(text="Analyzing...")
            # Debounce to avoid querying API on every single keystroke
            self.analyze_timer = self.after(500, self._start_analysis, password)
        else:
            self._update_ui_empty()

    def _start_analysis(self, password):
        # Run the heavy analysis (network IO) in a separate thread
        self.current_thread = threading.Thread(target=self._run_analysis, args=(password,), daemon=True)
        self.current_thread.start()

    def _run_analysis(self, password):
        result = analyze_password(password)
        # Schedule GUI update on the main thread
        self.after(0, self._update_ui, result, password)
        
    def _update_ui_empty(self):
        self.meter_progress.set(0)
        self.meter_progress.configure(progress_color="gray")
        self.strength_label.configure(text="Strength: None")
        self.crack_time_label.configure(text="Time to Crack: -")
        self.pwned_label.configure(text="Breaches Found: -", text_color="gray")
        self.warning_label.configure(text="")
        self.suggestions_textbox.configure(state="normal")
        self.suggestions_textbox.delete("0.0", "end")
        self.suggestions_textbox.configure(state="disabled")
        
    def _update_ui(self, result, requested_password):
        # If the user typed something else while this was processing, ignore
        if self.password_var.get() != requested_password:
            return

        score = result["score"]
        if score == 0:
            color = "#FF4B4B" # Red
            text = "Very Weak"
            val = 0.1
        elif score == 1:
            color = "#FF8C00" # Orange
            text = "Weak"
            val = 0.3
        elif score == 2:
            color = "#FFD700" # Yellow
            text = "Fair"
            val = 0.5
        elif score == 3:
            color = "#32CD32" # Green
            text = "Good"
            val = 0.8
        else:
            color = "#00FF00" # Bright Green
            text = "Strong"
            val = 1.0
            
        self.meter_progress.set(val)
        self.meter_progress.configure(progress_color=color)
        self.strength_label.configure(text=f"Strength: {text}")
        
        self.crack_time_label.configure(text=f"Time to Crack: {result['crack_time_str']}")
        
        # Breaches
        pwned_count = result['pwned_count']
        if pwned_count == -1:
            self.pwned_label.configure(text="Breaches Found: Error connecting to API", text_color="orange")
        elif pwned_count > 0:
            self.pwned_label.configure(text=f"Breaches Found: {pwned_count:,} times (DO NOT USE)", text_color="#FF4B4B")
        else:
            self.pwned_label.configure(text="Breaches Found: 0 (Safe)", text_color="#32CD32")

        # Feedback
        feedback = result["feedback"]
        warning = feedback.get("warning", "")
        suggestions = feedback.get("suggestions", [])
        
        if warning:
            self.warning_label.configure(text=f"Warning: {warning}")
        else:
            self.warning_label.configure(text="")
            
        self.suggestions_textbox.configure(state="normal")
        self.suggestions_textbox.delete("0.0", "end")
        
        if suggestions:
            suggestion_text = "\n".join([f"• {msg}" for msg in suggestions])
            self.suggestions_textbox.insert("0.0", suggestion_text)
        elif pwned_count == 0 and score >= 3:
            self.suggestions_textbox.insert("0.0", "This is a strong, safe password.")
            
        self.suggestions_textbox.configure(state="disabled")
