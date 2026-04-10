"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.llm_gateway import router as llm_gateway_router
from app.api.v1 import api_router
from app.config import settings
from app.db.clickhouse import close_clickhouse, init_clickhouse_tables
from app.db.mysql import close_db, init_db
from app.db.redis import close_redis, init_redis
from app.middleware.audit_log import AuditLogMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("Starting up...")
    
    # Initialize databases
    await init_db()
    await init_redis()
    init_clickhouse_tables()
    
    print("✅ Databases initialized")
    
    yield
    
    # Shutdown
    print("Shutting down...")
    await close_db()
    await close_redis()
    close_clickhouse()
    print("✅ Cleanup complete")


def create_application() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title="AI Gateway",
        description="Enterprise AI Gateway with MaaS capabilities",
        version="1.0.0",
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Audit log middleware
    app.add_middleware(AuditLogMiddleware)
    
    # Health check
    @app.get("/health")
    async def health_check():
        return {"status": "ok", "timestamp": __import__("datetime").datetime.utcnow().isoformat()}
    
    # Include routers
    app.include_router(api_router)
    app.include_router(llm_gateway_router)
    
    return app


app = create_application()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.server.port,
        reload=settings.server.reload,
        debug=settings.server.debug,
    )
