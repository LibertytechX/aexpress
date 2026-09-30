"""
LeaderboardService
Centralized domain service managing real-time rider leaderboards via Redis Sorted Sets (ZSET),
with PostgreSQL (LeaderboardEntry) fallback and background reconciliation.
"""

import logging
from datetime import timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from django.db.models import F
from django.utils import timezone
import django_redis
from django_redis.client import DefaultClient

from dispatcher.models import Rider
from riders.models import LeaderboardEntry, RiderEarning

logger = logging.getLogger(__name__)

# TTL configurations
WEEK_TTL_SECONDS = 30 * 86400  # 30 days
MONTH_TTL_SECONDS = 90 * 86400  # 90 days


class LeaderboardService:
    @staticmethod
    def get_redis_client() -> Optional[DefaultClient]:
        """Safely retrieves the configured redis client via django-redis."""
        try:
            return django_redis.get_redis_connection("default")
        except Exception as e:
            logger.warning(f"LeaderboardService: Failed to connect to Redis: {e}")
            return None

    @classmethod
    def get_period_tuples(cls, today=None) -> List[Tuple[str, str, Dict[str, Any]]]:
        """
        Returns list of (period_type, period_key, date_filter) for this_week, this_month, and all_time.
        Standardizes period_key generation across the entire codebase.
        """
        if today is None:
            today = timezone.now().date()

        # This week (Monday -> today)
        week_start = today - timedelta(days=today.weekday())
        week_key = today.strftime("%Y-W%W")

        # This month (1st of month -> today)
        month_start = today.replace(day=1)
        month_key = today.strftime("%Y-%m")

        return [
            (
                LeaderboardEntry.PeriodType.THIS_WEEK,
                week_key,
                {
                    "completed_at__date__gte": week_start,
                    "completed_at__date__lte": today,
                },
            ),
            (
                LeaderboardEntry.PeriodType.THIS_MONTH,
                month_key,
                {
                    "completed_at__date__gte": month_start,
                    "completed_at__date__lte": today,
                },
            ),
            (
                LeaderboardEntry.PeriodType.ALL_TIME,
                "all_time",
                {},
            ),
        ]

    @classmethod
    def record_order_completion(cls, order) -> None:
        """
        Invoked when an order transitions to 'Done'.
        Incrementally updates trips and earnings in Redis ZSETs and updates
        the PostgreSQL LeaderboardEntry rows for this_week, this_month, and all_time.
        """
        rider = getattr(order, "rider", None)
        if not rider:
            return

        completed_date = (
            order.completed_at.date() if order.completed_at else timezone.now().date()
        )

        # Retrieve earnings for this order if present
        earning_record = getattr(order, "rider_earning", None)
        if earning_record is None:
            earning_record = RiderEarning.objects.filter(order=order).first()

        net_earning = (
            float(earning_record.net_earning)
            if earning_record and earning_record.net_earning is not None
            else 0.0
        )
        decimal_earning = Decimal(str(net_earning))

        zone_name = rider.hub.zone.name if (rider.hub and rider.hub.zone) else ""
        periods = cls.get_period_tuples(completed_date)

        # 1. Update Redis Sorted Sets (Fast Path)
        redis_client = cls.get_redis_client()
        if redis_client:
            try:
                pipe = redis_client.pipeline()
                rider_str_id = str(rider.id)

                for period_type, period_key, _ in periods:
                    trips_key = f"leaderboard:trips:{period_key}"
                    earnings_key = f"leaderboard:earnings:{period_key}"

                    pipe.zincrby(trips_key, 1, rider_str_id)
                    pipe.zincrby(earnings_key, net_earning, rider_str_id)

                    if period_type == LeaderboardEntry.PeriodType.THIS_WEEK:
                        pipe.expire(trips_key, WEEK_TTL_SECONDS)
                        pipe.expire(earnings_key, WEEK_TTL_SECONDS)
                    elif period_type == LeaderboardEntry.PeriodType.THIS_MONTH:
                        pipe.expire(trips_key, MONTH_TTL_SECONDS)
                        pipe.expire(earnings_key, MONTH_TTL_SECONDS)

                pipe.execute()
            except Exception as e:
                logger.error(
                    f"LeaderboardService: Failed to update Redis for rider {rider.id}: {e}"
                )

        # 2. Update PostgreSQL LeaderboardEntry (Persistence / ACID)
        for period_type, period_key, _ in periods:
            try:
                entry, created = LeaderboardEntry.objects.get_or_create(
                    rider=rider,
                    period_type=period_type,
                    period_key=period_key,
                    defaults={
                        "trips_count": 1,
                        "earnings": decimal_earning,
                        "zone_name": zone_name,
                        "rank": 0,
                    },
                )
                if not created:
                    LeaderboardEntry.objects.filter(id=entry.id).update(
                        trips_count=F("trips_count") + 1,
                        earnings=F("earnings") + decimal_earning,
                        zone_name=zone_name if zone_name else entry.zone_name,
                        rebuilt_at=timezone.now(),
                    )
            except Exception as e:
                logger.error(
                    f"LeaderboardService: Failed to update DB LeaderboardEntry for rider {rider.id} ({period_key}): {e}"
                )

    @classmethod
    def get_leaderboard(
        cls,
        period_type: str,
        period_key: str,
        current_rider: Optional[Rider] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Returns ranked list of riders for the given period.
        Tries Redis first. If Redis is cold or down, falls back to PostgreSQL.
        """
        # redis_client = cls.get_redis_client()
        # if redis_client:
        #     try:
        #         trips_key = f"leaderboard:trips:{period_key}"
        #         earnings_key = f"leaderboard:earnings:{period_key}"

        #         top_members = redis_client.zrevrange(
        #             trips_key, 0, limit - 1, withscores=True
        #         )

        #         if top_members:
        #             rider_ids = [
        #                 m[0].decode("utf-8") if isinstance(m[0], bytes) else str(m[0])
        #                 for m in top_members
        #             ]

        #             # Single SQL query to fetch rider metadata
        #             riders = (
        #                 Rider.objects.filter(id__in=rider_ids)
        #                 .select_related("user", "hub__zone")
        #             )
        #             rider_map = {str(r.id): r for r in riders}

        #             # Fetch earnings via pipeline
        #             pipe = redis_client.pipeline()
        #             for r_id in rider_ids:
        #                 pipe.zscore(earnings_key, r_id)
        #             earnings_scores = pipe.execute()

        #             entries = []
        #             my_entry = None
        #             current_rider_id_str = str(current_rider.id) if current_rider else None

        #             for idx, (m, trips_score) in enumerate(top_members, start=1):
        #                 r_id = (
        #                     m.decode("utf-8") if isinstance(m, bytes) else str(m)
        #                 )
        #                 rider_obj = rider_map.get(r_id)
        #                 if not rider_obj:
        #                     continue

        #                 earning_val = earnings_scores[idx - 1] or 0.0
        #                 zone_name = (
        #                     rider_obj.hub.zone.name
        #                     if (rider_obj.hub and rider_obj.hub.zone)
        #                     else ""
        #                 )
        #                 is_me = (
        #                     current_rider_id_str is not None
        #                     and str(rider_obj.id) == current_rider_id_str
        #                 )

        #                 item = {
        #                     "rank": idx,
        #                     "rider_id": rider_obj.rider_id,
        #                     "name": rider_obj.user.contact_name or rider_obj.user.phone,
        #                     "zone": zone_name,
        #                     "trips_count": int(trips_score),
        #                     "earnings": Decimal(str(round(earning_val, 2))),
        #                     "is_me": is_me,
        #                 }
        #                 entries.append(item)
        #                 if is_me:
        #                     my_entry = item

        #             # Get current rider rank directly from Redis even if outside top 50
        #             my_rank = None
        #             if current_rider_id_str:
        #                 if my_entry:
        #                     my_rank = my_entry["rank"]
        #                 else:
        #                     rank_0_idx = redis_client.zrevrank(
        #                         trips_key, current_rider_id_str
        #                     )
        #                     if rank_0_idx is not None:
        #                         my_rank = rank_0_idx + 1

        #             return {
        #                 "period": period_type,
        #                 "period_key": period_key,
        #                 "my_rank": my_rank,
        #                 "entries": entries,
        #             }
        #     except Exception as e:
        #         logger.error(
        #             f"LeaderboardService: Redis query failed for {period_key}, falling back to DB: {e}"
        #         )

        # Fallback to PostgreSQL
        return cls._get_leaderboard_from_db(
            period_type=period_type,
            period_key=period_key,
            current_rider=current_rider,
            limit=limit,
        )

    @classmethod
    def _get_leaderboard_from_db(
        cls,
        period_type: str,
        period_key: str,
        current_rider: Optional[Rider] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Fall back to querying PostgreSQL LeaderboardEntry directly."""
        entries_qs = (
            LeaderboardEntry.objects.filter(
                period_type=period_type, period_key=period_key
            )
            .select_related("rider__user", "rider__hub__zone")
            .order_by("rank")[:limit]
        )

        result = []
        my_entry = None
        current_rider_id = current_rider.id if current_rider else None

        for entry in entries_qs:
            r = entry.rider
            is_me = current_rider_id is not None and r.id == current_rider_id
            item = {
                "rank": entry.rank,
                "rider_id": r.rider_id,
                "name": r.user.contact_name or r.user.phone,
                "zone": entry.zone_name,
                "trips_count": entry.trips_count,
                "earnings": entry.earnings,
                "is_me": is_me,
            }
            result.append(item)
            if is_me:
                my_entry = item

        my_rank = my_entry["rank"] if my_entry else None
        if current_rider and not my_rank:
            # Query rider's specific entry if ranked outside limit
            own_entry = LeaderboardEntry.objects.filter(
                rider=current_rider, period_type=period_type, period_key=period_key
            ).first()
            if own_entry:
                my_rank = own_entry.rank

        return {
            "period": period_type,
            "period_key": period_key,
            "my_rank": my_rank,
            "entries": result,
        }

    @classmethod
    def get_rider_rank(
        cls, rider_id: Any, period_type: str, period_key: str
    ) -> Optional[int]:
        """
        Retrieves rider's real-time rank.
        Tries Redis ZREVRANK first, falling back to PostgreSQL LeaderboardEntry.
        """
        redis_client = cls.get_redis_client()
        if redis_client:
            try:
                trips_key = f"leaderboard:trips:{period_key}"
                rank_0_idx = redis_client.zrevrank(trips_key, str(rider_id))
                if rank_0_idx is not None:
                    return rank_0_idx + 1
            except Exception as e:
                logger.error(
                    f"LeaderboardService: Failed to get rider rank from Redis for {rider_id}: {e}"
                )

        # Fallback to DB
        entry = LeaderboardEntry.objects.filter(
            rider_id=rider_id,
            period_type=period_type,
            period_key=period_key,
        ).first()
        return entry.rank if entry and entry.rank > 0 else None

    @classmethod
    def warm_redis_for_period(
        cls, period_type: str, period_key: str, entries: List[LeaderboardEntry]
    ) -> None:
        """
        Populates Redis Sorted Sets from LeaderboardEntry rows.
        Used by the rebuild_leaderboard management command to sync Redis with DB truth.
        """
        redis_client = cls.get_redis_client()
        if not redis_client or not entries:
            return

        trips_key = f"leaderboard:trips:{period_key}"
        earnings_key = f"leaderboard:earnings:{period_key}"

        try:
            pipe = redis_client.pipeline()
            pipe.delete(trips_key)
            pipe.delete(earnings_key)

            trips_mapping = {}
            earnings_mapping = {}

            for entry in entries:
                rider_str_id = str(entry.rider_id)
                trips_mapping[rider_str_id] = float(entry.trips_count)
                earnings_mapping[rider_str_id] = float(entry.earnings)

            if trips_mapping:
                pipe.zadd(trips_key, trips_mapping)
                pipe.zadd(earnings_key, earnings_mapping)

                if period_type == LeaderboardEntry.PeriodType.THIS_WEEK:
                    pipe.expire(trips_key, WEEK_TTL_SECONDS)
                    pipe.expire(earnings_key, WEEK_TTL_SECONDS)
                elif period_type == LeaderboardEntry.PeriodType.THIS_MONTH:
                    pipe.expire(trips_key, MONTH_TTL_SECONDS)
                    pipe.expire(earnings_key, MONTH_TTL_SECONDS)

            pipe.execute()
            logger.info(
                f"LeaderboardService: Warmed Redis for {period_key} with {len(entries)} entries."
            )
        except Exception as e:
            logger.error(
                f"LeaderboardService: Failed to warm Redis for {period_key}: {e}"
            )
