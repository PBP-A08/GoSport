import uuid
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
# Assuming your models are located here:
from main.models import ProductsData, Product 

# --- Configuration ---
FIXED_SELLER_USERNAME = 'gosport_admin' 
# You need to ensure this user exists in your main Django database.
# ---------------------

class Command(BaseCommand):
    help = 'Migrates data from read-only ProductsData to the editable Product model, aggregating stock.'

    def handle(self, *args, **options):
        # 1. Get the fixed seller User object
        try:
            seller_user = User.objects.get(username=FIXED_SELLER_USERNAME)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f"Seller user '{FIXED_SELLER_USERNAME}' not found. Please create this user first."
            ))
            return

        # 2. Clear existing data in the target model (OPTIONAL, but recommended for clean migration)
        # ONLY RUN THIS IF YOU ARE SURE YOU WANT TO DELETE EXISTING PRODUCTS!
        # Product.objects.all().delete()
        # self.stdout.write(self.style.SUCCESS('Cleared existing products from target Product model.'))


        # 3. Aggregate data from the read-only source
        self.stdout.write('Aggregating and transforming data from ProductsData...')
        all_raw_products = ProductsData.objects.all()
        product_groups = defaultdict(list)
        
        for p in all_raw_products:
            # Group by the unique product name to count stock
            product_groups[p.product_name].append(p)

        products_to_create = []
        category_map = {
            'racket': ['Racket', 'Badminton', 'Tennis'],
            'ball': ['Ball', 'Volley', 'Cricket Ball'],
            'accessory': ['Kit Bag', 'Guard', 'Grip', 'Shoe', 'Helmet'],
            # This mapping needs to be refined based on the full list of 'Product' values
            # For simplicity, we'll map all remaining to 'accessory' or a default.
        }
        
        # Helper to find a category
        def determine_category(product_label):
            product_label = product_label.lower()
            if 'racket' in product_label or 'racquet' in product_label: return 'hockey' # Re-using 'hockey' for Racket
            if 'ball' in product_label or 'volley' in product_label: return 'volleyball' # Re-using 'volleyball' for Ball
            if 'shoes' in product_label: return 'football' # Re-using 'football' for Shoes
            if 'kit bag' in product_label or 'guard' in product_label or 'glove' in product_label or 'helmet' in product_label: return 'accessory'
            return 'accessory' # Default category

        for product_name, items in product_groups.items():
            first_item = items[0]
            stock_count = len(items)
            
            # Map external fields to the OLD Product model fields
            new_product_data = Product(
                # Django will automatically generate the UUID
                seller=seller_user, 
                product_name=product_name,
                old_price=first_item.old_price,
                special_price=first_item.special_price,
                # Calculate discount percent from the float field
                discount_percent=int(round(first_item.discount_field)) if first_item.discount_field else 0,
                category=determine_category(first_item.product), # Map to one of your CATEGORY_CHOICES
                description=f"Category: {first_item.product}. {first_item.product_name} is a high-quality product.",
                stock=stock_count,
            )
            products_to_create.append(new_product_data)

        # 4. Bulk create the new, editable Product objects
        Product.objects.bulk_create(products_to_create)

        self.stdout.write(self.style.SUCCESS(
            f'Successfully created {len(products_to_create)} editable products in the Product model.'
        ))

# Note: Django management commands must be executed via 'python manage.py runscript' or similar setup.
# The code above is designed to be placed inside a custom Django management command for proper execution.