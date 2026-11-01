from __future__ import annotations

from mangum import Mangum

from app.main import app

# Mangum adapter wrapping the FastAPI app for AWS Lambda
handler = Mangum(app, lifespan="off")
