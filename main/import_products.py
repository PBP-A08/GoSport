import uuid
from collections import defaultdict
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from main.models import ProductsData, Product 

# --- Configuration ---
FIXED_SELLER_USERNAME = 'gosport_admin' 

class Command(BaseCommand):
    help = 'Migrates data from read-only ProductsData to the editable Product model, aggregating stock.'

    def handle(self, *args, **options):
        try:
            seller_user = User.objects.get(username=FIXED_SELLER_USERNAME)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f"Seller user '{FIXED_SELLER_USERNAME}' not found. Please create this user first."
            ))
            return

        self.stdout.write('Aggregating and transforming data from ProductsData...')
        all_raw_products = ProductsData.objects.all()
        product_groups = defaultdict(list)
        
        for p in all_raw_products:
            product_groups[p.product_name].append(p)

        products_to_create = []
        category_map = {
            'racket': ['Racket', 'Badminton', 'Tennis'],
            'ball': ['Ball', 'Volley', 'Cricket Ball'],
            'accessory': ['Kit Bag', 'Guard', 'Grip', 'Shoe', 'Helmet'],
        }
        
        # Helper to find a category
        def determine_category(product_label):
            product_label = product_label.lower()
            if 'racket' in product_label or 'racquet' in product_label: return 'hockey'
            if 'ball' in product_label or 'volley' in product_label: return 'volleyball'
            if 'shoes' in product_label: return 'football'
            if 'kit bag' in product_label or 'guard' in product_label or 'glove' in product_label or 'helmet' in product_label: return 'accessory'
            return 'accessory' # Default category

        for product_name, items in product_groups.items():
            first_item = items[0]
            stock_count = len(items)
            
            new_product_data = Product(
                seller=seller_user, 
                product_name=product_name,
                old_price=first_item.old_price,
                special_price=first_item.special_price,
                discount_percent=int(round(first_item.discount_field)) if first_item.discount_field else 0,
                category=determine_category(first_item.product), # Map to one of your CATEGORY_CHOICES
                description=f"Category: {first_item.product}. {first_item.product_name} is a high-quality product.",
                stock=stock_count,
            )
            products_to_create.append(new_product_data)

        Product.objects.bulk_create(products_to_create)

        self.stdout.write(self.style.SUCCESS(
            f'Successfully created {len(products_to_create)} editable products in the Product model.'
        ))
