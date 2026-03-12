from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth as auth_router, transactions, dashboard, users, debts
import models, database, crud, schemas

import time
from sqlalchemy.exc import OperationalError

def init_db():
    """Initializes the database with retries."""
    max_retries = 5
    retry_delay = 5
    for i in range(max_retries):
        try:
            print(f"🔄 Intentando conectar a la base de datos (Intento {i+1}/{max_retries})...", flush=True)
            models.Base.metadata.create_all(bind=database.engine)
            print("✅ Tablas creadas/verificadas exitosamente.", flush=True)
            return True
        except OperationalError as e:
            print(f"⚠️ Error de conexión: {e}")
            if i < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("❌ No se pudo conectar a la base de datos tras varios intentos.")
                return False
        except Exception as e:
            print(f"❌ Error inesperado al inicializar la BD: {e}")
            return False

# Inicialización robusta de la base de datos
init_db()

app = FastAPI(title="Dark Riders Tesorería API", version="3.0")

@app.on_event("startup")
def startup_event():
    db = database.SessionLocal()
    try:
        user = crud.get_user_by_email(db, "admin@darkriders.com")
        if not user:
            print("Creating default admin...", flush=True)
            crud.create_user(db, schemas.UserCreate(
                email="admin@darkriders.com", 
                password="admin", 
                name="Admin Director", 
                role="admin"
            ))
        else:
            print("Admin exists. Force resetting password to 'admin'.", flush=True)
            user.hashed_password = crud.get_password_hash("admin")
            db.add(user)
            db.commit()
            print("✅ Admin password reset to 'admin'", flush=True)
    except Exception as e:
        print(f"⚠️ Error en evento startup: {e}", flush=True)
    finally:
        db.close()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    return {"message": "Dark Riders Treasury System API - LATEST VERSION"}

@app.get("/health-db")
def health_db():
    db = database.SessionLocal()
    try:
        users = db.query(models.User).all()
        user_list = [{"email": u.email, "role": u.role, "active": u.is_active} for u in users]
        db_url = str(database.engine.url)
        # Mask password in URL
        masked_url = db_url.split(":")[0] + "://...@" + db_url.split("@")[-1] if "@" in db_url else db_url
        return {
            "v": "4",
            "status": "connected",
            "user_count": len(users),
            "users": user_list,
            "database_type": database.engine.name,
            "database_url_masked": masked_url
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
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