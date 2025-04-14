from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

from producer.routers.auth import router as auth_router
from producer.core.rabbitmq import rabbitmq_manager
from producer.core.exceptions import ValidationError, UnauthorizedError
from producer.core.security import verify_token

app = FastAPI()

class Middleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        public_paths = ["/docs", "/openapi.json", "/redoc", "/auth/login", "/auth/register"]

        if any(request.url.path.startswith(path) for path in public_paths):
            return await call_next(request)
        
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise UnauthorizedError("Missing or invalid Authorization header")
            token = auth_header.split(" ")[1]
            verify_token(token)
            response = call_next(request)
            return response
        except Exception as e:
            raise ValidationError

#Routers
app.include_router(auth_router)

#Middleware
app.add_middleware(Middleware)

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


