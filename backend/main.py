from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth as auth_router, transactions, dashboard, users, debts
import models, database, crud, schemas

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Dark Riders Tesorería API", version="3.0")

@app.on_event("startup")
def startup_event():
    db = database.SessionLocal()
    user = crud.get_user_by_email(db, "admin@darkriders.com")
    if not user:
        crud.create_user(db, schemas.UserCreate(
            email="admin@darkriders.com", 
            password="admin", 
            name="Admin Director", 
            role="admin"
        ))
    db.close()

# CORS configuration
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://127.0.0.1:5500",
    "*" # For ease
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(transactions.router)
app.include_router(dashboard.router)
app.include_router(users.router)
app.include_router(debts.router)

@app.get("/")
def read_root():
    return {"message": "Dark Riders Treasury System API is running"}
# --- AGREGA ESTO AL FINAL DEL ARCHIVO ---
from fastapi.staticfiles import StaticFiles
import os

# Ruta donde Docker guarda el frontend (según nuestro Dockerfile)
frontend_path = "/app/frontend"

# Verificamos si existe la carpeta (para que no falle en local)
if os.path.exists(frontend_path):
    # 'html=True' hace que al entrar a "/" cargue automáticamente index.html
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    print("⚠️ Corriendo en modo solo API (Frontend no encontrado)")