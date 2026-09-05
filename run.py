"""
Backend run script.

Use this to start the FastAPI server with development settings.
"""

if __name__ == "__main__":
    import uvicorn
    from app.config import get_settings

    settings = get_settings()

    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Server: {settings.SERVER_HOST}:{settings.SERVER_PORT}")
    print(f"Docs: http://localhost:{settings.SERVER_PORT}/docs")

    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
