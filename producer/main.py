from fastapi import FastAPI

from producer.routers.auth import router as auth_router
from producer.core.rabbitmq import rabbitmq_manager

app = FastAPI()

app.include_router(auth_router)


@app.on_event("startup")
async def startup():
    await rabbitmq_manager.connect()
    print("Connected to RabbitMQ")

@app.on_event("shutdown")
async def shutdown():
    await rabbitmq_manager.close()
    print("Connection with RabbitMQ was closed")

@app.get("/")
async def read_root():
    return {"message": "FastAPI приложение работает и подключено к RabbitMQ"}


