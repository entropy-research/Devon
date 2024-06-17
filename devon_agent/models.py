import json

from sqlalchemy import Column, Integer, String, Text, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

    
def sqlite_url(db_path):
    return "sqlite+aiosqlite:///" + db_path


class SingletonEngine:
    _instance = None

    def __new__(cls, db_path):
        if cls._instance is None:
            # cls._instance = super(SingletonEngine, cls).__new__(cls)
            cls._instance = create_async_engine(
                sqlite_url(db_path), connect_args={"check_same_thread": False}
            )
        return cls._instance

    @classmethod
    def get_engine(cls):
        print("get_engine", cls._instance)
        return cls._instance


# ENGINE = create_async_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()


def set_db_engine(db_path):
    SingletonEngine(db_path)


async def init_db():
    print(SingletonEngine.get_engine)
    engine = SingletonEngine.get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


class JSONData(Base):
    __tablename__ = "json_data"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(Text)


async def load_data(db: AsyncSession):
    result = await db.execute(select(JSONData))
    items = result.scalars().all()
    data = {item.key: json.loads(item.value) for item in items}
    return data


async def _save_data(db: AsyncSession, key, value):
    print("Saving data for: ", key)
    result = await db.execute(select(JSONData).filter_by(key=key))
    db_item = result.scalars().first()
    if db_item:
        db_item.value = json.dumps(value)
    else:
        db_item = JSONData(key=key, value=json.dumps(value))
        db.add(db_item)
    await db.commit()


async def _delete_data(db: AsyncSession, key):
    print("Deleting data for: ", key)
    await db.execute(delete(JSONData).where(JSONData.key == key))
    await db.commit()


async def _save_session_util(key, value):
    engine = SingletonEngine.get_engine()
    print()
    AsyncSessionLocal = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with AsyncSessionLocal() as db_session:
        await _save_data(db_session, key, value)


async def _delete_session_util(key):
    AsyncSessionLocal = sessionmaker(
        bind=SingletonEngine.get_engine(), class_=AsyncSession, expire_on_commit=False
    )
    async with AsyncSessionLocal() as db_session:
        await _delete_data(db_session, key)


async def save_data(db: AsyncSession, data: dict):
    for key, value in data.items():
        await _save_data(db, key, value)


async def del_data(db: AsyncSession, data: dict):
    for key, value in data.items():
        await _delete_session_util(db, key, value)


def get_async_session():
    AsyncSessionLocal = sessionmaker(
        bind=SingletonEngine.get_engine(), class_=AsyncSession, expire_on_commit=False
    )

    return AsyncSessionLocal
