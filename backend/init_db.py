from database.db import engine, Base
from database.models import User  # noqa: F401 -- import ensures model is registered

Base.metadata.create_all(bind=engine)
print("Tables created.")