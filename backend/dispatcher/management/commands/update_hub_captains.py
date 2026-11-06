from django.core.management.base import BaseCommand
from django.db import transaction
from dispatcher.models import RelayNode


class Command(BaseCommand):
    help = "Updates the hub captain name and phone number for RelayNodes based on provided mapping."

    def handle(self, *args, **options):
        # Hub mapping: {Hub Name: (Captain Name, Captain Phone)}
        # Using a list of tuples to handle potential naming variations in a loop
        mapping = [
            ("Osapa/Jakande", "Saakon Aondongu Wisdom", "8163420766"),
            ("Jakande/Osapa", "Saakon Aondongu Wisdom", "8163420766"),
            ("Awoyaya", "Saakon Aondongu Wisdom", "8163420766"),
            ("Ajah", "Ayobami Ajiboye J", "8066682652"),
            ("Oshodi", "AJAYI KUDIRAT OPEYEMI", "0816 970 7993"),
            ("Oyingbo", "AJAYI KUDIRAT OPEYEMI", "0816 970 7993"),
            ("Tejuosho", "Akinrinola Oluwadamilola Dorcas", "9035373242"),
            ("Tejousho", "Akinrinola Oluwadamilola Dorcas", "9035373242"),
            ("Sabo", "MUSTAPHA FARUOQ OLAMILEKAN", "9165447665"),
            ("Bariga", "Oluwaseyi sherif", "7083281615"),
            ("Ajegunle", "Adeyemi mojisola grace", "7033056983"),
            ("Festac", "chife macdavies", "9059142084"),
            ("Iyana ipaja/egbeda", "Shonola Theresa Elizabeth", "8160712240"),
            ("iyana ipaja/egbeda", "Shonola Theresa Elizabeth", "8160712240"),
            ("Ikotun", "Wuraola Bankole", "901 663 0722"),
            ("Tradefair", "Tsegba Ayar Michelle", "816 243 2505"),
            ("Iyana Iba", "Orji Imo", "7066264357"),
            ("iyana Iba", "Orji Imo", "7066264357"),
            ("Ayobo", "Augustine Samson Sunday", "8024591944"),
            ("Agege", "Victoria Ajetumobi", "9064093196"),
            ("Ikeja", "Onyekwere Paul", "809 175 3021"),
            ("Mile 12", "fashola afolabi", "7073367543"),
            ("Mile12", "fashola afolabi", "7073367543"),
            ("Obalende", "JOHN PETER", "9063137380"),
            ("Ikorodu", "JOHN PETER", "9063137380"),
            ("Berger", "Balogun temitayo kehinde", "080 8573 83 77"),
        ]

        updated_count = 0
        not_found = set()
        matched_hubs = set()

        with transaction.atomic():
            for hub_name, captain, phone in mapping:
                # Find relay node with similar name (case-insensitive exact match)
                # We try exact match first
                relay_node = RelayNode.objects.filter(name__iexact=hub_name).first()

                # If not found and has a slash, try swapping or searching subsets if needed
                # but for simplicity we rely on the mapping variations we provided above.

                if relay_node:
                    if relay_node.id in matched_hubs:
                        continue  # Already matched via another name variation

                    relay_node.hub_captain_name = captain
                    relay_node.hub_captain_phone = phone
                    relay_node.save(
                        update_fields=["hub_captain_name", "hub_captain_phone"]
                    )

                    matched_hubs.add(relay_node.id)
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Updated: '{relay_node.name}' -> {captain} ({phone})"
                        )
                    )
                else:
                    not_found.add(hub_name)

        # Report unmatched variations
        # Note: Some variations in the list are expected to fail if the other one matches.
        # So we only report if NO variation for a logical group matched.
        # But for this simple script, reporting all misses is fine for verification.
        if not_found:
            self.stdout.write(self.style.WARNING("\nVariations not found in DB:"))
            for name in sorted(not_found):
                self.stdout.write(f"- {name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSuccessfully updated {updated_count} unique RelayNodes."
            )
        )
