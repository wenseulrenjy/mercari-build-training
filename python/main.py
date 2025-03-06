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
    pass


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


# add_item is a handler to add a new item for POST /items .
@app.post("/items", response_model=AddItemResponse)
def add_item(
    name: str = Form(...),
    category: str = Form(...),
    image: UploadFile = File(...),  
    db: sqlite3.Connection = Depends(get_db),
):
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    
    image_name=hash_and_rename_image(image)

    insert_item(Item(name=name, category=category, image_name=image_name))
    return AddItemResponse(**{"message": f"item received: {name}"})

# STEP 4-3 
@app.get("/items", response_model=GetItemResponse)
def get_item():
    with open('items.json') as f:
        items = json.load(f)
    return items 

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
    os.rename(image_binary, image_name)
    
    return image_name

class Item(BaseModel):
    name: str
    category: str
    image_name: str


def insert_item(item: Item):
    # STEP 4-1: add an implementation to store an item
    file_path = "items.json"
    data = {"items": []}

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f) #JSONをPythonのオブジェクトとして読み込む。
            except json.JSONDecodeError:
                pass 

    data["items"].append({"name": item.name, "category": item.category,"image_name": item.image_name})
    
    with open("items.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False , indent=2)
