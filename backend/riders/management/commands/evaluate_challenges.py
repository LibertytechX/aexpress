"""
evaluate_challenges — management command
Evaluates all completed, unrewarded challenges and credits the
rider's wallet with the reward amount.

Run daily via cron:
  python manage.py evaluate_challenges
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from riders.models import RiderChallengeProgress, Challenge


class Command(BaseCommand):
    help = "Evaluates completed challenges and credits wallet rewards to riders."

    def handle(self, *args, **options):
        self.stdout.write("🎯 Evaluating completed challenge rewards...")

        completed_unpaid = RiderChallengeProgress.objects.filter(
            is_completed=True,
            reward_paid=False,
            challenge__reward_type=Challenge.RewardType.CASH,
            challenge__reward_amount__isnull=False,
        ).select_related("rider__user", "challenge")

        paid = 0
        failed = 0

        for progress in completed_unpaid:
            rider = progress.rider
            challenge = progress.challenge
            amount = challenge.reward_amount

            try:
                from wallet.models import Wallet
                wallet = Wallet.objects.get(user=rider.user)
                wallet.credit(
                    amount=amount,
                    description=f"Challenge reward: {challenge.name}",
                    reference=f"CHG-{progress.id}",
                    metadata={
                        "type": "challenge_reward",
                        "challenge_id": str(challenge.id),
                        "challenge_name": challenge.name,
                        "rider_id": rider.rider_id,
                    },
                )
                progress.reward_paid = True
                progress.save(update_fields=["reward_paid"])
                paid += 1
                self.stdout.write(
                    f"  ✅ ₦{amount} → {rider.rider_id} ({challenge.name})"
                )
            except Exception as e:
                failed += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"  ❌ Failed for {rider.rider_id} ({challenge.name}): {e}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Done — {paid} rewards paid, {failed} failed."
            )
        )
