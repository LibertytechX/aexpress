import pytest
from tablib import Dataset
from django.contrib.admin.sites import AdminSite
from django.core.cache import cache
from import_export.admin import ImportExportModelAdmin
from wallet.models import Bank
from wallet.admin import BankAdmin, BankResource


@pytest.mark.django_db
class TestBankAdminImportExport:
    def setup_method(self):
        cache.delete("all_bank_list")
        self.site = AdminSite()
        self.admin = BankAdmin(Bank, self.site)

    def test_bank_admin_inherits_import_export_model_admin(self):
        assert issubclass(BankAdmin, ImportExportModelAdmin)
        assert self.admin.resource_class == BankResource

    def test_bank_resource_export(self):
        bank = Bank.objects.create(
            name="Test Zenith Bank",
            bank_code="057",
            cbn_code="000015",
            bank_short_name="ZENITH",
            ussd_short_code="*966#",
        )
        resource = BankResource()
        dataset = resource.export(Bank.objects.filter(id=bank.id))

        assert "name" in dataset.headers
        assert "bank_code" in dataset.headers
        assert "cbn_code" in dataset.headers
        assert "Test Zenith Bank" in [row[dataset.headers.index("name")] for row in dataset]

    def test_bank_resource_import_creates_new_bank(self):
        data = Dataset()
        data.headers = ["name", "bank_code", "cbn_code", "bank_short_name", "ussd_short_code"]
        data.append(["Brand New Bank", "888", "000888", "BNB", "*888#"])

        resource = BankResource()
        result = resource.import_data(data, dry_run=False)

        assert not result.has_errors()
        bank = Bank.objects.filter(bank_code="888").first()
        assert bank is not None
        assert bank.name == "Brand New Bank"
        assert bank.cbn_code == "000888"
        assert bank.bank_short_name == "BNB"

    def test_bank_resource_import_updates_existing_by_cbn_code(self):
        Bank.objects.create(
            name="Old Name Bank",
            bank_code="123",
            cbn_code="000123",
            bank_short_name="OLD",
        )

        data = Dataset()
        data.headers = ["name", "bank_code", "cbn_code", "bank_short_name", "ussd_short_code"]
        data.append(["Updated Name Bank", "123", "000123", "NEW", "*123#"])

        resource = BankResource()
        result = resource.import_data(data, dry_run=False)

        assert not result.has_errors()
        assert Bank.objects.filter(cbn_code="000123").count() == 1
        updated_bank = Bank.objects.get(cbn_code="000123")
        assert updated_bank.name == "Updated Name Bank"
        assert updated_bank.bank_short_name == "NEW"
        assert updated_bank.ussd_short_code == "*123#"

    def test_bank_resource_import_updates_existing_by_name(self):
        Bank.objects.create(
            name="Special Bank Nigeria",
            bank_code="",
            cbn_code="",
        )

        data = Dataset()
        data.headers = ["name", "bank_code", "cbn_code", "bank_short_name", "ussd_short_code"]
        data.append(["Special Bank Nigeria", "991", "000991", "SBN", "*991#"])

        resource = BankResource()
        result = resource.import_data(data, dry_run=False)

        assert not result.has_errors()
        assert Bank.objects.filter(name__iexact="Special Bank Nigeria").count() == 1
        bank = Bank.objects.get(name__iexact="Special Bank Nigeria")
        assert bank.bank_code == "991"
        assert bank.cbn_code == "000991"

    def test_bank_resource_import_clears_cache(self):
        cache.set("all_bank_list", ["dummy_cache"], 60)
        assert cache.get("all_bank_list") is not None

        data = Dataset()
        data.headers = ["name", "bank_code", "cbn_code"]
        data.append(["Cached Test Bank", "992", "000992"])

        resource = BankResource()
        resource.import_data(data, dry_run=False)

        assert cache.get("all_bank_list") is None
