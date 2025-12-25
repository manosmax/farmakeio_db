import tkinter as tk
from tkinter import messagebox, ttk

from models import (
    CONTRACT_DURATION_CHOICES,
    CONTRACT_DURATION_LOOKUP,
    DISCOUNT_BY_MONTHS,
    InventoryRepository,
    PharmacyRepository,
    calculate_delivery_days,
    format_delivery_remaining,
)
from screens.order_screen import ProductOrderScreen
from screens.utils import apply_treeview_striping, center_card, enable_vertical_scroll


class ScreenOne(ttk.Frame):
    """Κεντρικό μενού φαρμακείου με πρόσβαση σε παραγγελίες, ιστορικό και συμβόλαια."""

    def __init__(self, parent, controller):
        super().__init__(parent, style="Card.TFrame")
        self.controller = controller
        self.has_active_contract = False
        main_card = center_card(self, width_ratio=0.6, height_ratio=None)

        top_bar = ttk.Frame(main_card, style="Card.TFrame")
        top_bar.pack(fill="x", pady=(0, 10))
        ttk.Label(top_bar, text="Μενού Φαρμακείου", style="Header.TLabel").pack(side="left")

        self.user_label = ttk.Label(top_bar, text="", style="Label.TLabel", font=("Segoe UI", 12, "bold"))
        self.user_label.pack(side="right", padx=(10, 0))
        ttk.Button(
            top_bar,
            text="Αποσύνδεση",
            style="Secondary.TButton",
            command=self.logout,
        ).pack(side="right")

        subheader = ttk.Label(
            main_card,
            text="Γρήγορη πρόσβαση στις βασικές λειτουργίες",
            style="SubHeader.TLabel",
        )
        subheader.pack(fill="x", pady=(0, 15))

        button_container = ttk.Frame(main_card, style="Card.TFrame")
        button_container.pack(fill="both", expand=True, pady=(10, 0))

        self.new_order_button = ttk.Button(
            button_container,
            text="➕ Νέα Παραγγελία",
            style="MenuPrimary.TButton",
            command=self.open_new_order,
        )
        self.new_order_button.pack(pady=12, fill="x")

        self.history_button = ttk.Button(
            button_container,
            text="📜 Ιστορικό",
            style="MenuSecondary.TButton",
            command=self.open_history,
        )
        self.history_button.pack(pady=12, fill="x")

        self.contract_button = ttk.Button(
            button_container,
            text="🤝 Συμβόλαιο",
            style="MenuSecondary.TButton",
            command=lambda: controller.show_frame_busy(ScreenContract),
        )
        self.contract_button.pack(pady=12, fill="x")

    def logout(self):
        """Εκκαθαρίζει την τρέχουσα συνεδρία και επιστρέφει στην οθόνη σύνδεσης."""
        answer = messagebox.askyesno("Αποσύνδεση", "Είστε σίγουροι ότι θέλετε να αποσυνδεθείτε;")
        if answer:
            self.controller.current_user = None
            self.controller.current_role = None
            self.controller.show_frame_busy(self.controller.login_screen)

    def refresh(self):
        """Ενημερώνει την ένδειξη χρήστη και ελέγχει αν υπάρχει ενεργό συμβόλαιο."""
        username = self.controller.current_user or ""
        self.user_label.configure(text=f"👤 {username}")
        contract = PharmacyRepository.fetch_contract(username)
        self.has_active_contract = bool(contract and contract.get("is_active"))

    def _require_contract(self):
        """Ελέγχει αν υπάρχει ενεργό συμβόλαιο και προτρέπει τον χρήστη να υπογράψει αν όχι."""
        if self.has_active_contract:
            return True
        answer = messagebox.askyesno(
            "Συμβόλαιο",
            "Δεν υπάρχει ενεργό συμβόλαιο. Θέλετε να μεταβείτε στην υπογραφή τώρα;",
        )
        if answer:
            self.controller.show_frame_busy(ScreenContract)
        return False

    def open_new_order(self):
        """Ανοίγει την οθόνη επιλογής προϊόντων αφού βεβαιωθεί ότι υπάρχει συμβόλαιο."""
        if self._require_contract():
            self.controller.show_frame_busy(ScreenTwo)

    def open_history(self):
        """Μεταφέρει τον χρήστη στο ιστορικό εφόσον επιτρέπεται από το συμβόλαιο."""
        if self._require_contract():
            self.controller.show_frame_busy(ScreenHistory)


