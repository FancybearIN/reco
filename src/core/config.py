from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "reco"
    
    # Infrastructure
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password123"
    
    # Paths
    RECO_ROOT: str = "/home/kali/reco"
    OUTPUT_ROOT: str = "/home/kali/bugbounty"
    DATABASE_URL: str = "sqlite:///./recon_sqlite.db"

    def get_target_path(self, target_name: str) -> str:
        return os.path.join(self.OUTPUT_ROOT, target_name)

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
