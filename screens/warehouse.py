import tkinter as tk
from tkinter import messagebox, ttk

from models import WarehouseRepository
from screens.order_screen import ProductOrderScreen
from screens.utils import apply_treeview_striping, center_card, enable_vertical_scroll


class ScreenWarehouseMenu(ttk.Frame):
    """Κεντρικό μενού αποθήκης με πρόσβαση στις βασικές λειτουργίες."""

    def __init__(self, parent, controller):
        super().__init__(parent, style="Card.TFrame")
        self.controller = controller

        main_card = center_card(self, width_ratio=0.65, height_ratio=None)

        top_bar = ttk.Frame(main_card, style="Card.TFrame")
        top_bar.pack(fill="x", pady=(0, 10))
        ttk.Label(top_bar, text="Μενού Αποθήκης", style="Header.TLabel").pack(side="left")

        self.user_label = ttk.Label(top_bar, text="", style="Label.TLabel", font=("Segoe UI", 12, "bold"))
        self.user_label.pack(side="right", padx=(10, 0))
        ttk.Button(top_bar, text="Αποσύνδεση", style="Secondary.TButton", command=self.logout).pack(side="right")

        ttk.Label(
            main_card,
            text="Διαχείριση Προμηθειών & Παραγγελιών",
            style="SubHeader.TLabel",
        ).pack(fill="x", pady=(0, 20))

        button_container = ttk.Frame(main_card, style="Card.TFrame")
        button_container.pack(fill="both", expand=True)

        ttk.Button(
            button_container,
            text="📦 Διαχείριση Παραγγελιών Φαρμακείων",
            style="MenuPrimary.TButton",
            command=lambda: controller.show_frame_busy(ScreenWarehouseOrders),
        ).pack(pady=12, fill="x")

        ttk.Button(
            button_container,
            text="🚚 Παραγγελία Προμήθειας",
            style="MenuSecondary.TButton",
            command=lambda: controller.show_frame_busy(ScreenWarehouseSupply),
        ).pack(pady=12, fill="x")

        ttk.Button(
            button_container,
            text="📄 Παραγγελίες προς Προμηθευτές",
            style="MenuSecondary.TButton",
            command=lambda: controller.show_frame_busy(ScreenSupplierOrders),
        ).pack(pady=12, fill="x")

    def logout(self):
        """Καθαρίζει την session και μεταφέρει τον χρήστη στην οθόνη login."""
        answer = messagebox.askyesno("Αποσύνδεση", "Θέλετε να αποσυνδεθείτε;")
        if answer:
            self.controller.current_user = None
            self.controller.current_role = None
            self.controller.show_frame_busy(self.controller.login_screen)

    def refresh(self):
        """Ενημερώνει την ένδειξη ενεργού χρήστη κάθε φορά που ανοίγει η οθόνη."""
        username = self.controller.current_user or ""
        self.user_label.configure(text=f"👤 {username}")


