from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # RabbitMQ [rabbit-mq-log-consumer]
    rabbitmq_enabled: bool = False
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_username: str = "guest"
    rabbitmq_password: str = "guest"
    rabbitmq_queue_name: str = "INCIDENT_TRIAGE_LOGS"
    rabbitmq_prefetch_count: int = 20

    ingest_batch_size: int = 10
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "payment_logs"
    http_port: int = 8001

    class Config:
        env_prefix = ""
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
