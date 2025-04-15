from fastapi import FastAPI, Depends
from starlette.middleware.base import BaseHTTPMiddleware

from producer.routers.auth import router as auth_router
from producer.core.rabbitmq import rabbitmq_manager
from producer.core.exceptions import ValidationError, UnauthorizedError
from producer.core.security import verify_token

# dev only
from producer.core.dependencies import oauth2_scheme

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
            payload = verify_token(token)

            request.state.token_payload = payload

            response = await call_next(request)
            return response
        
        except Exception as e:
            raise ValidationError(str(e))

#Routers
app.include_router(auth_router)

#Middleware
app.add_middleware(Middleware)

#dev_only
@app.get("/auth/docs-helper", include_in_schema=False)
async def docs_helper(token: str = Depends(oauth2_scheme)):
    return {"msg": "This makes the Authorize button appear"}

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
    return {"message": "FastAPI is working and connected to RabbitMQ"}