class ScreenTwo(ProductOrderScreen):
    def __init__(self, parent, controller):
        self.controller = controller
        config = {
            "title": "Αναζήτηση Φαρμάκων",
            "back_command": lambda: controller.show_frame_busy(ScreenOne),
            "fetch_products": PharmacyRepository.fetch_products,
            "empty_message": "Ξεκινήστε την αναζήτηση πληκτρολογώντας το όνομα ενός φαρμάκου.",
            "cart_title": "🛒 Καλάθι",
            "qty_spin_max": 50,
            "complete_button_text": "Ολοκλήρωση",
            "complete_handler": self._complete_order,
            "status_formatter": self._format_status,
            "success_title": "Επιτυχία",
            "error_title": "Σφάλμα",
            "discount_provider": lambda: PharmacyRepository.get_active_discount(self.controller.current_user),
        }
        super().__init__(parent, controller, config)

    def _format_status(self, item):
        """Δίνει οπτική ένδειξη διαθεσιμότητας για κάθε προϊόν στην λίστα."""
        stock_qty = int(item.get("stock_qty", 0))
        in_stock = stock_qty > 0
        status_text = "Διαθέσιμο" if in_stock else "Εκτός αποθέματος"
        status_color = "#059669" if in_stock else "#dc2626"
        tooltip = None
        if not in_stock:
            tooltip = "Το προϊόν δεν βρίσκεται σε απόθεμα και θα επηρεάσει τον χρόνο παράδοσης."
        return {
            "text": f"{status_text} ({stock_qty})",
            "color": status_color,
            "tooltip": tooltip,
        }

    def _complete_order(self, order_items, total_cost):
        """Μεταφέρει το καλάθι στην υπηρεσία δημιουργίας παραγγελίας και εμφανίζει ETA."""
        success, msg = PharmacyRepository.create_order(
            self.controller.current_user,
            order_items,
            total_cost,
        )
        if success:
            product_ids = [product_id for product_id, _, _ in order_items]
            available_map = InventoryRepository.fetch_available_counts(product_ids)
            eta_days = calculate_delivery_days(order_items, available_map)
            day_label = "ημέρα" if eta_days == 1 else "ημέρες"
            full_msg = f"{msg}\nΕκτιμώμενη παράδοση σε {eta_days} {day_label}."
            return True, full_msg, "info"
        return False, msg, "error"

