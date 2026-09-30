from database import engine, Base
from models import MiRNA

Base.metadata.create_all(bind=engine)
print("Tables created successfully")
