"""Απομονωμένη αποθήκη JSON για πρόχειρη καταγραφή παραγγελιών προς προμηθευτές."""

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class SupplierOrderStore:
    """Απλή αποθήκη JSON για παραγγελίες προμηθευτών (εκτός βάσης δεδομένων)."""

    _lock = threading.Lock()
    _file_path = Path(__file__).resolve().parent / "supplier_orders.json"

    @classmethod
    def _load(cls) -> List[Dict[str, Any]]:
        if not cls._file_path.exists():
            return []
        try:
            with cls._file_path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except (json.JSONDecodeError, OSError):
            return []

    @classmethod
    def _save(cls, orders: List[Dict[str, Any]]):
        cls._file_path.parent.mkdir(parents=True, exist_ok=True)
        with cls._file_path.open("w", encoding="utf-8") as handle:
            json.dump(orders, handle, ensure_ascii=False, indent=2)

    @classmethod
    def _next_id(cls, orders: List[Dict[str, Any]]) -> int:
        return max((order.get("supplier_order_id", 0) for order in orders), default=0) + 1

    @classmethod
    def create_order(cls, items: List[Dict[str, Any]], total_cost: float) -> int:
        """Δημιουργεί νέα παραγγελία προμηθευτή και επιστρέφει το ID."""
        with cls._lock:
            orders = cls._load()
            order_id = cls._next_id(orders)
            # Χρησιμοποιούμε ISO timestamp για να είναι ευανάγνωστο και JSON-συμβατό.
            order = {
                "supplier_order_id": order_id,
                "created_at": datetime.utcnow().isoformat(),
                "status": "Σε εξέλιξη",
                "total_cost": total_cost,
                "items": items,
            }
            # Εισάγουμε στην αρχή της λίστας ώστε οι νεότερες παραγγελίες να εμφανίζονται πρώτες.
            orders.insert(0, order)
            cls._save(orders)
            return order_id

    @classmethod
    def list_orders(cls, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Επιστρέφει όλες τις παραγγελίες με προαιρετικό φίλτρο κατάστασης."""
        with cls._lock:
            orders = cls._load()
            if status_filter and status_filter != "Όλες":
                orders = [o for o in orders if o.get("status") == status_filter]
            return [json.loads(json.dumps(order)) for order in orders]

    @classmethod
    def get_order(cls, order_id: int) -> Optional[Dict[str, Any]]:
        """Επιστρέφει αντίγραφο παραγγελίας με συγκεκριμένο ID."""
        with cls._lock:
            orders = cls._load()
            for order in orders:
                if order.get("supplier_order_id") == order_id:
                    return json.loads(json.dumps(order))
            return None

    @classmethod
    def update_status(cls, order_id: int, new_status: str) -> bool:
        """Ενημερώνει την κατάσταση μιας παραγγελίας."""
        with cls._lock:
            orders = cls._load()
            updated = False
            for order in orders:
                if order.get("supplier_order_id") == order_id:
                    order["status"] = new_status
                    updated = True
                    break
            if updated:
                cls._save(orders)
            return updated
