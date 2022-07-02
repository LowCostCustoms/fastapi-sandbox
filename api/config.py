from environs import Env

env = Env()

DATABASE_URL = env.str("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/api")

MIN_RUN_LEASE_DURATION = env.timedelta("MIN_RUN_LEASE_DURATION", 30)
MAX_RUN_LEASE_DURATION = env.timedelta("MAX_RUN_LEASE_DURATION", 120)
