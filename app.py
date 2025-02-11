from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from mangum import Mangum
from dotenv import load_dotenv
from pipelines.YOLOSegmenter import YOLOSegmenter
from pipelines.Detection import Detection

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Fruit Detection API",
    description="API for fruit detection and ripeness analysis",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize detector
detector = Detection()

# Pydantic models for request validation
class DetectionRequest(BaseModel):
    image: str
    fruit_type: str

class SegmentationRequest(BaseModel):
    image_path: str
    model_type: str
    distance: Optional[float] = 30.0
    confidence: Optional[float] = 0.3

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": str(exc)},
    )

@app.post("/detect")
async def detect(request: DetectionRequest):
    try:
        results = detector.process_image(request.image, request.fruit_type)
        return results
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/segment")
async def segment(request: SegmentationRequest):
    try:
        segmenter = YOLOSegmenter(request.model_type)
        result = segmenter.process_image(
            request.image_path,
            segmentation=True,
            ripeness=True,
            conf=request.confidence,
            legend=True,
            distance_cm=request.distance
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Fruit Detection API is running!"}

# Create handler for AWS Lambda
handler = Mangum(app, lifespan="off")