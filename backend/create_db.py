from app.core.database import Base, engine
import os
import glob
import importlib

# dynamically import all models so Base metadata is populated
for model_file in glob.glob("app/models/*.py"):
    basename = os.path.basename(model_file)
    if basename != "__init__.py":
        module_name = f"app.models.{basename[:-3]}"
        try:
            importlib.import_module(module_name)
            print(f"Imported {module_name}")
        except Exception as e:
            print(f"Failed to import {module_name}: {e}")

print("Resetting database: Dropping all tables...")
Base.metadata.drop_all(bind=engine)
print("Creating all tables in the database...")
Base.metadata.create_all(bind=engine)
print("Done.")
