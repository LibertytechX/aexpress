from django.core.management.base import BaseCommand
from wallet.models import Bank

NIGERIAN_BANKS = [
    {
        "name": "Access Bank",
        "bank_code": "044",
        "cbn_code": "000014",
        "bank_short_name": "ACCESS",
        "ussd_short_code": "*901#",
    },
    {
        "name": "Guaranty Trust Bank",
        "bank_code": "058",
        "cbn_code": "000013",
        "bank_short_name": "GTBANK",
        "ussd_short_code": "*737#",
    },
    {
        "name": "Zenith Bank",
        "bank_code": "057",
        "cbn_code": "000015",
        "bank_short_name": "ZENITH",
        "ussd_short_code": "*966#",
    },
    {
        "name": "United Bank for Africa",
        "bank_code": "033",
        "cbn_code": "000004",
        "bank_short_name": "UBA",
        "ussd_short_code": "*919#",
    },
    {
        "name": "First Bank of Nigeria",
        "bank_code": "011",
        "cbn_code": "000016",
        "bank_short_name": "FIRSTBANK",
        "ussd_short_code": "*894#",
    },
    {
        "name": "Wema Bank",
        "bank_code": "035",
        "cbn_code": "000017",
        "bank_short_name": "WEMA",
        "ussd_short_code": "*945#",
    },
    {
        "name": "Fidelity Bank",
        "bank_code": "070",
        "cbn_code": "000007",
        "bank_short_name": "FIDELITY",
        "ussd_short_code": "*770#",
    },
    {
        "name": "First City Monument Bank",
        "bank_code": "214",
        "cbn_code": "000003",
        "bank_short_name": "FCMB",
        "ussd_short_code": "*329#",
    },
    {
        "name": "Union Bank of Nigeria",
        "bank_code": "032",
        "cbn_code": "000018",
        "bank_short_name": "UNION",
        "ussd_short_code": "*826#",
    },
    {
        "name": "Sterling Bank",
        "bank_code": "232",
        "cbn_code": "000001",
        "bank_short_name": "STERLING",
        "ussd_short_code": "*822#",
    },
    {
        "name": "Stanbic IBTC Bank",
        "bank_code": "039",
        "cbn_code": "000012",
        "bank_short_name": "STANBIC",
        "ussd_short_code": "*909#",
    },
    {
        "name": "Ecobank Nigeria",
        "bank_code": "050",
        "cbn_code": "000010",
        "bank_short_name": "ECOBANK",
        "ussd_short_code": "*326#",
    },
    {
        "name": "Keystone Bank",
        "bank_code": "082",
        "cbn_code": "000002",
        "bank_short_name": "KEYSTONE",
        "ussd_short_code": "*7111#",
    },
    {
        "name": "Polaris Bank",
        "bank_code": "076",
        "cbn_code": "000008",
        "bank_short_name": "POLARIS",
        "ussd_short_code": "*833#",
    },
    {
        "name": "Unity Bank",
        "bank_code": "215",
        "cbn_code": "000011",
        "bank_short_name": "UNITY",
        "ussd_short_code": "*7799#",
    },
    {
        "name": "Providus Bank",
        "bank_code": "101",
        "cbn_code": "000023",
        "bank_short_name": "PROVIDUS",
        "ussd_short_code": "",
    },
    {
        "name": "Jaiz Bank",
        "bank_code": "301",
        "cbn_code": "000006",
        "bank_short_name": "JAIZ",
        "ussd_short_code": "*773#",
    },
    {
        "name": "Taj Bank",
        "bank_code": "302",
        "cbn_code": "000026",
        "bank_short_name": "TAJ",
        "ussd_short_code": "*898#",
    },
    {
        "name": "Lotus Bank",
        "bank_code": "303",
        "cbn_code": "000029",
        "bank_short_name": "LOTUS",
        "ussd_short_code": "*5045#",
    },
    {
        "name": "Premium Trust Bank",
        "bank_code": "105",
        "cbn_code": "000031",
        "bank_short_name": "PREMIUMTRUST",
        "ussd_short_code": "",
    },
    {
        "name": "Titan Trust Bank",
        "bank_code": "102",
        "cbn_code": "000025",
        "bank_short_name": "TITAN",
        "ussd_short_code": "*922#",
    },
    {
        "name": "OPay Digital Services (PayCom)",
        "bank_code": "999992",
        "cbn_code": "100004",
        "bank_short_name": "OPAY",
        "ussd_short_code": "*955#",
    },
    {
        "name": "PalmPay",
        "bank_code": "999991",
        "cbn_code": "100033",
        "bank_short_name": "PALMPAY",
        "ussd_short_code": "*652#",
    },
    {
        "name": "Kuda Microfinance Bank",
        "bank_code": "50211",
        "cbn_code": "090267",
        "bank_short_name": "KUDA",
        "ussd_short_code": "",
    },
    {
        "name": "Moniepoint Microfinance Bank",
        "bank_code": "50515",
        "cbn_code": "090405",
        "bank_short_name": "MONIEPOINT",
        "ussd_short_code": "*5573#",
    },
    {
        "name": "Rubies Bank",
        "bank_code": "125",
        "cbn_code": "090175",
        "bank_short_name": "RUBIES",
        "ussd_short_code": "*779#",
    },
    {
        "name": "VFD Microfinance Bank",
        "bank_code": "566",
        "cbn_code": "090110",
        "bank_short_name": "VFD",
        "ussd_short_code": "",
    },
    {
        "name": "Sparkle Microfinance Bank",
        "bank_code": "51310",
        "cbn_code": "090325",
        "bank_short_name": "SPARKLE",
        "ussd_short_code": "",
    },
    {
        "name": "Carbon",
        "bank_code": "565",
        "cbn_code": "090130",
        "bank_short_name": "CARBON",
        "ussd_short_code": "*1303#",
    },
    {
        "name": "FairMoney Microfinance Bank",
        "bank_code": "51318",
        "cbn_code": "090551",
        "bank_short_name": "FAIRMONEY",
        "ussd_short_code": "",
    },
    {
        "name": "Parallex Bank",
        "bank_code": "104",
        "cbn_code": "000030",
        "bank_short_name": "PARALLEX",
        "ussd_short_code": "",
    },
    {
        "name": "Signature Bank",
        "bank_code": "106",
        "cbn_code": "000034",
        "bank_short_name": "SIGNATURE",
        "ussd_short_code": "",
    },
    {
        "name": "Optimus Bank",
        "bank_code": "107",
        "cbn_code": "000036",
        "bank_short_name": "OPTIMUS",
        "ussd_short_code": "",
    },
]


class Command(BaseCommand):
    help = "Seeds supported Nigerian commercial, microfinance, and neobanks into the Bank table."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding Nigerian banks directory..."))
        created_count = 0
        updated_count = 0

        for bank_data in NIGERIAN_BANKS:
            bank, created = Bank.objects.update_or_create(
                name=bank_data["name"],
                defaults={
                    "bank_code": bank_data["bank_code"],
                    "cbn_code": bank_data["cbn_code"],
                    "bank_short_name": bank_data["bank_short_name"],
                    "ussd_short_code": bank_data["ussd_short_code"],
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        # Invalidate cache
        from django.core.cache import cache
        cache.delete("all_bank_list")

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded banks: {created_count} created, {updated_count} updated."
            )
        )
