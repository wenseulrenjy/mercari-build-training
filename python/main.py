import os
import logging
import pathlib
from fastapi import FastAPI, Form, HTTPException, Depends, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from pydantic import BaseModel
from contextlib import asynccontextmanager
import json
from typing import List
import hashlib


# Define the path to the images & sqlite3 database
images = pathlib.Path(__file__).parent.resolve() / "images"
db = pathlib.Path(__file__).parent.resolve() / "db" / "mercari.sqlite3"
sql_path=pathlib.Path(__file__).parent.resolve() / "db" / "items.sql"


def get_db():
    if not db.exists():
        yield

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    try:
        yield conn
    finally:
        conn.close()


# STEP 5-1: set up the database connection
def setup_database():
    # データベースに接続して、ファイルがなければ新しく作る
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # schema.sqlを開いてSQLコマンドを実行
    with open(sql_path, "r", encoding="utf-8") as file:
        sql_script = file.read()
        cursor.executescript(sql_script)

    # 変更を保存して接続を閉じる
    conn.commit()
    conn.close()



@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_database()
    yield


app = FastAPI(lifespan=lifespan)

logger = logging.getLogger("uvicorn")
logger.level = logging.INFO
images = pathlib.Path(__file__).parent.resolve() / "images"
origins = [os.environ.get("FRONT_URL", "http://localhost:3000")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


class HelloResponse(BaseModel):
    message: str


@app.get("/", response_model=HelloResponse)
def hello():
    return HelloResponse(**{"message": "Hello, world!"})


class AddItemResponse(BaseModel):
    message: str

class GetItemResponse(BaseModel):
    items: List

class Item(BaseModel):
    name: str
    category: str
    image_name: str

# add_item is a handler to add a new item for POST /items .
@app.post("/items", response_model=AddItemResponse)
async def add_item(
    name: str = Form(...),
    category: str = Form(...),
    image: UploadFile = File(...),  
    db: sqlite3.Connection = Depends(get_db),
):
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    
    image_name= await hash_and_rename_image(image)

    insert_item(Item(name=name, category=category, image_name=image_name))
    return AddItemResponse(**{"message": f"item received: {name}{category}{image_name}"})

# STEP 4-3 
@app.get("/items", response_model=GetItemResponse)
def get_item(db : sqlite3.Connection):
    cursor = db.cursor()
    
    query = """SELECT name, categories.name AS category, image_name FROM items
    INNER JOIN categories ON items.category_id = categories.id"""
    
    cursor.execute(query)

    rows = cursor.fetchall()
    items_list = [{"name": name, "category": category, "image_name": image_name} for name, category, image_name in rows]
    result = {"items": items_list}

    cursor.close()
    
    return result 

# get_image is a handler to return an image for GET /images/{filename} .
@app.get("/image/{image_name}")

async def get_image(image_name):
    # Create image path
    image = images / image_name

    if not image_name.endswith(".jpg"):
        raise HTTPException(status_code=400, detail="Image path does not end with .jpg")

    if not image.exists():
        logger.debug(f"Image not found: {image}")
        image = images / "default.jpg"

    return FileResponse(image)

async def hash_and_rename_image(image: UploadFile):
    image_binary = await image.read()
    
    # SHA-256 ハッシュを計算
    hash_value = hashlib.sha256(image_binary).hexdigest()
    
    # 新しいファイル名を生成
    image_name = f"{hash_value}.jpg"
    
    # ファイルをリネーム
    image_path = images / image_name
    with open(image_path, "wb") as f:
        f.write(image_binary)
    
    return image_name

@app.get("/items/{item_id}", response_model=Item)
def get_single_item(item_id: int , db : sqlite3.Connection ):
    cursor = db.cursor()
    
    query = """
            SELECT items.name, categories.name AS category, items.image_name
            FROM items
            INNER JOIN categories ON items.category_id = categories.id
            WHERE items.id = ?
            """
    
    cursor.execute(query, (item_id,))

    rows = cursor.fetchall()
    items_list = [{"name": name, "category": category, "image_name": image_name} for name, category, image_name in rows]
    
    result = {"items":items_list} 

    db.commit()

    cursor.close()
    
    return result  

def insert_item(item: Item , db:sqlite3.Connection):
    cursor = db.cursor()
    query_category ="""SELECT id AS category_id FROM categories WHERE categories.name LIKE ?;"""

    cursor.execute(query_category, (item.category))

    row = cursor.fetchone()

    if row == None:
        query_insert = """INSERT INTO categories (name) VALUES (?)"""
        cursor.execute(query_insert,(item.category))
        category_id = cursor.lastrowid
    else:
        category_id = row[0] #id

    query = """INSERT INTO items (name, category_id, image_name) VALUES (?,?,? );""" #?はセキュリティのため　または{item.name}...

    cursor.execute(query, (item.name, category_id, item.image_name))

    db.commit()

    cursor.close()
    #新しいrowのid
    return cursor.lastrowid

@app.get("/search", response_model=GetItemResponse)
def get_item(db : sqlite3.Connection, keyword : str):

    cursor = db.cursor()
    
    query = """SELECT items.name AS name, categories.name AS category, image_name FROM items JOIN categories ON category_id = categories.id
    WHERE items.name LIKE ?;"""
    
    cursor.execute(query, ('%'+ keyword + '%',))

    rows = cursor.fetchall()
    items_list = [{"name": name, "category": category, "image_name": image_name} for name, category, image_name in rows]
    result = {"items": items_list}

    db.commit()

    cursor.close()
    
    return result 