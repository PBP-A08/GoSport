class ProductDataRouter:
    """
    A router to control all database operations on models in the
    main application that should use the 'product_data' database.
    
    This is specifically for the temporary ProductsData model.
    """
    
    def db_for_read(self, model, **hints):
        """Reads ProductsData from the 'product_data' database."""
        if model._meta.app_label == 'main' and model._meta.model_name == 'productsdata':
            return 'product_data'
        return 'default'

    def db_for_write(self, model, **hints):
        """Writes ProductsData to the 'product_data' database (though we won't be writing to it)."""
        if model._meta.app_label == 'main' and model._meta.model_name == 'productsdata':
            return 'product_data'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations if both objects are in the default database."""
        if obj1._state.db in ['default', 'product_data'] and obj2._state.db in ['default', 'product_data']:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Ensure the ProductsData model is only migrated on its specific database,
        and all others on 'default'.
        """
        if model_name == 'productsdata':
            return db == 'product_data'
        # All other models (like Product, Profile, etc.) only run migrations on 'default'
        return db == 'default'
