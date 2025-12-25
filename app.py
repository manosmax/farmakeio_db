import tkinter as tk
from contextlib import contextmanager
from tkinter import ttk

from screens import (
    ScreenContract,
    ScreenHistory,
    ScreenLogin,
    ScreenOne,
    ScreenRegister,
    ScreenSupplierOrders,
    ScreenTwo,
    ScreenWarehouseMenu,
    ScreenWarehouseOrders,
    ScreenWarehouseSupply,
)


class App(tk.Tk):
    """Κεντρικό παράθυρο της εφαρμογής με διαχείριση οθονών και θεματικών."""

    def __init__(self):
        super().__init__()

        self.title("Order System Pro")
        self._init_window_state()
        self.configure(bg="#f0f2f5")

        # Αποθηκεύουμε ποιος χρήστης είναι ενεργός και τι ρόλο έχει.
        self.current_user = None
        self.current_role = None

        style = ttk.Style(self)
        style.theme_use("clam")

        bg_color = "#f0f2f5"
        card_color = "#ffffff"
        primary_color = "#4f46e5"
        primary_hover = "#4338ca"
        danger_color = "#dc2626"
        danger_hover = "#b91c1c"
        text_color = "#1f2937"
        input_bg = "#f9fafb"

        style.configure("Card.TFrame", background=card_color, relief="flat")
        style.configure("Main.TFrame", background=bg_color)

        style.configure("Header.TLabel", font=("Segoe UI", 26, "bold"), background=card_color, foreground=text_color)
        style.configure("SubHeader.TLabel", font=("Segoe UI", 12), background=card_color, foreground="#6b7280")
        style.configure("Total.TLabel", font=("Segoe UI", 18, "bold"), background=card_color, foreground=primary_color)
        style.configure("Label.TLabel", font=("Segoe UI", 11), background=card_color, foreground=text_color)
        style.configure("Small.TLabel", font=("Segoe UI", 9), background=card_color, foreground="#6b7280")
        style.configure("TLabelframe", background=card_color, foreground=text_color)
        style.configure("TLabelframe.Label", background=card_color, foreground=text_color, font=("Segoe UI", 10, "bold"))

        style.configure("ProductCard.TFrame", background="white", relief="solid", borderwidth=1)
        style.configure("ProductTitle.TLabel", font=("Segoe UI", 12, "bold"), background="white", foreground=text_color)
        style.configure("ProductPrice.TLabel", font=("Segoe UI", 11, "bold"), background="white", foreground=primary_color)
        style.configure("ProductDesc.TLabel", font=("Segoe UI", 9), background="white", foreground="#6b7280")

        style.configure(
            "Modern.TButton",
            font=("Segoe UI", 11, "bold"),
            background=primary_color,
            foreground="white",
            borderwidth=0,
            focuscolor="none",
            padding=(20, 10),
        )
        style.map("Modern.TButton", background=[("active", primary_hover), ("pressed", "#312e81")])
        style.configure(
            "Compact.TButton",
            font=("Segoe UI", 10, "bold"),
            background=primary_color,
            foreground="white",
            borderwidth=0,
            padding=(12, 6),
        )
        style.map("Compact.TButton", background=[("active", primary_hover), ("pressed", "#312e81")])
        style.configure(
            "Icon.TButton",
            font=("Segoe UI", 12, "bold"),
            background=primary_color,
            foreground="white",
            borderwidth=0,
            padding=(10, 6),
        )
        style.map("Icon.TButton", background=[("active", primary_hover), ("pressed", "#312e81")])

        style.configure(
            "Secondary.TButton",
            font=("Segoe UI", 11),
            background="#e5e7eb",
            foreground="#374151",
            borderwidth=0,
            padding=(15, 8),
        )
        style.map("Secondary.TButton", background=[("active", "#d1d5db")])

        style.configure(
            "Danger.TButton",
            font=("Segoe UI", 11, "bold"),
            background=danger_color,
            foreground="white",
            borderwidth=0,
            focuscolor="none",
            padding=(20, 10),
        )
        style.map("Danger.TButton", background=[("active", danger_hover)])

        style.configure(
            "MenuPrimary.TButton",
            font=("Segoe UI", 12, "bold"),
            background=primary_color,
            foreground="white",
            borderwidth=0,
            padding=(24, 12),
        )
        style.map("MenuPrimary.TButton", background=[("active", primary_hover), ("pressed", "#312e81")])

        style.configure(
            "MenuSecondary.TButton",
            font=("Segoe UI", 11),
            background="#e5e7eb",
            foreground="#111827",
            borderwidth=0,
            padding=(20, 10),
        )
        style.map("MenuSecondary.TButton", background=[("active", "#d1d5db")])

        style.configure("Modern.TEntry", fieldbackground=input_bg, borderwidth=1, relief="solid", padding=8)
        style.configure("Modern.TSpinbox", fieldbackground=input_bg, borderwidth=1, relief="solid", padding=6)

        style.configure(
            "Modern.TCombobox",
            background=card_color,
            fieldbackground=input_bg,
            foreground=text_color,
            arrowcolor=primary_color,
            borderwidth=1,
            relief="solid",
            padding=8,
        )

        style.map(
            "Modern.TCombobox",
            fieldbackground=[("readonly", input_bg)],
            selectbackground=[("readonly", input_bg)],
            selectforeground=[("readonly", text_color)],
            background=[("active", input_bg)],
        )

        style.configure(
            "Treeview",
            background="white",
            foreground=text_color,
            rowheight=30,
            fieldbackground="white",
            font=("Segoe UI", 11),
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 10, "bold"),
            background="#f3f4f6",
            foreground="#374151",
            relief="flat",
        )
        style.map("Treeview", background=[("selected", primary_color)], foreground=[("selected", "white")])

        self._bind_shortcuts()

        outer_container = tk.Frame(self, bg=bg_color)
        outer_container.pack(fill="both", expand=True)

        self.card = ttk.Frame(outer_container, style="Card.TFrame")
        self.card.pack(fill="both", expand=True, padx=40, pady=40)
        self._busy_count = 0

        self.frames = {}
        self.login_screen = ScreenLogin
        self.pharmacy_menu_screen = ScreenOne
        self.warehouse_menu_screen = ScreenWarehouseMenu

        for screen_cls in (
            ScreenLogin,
            ScreenRegister,
            ScreenOne,
            ScreenTwo,
            ScreenHistory,
            ScreenContract,
            ScreenWarehouseMenu,
            ScreenWarehouseOrders,
            ScreenSupplierOrders,
            ScreenWarehouseSupply,
        ):
            frame = screen_cls(self.card, self)
            self.frames[screen_cls] = frame
            frame.place(relwidth=1, relheight=1)

        self.show_frame(ScreenLogin)

    def show_frame(self, screen_cls):
        """Προβάλει την ζητούμενη οθόνη και καλεί τυχόν refresh."""
        frame = self.frames[screen_cls]
        if hasattr(frame, "refresh"):
            frame.refresh()
        frame.tkraise()

    def show_frame_busy(self, screen_cls):
        """Βοηθητική μέθοδος για εναλλαγή οθόνης με busy cursor."""
        with self.busy_cursor():
            self.show_frame(screen_cls)

    @contextmanager
    def busy_cursor(self, message=None):
        """Εναλλάσσει τον δείκτη ποντικιού σε 'απασχολημένο' όσο διαρκεί μια διεργασία."""
        try:
            self._busy_count += 1
            if self._busy_count == 1:
                self.config(cursor="watch")
                self.update_idletasks()
            yield
        finally:
            self._busy_count = max(0, self._busy_count - 1)
            if self._busy_count == 0:
                self.config(cursor="")

    def _init_window_state(self):
        """Ρυθμίζει αρχικά μεγέθη παραθύρου και προσπαθεί να το μεγιστοποιήσει."""
        self.minsize(600, 400)
        self.geometry("1200x800")
        self.after(0, self._maximize_window)

    def _maximize_window(self):
        """Προσπαθεί να μεγιστοποιήσει το παράθυρο ανάλογα με την πλατφόρμα."""
        self.update_idletasks()
        try:
            self.state("zoomed")
            return
        except tk.TclError:
            pass

        try:
            self.attributes("-zoomed", True)
        except tk.TclError:
            pass

    def _bind_shortcuts(self):
        """Δημιουργεί καθολικά shortcuts (Ctrl+A) τόσο για Entry όσο και για Text widgets."""
        def select_all_entry(event):
            event.widget.select_range(0, "end")
            event.widget.icursor("end")
            return "break"

        def select_all_text(event):
            event.widget.tag_add("sel", "1.0", "end-1c")
            return "break"

        for cls in ("Entry", "TEntry"):
            self.bind_class(cls, "<Control-a>", select_all_entry)
            self.bind_class(cls, "<Control-A>", select_all_entry)
        for cls in ("Text",):
            self.bind_class(cls, "<Control-a>", select_all_text)
            self.bind_class(cls, "<Control-A>", select_all_text)


if __name__ == "__main__":
    App().mainloop()
