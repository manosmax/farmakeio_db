import tkinter as tk
from difflib import SequenceMatcher
from tkinter import messagebox, ttk

from screens.utils import HoverTooltip, apply_treeview_striping, enable_vertical_scroll


class ProductOrderScreen(ttk.Frame):
    """Επαναχρησιμοποιήσιμη οθόνη για αναζήτηση/προσθήκη προϊόντων σε καλάθι."""
    FUZZY_THRESHOLD = 0.7

    def __init__(self, parent, controller, config):
        super().__init__(parent, style="Card.TFrame")
        self.controller = controller
        self.config = self._with_defaults(config or {})
        self.total_cost = 0.0
        self.discount_percent = 0.0
        self.products = []
        self._search_index = []
        self._cart_index = {}
        self._last_query = None
        self.suggestion_popup = None
        self.suggestion_list = None
        self.empty_message = None
        self.discount_label = None
        self.base_total_label = None

        self._build_layout()
        self.update_discount()
        self.reload_products(initial=True)

    def _with_defaults(self, config):
        """Συγχωνεύει τις προκαθορισμένες επιλογές με τις ρυθμίσεις της εκάστοτε οθόνης."""
        defaults = {
            "title": "",
            "back_command": None,
            "fetch_products": lambda: [],
            "empty_message": "",
            "cart_title": "🛒 Καλάθι",
            "qty_spin_max": 50,
            "complete_button_text": "Ολοκλήρωση",
            "complete_handler": lambda items, total: (False, "Not configured", "error"),
            "success_title": "Επιτυχία",
            "error_title": "Σφάλμα",
            "status_formatter": lambda item: None,
            "discount_provider": None,
        }
        data = defaults.copy()
        data.update(config)
        return data

    def _build_layout(self):
        """Στήνει το βασικό UI (αποτελέσματα αριστερά / καλάθι δεξιά)."""
        main_container = tk.Frame(self, bg="white")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        main_container.grid_columnconfigure(0, weight=3)
        main_container.grid_columnconfigure(1, weight=1)
        main_container.grid_rowconfigure(0, weight=1)

        left_frame = tk.Frame(main_container, bg="white")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        top_bar = tk.Frame(left_frame, bg="white")
        top_bar.pack(fill="x", pady=(0, 20))
        ttk.Label(top_bar, text=self.config["title"], style="Header.TLabel", font=("Segoe UI", 20, "bold")).pack(
            side="left"
        )
        if self.config["back_command"]:
            ttk.Button(top_bar, text="← Πίσω", style="Secondary.TButton", command=self.config["back_command"]).pack(
                side="right"
            )

        search_frame = tk.Frame(left_frame, bg="#f9fafb", pady=15, padx=15)
        search_frame.pack(fill="x", pady=(0, 20))

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(
            search_frame, width=40, textvariable=self.search_var, style="Modern.TEntry", font=("Segoe UI", 12)
        )
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self.on_search_change)
        self.search_entry.bind("<Return>", self._on_search_submit)
        self.search_entry.bind("<Down>", lambda e: self._handle_entry_navigation(1))
        self.search_entry.bind("<Up>", lambda e: self._handle_entry_navigation(-1))
        self.search_entry.bind("<FocusOut>", lambda e: self.after(150, self.hide_suggestions))
        self.search_entry.bind("<FocusIn>", self._on_entry_focus_in)
        ttk.Button(search_frame, text="🔎", style="Icon.TButton", command=self._on_search_submit).pack(side="left")
        # Το bind_all μας επιτρέπει να κλείνουμε τα προτεινόμενα αποτελέσματα όταν ο χρήστης κάνει κλικ εκτός.
        self.bind_all("<Button-1>", self._handle_outside_click, add="+")

        self.results_container = tk.Frame(left_frame, bg="white")
        self.results_container.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(self.results_container, bg="white", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.results_container, orient="vertical", command=self.canvas.yview)
        self.grid_frame = tk.Frame(self.canvas, bg="white")
        self.grid_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        enable_vertical_scroll(self.canvas)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        right_frame = tk.Frame(main_container, bg="#f3f4f6")
        right_frame.grid(row=0, column=1, sticky="nsew")
        right_frame.grid_rowconfigure(1, weight=1)

        footer_frame = tk.Frame(right_frame, bg="#f3f4f6")
        footer_frame.pack(side="bottom", fill="x", padx=20, pady=20)
        if self.config.get("discount_provider"):
            self.discount_label = tk.Label(
                footer_frame,
                text="",
                font=("Segoe UI", 10, "bold"),
                bg="#f3f4f6",
                fg="#6b7280",
            )
            self.discount_label.pack(anchor="e", pady=(0, 6))

        total_row = tk.Frame(footer_frame, bg="#f3f4f6")
        total_row.pack(fill="x", pady=(0, 15))
        self.total_label = tk.Label(
            total_row,
            text="Σύνολο: 0.00 €",
            font=("Segoe UI", 16, "bold"),
            bg="#f3f4f6",
            fg="#4f46e5",
        )
        self.total_label.pack(side="right")
        self.base_total_label = tk.Label(
            total_row,
            text="",
            font=("Segoe UI", 11, "overstrike"),
            bg="#f3f4f6",
            fg="#9ca3af",
        )
        self.base_total_label.pack(side="right", padx=(0, 8))
        if not self.config.get("discount_provider"):
            self.base_total_label.pack_forget()
        ttk.Button(
            footer_frame,
            text=self.config["complete_button_text"],
            style="Modern.TButton",
            command=self.complete,
        ).pack(fill="x", pady=(0, 10))
        ttk.Button(footer_frame, text="🗑 Διαγραφή", style="Danger.TButton", command=self.delete_item).pack(fill="x")

        tk.Label(right_frame, text=self.config["cart_title"], font=("Segoe UI", 14, "bold"), bg="#f3f4f6").pack(
            side="top", pady=(20, 15), padx=20, anchor="w"
        )

        columns = ("product_id", "product", "qty", "unit_price", "total_row")
        self.tree = ttk.Treeview(right_frame, columns=columns, show="headings")
        self.tree.heading("product_id", text="")
        self.tree.heading("product", text="Προϊόν")
        self.tree.heading("qty", text="Ποσ.")
        self.tree.heading("unit_price", text="Τιμή")
        self.tree.heading("total_row", text="Σύνολο")
        self.tree.column("product_id", width=0, stretch=False)
        self.tree.column("product", anchor="w", width=220, stretch=False)
        self.tree.column("qty", anchor="center", width=90, stretch=False)
        self.tree.column("unit_price", anchor="e", width=110, stretch=False)
        self.tree.column("total_row", anchor="e", width=140, stretch=False)
        self.tree.pack(side="top", fill="both", expand=True, padx=20)
        enable_vertical_scroll(self.tree)

    def refresh(self):
        """Ανανεώνει τα δεδομένα (σε περίπτωση που αλλάξει η έκπτωση ή το stock)."""
        self.update_discount()
        self.reload_products(initial=True)

    def update_discount(self):
        provider = self.config.get("discount_provider")
        if callable(provider):
            try:
                value = float(provider())
            except (TypeError, ValueError):
                value = 0.0
            self.discount_percent = max(0.0, value)
            if self.discount_label:
                self.discount_label.config(text=f"Έκπτωση συμβολαίου: {self.discount_percent:.0f}%")
        else:
            self.discount_percent = 0.0
        self.recalculate()

    def reload_products(self, initial=False):
        """Φορτώνει ξανά τα προϊόντα και ανανεώνει τα αποτελέσματα αναζήτησης."""
        fetcher = self.config["fetch_products"]
        self.products = fetcher() if callable(fetcher) else []
        self._build_search_index()
        self.perform_search(initial=initial)

    def _build_search_index(self):
        """Δημιουργεί δομή για γρήγορο fuzzy search με βάση το όνομα."""
        self._search_index = [(product["onoma"].lower(), product) for product in self.products]

    # --- Search & suggestion logic (same as previous implementation) ---
    def on_search_change(self, *_):
        """Καταγράφει κάθε αλλαγή στο πεδίο αναζήτησης ώστε να ενημερωθούν οι προτάσεις."""
        query = self.search_var.get().strip()
        if self._last_query is not None and query == self._last_query:
            return
        self._last_query = query
        self.update_suggestions(query)

    def update_suggestions(self, query):
        """Ενεργοποιεί λογική fuzzy αναζήτησης και εμφανίζει την popover λίστα."""
        normalized = query.lower()
        matches = []
        if normalized:
            for name_lower, product in self._search_index:
                name = product["onoma"]
                if normalized in name_lower or SequenceMatcher(None, normalized, name_lower).ratio() >= self.FUZZY_THRESHOLD:
                    matches.append(name)
                if len(matches) >= 5:
                    break
        matches = matches[:5]
        if not matches:
            self.hide_suggestions()
            return
        if self.suggestion_popup is None:
            self.suggestion_popup = tk.Toplevel(self)
            self.suggestion_popup.overrideredirect(True)
            self.suggestion_popup.configure(bg="#ffffff", padx=1, pady=1)
            self.suggestion_list = tk.Listbox(
                self.suggestion_popup,
                activestyle="none",
                highlightthickness=0,
                relief="flat",
                borderwidth=0,
            )
            self.suggestion_list.pack(fill="both", expand=True)
            self.suggestion_list.bind("<ButtonRelease-1>", self.on_suggestion_click)
            self.suggestion_list.bind("<Button-1>", self._on_suggestion_press)
            self.suggestion_list.bind("<FocusOut>", lambda e: self.after(0, self.hide_suggestions))
            self.suggestion_list.bind("<Return>", self.on_suggestion_click)
            self.suggestion_list.bind("<Down>", lambda e: self._handle_list_navigation(1))
            self.suggestion_list.bind("<Up>", lambda e: self._handle_list_navigation(-1))
            self.suggestion_list.bind("<Motion>", self._on_suggestion_hover)
            self.suggestion_list.bind("<Leave>", lambda e: self.suggestion_list.selection_clear(0, "end"))
            for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                self.suggestion_list.bind(seq, lambda e: "break")
        self.suggestion_list.delete(0, "end")
        for match in matches:
            self.suggestion_list.insert("end", match)
        self.suggestion_list.configure(height=len(matches))
        self.suggestion_popup.deiconify()
        self.suggestion_popup.update_idletasks()
        entry_x = self.search_entry.winfo_rootx()
        entry_y = self.search_entry.winfo_rooty() + self.search_entry.winfo_height()
        entry_w = self.search_entry.winfo_width()
        popup_h = self.suggestion_list.winfo_reqheight()
        self.suggestion_popup.geometry(f"{entry_w}x{popup_h}+{entry_x}+{entry_y}")
        if not self.suggestion_list.focus_displayof():
            self.suggestion_list.focus_set()

    def on_suggestion_click(self, event):
        """Μεταφέρει το επιλεγμένο όνομα στο πεδίο αναζήτησης και εκτελεί αναζήτηση."""
        if not self.suggestion_list.curselection():
            return
        value = self.suggestion_list.get(self.suggestion_list.curselection()[0])
        self.search_var.set(value)
        self.hide_suggestions(force=True)
        self.perform_search()

    def hide_suggestions(self, force=False):
        """Αποκρύπτει το παράθυρο προτάσεων με βάση την εστίαση ή force flag."""
        if self.suggestion_popup and self.suggestion_list:
            should_hide = force or not self.suggestion_list.focus_displayof()
            if should_hide:
                self.suggestion_list.selection_clear(0, "end")
                self.suggestion_popup.withdraw()

    def _on_suggestion_hover(self, event):
        idx = self.suggestion_list.nearest(event.y)
        self.suggestion_list.selection_clear(0, "end")
        if idx >= 0:
            self.suggestion_list.selection_set(idx)

    def _on_suggestion_press(self, event):
        idx = self.suggestion_list.nearest(event.y)
        if idx >= 0:
            self.suggestion_list.selection_clear(0, "end")
            self.suggestion_list.selection_set(idx)
        return None

    def _on_search_submit(self, *_):
        if self.suggestion_popup and self.suggestion_list:
            selection = self.suggestion_list.curselection()
            if selection:
                value = self.suggestion_list.get(selection[0])
                self.search_var.set(value)
        self.hide_suggestions(force=True)
        self.focus_set()
        self.perform_search()

    def _on_entry_focus_in(self, *_):
        query = self.search_var.get().strip()
        self._last_query = None
        if query:
            self.update_suggestions(query)
            self._last_query = query

    def _handle_outside_click(self, event):
        """Κλείνει την popup όταν ο χρήστης κάνει κλικ εκτός του πεδίου/λίστας."""
        try:
            current_focus = self.focus_get()
        except (tk.TclError, KeyError):
            return
        if self.search_entry != current_focus:
            return
        target = event.widget
        if target is self.search_entry:
            return
        if self.suggestion_list and target is self.suggestion_list:
            return
        if self.suggestion_popup and target is self.suggestion_popup:
            return
        self.hide_suggestions(force=True)
        self.focus_set()

    def _handle_entry_navigation(self, direction):
        return "break" if self._move_suggestion(direction, focus_list=False) else None

    def _handle_list_navigation(self, direction):
        return "break" if self._move_suggestion(direction, focus_list=True) else None

    def _move_suggestion(self, direction, focus_list=True):
        if not self.suggestion_popup or not self.suggestion_list:
            return False
        size = self.suggestion_list.size()
        if size <= 0:
            return False
        selection = self.suggestion_list.curselection()
        if selection:
            idx = (selection[0] + direction) % size
        else:
            idx = 0 if direction > 0 else size - 1
        self.suggestion_list.selection_clear(0, "end")
        self.suggestion_list.selection_set(idx)
        self.suggestion_list.activate(idx)
        if focus_list:
            self.suggestion_list.focus_set()
        return True

    # --- Search results ---
    def perform_search(self, initial=False):
        """Αναζητά προϊόντα με βάση το query και δημιουργεί κάρτες προβολής."""
        if not initial:
            self.hide_suggestions(force=True)
        query = self.search_var.get().strip().lower()
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        self.empty_message = None

        if not query:
            self._show_empty_message(self.config["empty_message"])
            return

        candidates = []
        for name_lower, product in self._search_index:
            if query in name_lower:
                candidates.append((1.0, product))
            else:
                ratio = SequenceMatcher(None, query, name_lower).ratio()
                if ratio >= self.FUZZY_THRESHOLD:
                    candidates.append((ratio, product))

        if not candidates:
            self._show_empty_message("Δεν βρέθηκαν αποτελέσματα για την αναζήτησή σας.")
            return

        candidates.sort(key=lambda item: item[0], reverse=True)
        row, col = 0, 0
        for _, item in candidates:
            self.create_card(item, row, col)
            col += 1
            if col >= 3:
                col, row = 0, row + 1

    def _show_empty_message(self, text):
        """Εμφανίζει ενημερωτικό μήνυμα όταν δεν υπάρχουν αποτελέσματα."""
        if self.empty_message:
            self.empty_message.destroy()
        self.empty_message = ttk.Label(
            self.grid_frame,
            text=text,
            style="SubHeader.TLabel",
            anchor="center",
            justify="center",
        )
        self.empty_message.pack(expand=True, pady=40)

    def create_card(self, item, row, col):
        """Δημιουργεί μια οπτική κάρτα προϊόντος με κουμπί προσθήκης στο καλάθι."""
        card = ttk.Frame(self.grid_frame, style="ProductCard.TFrame", padding=15)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        desc = f"{item.get('katigoria', '')} • {item.get('etairia', '')}"
        ttk.Label(card, text=item["onoma"], style="ProductTitle.TLabel").pack(anchor="w")
        ttk.Label(card, text=desc, style="ProductDesc.TLabel", wraplength=180).pack(anchor="w", pady=(2, 6))
        ttk.Label(card, text=f"{item['arx_kostos_temaxiou']:.2f} €", style="ProductPrice.TLabel").pack(anchor="w")

        status_info = None
        formatter = self.config.get("status_formatter")
        if formatter:
            status_info = formatter(item)
        if status_info:
            status_frame = tk.Frame(card, bg="white")
            status_frame.pack(anchor="w", pady=(2, 0))
            label = tk.Label(
                status_frame,
                text=status_info.get("text", ""),
                bg="white",
                fg=status_info.get("color", "#111827"),
                font=("Segoe UI", 10, "bold"),
            )
            label.pack(side="left")
            tooltip_text = status_info.get("tooltip")
            if tooltip_text:
                HoverTooltip(label, tooltip_text)

        action_frame = tk.Frame(card, bg="white")
        action_frame.pack(fill="x", pady=(5, 0))

        qty_var = tk.StringVar(value="1")
        ttk.Spinbox(
            action_frame,
            from_=1,
            to=self.config["qty_spin_max"],
            width=3,
            textvariable=qty_var,
            style="Modern.TSpinbox",
        ).pack(side="left")

        ttk.Button(
            action_frame,
            text="Προσθήκη",
            style="Compact.TButton",
            command=lambda i=item, q=qty_var: self.add_to_cart(i, q),
        ).pack(side="right")

    # --- Cart actions ---
    def add_to_cart(self, item, qty_var):
        """Εισάγει ή ενημερώνει προϊόν στο καλάθι υπολογίζοντας νέο σύνολο."""
        try:
            q = int(qty_var.get())
        except ValueError:
            q = 1
        q = max(1, q)
        price = float(item["arx_kostos_temaxiou"])
        total = q * price

        product_key = str(item["product_id"])
        row_id = self._cart_index.get(product_key)
        if row_id:
            values = self.tree.item(row_id)["values"]
            current_qty = int(values[2])
            new_qty = current_qty + q
            total = new_qty * price
            self.tree.item(
                row_id,
                values=(values[0], values[1], new_qty, f"{price:.2f}", f"{total:.2f}"),
            )
        else:
            row_id = self.tree.insert(
                "",
                "end",
                values=(item["product_id"], item["onoma"], q, f"{price:.2f}", f"{total:.2f}"),
            )
            self._cart_index[product_key] = row_id
        self.recalculate()

    def delete_item(self):
        """Απομακρύνει τις επιλεγμένες γραμμές από το καλάθι και ανανεώνει τους δείκτες."""
        for item in self.tree.selection():
            values = self.tree.item(item)["values"]
            if values:
                self._cart_index.pop(str(values[0]), None)
            self.tree.delete(item)
        self.recalculate()

    def recalculate(self):
        """Εκ νέου υπολογισμός συνόλου/έκπτωσης για τις ετικέτες στο footer."""
        base_total = sum(float(self.tree.item(c)["values"][4]) for c in self.tree.get_children())
        discount_factor = max(0.0, 1 - (self.discount_percent / 100))
        discounted_total = max(0.0, base_total * discount_factor)
        self.total_cost = discounted_total
        self.total_label.config(text=f"Σύνολο: {discounted_total:.2f} €")
        if self.base_total_label:
            if self.discount_percent > 0:
                if not self.base_total_label.winfo_manager():
                    self.base_total_label.pack(side="right", padx=(0, 8))
                self.base_total_label.config(text=f"Αρχικό: {base_total:.2f} €")
            else:
                self.base_total_label.pack_forget()
        apply_treeview_striping(self.tree)

    def complete(self):
        """Καλεί τον παρεχόμενο χειριστή ολοκλήρωσης με τα προϊόντα του καλαθιού."""
        if self.total_cost <= 0:
            messagebox.showwarning("Προσοχή", "Το καλάθι είναι άδειο.")
            return

        order_items = []
        for child in self.tree.get_children():
            product_id, _, qty, unit_price, _ = self.tree.item(child)["values"]
            order_items.append((int(product_id), int(qty), float(unit_price)))

        handler = self.config["complete_handler"]
        with self.controller.busy_cursor():
            success, msg, level = handler(order_items, self.total_cost)
        if success:
            messagebox.showinfo(self.config["success_title"], msg)
            self.tree.delete(*self.tree.get_children())
            self._cart_index.clear()
            self.recalculate()
        else:
            if level == "warning":
                messagebox.showwarning(self.config["error_title"], msg)
            else:
                messagebox.showerror(self.config["error_title"], msg)
