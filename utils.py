import tkinter as tk
from tkinter import ttk


def center_card(parent, width_ratio=0.5, height_ratio=0.7, padding=30):
    """Δημιουργεί κάρτα-πλαίσιο κεντραρισμένη σε γονέα με σχετικές αναλογίες."""
    frame = ttk.Frame(parent, style="Card.TFrame", padding=padding)
    place_args = {"relx": 0.5, "rely": 0.5, "relwidth": width_ratio, "anchor": "center"}
    if height_ratio is not None:
        place_args["relheight"] = height_ratio
    frame.place(**place_args)
    return frame


def enable_vertical_scroll(widget):
    """Ενεργοποιεί το scroll του τροχού ποντικιού σε widget (Treeview/Canvas κτλ)."""

    def _on_mousewheel(event):
        if event.delta:
            widget.yview_scroll(int(-event.delta / 120), "units")
        elif event.num == 4:
            widget.yview_scroll(-1, "units")
        elif event.num == 5:
            widget.yview_scroll(1, "units")
        return "break"

    def _bind_all(_):
        widget.bind_all("<MouseWheel>", _on_mousewheel)
        widget.bind_all("<Button-4>", _on_mousewheel)
        widget.bind_all("<Button-5>", _on_mousewheel)

    def _unbind_all(_):
        widget.unbind_all("<MouseWheel>")
        widget.unbind_all("<Button-4>")
        widget.unbind_all("<Button-5>")

    widget.bind("<Enter>", _bind_all)
    widget.bind("<Leave>", _unbind_all)


def apply_treeview_striping(tree, even="#ffffff", odd="#f9fafb"):
    """Ορίζει εναλλάξ χρωματισμό γραμμών χωρίς να αλλοιώνει τα υπάρχοντα tags."""
    tree.tag_configure("row_even", background=even)
    tree.tag_configure("row_odd", background=odd)

    index = 0

    def _apply(item_id):
        nonlocal index
        row_tag = "row_even" if index % 2 == 0 else "row_odd"
        tags = list(tree.item(item_id, "tags") or ())
        if row_tag not in tags:
            tags.append(row_tag)
        tree.item(item_id, tags=tuple(tags))
        index += 1
        for child_id in tree.get_children(item_id):
            _apply(child_id)

    for top_id in tree.get_children(""):
        _apply(top_id)


class HoverTooltip:
    """Απλό tooltip που εμφανίζεται όταν περνά ο δείκτης πάνω από widget."""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show_tooltip)
        widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, *_):
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 10
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw,
            text=self.text,
            justify="left",
            background="#111827",
            foreground="#f9fafb",
            relief="solid",
            borderwidth=1,
            font=("Segoe UI", 9),
            padx=6,
            pady=4,
        )
        label.pack()

    def hide_tooltip(self, *_):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None
