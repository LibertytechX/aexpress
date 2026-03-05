import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone

from orders.models import Delivery
from orders.utils import calculate_route


def _coord_ok(lat, lng) -> bool:
    if lat is None or lng is None:
        return False
    try:
        lat_f = float(lat)
        lng_f = float(lng)
    except Exception:
        return False
    # Treat 0,0 as missing (typical sentinel in this codebase)
    return not (abs(lat_f) < 1e-9 and abs(lng_f) < 1e-9)


def _as_decimal(val):
    if val is None:
        return None
    try:
        return Decimal(str(val))
    except Exception:
        return None


def _ratio_diff(stored, expected):
    """Return abs(stored-expected)/expected as Decimal, or None if not comparable."""
    s = _as_decimal(stored)
    e = _as_decimal(expected)
    if s is None or e is None:
        return None
    if e == 0:
        return None
    return (s - e).copy_abs() / e


class Command(BaseCommand):
    help = (
        "End-of-day reconciliation: refetch expected route distance/duration per delivery leg "
        "and report discrepancies > threshold (flag-only; does not write to DB)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            type=str,
            default=None,
            help="Target local date (YYYY-MM-DD). Defaults to today.",
        )
        parser.add_argument(
            "--threshold",
            type=float,
            default=0.2,
            help="Flag when relative diff > threshold (default 0.2 = 20 percent).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Optional cap on number of deliveries scanned.",
        )

    def handle(self, *args, **options):
        date_str = options.get("date")
        threshold = float(options.get("threshold") or 0.2)
        limit = options.get("limit")

        if threshold < 0:
            raise CommandError("--threshold must be >= 0")

        if date_str:
            try:
                target_date = datetime.date.fromisoformat(date_str)
            except Exception as e:
                raise CommandError(f"Invalid --date {date_str!r}: {e}")
        else:
            target_date = timezone.localdate()

        qs = Delivery.objects.filter(
            Q(delivered_at__date=target_date)
            | Q(delivered_at__isnull=True, order__completed_at__date=target_date)
        ).select_related("order")
        qs = qs.order_by("order_id", "sequence")
        if limit:
            qs = qs[: int(limit)]

        scanned_deliveries = 0
        flagged_deliveries = 0
        flagged_orders = 0
        calc_errors = 0
        missing_coords = 0

        current_order_id = None
        batch = []

        def _process(order_deliveries):
            nonlocal flagged_deliveries, flagged_orders, calc_errors, missing_coords
            if not order_deliveries:
                return

            order = order_deliveries[0].order

            prev_lat = getattr(order, "pickup_latitude", None)
            prev_lng = getattr(order, "pickup_longitude", None)
            if not _coord_ok(prev_lat, prev_lng):
                prev_lat = getattr(order_deliveries[0], "pickup_latitude", None)
                prev_lng = getattr(order_deliveries[0], "pickup_longitude", None)

            expected_total_km = Decimal("0")
            expected_total_min = 0

            for d in order_deliveries:
                dest_lat = getattr(d, "dropoff_latitude", None)
                dest_lng = getattr(d, "dropoff_longitude", None)

                if not _coord_ok(prev_lat, prev_lng) or not _coord_ok(dest_lat, dest_lng):
                    missing_coords += 1
                    self.stdout.write(
                        f"SKIP missing_coords order={order.order_number} delivery_id={d.id} seq={d.sequence}"
                    )
                    prev_lat, prev_lng = dest_lat, dest_lng
                    continue

                try:
                    result = calculate_route(
                        {"lat": float(prev_lat), "lng": float(prev_lng)},
                        [{"lat": float(dest_lat), "lng": float(dest_lng)}],
                    )
                except Exception as e:
                    calc_errors += 1
                    self.stdout.write(
                        f"ERROR order={order.order_number} delivery_id={d.id} seq={d.sequence} err={e}"
                    )
                    prev_lat, prev_lng = dest_lat, dest_lng
                    continue

                if not result:
                    calc_errors += 1
                    self.stdout.write(
                        f"ERROR order={order.order_number} delivery_id={d.id} seq={d.sequence} err=no_route"
                    )
                    prev_lat, prev_lng = dest_lat, dest_lng
                    continue

                expected_km = _as_decimal(result.get("distance_km"))
                expected_min = result.get("duration_minutes")
                if expected_km is not None:
                    expected_total_km += expected_km
                if expected_min is not None:
                    expected_total_min += int(expected_min)

                km_diff = _ratio_diff(d.distance_km, expected_km)
                min_diff = _ratio_diff(d.duration_minutes, expected_min)

                should_flag = (
                    km_diff is None
                    or min_diff is None
                    or km_diff > Decimal(str(threshold))
                    or min_diff > Decimal(str(threshold))
                )

                if should_flag:
                    flagged_deliveries += 1
                    self.stdout.write(
                        "FLAG delivery "
                        f"order={order.order_number} delivery_id={d.id} seq={d.sequence} "
                        f"stored_km={d.distance_km} expected_km={expected_km} diff_km={km_diff} "
                        f"stored_min={d.duration_minutes} expected_min={expected_min} diff_min={min_diff}"
                    )

                prev_lat, prev_lng = dest_lat, dest_lng

            # Order totals reconciliation (optional but useful)
            order_km_diff = _ratio_diff(order.distance_km, expected_total_km)
            order_min_diff = _ratio_diff(order.duration_minutes, expected_total_min)
            if (
                order_km_diff is None
                or order_min_diff is None
                or order_km_diff > Decimal(str(threshold))
                or order_min_diff > Decimal(str(threshold))
            ):
                flagged_orders += 1
                self.stdout.write(
                    "FLAG order_total "
                    f"order={order.order_number} stored_km={order.distance_km} expected_km={expected_total_km} diff_km={order_km_diff} "
                    f"stored_min={order.duration_minutes} expected_min={expected_total_min} diff_min={order_min_diff}"
                )

        for d in qs:
            scanned_deliveries += 1
            if current_order_id is None:
                current_order_id = d.order_id
            if d.order_id != current_order_id:
                _process(batch)
                batch = []
                current_order_id = d.order_id
            batch.append(d)

        _process(batch)

        self.stdout.write(
            self.style.SUCCESS(
                "Reconciliation complete "
                f"date={target_date} scanned_deliveries={scanned_deliveries} "
                f"flagged_deliveries={flagged_deliveries} flagged_orders={flagged_orders} "
                f"missing_coords={missing_coords} calc_errors={calc_errors} threshold={threshold}"
            )
        )

