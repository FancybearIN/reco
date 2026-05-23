from src.core.db import engine
from src.core.models import Base

def init_db():
    print("Initializing Database...")
    Base.metadata.create_all(bind=engine)
    print("Database Initialized.")

if __name__ == "__main__":
    init_db()
