from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from pipelines.YOLOSegmenter import YOLOSegmenter
from pipelines.Detection import Detection

# Load environment variables
load_dotenv()

app = FastAPI(title="Fruit Detection API")

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

class ErrorResponse(BaseModel):
    status: str = "error"
    message: str

@app.post("/detect")
async def detect(request: DetectionRequest):
    try:
        # Process the image with specified fruit type
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
async def home():
    return {"message": "WhatsApp Bot is running!"}