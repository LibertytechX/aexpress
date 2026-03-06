"""
seed_challenges — management command
Populates the system with initial/standard challenges.

Run once to initialize:
  python manage.py seed_challenges
"""

from django.core.management.base import BaseCommand
from riders.models import Challenge


class Command(BaseCommand):
    help = "Seeds the system with initial standard challenges."

    def handle(self, *args, **options):
        challenges = [
            {
                "name": "Early Bird",
                "description": "Complete 5 orders before 9:00 AM today.",
                "icon_emoji": "🌅",
                "metric": Challenge.Metric.ORDERS_COUNT_DAY,
                "metric_target": 5,
                "metric_condition": {"before_hour": 9},
                "reward_type": Challenge.RewardType.CASH,
                "reward_amount": 500,
                "period": Challenge.Period.DAILY,
            },
            {
                "name": "Century Club",
                "description": "Complete 100 orders this week.",
                "icon_emoji": "💯",
                "metric": Challenge.Metric.ORDERS_COUNT_WEEK,
                "metric_target": 100,
                "reward_type": Challenge.RewardType.CASH,
                "reward_amount": 10000,
                "period": Challenge.Period.WEEKLY,
            },
            {
                "name": "7-Day Streak",
                "description": "Maintain your 25-order daily streak for 7 consecutive days.",
                "icon_emoji": "🔥",
                "metric": Challenge.Metric.STREAK_DAYS,
                "metric_target": 7,
                "reward_type": Challenge.RewardType.CASH,
                "reward_amount": 5000,
                "period": Challenge.Period.ONGOING,
            },
            {
                "name": "Referral King",
                "description": "Bring 10 new active businesses to the platform.",
                "icon_emoji": "👑",
                "metric": Challenge.Metric.REFERRALS_COUNT,
                "metric_target": 10,
                "reward_type": Challenge.RewardType.CASH,
                "reward_amount": 20000,
                "period": Challenge.Period.ONGOING,
            },
            {
                "name": "Zero Cancel",
                "description": "Complete 30 days without a single rider-initiated cancellation.",
                "icon_emoji": "🛡️",
                "metric": Challenge.Metric.NO_CANCELLATIONS,
                "metric_target": 30,
                "reward_type": Challenge.RewardType.PERK,
                "reward_perk": "Priority Dispatch & Higher Rating Boost",
                "period": Challenge.Period.ONGOING,
            },
        ]

        self.stdout.write("🌱 Seeding challenges...")
        created_count = 0
        updated_count = 0

        for ch_data in challenges:
            obj, created = Challenge.objects.update_or_create(
                name=ch_data["name"], defaults=ch_data
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Done — {created_count} challenges created, {updated_count} updated."
            )
        )
