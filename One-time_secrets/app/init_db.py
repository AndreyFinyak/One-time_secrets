from app.database import engine
from app.models import Base

# Создаём все таблицы в базе данных
Base.metadata.create_all(bind=engine)