class ScreenHistory(ttk.Frame):
    """Προβολή ιστορικού παραγγελιών φαρμακείου με φίλτρο κατάστασης."""
    STATUS_OPTIONS = ["Όλες", "Εκκρεμεί", "Σε επεξεργασία", "Απεστάλη", "Ακυρώθηκε"]

    def __init__(self, parent, controller):
        super().__init__(parent, style="Card.TFrame")
        self.controller = controller

        header = ttk.Frame(self, style="Card.TFrame")
        header.pack(fill="x", padx=40, pady=30)
        ttk.Label(header, text="Ιστορικό", style="Header.TLabel").pack(side="left")
        ttk.Button(
            header,
            text="← Πίσω",
            style="Secondary.TButton",
            command=lambda: self._go_back(controller),
        ).pack(side="right")

        filter_frame = ttk.Frame(self, style="Card.TFrame")
        filter_frame.pack(fill="x", padx=40, pady=(0, 10))
        ttk.Label(filter_frame, text="Φίλτρο κατάστασης", style="Label.TLabel").pack(side="left")
        self.status_filter = tk.StringVar(value=self.STATUS_OPTIONS[0])
        self.status_combo = ttk.Combobox(
            filter_frame,
            values=self.STATUS_OPTIONS,
            state="readonly",
            width=20,
            textvariable=self.status_filter,
            style="Modern.TCombobox",
        )
        self.status_combo.pack(side="left", padx=(10, 0))
        self.status_combo.bind("<<ComboboxSelected>>", lambda *_: self.refresh())

        tree_frame = ttk.Frame(self, style="Card.TFrame")
        tree_frame.pack(fill="both", expand=True, padx=40, pady=20)
        columns = ("col_main", "col_date", "col_qty", "col_shipped", "col_total", "col_status", "col_delivery")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("col_main", text="Παραγγελία / Προϊόν")
        self.tree.heading("col_date", text="Ημερομηνία")
        self.tree.heading("col_qty", text="Ποσότητα")
        self.tree.heading("col_shipped", text="Απεσταλμένα")
        self.tree.heading("col_total", text="Τιμή/Σύνολο")
        self.tree.heading("col_status", text="Κατάσταση")
        self.tree.heading("col_delivery", text="Παράδοση")

        self.tree.column("col_main", anchor="w", width=220, stretch=False)
        self.tree.column("col_date", anchor="center", width=170, stretch=False)
        self.tree.column("col_qty", anchor="center", width=110, stretch=False)
        self.tree.column("col_shipped", anchor="center", width=130, stretch=False)
        self.tree.column("col_total", anchor="e", width=140, stretch=False)
        self.tree.column("col_status", anchor="center", width=150, stretch=False)
        self.tree.column("col_delivery", anchor="center", width=150, stretch=False)

        self.tree.tag_configure("parent", font=("Segoe UI", 10, "bold"))
        self.tree.tag_configure("child", font=("Segoe UI", 10))
        self.tree.pack(fill="both", expand=True)

    def _go_back(self, controller):
        """Επιστρέφει στο κεντρικό μενού φαρμακείου με busy cursor για ομαλή μετάβαση."""
        controller.show_frame_busy(ScreenOne)

    def refresh(self):
        """Φορτώνει το ιστορικό για το συνδεδεμένο φαρμακείο και ενημερώνει το TreeView."""
        self.tree.delete(*self.tree.get_children())
        user = self.controller.current_user
        selected_status = self.status_filter.get() if hasattr(self, "status_filter") else "Όλες"
        with self.controller.busy_cursor():
            orders = PharmacyRepository.fetch_history(user, selected_status)
        for order in orders:
            date_display = order["executed_at"].strftime("%d/%m/%Y %H:%M") if order["executed_at"] else "-"
            # Η παράδοση μπορεί να είναι ακριβής ημερομηνία αποστολής ή εκτίμηση.
            if order["katastasi"] == "Ακυρώθηκε":
                delivery_display = "-"
            elif order.get("shipment_at"):
                delivery_display = order["shipment_at"].strftime("%d/%m/%Y %H:%M")
            elif order["executed_at"]:
                delivery_display = format_delivery_remaining(order["executed_at"], order["items"])
            else:
                delivery_display = "-"
            parent_id = self.tree.insert(
                "",
                "end",
                values=(
                    f"#{order['order_id']}",
                    date_display,
                    "-",
                    "-",
                    f"{order['arxiko_kostos']:.2f} €",
                    order["katastasi"],
                    delivery_display,
                ),
                tags=("parent",),
                open=False,
            )
            for product in order["items"]:
                row_total = float(product["temaxia_zitisis"]) * float(product["arx_kostos_temaxiou"])
                self.tree.insert(
                    parent_id,
                    "end",
                    values=(
                        f"  ↳ {product['onoma']}",
                        "",
                        product["temaxia_zitisis"],
                        product.get("shipped_qty", 0),
                        f"{row_total:.2f} €",
                        "",
                        "",
                    ),
                    tags=("child",),
                )
        apply_treeview_striping(self.tree)


