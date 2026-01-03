from tkinter import messagebox, ttk
from models import AuthManager
from screens.utils import center_card


class ScreenLogin(ttk.Frame):
    """Οθόνη σύνδεσης χρηστών με μετάβαση σε φαρμακείο/αποθήκη."""

    def __init__(self, parent, controller):
        super().__init__(parent, style="Card.TFrame")
        self.controller = controller


        content_frame = center_card(self, width_ratio=0.5, height_ratio=0.75)

        ttk.Label(content_frame, text="Καλωσήρθατε", style="Header.TLabel").pack(pady=(0, 5))
        ttk.Label(content_frame, text="Συνδεθείτε για να συνεχίσετε", style="SubHeader.TLabel").pack(pady=(0, 30))


        form_container = ttk.Frame(content_frame, style="Card.TFrame")
        form_container.pack(fill="x", padx=20)

        ttk.Label(form_container, text="Όνομα Χρήστη", style="Label.TLabel").pack(anchor="w", pady=(0, 5))
        self.user_entry = ttk.Entry(form_container, style="Modern.TEntry", font=("Segoe UI", 11))
        self.user_entry.pack(fill="x", pady=(0, 15))

        ttk.Label(form_container, text="Κωδικός Πρόσβασης", style="Label.TLabel").pack(anchor="w", pady=(0, 5))
        self.pass_entry = ttk.Entry(form_container, style="Modern.TEntry", font=("Segoe UI", 11), show="•")
        self.pass_entry.pack(fill="x", pady=(0, 25))

        ttk.Button(form_container, text="Είσοδος", style="Modern.TButton", command=self.login).pack(fill="x",
                                                                                                    pady=(0, 10))


        ttk.Separator(content_frame, orient="horizontal").pack(fill="x", pady=20)

        ttk.Label(content_frame, text="Δεν έχετε λογαριασμό;", style="Small.TLabel").pack(pady=(0, 5))
        ttk.Button(
            content_frame,
            text="Εγγραφή",
            style="Secondary.TButton",
            command=self._go_to_register,
        ).pack(fill="x", padx=20)

    def login(self):
        """Χειρίζεται τη διαδικασία σύνδεσης."""
        raw_username = self.user_entry.get().strip()
        username = raw_username.lower()
        password = self.pass_entry.get().strip()

        with self.controller.busy_cursor():
            success, msg, role = AuthManager.login(username, password)

        if success:
            self.user_entry.delete(0, "end")
            self.pass_entry.delete(0, "end")
            self.controller.current_user = username
            self.controller.current_role = role

            if role == "Φαρμακείο":
                self.controller.show_frame_busy(self.controller.pharmacy_menu_screen)
            elif role == "Προσωπικό Αποθήκης":
                self.controller.show_frame_busy(self.controller.warehouse_menu_screen)
            else:
                messagebox.showerror("Σφάλμα", "Άγνωστος ρόλος χρήστη.")
        else:
            messagebox.showerror("Σφάλμα Σύνδεσης", msg)

    def _go_to_register(self):
        with self.controller.busy_cursor():
            self.controller.show_frame(ScreenRegister)


