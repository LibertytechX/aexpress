from django.core.management.base import BaseCommand
from orders.models import Vehicle


class Command(BaseCommand):
    help = 'Seed initial vehicle data'

    def handle(self, *args, **kwargs):
        """Create initial vehicle types with pricing."""
        
        vehicles_data = [
            {
                'name': 'Bike',
                'max_weight_kg': 10,
                'base_price': 1200.00,
                'description': 'Motorcycle delivery for small packages up to 10kg',
                'is_active': True
            },
            {
                'name': 'Car',
                'max_weight_kg': 70,
                'base_price': 4500.00,
                'description': 'Car delivery for medium packages up to 70kg',
                'is_active': True
            },
            {
                'name': 'Van',
                'max_weight_kg': 600,
                'base_price': 12000.00,
                'description': 'Van delivery for large packages up to 600kg',
                'is_active': True
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for vehicle_data in vehicles_data:
            vehicle, created = Vehicle.objects.update_or_create(
                name=vehicle_data['name'],
                defaults={
                    'max_weight_kg': vehicle_data['max_weight_kg'],
                    'base_price': vehicle_data['base_price'],
                    'description': vehicle_data['description'],
                    'is_active': vehicle_data['is_active']
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created vehicle: {vehicle.name} - ₦{vehicle.base_price}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated vehicle: {vehicle.name} - ₦{vehicle.base_price}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Seeding complete! Created: {created_count}, Updated: {updated_count}'
            )
        )