class ScreenContract(ttk.Frame):
    """Οθόνη διαχείρισης και υπογραφής συμβολαίων για τα φαρμακεία."""
    FREQUENCY_OPTIONS = ["Εβδομαδιαία", "Δεκαπενθήμερη", "Μηνιαία"]
    PAYMENT_OPTIONS = ["Μετρητά", "Κάρτα", "Τραπεζική Μεταφορά"]
    DURATION_LABELS = {months: label for label, months in CONTRACT_DURATION_CHOICES}

    def __init__(self, parent, controller):
        super().__init__(parent, style="Card.TFrame")
        self.controller = controller
        self.current_contract = None
        self.contracts = []
        header = ttk.Frame(self, style="Card.TFrame")
        header.pack(fill="x", padx=40, pady=30)
        ttk.Label(header, text="Συμβόλαιο", style="Header.TLabel").pack(side="left")
        ttk.Button(
            header,
            text="← Πίσω",
            style="Secondary.TButton",
            command=lambda: self._go_back(controller),
        ).pack(side="right")

        self.body = ttk.Frame(self, style="Card.TFrame")
        self.body.pack(fill="both", expand=True, padx=40, pady=(0, 40))

        self.status_section = ttk.LabelFrame(self.body, text="Τρέχον Συμβόλαιο", padding=(20, 15))
        self.status_message = ttk.Label(self.status_section, text="", style="Label.TLabel")
        self.status_message.pack(anchor="w", pady=(0, 10))

        info_grid = ttk.Frame(self.status_section, style="Card.TFrame")
        info_grid.pack(fill="x")
        self.status_values = {}
        labels = [
            ("Συχνότητα Παράδοσης", "frequency_label"),
            ("Τρόπος Πληρωμής", "payment_label"),
            ("Διάρκεια", "duration_label"),
            ("Έκπτωση", "discount_percent"),
            ("Ημ/νία Υπογραφής", "hm_ypografis"),
            ("Ημ/νία Λήξης", "hm_liksis"),
        ]
        for idx, (text, key) in enumerate(labels):
            ttk.Label(info_grid, text=text, style="Label.TLabel").grid(row=idx, column=0, sticky="w", pady=4, padx=(0, 20))
            value = ttk.Label(info_grid, text="-", style="SubHeader.TLabel")
            value.grid(row=idx, column=1, sticky="w", pady=4)
            self.status_values[key] = value
        self.cancel_button = ttk.Button(
            self.status_section, text="Ακύρωση Συμβολαίου", style="Danger.TButton", command=self.cancel_contract
        )

        self.empty_label = ttk.Label(
            self.body,
            text="",
            style="SubHeader.TLabel",
            anchor="center",
            justify="center",
        )

        self.sign_section = ttk.LabelFrame(self.body, text="Υπογραφή Νέου Συμβολαίου", padding=(20, 15))
        ttk.Label(
            self.sign_section,
            text="Επιλέξτε διάρκεια, συχνότητα παράδοσης και τρόπο πληρωμής για το νέο συμβόλαιο.",
            style="SubHeader.TLabel",
            wraplength=600,
        ).pack(anchor="w", pady=(0, 15))

        form_grid = ttk.Frame(self.sign_section, style="Card.TFrame")
        form_grid.pack(fill="x")

        duration_labels = [label for label, _ in CONTRACT_DURATION_CHOICES]
        ttk.Label(form_grid, text="Διάρκεια", style="Label.TLabel").grid(row=0, column=0, sticky="w", pady=5)
        self.duration_combo = ttk.Combobox(
            form_grid,
            values=duration_labels,
            state="readonly",
            width=25,
            style="Modern.TCombobox",
        )
        if duration_labels:
            self.duration_combo.current(len(duration_labels) - 1)
        self.duration_combo.grid(row=0, column=1, sticky="w", pady=5, padx=(0, 15))
        self.duration_combo.bind("<<ComboboxSelected>>", lambda *_: self._update_discount_hint())
        self.discount_hint = ttk.Label(form_grid, text="", style="Small.TLabel")
        self.discount_hint.grid(row=0, column=2, sticky="w")
        self._update_discount_hint()

        ttk.Label(form_grid, text="Συχνότητα Παράδοσης", style="Label.TLabel").grid(row=1, column=0, sticky="w", pady=5)
        self.frequency_combo = ttk.Combobox(
            form_grid,
            values=self.FREQUENCY_OPTIONS,
            state="readonly",
            width=25,
            style="Modern.TCombobox",
        )
        self.frequency_combo.current(2)
        self.frequency_combo.grid(row=1, column=1, sticky="w", pady=5, padx=(0, 15))

        ttk.Label(form_grid, text="Τρόπος Πληρωμής", style="Label.TLabel").grid(row=2, column=0, sticky="w", pady=5)
        self.payment_combo = ttk.Combobox(
            form_grid,
            values=self.PAYMENT_OPTIONS,
            state="readonly",
            width=25,
            style="Modern.TCombobox",
        )
        self.payment_combo.current(2)
        self.payment_combo.grid(row=2, column=1, sticky="w", pady=5, padx=(0, 15))

        ttk.Button(self.sign_section, text="Υπογραφή Συμβολαίου", style="Modern.TButton", command=self.sign_contract).pack(
            anchor="e", pady=(20, 0)
        )

        self.history_section = ttk.LabelFrame(self.body, text="Ιστορικό Συμβολαίων", padding=(20, 15))
        self.history_section.pack(fill="both", expand=True, pady=(30, 0))
        self.history_container = ttk.Frame(self.history_section, style="Card.TFrame")
        columns = ("id", "start", "end", "duration", "discount", "freq", "pay", "status")
        self.history_tree = ttk.Treeview(self.history_container, columns=columns, show="headings", height=6)
        headings = {
            "id": "ID",
            "start": "Υπογραφή",
            "end": "Λήξη",
            "duration": "Διάρκεια",
            "discount": "Έκπτωση",
            "freq": "Συχνότητα",
            "pay": "Πληρωμή",
            "status": "Κατάσταση",
        }
        for key, title in headings.items():
            self.history_tree.heading(key, text=title)
        self.history_tree.column("id", width=90, anchor="w", stretch=False)
        self.history_tree.column("start", width=140, anchor="center", stretch=False)
        self.history_tree.column("end", width=140, anchor="center", stretch=False)
        self.history_tree.column("duration", width=110, anchor="center", stretch=False)
        self.history_tree.column("discount", width=110, anchor="center", stretch=False)
        self.history_tree.column("freq", width=150, anchor="center", stretch=False)
        self.history_tree.column("pay", width=150, anchor="center", stretch=False)
        self.history_tree.column("status", width=120, anchor="center", stretch=False)
        # Χρησιμοποιούμε ξεχωριστό scrollbar για να μπορεί ο χρήστης να δει παλαιότερα συμβόλαια.
        history_scroll = ttk.Scrollbar(self.history_container, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=history_scroll.set)
        self.history_tree.pack(side="left", fill="both", expand=True)
        history_scroll.pack(side="right", fill="y")
        enable_vertical_scroll(self.history_tree)
        self.history_empty_label = ttk.Label(
            self.history_section, text="Δεν υπάρχουν προηγούμενα συμβόλαια.", style="SubHeader.TLabel"
        )

    def refresh(self):
        """Καλείται σε κάθε προβολή της οθόνης για να φέρει συμβόλαια και να ενημερώσει την κατάσταση."""
        username = self.controller.current_user
        with self.controller.busy_cursor():
            self.contracts = PharmacyRepository.fetch_contracts(username)
            self.current_contract = PharmacyRepository.select_current_contract(self.contracts)
        self._render_state()
        self._render_history()

    def _render_state(self):
        """Αποφασίζει ποια panels θα είναι ορατά (status, φόρμα, notice) και ενημερώνει τις τιμές."""
        for widget in (self.status_section, self.empty_label, self.sign_section):
            widget.pack_forget()
        notice_text = ""
        if self.current_contract:
            self.status_section.pack(fill="x", pady=(0, 20))
            contract = self.current_contract
            status_text = "Ενεργό" if contract.get("is_active") else "Έχει λήξει"
            status_color = "#059669" if contract.get("is_active") else "#dc2626"
            self.status_message.configure(text=status_text, foreground=status_color)
            for key, label in self.status_values.items():
                if key == "duration_label":
                    value = self._format_duration_label(contract.get("duration_months"))
                elif key == "discount_percent":
                    value = self._format_discount_display(contract.get("discount_percent"))
                else:
                    value = contract.get(key)
                if hasattr(value, "strftime"):
                    label.configure(text=value.strftime("%d/%m/%Y"))
                else:
                    label.configure(text=value or "-")
            if contract.get("is_active"):
                self.cancel_button.pack(anchor="e", pady=(15, 0))
            else:
                self.cancel_button.pack_forget()
                notice_text = "Το συμβόλαιο έχει λήξει. Υπογράψτε νέο για να συνεχίσετε."
        else:
            self.status_section.pack_forget()
            notice_text = "Δεν υπάρχει ενεργό συμβόλαιο. Συμπληρώστε τα στοιχεία για να υπογράψετε νέο."

        if notice_text:
            self.empty_label.configure(text=notice_text)
            self.empty_label.pack(fill="x", pady=(0, 20))
        else:
            self.empty_label.pack_forget()

        should_show_form = not self.current_contract or not self.current_contract.get("is_active")
        if should_show_form:
            self.sign_section.pack(fill="x")
        else:
            self.sign_section.pack_forget()

    def _render_history(self):
        """Ενημερώνει το TreeView ιστορικού ή δείχνει μήνυμα όταν δεν υπάρχουν συμβόλαια."""
        for child in self.history_tree.get_children():
            self.history_tree.delete(child)
        self.history_container.pack_forget()
        self.history_empty_label.pack_forget()

        if not self.contracts:
            self.history_empty_label.pack(fill="x")
            return

        self.history_container.pack(fill="both", expand=True)
        for contract in self.contracts:
            start = contract.get("hm_ypografis")
            end = contract.get("hm_liksis")
            start_display = start.strftime("%d/%m/%Y") if hasattr(start, "strftime") else "-"
            end_display = end.strftime("%d/%m/%Y") if hasattr(end, "strftime") else "-"
            duration_display = self._format_duration_label(contract.get("duration_months"))
            discount_display = self._format_discount_display(contract.get("discount_percent"))
            status_text = "Ενεργό" if contract.get("is_active") else "Ληγμένο"
            self.history_tree.insert(
                "",
                "end",
                values=(
                    f"#{contract['agreement_id']}",
                    start_display,
                    end_display,
                    duration_display,
                    discount_display,
                    contract.get("frequency_label", "-"),
                    contract.get("payment_label", "-"),
                    status_text,
                ),
            )
        apply_treeview_striping(self.history_tree)

    @classmethod
    def _format_duration_label(cls, months):
        """Μετατρέπει ακέραιους μήνες σε φιλική ετικέτα (π.χ. '1 έτος')."""
        try:
            months = int(months or 0)
        except (TypeError, ValueError):
            return "-"
        if months <= 0:
            return "-"
        label = cls.DURATION_LABELS.get(months)
        if label:
            return label
        if months == 1:
            return "1 μήνας"
        return f"{months} μήνες"

    @staticmethod
    def _format_discount_display(percent):
        """Format helper για να εμφανίζονται οι εκπτώσεις με ποσοστό."""
        try:
            percent = float(percent or 0)
        except (TypeError, ValueError):
            percent = 0
        return f"{percent:.0f}%"

    def _update_discount_hint(self):
        """Υπολογίζει γρήγορα την αναμενόμενη έκπτωση για το επιλεγμένο πακέτο."""
        label = self.duration_combo.get()
        months = CONTRACT_DURATION_LOOKUP.get(label)
        percent = 0
        if months is not None:
            for term, value in sorted(DISCOUNT_BY_MONTHS.items()):
                if months >= term:
                    percent = value
        self.discount_hint.configure(text=f"Έκπτωση: {percent}%")

    def sign_contract(self):
        """Στέλνει τις επιλογές διάρκειας/συχνότητας/πληρωμής για δημιουργία νέου συμβολαίου."""
        duration = self.duration_combo.get()
        frequency = self.frequency_combo.get()
        payment = self.payment_combo.get()
        with self.controller.busy_cursor():
            success, msg = PharmacyRepository.sign_contract(self.controller.current_user, duration, frequency, payment)
        if success:
            messagebox.showinfo("Συμβόλαιο", msg)
            self.refresh()
        else:
            messagebox.showerror("Συμβόλαιο", msg)

    def cancel_contract(self):
        """Ακυρώνει το ενεργό συμβόλαιο αφού ζητήσει επιβεβαίωση."""
        answer = messagebox.askyesno("Ακύρωση", "Είστε βέβαιοι ότι θέλετε να ακυρώσετε το συμβόλαιο;")
        if not answer:
            return
        with self.controller.busy_cursor():
            success, msg = PharmacyRepository.cancel_contract(self.controller.current_user)
        if success:
            messagebox.showinfo("Συμβόλαιο", msg)
            self.refresh()
        else:
            messagebox.showerror("Συμβόλαιο", msg)

    def _go_back(self, controller):
        """Επιστρέφει στο μενού φαρμακείου κρατώντας ενιαία εμπειρία πλοήγησης."""
        controller.show_frame_busy(ScreenOne)
