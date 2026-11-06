import pytest
from django.core.management import call_command
from django.contrib.auth import get_user_model
from dispatcher.models import DispatcherProfile

User = get_user_model()


@pytest.mark.django_db
class TestRegenerateDispatcherCodesCommand:
    @pytest.fixture(autouse=True)
    def setup_dispatchers(self):
        self.user1 = User.objects.create_user(
            phone="+2348011110001",
            first_name="Hub",
            last_name="Captain",
            usertype="Dispatcher",
        )
        self.user2 = User.objects.create_user(
            phone="+2348011110002",
            first_name="Zone",
            last_name="Lead",
            usertype="Dispatcher",
        )
        self.user3 = User.objects.create_user(
            phone="+2348011110003",
            first_name="General",
            last_name="Admin",
            usertype="Dispatcher",
        )

        self.disp_hub = self.user1.dispatcher_profile
        self.disp_hub.role = DispatcherProfile.Role.HUB_CAPTAIN
        self.disp_hub.affiliation_code = "OLD001"
        self.disp_hub.save()

        self.disp_zone = self.user2.dispatcher_profile
        self.disp_zone.role = DispatcherProfile.Role.ZONE_LEAD
        self.disp_zone.affiliation_code = "OLD002"
        self.disp_zone.save()

        self.disp_admin = self.user3.dispatcher_profile
        self.disp_admin.role = DispatcherProfile.Role.ADMIN
        self.disp_admin.affiliation_code = "OLD003"
        self.disp_admin.save()

    def test_regenerate_all_dispatchers(self):
        """Regenerates unique codes for all dispatchers by default."""
        call_command("regenerate_dispatcher_codes")

        self.disp_hub.refresh_from_db()
        self.disp_zone.refresh_from_db()
        self.disp_admin.refresh_from_db()

        assert self.disp_hub.affiliation_code != "OLD001"
        assert self.disp_zone.affiliation_code != "OLD002"
        assert self.disp_admin.affiliation_code != "OLD003"

        # Ensure all codes are distinct
        codes = {
            self.disp_hub.affiliation_code,
            self.disp_zone.affiliation_code,
            self.disp_admin.affiliation_code,
        }
        assert len(codes) == 3
        for c in codes:
            assert len(c) == 6

    def test_regenerate_only_affiliates(self):
        """When --only-affiliates is passed, clears admin and regenerates captains/leads."""
        call_command("regenerate_dispatcher_codes", "--only-affiliates")

        self.disp_hub.refresh_from_db()
        self.disp_zone.refresh_from_db()
        self.disp_admin.refresh_from_db()

        assert self.disp_hub.affiliation_code != "OLD001"
        assert len(self.disp_hub.affiliation_code) == 6

        assert self.disp_zone.affiliation_code != "OLD002"
        assert len(self.disp_zone.affiliation_code) == 6

        assert self.disp_admin.affiliation_code is None

    def test_regenerate_dry_run(self):
        """When --dry-run is passed, no database changes are persisted."""
        call_command("regenerate_dispatcher_codes", "--dry-run")

        self.disp_hub.refresh_from_db()
        self.disp_zone.refresh_from_db()
        self.disp_admin.refresh_from_db()

        assert self.disp_hub.affiliation_code == "OLD001"
        assert self.disp_zone.affiliation_code == "OLD002"
        assert self.disp_admin.affiliation_code == "OLD003"

    def test_regenerate_specific_dispatcher(self):
        """When --dispatcher-id is specified, only that dispatcher is regenerated."""
        call_command("regenerate_dispatcher_codes", f"--dispatcher-id={self.disp_hub.id}")

        self.disp_hub.refresh_from_db()
        self.disp_zone.refresh_from_db()
        self.disp_admin.refresh_from_db()

        assert self.disp_hub.affiliation_code != "OLD001"
        assert self.disp_zone.affiliation_code == "OLD002"
        assert self.disp_admin.affiliation_code == "OLD003"
