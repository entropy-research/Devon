import time
from sqlalchemy import create_engine, text
from fastapi import FastAPI, Depends
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
import json
from contextlib import asynccontextmanager

DATABASE_PATH = "./.devon_environment.db"
DATABASE_URL = "sqlite+aiosqlite:///" + DATABASE_PATH

ENGINE = create_async_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()

async def init_db():
    async with ENGINE.begin() as conn:
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

async def _save_session_util(key, value):
    AsyncSessionLocal = sessionmaker(bind=ENGINE, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionLocal() as db_session:
        await _save_data(
            db_session,
            key,
            value
        )

async def save_data(db: AsyncSession, data: dict):
    t1 = time.time()
    for key, value in data.items():
        await _save_data(db, key, value)
    
    t2 = time.time()
    print(t2-t1)

def get_async_session():

    AsyncSessionLocal = sessionmaker(bind=ENGINE, class_=AsyncSession, expire_on_commit=False)

    return AsyncSessionLocal