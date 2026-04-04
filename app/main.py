from fastapi import FastAPI

from app.module_users.controller import user_controller

# Equivalente a @SpringBootApplication
app = FastAPI(title="Taller Mecánico API")

# Un endpoint de prueba para ver que todo funciona
@app.get("/")
def health_check():
    return {"status": "ok", "message": "Servidor FastAPI funcionando correctamente"}

app.include_router(user_controller.router)