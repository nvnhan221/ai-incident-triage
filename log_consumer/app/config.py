from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_logs: str = "payment-logs"
    kafka_group_id: str = "log-consumer-vector"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "payment_logs"
    http_port: int = 8001

    class Config:
        env_prefix = ""
        env_file = ".env"


settings = Settings()
