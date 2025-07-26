import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sql_analysis.db.database import init_db
from sql_analysis.routers import movies

app = FastAPI(
    title="IMDb Scraper API",
    version="1.0.0",
    description="An API to serve IMDb scraping data and newsletter services."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
async def root():
    """
    Classic FastAPI welcome page.
    """
    return {"page": "home", "Version": "1.0", "Update Date": "Jul 26 2025"}


app.include_router(movies.router)

if __name__ == "__main__":
    uvicorn.run(
        "sql_analysis.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[os.path.dirname(os.path.abspath(__file__))],
        reload_excludes=[
            "*/.git/*",
            "*/__pycache__/*",
            "*.pyc",
            "*/.pytest_cache/*",
            "*/.vscode/*",
            "*/.idea/*"
        ],
        reload_delay=1,
        reload_includes=["*.py", "*.html", "*.css", "*.js"]
    )
