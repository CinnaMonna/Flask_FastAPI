# Необходимо создать базу данных для интернет-магазина. База данных должна
# состоять из трех таблиц: товары, заказы и пользователи. Таблица товары должна
# содержать информацию о доступных товарах, их описаниях и ценах. Таблица
# пользователи должна содержать информацию о зарегистрированных
# пользователях магазина. Таблица заказы должна содержать информацию о
# заказах, сделанных пользователями.
# ○ Таблица пользователей должна содержать следующие поля: id (PRIMARY KEY),
# имя, фамилия, адрес электронной почты и пароль.
# ○ Таблица товаров должна содержать следующие поля: id (PRIMARY KEY),
# название, описание и цена.
# ○ Таблица заказов должна содержать следующие поля: id (PRIMARY KEY), id
# пользователя (FOREIGN KEY), id товара (FOREIGN KEY), дата заказа и статус
# заказа.
# Создайте модели pydantic для получения новых данных и
# возврата существующих в БД для каждой из трёх таблиц
# (итого шесть моделей).
# Реализуйте CRUD операции для каждой из таблиц через
# создание маршрутов, REST API (итого 15 маршрутов).
# ○ Чтение всех
# ○ Чтение одного
# ○ Запись
# ○ Изменение
# ○ Удаление


from contextlib import asynccontextmanager
import datetime
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel, Field
import databases
import sqlalchemy

DATABASE_URL = "sqlite:///mydatabase.db"

database = databases.Database(DATABASE_URL) 

metadata = sqlalchemy.MetaData()

users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("user_id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("user_name", sqlalchemy.String(32)),
    sqlalchemy.Column("last_name", sqlalchemy.String(32)),
    sqlalchemy.Column("email", sqlalchemy.String(128)),
    sqlalchemy.Column("password", sqlalchemy.String(128))
)

products = sqlalchemy.Table(
    "products",
    metadata,
    sqlalchemy.Column("product_id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("product_name", sqlalchemy.String(32)),
    sqlalchemy.Column("description", sqlalchemy.String(128)),
    sqlalchemy.Column("price", sqlalchemy.Float)
)

orders = sqlalchemy.Table(
    "orders",
    metadata,
    sqlalchemy.Column("order_id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("user_id", sqlalchemy.Integer, foreign_key=True),
    sqlalchemy.Column("product_id", sqlalchemy.Integer, foreign_key=True),
    sqlalchemy.Column("order_date", sqlalchemy.Date),
    sqlalchemy.Column("status", sqlalchemy.Boolean)
)

engine = sqlalchemy.create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()

    yield

    await database.disconnect()

app = FastAPI(lifespan=lifespan)


class UserIn(BaseModel):
    user_name: str = Field(max_length=32)
    last_name: str = Field(max_length=32)
    email: str = Field(max_length=128)
    password: str = Field(max_length=128)

class User(BaseModel):
    user_id: int
    user_name: str = Field(max_length=32)
    last_name: str = Field(max_length=32)
    email: str = Field(max_length=128)
    password: str = Field(max_length=128)

class ProductIn(BaseModel):
    product_name: str = Field(max_length=32)
    description: str = Field(max_length=128)
    price: float

class Product(BaseModel):
    product_id: int
    product_name: str = Field(max_length=32)
    description: str = Field(max_length=128)
    price: float

class OrderIn(BaseModel):
    user_id: int
    product_id: int
    order_date: datetime.date
    status: bool

class Order(BaseModel):
    order_id: int
    user_id: int
    product_id: int
    order_date: datetime.date
    status: bool


@app.post("/users/", response_model=User)
async def create_user(user: UserIn):
    query = users.insert().values(**user.model_dump())
    # query = users.insert().values(user_name=user.user_name, last_name=user.last_name, email=user.email, password=user.password)
    last_record_id = await database.execute(query)
    return {**user.model_dump(), "user_id": last_record_id}

@app.get("/users/", response_model=List[User])
async def read_users():
    query = users.select()
    return await database.fetch_all(query)

@app.get("/users/{user_id}", response_model=User)
async def read_user(user_id: int):
    query = users.select().where(users.c.user_id == user_id)
    return await database.fetch_one(query)

@app.put("/users/{user_id}", response_model=User)
async def update_user(user_id: int, new_user: UserIn):
    query = users.update().where(users.c.user_id == user_id).values(**new_user.model_dump())
    await database.execute(query)
    return {**new_user.model_dump(), "user_id": user_id}

@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    query = users.delete().where(users.c.user_id == user_id)
    await database.execute(query)
    return {'message': 'User deleted'}


@app.post("/products/", response_model=Product)
async def create_product(product: ProductIn):
    query = products.insert().values(**product.model_dump())
    last_record_id = await database.execute(query)
    return {**product.model_dump(), "product_id": last_record_id}

@app.get("/products/", response_model=List[Product])
async def read_products():
    query = products.select()
    return await database.fetch_all(query)

@app.get("/products/{product_id}", response_model=Product)
async def read_product(product_id: int):
    query = products.select().where(products.c.product_id == product_id)
    return await database.fetch_one(query)

@app.put("/products/{product_id}", response_model=Product)
async def update_product(product_id: int, new_product: ProductIn):
    query = products.update().where(products.c.product_id == product_id).values(**new_product.model_dump())
    await database.execute(query)
    return {**new_product.model_dump(), "product_id": product_id}

@app.delete("/products/{product_id}")
async def delete_product(product_id: int):
    query = products.delete().where(products.c.product_id == product_id)
    await database.execute(query)
    return {'message': 'Product deleted'}


@app.post("/orders/", response_model=Order)
async def create_order(order: OrderIn):
    query = orders.insert().values(**order.model_dump())
    last_record_id = await database.execute(query)
    return {**order.model_dump(), "order_id": last_record_id}

@app.get("/orders/", response_model=List[Order])
async def read_orders():
    query = orders.select()
    return await database.fetch_all(query)

@app.get("/orders/{order_id}", response_model=Order)
async def read_order(order_id: int):
    query = orders.select().where(orders.c.order_id == order_id)
    return await database.fetch_one(query)

@app.put("/orders/{order_id}", response_model=Order)
async def update_order(order_id: int, new_order: OrderIn):
    query = orders.update().where(orders.c.order_id == order_id).values(**new_order.model_dump())
    await database.execute(query)
    return {**new_order.model_dump(), "order_id": order_id}

@app.delete("/orders/{order_id}")
async def delete_order(order_id: int):
    query = orders.delete().where(orders.c.order_id == order_id)
    await database.execute(query)
    return {'message': 'Order deleted'}