class ScreenRegister(ttk.Frame):
    """Οθόνη δημιουργίας νέου λογαριασμού με βελτιωμένη ευθυγράμμιση."""

    def __init__(self, parent, controller):
        super().__init__(parent, style="Card.TFrame")
        self.controller = controller


        content_frame = center_card(self, width_ratio=0.7, height_ratio=0.9)

        ttk.Label(content_frame, text="Δημιουργία Λογαριασμού", style="Header.TLabel").pack(pady=(0, 20))


        self.form_inner = ttk.Frame(content_frame, style="Card.TFrame")
        self.form_inner.pack(fill="x", padx=40)
        self.form_inner.columnconfigure(1, weight=1)  # Entries will expand, labels won't


        self.create_form_row("Ονοματεπώνυμο", "name_entry", 0)
        self.create_form_row("Όνομα Χρήστη", "user_entry", 1)
        self.create_form_row("Τηλέφωνο", "phone_entry", 2)
        self.create_form_row("Κωδικός", "pass_entry", 3, show="•")
        self.create_form_row("Επιβεβαίωση", "confirm_entry", 4, show="•")


        ttk.Label(self.form_inner, text="Ιδιότητα", style="Label.TLabel").grid(row=5, column=0, sticky="w", pady=10)
        self.role_combo = ttk.Combobox(
            self.form_inner,
            values=["Φαρμακείο", "Προσωπικό Αποθήκης"],
            state="readonly",
            font=("Segoe UI", 11),
            style="Modern.TCombobox",
        )
        self.role_combo.grid(row=5, column=1, sticky="ew", pady=10)
        self.role_combo.current(0)
        self.role_combo.bind("<<ComboboxSelected>>", self.toggle_pharmacy_fields)


        self.pharmacy_frame = ttk.LabelFrame(content_frame, text="Στοιχεία Φαρμακείου", padding=(15, 10))
        self.pharmacy_frame.columnconfigure(1, weight=1)

        ttk.Label(self.pharmacy_frame, text="ΑΦΜ", style="Label.TLabel").grid(row=0, column=0, sticky="w", pady=5)
        self.afm_entry = ttk.Entry(self.pharmacy_frame, style="Modern.TEntry", font=("Segoe UI", 11))
        self.afm_entry.grid(row=0, column=1, padx=(10, 0), pady=5, sticky="ew")

        ttk.Label(self.pharmacy_frame, text="Διεύθυνση", style="Label.TLabel").grid(row=1, column=0, sticky="w", pady=5)
        self.address_entry = ttk.Entry(self.pharmacy_frame, style="Modern.TEntry", font=("Segoe UI", 11))
        self.address_entry.grid(row=1, column=1, padx=(10, 0), pady=5, sticky="ew")

        self.pharmacy_frame.pack(fill="x", padx=40, pady=10)


        self.btn_container = ttk.Frame(content_frame, style="Card.TFrame")
        self.btn_container.pack(fill="x", padx=40, pady=20)

        self.register_button = ttk.Button(self.btn_container, text="Εγγραφή", style="Modern.TButton",
                                          command=self.register)
        self.register_button.pack(fill="x", pady=(0, 10))

        ttk.Button(
            self.btn_container,
            text="Πίσω στη Σύνδεση",
            style="Secondary.TButton",
            command=self._back_to_login,
        ).pack(fill="x")

        self.reset_form()

    def create_form_row(self, label_text, attr_name, row_idx, show=None):
        """Helper to create a standard grid row for the form."""
        ttk.Label(self.form_inner, text=label_text, style="Label.TLabel").grid(row=row_idx, column=0, sticky="w",
                                                                               pady=5, padx=(0, 15))
        entry = ttk.Entry(self.form_inner, style="Modern.TEntry", font=("Segoe UI", 11), show=show)
        entry.grid(row=row_idx, column=1, sticky="ew", pady=5)
        setattr(self, attr_name, entry)

    def register(self):
        """Εγγραφή με έλεγχο στοιχείων."""
        username = self.user_entry.get().strip().lower()
        password = self.pass_entry.get().strip()
        confirm = self.confirm_entry.get().strip()
        fullname = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()
        role = self.role_combo.get()

        if password != confirm:
            messagebox.showerror("Σφάλμα", "Οι κωδικοί δεν ταιριάζουν.")
            return

        pharmacy_details = None
        if role == "Φαρμακείο":
            pharmacy_details = {
                "afm": self.afm_entry.get().strip(),
                "address": self.address_entry.get().strip(),
            }

        with self.controller.busy_cursor():
            success, msg = AuthManager.register(username, password, role, fullname, phone, pharmacy_details)

        if success:
            messagebox.showinfo("Επιτυχία", msg)
            self.reset_form()
            self.controller.show_frame_busy(ScreenLogin)
        else:
            messagebox.showerror("Σφάλμα", msg)

    def toggle_pharmacy_fields(self, *_):
        """Δυναμική εμφάνιση των πεδίων ΑΦΜ/Διεύθυνσης."""
        if self.role_combo.get() == "Φαρμακείο":
            if not self.pharmacy_frame.winfo_ismapped():
                self.pharmacy_frame.pack(fill="x", padx=40, pady=10, before=self.btn_container)
        else:
            if self.pharmacy_frame.winfo_ismapped():
                self.pharmacy_frame.pack_forget()

    def reset_form(self):
        """Καθαρισμός όλων των πεδίων."""
        for entry in (self.name_entry, self.user_entry, self.phone_entry,
                      self.pass_entry, self.confirm_entry, self.afm_entry, self.address_entry):
            entry.delete(0, "end")
        self.role_combo.current(0)
        self.toggle_pharmacy_fields()

    def _back_to_login(self):
        with self.controller.busy_cursor():
            self.controller.show_frame(ScreenLogin)