class ScreenWarehouseOrders(ttk.Frame):
    """Διαχείριση παραγγελιών φαρμακείων από την πλευρά της αποθήκης."""
    STATUS_OPTIONS = ["Όλες", "Εκκρεμεί", "Σε επεξεργασία", "Απεστάλη", "Ακυρώθηκε"]
    def __init__(self, parent, controller):
        super().__init__(parent, style="Card.TFrame")
        self.controller = controller

        header = ttk.Frame(self, style="Card.TFrame")
        header.pack(side="top", fill="x", padx=40, pady=30)
        ttk.Label(header, text="Παραγγελίες Φαρμακείων", style="Header.TLabel").pack(side="left", expand=True, fill="x")
        ttk.Button(
            header,
            text="← Πίσω",
            style="Secondary.TButton",
            command=lambda: controller.show_frame_busy(ScreenWarehouseMenu),
        ).pack(side="right")

        actions = ttk.Frame(self, style="Card.TFrame")
        actions.pack(fill="x", padx=40, pady=(0, 20))

        self.auto_order_btn = ttk.Button(
            actions,
            text="🧾 Αυτόματη παραγγελία ελλείψεων",
            style="Secondary.TButton",
            command=self.auto_order_missing,
        )
        self.auto_order_btn.pack(side="left")
        self.auto_order_btn.pack_forget()
        ttk.Button(
            actions,
            text="❌ Ακύρωση",
            style="Secondary.TButton",
            command=self.cancel_order,
        ).pack(side="left", padx=(10, 0))
        ttk.Button(
            actions,
            text="⚙️ Σε επεξεργασία",
            style="Secondary.TButton",
            command=self.mark_processing,
        ).pack(side="left", padx=(10, 0))
        ttk.Button(
            actions,
            text="🚚 Αποστολή",
            style="Modern.TButton",
            command=self.send_selected_order,
        ).pack(side="left", padx=(10, 0))

        filter_frame = ttk.Frame(self, style="Card.TFrame")
        filter_frame.pack(fill="x", padx=40, pady=(0, 15))
        ttk.Label(filter_frame, text="Φίλτρο κατάστασης", style="Label.TLabel").pack(side="left")
        self.status_filter = tk.StringVar(value=self.STATUS_OPTIONS[0])
        filter_combo = ttk.Combobox(
            filter_frame,
            values=self.STATUS_OPTIONS,
            state="readonly",
            width=22,
            textvariable=self.status_filter,
            style="Modern.TCombobox",
        )
        filter_combo.pack(side="left", padx=(10, 0))
        filter_combo.bind("<<ComboboxSelected>>", lambda *_: self.refresh())

        tree_frame = ttk.Frame(self, style="Card.TFrame")
        tree_frame.pack(fill="both", expand=True, padx=40, pady=(0, 40))

        columns = (
            "col_main",
            "col_pharm",
            "col_date",
            "col_qty",
            "col_available",
            "col_shipped",
            "col_total",
            "col_status",
        )
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("col_main", text="ID Παραγγελίας / Φάρμακο")
        self.tree.heading("col_pharm", text="Φαρμακείο")
        self.tree.heading("col_date", text="Ημερομηνία")
        self.tree.heading("col_qty", text="Ποσότητα")
        self.tree.heading("col_available", text="Διαθέσιμα")
        self.tree.heading("col_shipped", text="Απεσταλμένα")
        self.tree.heading("col_total", text="Τιμή/Σύνολο")
        self.tree.heading("col_status", text="Κατάσταση")

        self.tree.column("col_main", anchor="w", width=240, stretch=False)
        self.tree.column("col_pharm", anchor="w", width=200, stretch=False)
        self.tree.column("col_date", anchor="center", width=170, stretch=False)
        self.tree.column("col_qty", width=110, anchor="center", stretch=False)
        self.tree.column("col_available", width=130, anchor="center", stretch=False)
        self.tree.column("col_shipped", width=130, anchor="center", stretch=False)
        self.tree.column("col_total", width=160, anchor="e", stretch=False)
        self.tree.column("col_status", width=160, anchor="center", stretch=False)

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        enable_vertical_scroll(self.tree)

        self.tree.tag_configure("parent", font=("Segoe UI", 10, "bold"))
        self.tree.tag_configure("child", font=("Segoe UI", 10))
        self.tree.bind("<<TreeviewSelect>>", self.on_order_select)
        self.selected_order_id = None
        self.order_items = {}

    def _normalize_order_id(self, raw_value):
        """Μετατρέπει display string (#123) σε ακέραιο ID παραγγελίας."""
        if raw_value is None:
            return None
        if isinstance(raw_value, str):
            raw_value = raw_value.strip().lstrip("#")
            if not raw_value:
                return None
        try:
            return int(raw_value)
        except (TypeError, ValueError):
            return None

    def refresh(self):
        """Ανανεώνει τη λίστα παραγγελιών και κρατά mapping προϊόντων ανά ID."""
        self.tree.delete(*self.tree.get_children())
        self.order_items = {}
        self.selected_order_id = None
        self.auto_order_btn.pack_forget()

        selected_status = self.status_filter.get() if hasattr(self, "status_filter") else "Όλες"
        with self.controller.busy_cursor():
            orders = WarehouseRepository.fetch_pharmacy_orders(selected_status)
        for order in orders:
            display_status = order["katastasi"]
            date_display = order["executed_at"].strftime("%d/%m/%Y %H:%M") if order["executed_at"] else "-"
            parent_id = self.tree.insert(
                "",
                "end",
                values=(
                    f"#{order['order_id']}",
                    order["pharmacy"],
                    date_display,
                    "-",
                    "-",
                    "-",
                    f"{order['arxiko_kostos']:.2f} €",
                    display_status,
                ),
                tags=("parent",),
                open=False,
            )
            self.order_items[order["order_id"]] = order["items"]

            for item in order["items"]:
                row_total = float(item["temaxia_zitisis"]) * float(item["arx_kostos_temaxiou"])
                self.tree.insert(
                    parent_id,
                    "end",
                    values=(
                        f"  ↳ {item['onoma']}",
                        "",
                        "",
                        item["temaxia_zitisis"],
                        item.get("available", 0),
                        item.get("shipped_qty", 0),
                        f"{row_total:.2f} €",
                        "",
                    ),
                    tags=("child",),
                )
        apply_treeview_striping(self.tree)

    def auto_order_missing(self):
        """Δημιουργεί αυτόματα παραγγελία προς προμηθευτές για τα ελλείποντα προϊόντα."""
        if not self.selected_order_id:
            messagebox.showwarning("Προσοχή", "Επιλέξτε μια παραγγελία πρώτα.")
            return
        order_id = self.selected_order_id
        try:
            order_id = int(order_id)
        except (TypeError, ValueError):
            pass
        items = self.order_items.get(order_id, [])
        missing_items = []
        for item in items:
            missing_qty = int(item["temaxia_zitisis"]) - int(item.get("available", 0))
            if missing_qty > 0:
                missing_items.append((item["product_id"], missing_qty, float(item["arx_kostos_temaxiou"])))

        if not missing_items:
            messagebox.showinfo("Αυτόματη Παραγγελία", "Δεν υπάρχουν ελλείψεις για την παραγγελία.")
            return

        with self.controller.busy_cursor():
            success, order_id_or_msg = WarehouseRepository.create_supplier_order(missing_items)
        if not success:
            messagebox.showwarning("Προσοχή", order_id_or_msg)
            return

        messagebox.showinfo(
            "Αυτόματη Παραγγελία",
            f"Η παραγγελία SUP-{order_id_or_msg} δημιουργήθηκε για τις ελλείψεις.",
        )
        self._set_status("Σε επεξεργασία", order_id=order_id, silent=True)
        self.refresh()

    def on_order_select(self, *_):
        """Ανίχνευση επιλογής γραμμής ώστε να εμφανιστεί το κουμπί αυτοματοποιημένης προμήθειας."""
        selected = self.tree.selection()
        if not selected:
            self.selected_order_id = None
            self.auto_order_btn.pack_forget()
            return

        item_id = selected[0]
        if "parent" not in self.tree.item(item_id, "tags"):
            self.selected_order_id = None
            self.auto_order_btn.pack_forget()
            return

        raw_id = self.tree.item(item_id, "values")[0]
        order_id = self._normalize_order_id(raw_id)
        if order_id is None:
            self.selected_order_id = None
            self.auto_order_btn.pack_forget()
            messagebox.showwarning("Προσοχή", "Μη έγκυρο ID παραγγελίας.")
            return
        self.selected_order_id = order_id
        if self._order_has_shortage(order_id):
            if not self.auto_order_btn.winfo_ismapped():
                self.auto_order_btn.pack(side="left")
        else:
            self.auto_order_btn.pack_forget()

    def _order_has_shortage(self, order_id):
        """Ελέγχει αν κάποια γραμμή έχει ζητούμενα τεμάχια περισσότερα από διαθέσιμα."""
        items = self.order_items.get(order_id, [])
        for item in items:
            if int(item.get("available", 0)) < int(item["temaxia_zitisis"]):
                return True
        return False

    def cancel_order(self):
        """Ορίζει την επιλεγμένη παραγγελία ως ακυρωμένη."""
        self._set_status("Ακυρώθηκε")

    def mark_processing(self):
        """Θέτει την παραγγελία σε κατάσταση 'Σε επεξεργασία'."""
        self._set_status("Σε επεξεργασία")

    def send_selected_order(self):
        """Καλεί την επιχειρησιακή λογική αποστολής μειώνοντας απόθεμα."""
        selection = self._get_selected_order()
        if not selection:
            return
        _, order_id = selection
        with self.controller.busy_cursor():
            success, msg = WarehouseRepository.send_order(order_id)
        if success:
            messagebox.showinfo("Επιτυχία", msg)
            self.refresh()
        else:
            messagebox.showwarning("Προσοχή", msg)

    def _get_selected_order(self):
        """Επιστρέφει το tuple (item_id, order_id) όταν έχει επιλεγεί γονική εγγραφή."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Προσοχή", "Επιλέξτε μια παραγγελία (γονική γραμμή).")
            return None
        item_id = selected[0]
        tags = self.tree.item(item_id, "tags")
        if "parent" not in tags:
            messagebox.showwarning("Προσοχή", "Επιλέξτε την παραγγελία, όχι το φάρμακο.")
            return None
        values = self.tree.item(item_id, "values")
        order_id = self._normalize_order_id(values[0])
        if order_id is None:
            messagebox.showwarning("Προσοχή", "Μη έγκυρο ID παραγγελίας.")
            return None
        return item_id, order_id

    def _set_status(self, status, order_id=None, silent=False):
        """Κεντρική ρουτίνα αλλαγής κατάστασης τόσο για UI όσο και για βάση."""
        selection = None
        if order_id is None:
            result = self._get_selected_order()
            if not result:
                return
            selection, order_id = result
        normalized_id = self._normalize_order_id(order_id)
        if normalized_id is None:
            if not silent:
                messagebox.showwarning("Προσοχή", "Μη έγκυρο ID παραγγελίας.")
            return
        order_id = normalized_id
        with self.controller.busy_cursor():
            success, msg = WarehouseRepository.update_order_status(order_id, status)
        if not success:
            if not silent:
                messagebox.showwarning("Προσοχή", msg)
            return
        if not silent:
            messagebox.showinfo("Επιτυχία", msg)
        self.refresh()


class ScreenWarehouseSupply(ProductOrderScreen):
    """Οθόνη δημιουργίας εσωτερικής προμήθειας αποθήκης."""
    def __init__(self, parent, controller):
        self.controller = controller
        config = {
            "title": "Προμήθεια Αποθήκης",
            "back_command": lambda: controller.show_frame_busy(ScreenWarehouseMenu),
            "fetch_products": WarehouseRepository.fetch_supplier_products,
            "empty_message": "Ξεκινήστε την αναζήτηση πληκτρολογώντας το όνομα ενός φαρμάκου.",
            "cart_title": "🛒 Λίστα Προμήθειας",
            "qty_spin_max": 500,
            "complete_button_text": "Αποστολή στους Προμηθευτές",
            "complete_handler": self._complete_order,
            "status_formatter": self._format_status,
            "success_title": "Επιτυχία",
            "error_title": "Προσοχή",
        }
        super().__init__(parent, controller, config)

    def refresh(self):
        """Καλεί εκ νέου τα προϊόντα ώστε να εμφανίζεται ενημερωμένο stock."""
        self.reload_products(initial=True)

    def _format_status(self, item):
        """Δείχνει τα συνολικά διαθέσιμα στην αποθήκη για κάθε προϊόν."""
        stock_qty = int(item.get("stock_qty", 0))
        return {
            "text": f"Σε απόθεμα: {stock_qty}",
            "color": "#111827",
        }

    def _complete_order(self, order_items, total_cost):
        """Στέλνει την επιλεγμένη λίστα προϊόντων στον μηχανισμό δημιουργίας προμήθειας."""
        prepared = []
        for product_id, qty, unit_price in order_items:
            if qty <= 0 or unit_price <= 0:
                continue
            prepared.append((int(product_id), int(qty), float(unit_price)))
        if not prepared:
            return False, "Δεν έχετε επιλέξει προϊόντα.", "warning"
        with self.controller.busy_cursor():
            success, order_id_or_msg = WarehouseRepository.create_supplier_order(prepared)
        if success:
            return True, f"Η παραγγελία SUP-{order_id_or_msg} εστάλη στους προμηθευτές!", "info"
        return False, order_id_or_msg, "warning"


class ScreenSupplierOrders(ttk.Frame):
    """Προβολή/ολοκλήρωση παραγγελιών που στέλνονται στους προμηθευτές."""
    STATUS_OPTIONS = ["Όλες", "Σε εξέλιξη", "Ολοκληρώθηκε"]
    def __init__(self, parent, controller):
        super().__init__(parent, style="Card.TFrame")
        self.controller = controller

        header = ttk.Frame(self, style="Card.TFrame")
        header.pack(fill="x", padx=40, pady=30)
        ttk.Label(header, text="Παραγγελίες προς Προμηθευτές", style="Header.TLabel").pack(side="left", expand=True, fill="x")
        ttk.Button(
            header,
            text="← Πίσω",
            style="Secondary.TButton",
            command=lambda: controller.show_frame_busy(ScreenWarehouseMenu),
        ).pack(side="right")

        action_bar = ttk.Frame(self, style="Card.TFrame")
        action_bar.pack(fill="x", padx=40, pady=(0, 10))
        ttk.Button(
            action_bar,
            text="✅ Ολοκλήρωση Παραγγελίας",
            style="Modern.TButton",
            command=self.mark_complete,
        ).pack(side="left")

        filter_frame = ttk.Frame(self, style="Card.TFrame")
        filter_frame.pack(fill="x", padx=40, pady=(0, 10))
        ttk.Label(filter_frame, text="Φίλτρο κατάστασης", style="Label.TLabel").pack(side="left")
        self.status_filter = tk.StringVar(value=self.STATUS_OPTIONS[0])
        supplier_filter = ttk.Combobox(
            filter_frame,
            values=self.STATUS_OPTIONS,
            state="readonly",
            width=22,
            textvariable=self.status_filter,
            style="Modern.TCombobox",
        )
        supplier_filter.pack(side="left", padx=(10, 0))
        supplier_filter.bind("<<ComboboxSelected>>", lambda *_: self.refresh())

        tree_frame = ttk.Frame(self, style="Card.TFrame")
        tree_frame.pack(fill="both", expand=True, padx=40, pady=(0, 40))

        columns = ("col_main", "col_date", "col_qty", "col_total", "col_status")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("col_main", text="ID Παραγγελίας / Είδος")
        self.tree.heading("col_date", text="Ημερομηνία")
        self.tree.heading("col_qty", text="Ποσότητα")
        self.tree.heading("col_total", text="Σύνολο")
        self.tree.heading("col_status", text="Κατάσταση")

        self.tree.column("col_main", anchor="w", width=260, stretch=False)
        self.tree.column("col_date", anchor="center", width=180, stretch=False)
        self.tree.column("col_qty", width=140, anchor="center", stretch=False)
        self.tree.column("col_total", width=170, anchor="e", stretch=False)
        self.tree.column("col_status", width=170, anchor="center", stretch=False)

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        enable_vertical_scroll(self.tree)

        self.tree.tag_configure("parent", font=("Segoe UI", 10, "bold"))
        self.tree.tag_configure("child", font=("Segoe UI", 10))

    def refresh(self):
        """Ανανεώνει τα δεδομένα JSON και εμπλουτίζει με ονόματα προϊόντων."""
        self.tree.delete(*self.tree.get_children())

        selected_status = self.status_filter.get() if hasattr(self, "status_filter") else "Όλες"
        with self.controller.busy_cursor():
            orders = WarehouseRepository.fetch_supplier_orders(selected_status)
        for order in orders:
            display_id = f"#SUP-{order['supplier_order_id']}"
            created_at = order["created_at"].strftime("%d/%m/%Y %H:%M") if order["created_at"] else "-"
            parent_id = self.tree.insert(
                "",
                "end",
                values=(
                    display_id,
                    created_at,
                    "-",
                    f"{order['total_cost']:.2f} €",
                    order["status"],
                ),
                tags=("parent",),
                open=False,
            )
            for item in order["items"]:
                row_total = float(item["quantity"]) * float(item["unit_price"])
                self.tree.insert(
                    parent_id,
                    "end",
                    values=(f"  ↳ {item['onoma']}", "", item["quantity"], f"{row_total:.2f} €", ""),
                    tags=("child",),
                )
        apply_treeview_striping(self.tree)

    def mark_complete(self):
        """Σημειώνει την επιλεγμένη προμήθεια ως ολοκληρωμένη και ενημερώνει το UI."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Προσοχή", "Επιλέξτε την παραγγελία που θέλετε να ολοκληρώσετε.")
            return

        item_id = selected[0]
        if "parent" not in self.tree.item(item_id, "tags"):
            messagebox.showwarning("Προσοχή", "Επιλέξτε το ID παραγγελίας, όχι τα προϊόντα της.")
            return

        raw_value = self.tree.item(item_id, "values")[0]
        order_id = self._normalize_order_id(raw_value)
        if order_id is None:
            messagebox.showwarning("Προσοχή", "Μη έγκυρο ID παραγγελίας.")
            return
        with self.controller.busy_cursor():
            success, msg = WarehouseRepository.mark_supplier_order_complete(order_id)
        if success:
            self.tree.set(item_id, column="col_status", value="Ολοκληρώθηκε")
            messagebox.showinfo("Επιτυχία", msg)
            self.refresh()
        else:
            messagebox.showwarning("Προσοχή", msg)

    @staticmethod
    def _normalize_order_id(raw_value):
        """Μετατρέπει την ένδειξη #SUP-ΧΧ σε ακέραιο ID."""
        if raw_value is None:
            return None
        if isinstance(raw_value, str):
            raw_value = raw_value.strip()
            if raw_value.startswith("#SUP-"):
                raw_value = raw_value.replace("#SUP-", "", 1)
            raw_value = raw_value.lstrip("#")
            if not raw_value:
                return None
        try:
            return int(raw_value)
        except (TypeError, ValueError):
            return None
