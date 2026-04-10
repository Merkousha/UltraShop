"""
Smart Routing Service (SO-52) — Phase 4.

Given an Order with lines, selects the best warehouse(s) to fulfill each item.

Algorithm:
  1. Try to find a single warehouse that can satisfy ALL order lines
     (prefer lower priority number, i.e. higher routing priority).
  2. If no single warehouse can satisfy all lines, fall back to a
     multi-warehouse split: each line is assigned to the warehouse
     with the most available stock for that variant.

Returns a "fulfillment plan":
    [
        {"warehouse": <Warehouse>, "lines": [<OrderLine>, ...]},
        ...
    ]
"""

from django.db.models import F

from catalog.models import WarehouseStock
from core.models import Warehouse


class SmartRoutingService:
    """Compute and confirm a smart fulfillment plan for a given order."""

    def __init__(self, order):
        self.order = order

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def compute_plan(self):
        """
        Return a fulfillment plan (list of dicts) for `self.order`.

        Each dict has keys:
            - "warehouse": Warehouse instance
            - "lines": list of OrderLine instances assigned to that warehouse
        """
        lines = list(
            self.order.lines.select_related("variant").all()
        )
        warehouses = list(
            Warehouse.objects.filter(
                store=self.order.store, is_active=True
            ).order_by("priority", "pk")
        )

        # ── Sort warehouses by geographic proximity to the customer ──────
        shipping_city = self.order.shipping_city or ""
        shipping_province = self.order.shipping_province or ""
        warehouses = self._sort_warehouses_by_proximity(
            warehouses, shipping_city, shipping_province
        )

        # ── 1. Try single-warehouse fulfillment ──────────────────────────
        for wh in warehouses:
            if self._can_fulfill_all(wh, lines):
                return [{"warehouse": wh, "lines": lines}]

        # ── 2. Fall back to multi-warehouse split ────────────────────────
        return self._multi_warehouse_plan(lines, warehouses)

    def reserve_stock_for_plan(self, plan):
        """
        Decrement `WarehouseStock.reserved` for each line in the plan.
        Uses F() expressions so the update is atomic at the DB level.
        """
        for entry in plan:
            wh = entry["warehouse"]
            for line in entry["lines"]:
                if not line.variant_id:
                    continue
                WarehouseStock.objects.filter(
                    warehouse=wh,
                    variant_id=line.variant_id,
                ).update(reserved=F("reserved") + line.quantity)

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _sort_warehouses_by_proximity(self, warehouses, shipping_city, shipping_province):
        """
        Return warehouses sorted by geographic proximity to the customer:
          1. Same city (case-insensitive)
          2. Same province (case-insensitive)
          3. All others (original priority order preserved within each tier)
        """
        city_lower = shipping_city.strip().lower()
        province_lower = shipping_province.strip().lower()

        tier_city = []
        tier_province = []
        tier_other = []

        for wh in warehouses:
            wh_city = (wh.city or "").strip().lower()
            wh_province = (wh.province or "").strip().lower()
            if city_lower and wh_city == city_lower:
                tier_city.append(wh)
            elif province_lower and wh_province == province_lower:
                tier_province.append(wh)
            else:
                tier_other.append(wh)

        return tier_city + tier_province + tier_other

    def _can_fulfill_all(self, warehouse, lines):
        """Return True if `warehouse` has enough available stock for every line."""
        for line in lines:
            if not line.variant_id:
                # Lines without a linked variant are skipped (e.g. deleted products)
                continue
            try:
                ws = WarehouseStock.objects.get(
                    warehouse=warehouse, variant_id=line.variant_id
                )
                if ws.available < line.quantity:
                    return False
            except WarehouseStock.DoesNotExist:
                return False
        return True

    def _multi_warehouse_plan(self, lines, warehouses):
        """
        Assign each line to the warehouse with the highest available stock
        for that variant.  Lines without a variant or with no stock anywhere
        are grouped under a sentinel entry with warehouse=None.
        """
        plan = {}  # warehouse_pk -> {"warehouse": wh, "lines": [...]}
        unroutable = []

        for line in lines:
            if not line.variant_id:
                unroutable.append(line)
                continue

            best_wh = None
            best_available = 0

            for wh in warehouses:
                try:
                    ws = WarehouseStock.objects.get(
                        warehouse=wh, variant_id=line.variant_id
                    )
                    if ws.available > best_available:
                        best_available = ws.available
                        best_wh = wh
                except WarehouseStock.DoesNotExist:
                    pass

            if best_wh is not None:
                if best_wh.pk not in plan:
                    plan[best_wh.pk] = {"warehouse": best_wh, "lines": []}
                plan[best_wh.pk]["lines"].append(line)
            else:
                unroutable.append(line)

        result = list(plan.values())

        # Lines that couldn't be routed (no stock anywhere) are appended
        # as a separate entry with warehouse=None so the caller can surface
        # them to the operator.
        if unroutable:
            result.append({"warehouse": None, "lines": unroutable})

        return result

    # ------------------------------------------------------------------ #
    # Serialisation helpers (for storing plan in routing_plan JSONField)  #
    # ------------------------------------------------------------------ #

    @staticmethod
    def plan_to_json(plan):
        """Convert a plan (list of dicts with ORM objects) to a JSON-serialisable list."""
        result = []
        for entry in plan:
            wh = entry["warehouse"]
            result.append(
                {
                    "warehouse_id": wh.pk if wh else None,
                    "warehouse_name": wh.name if wh else "بدون انبار",
                    "line_ids": [line.pk for line in entry["lines"]],
                }
            )
        return result

    @staticmethod
    def plan_from_json(json_plan, order):
        """
        Reconstruct a lightweight plan from the stored JSON.
        Returns list of dicts with Warehouse instances (or None) and
        QuerySet-derived line lists.
        """
        from orders.models import OrderLine

        lines_by_pk = {line.pk: line for line in order.lines.all()}
        result = []
        for entry in json_plan:
            wh_id = entry.get("warehouse_id")
            wh = Warehouse.objects.filter(pk=wh_id).first() if wh_id else None
            line_objs = [
                lines_by_pk[lid]
                for lid in entry.get("line_ids", [])
                if lid in lines_by_pk
            ]
            result.append({"warehouse": wh, "lines": line_objs})
        return result
