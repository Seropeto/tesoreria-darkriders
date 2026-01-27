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
