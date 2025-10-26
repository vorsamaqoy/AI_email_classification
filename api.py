"""
Email Classifier REST API
Production-ready API service with FastAPI, authentication, rate limiting, and monitoring
Updated for modular architecture
"""

from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
import uvicorn
import asyncio
import time
import logging
from datetime import datetime, timedelta
import os
import hashlib
import json
from collections import defaultdict
import threading

# Updated imports for modular architecture
from email_classifier import EmailClassifier
from config.models import create_sample_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================================
# PYDANTIC MODELS
# ================================

class EmailRequest(BaseModel):
    """Request model for email classification"""
    subject: str = Field(..., description="Email subject", max_length=200)
    content: str = Field(..., alias="testo_email", description="Email content", max_length=10000)
    sender: Optional[str] = Field(None, description="Sender email address", max_length=100)
    
    @validator('subject', 'content')
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Subject and content cannot be empty')
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "subject": "Production server issue",
                "content": "Our main database server is experiencing high load and slow response times. Customer complaints are increasing.",
                "sender": "ops@company.com"
            }
        }

class EmailBatchRequest(BaseModel):
    """Request model for batch classification"""
    emails: List[EmailRequest] = Field(..., description="List of emails to classify", max_items=50)
    
    class Config:
        schema_extra = {
            "example": {
                "emails": [
                    {
                        "subject": "Server down",
                        "content": "Production server crashed",
                        "sender": "ops@company.com"
                    },
                    {
                        "subject": "Thank you",
                        "content": "Thanks for the great support",
                        "sender": "customer@example.com"
                    }
                ]
            }
        }

class ClassificationResponse(BaseModel):
    """Response model for single email classification"""
    urgency: str = Field(..., description="Urgency level: critical, high, medium, low")
    urgency_confidence: float = Field(..., description="Confidence score for urgency (0-1)")
    department: str = Field(..., description="Department: technical, billing, sales, support")
    department_confidence: float = Field(..., description="Confidence score for department (0-1)")
    overall_confidence: float = Field(..., description="Overall classification confidence (0-1)")
    processing_time: float = Field(..., description="Processing time in seconds")
    timestamp: datetime = Field(..., description="Classification timestamp")
    version: str = Field(..., description="Classifier version")
    
    class Config:
        schema_extra = {
            "example": {
                "urgency": "high",
                "urgency_confidence": 0.85,
                "department": "technical",
                "department_confidence": 0.90,
                "overall_confidence": 0.875,
                "processing_time": 0.15,
                "timestamp": "2025-09-12T10:30:00Z",
                "version": "modular_v3.0"
            }
        }

class BatchResponse(BaseModel):
    """Response model for batch classification"""
    results: List[ClassificationResponse]
    total_processed: int
    total_processing_time: float
    average_confidence: float

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: datetime
    uptime: float
    models_loaded: Dict[str, bool]
    total_requests: int
    average_response_time: float
    
class StatsResponse(BaseModel):
    """Statistics response"""
    total_requests: int
    requests_by_urgency: Dict[str, int]
    requests_by_department: Dict[str, int]
    average_response_time: float
    error_rate: float
    uptime: float

# ================================
# RATE LIMITING
# ================================

class RateLimiter:
    """Simple rate limiter implementation"""
    
    def __init__(self, max_requests: int = 100, time_window: int = 3600):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(list)
        self.lock = threading.Lock()
    
    def is_allowed(self, client_id: str) -> bool:
        with self.lock:
            now = time.time()
            
            # Clean old requests
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if now - req_time < self.time_window
            ]
            
            # Check rate limit
            if len(self.requests[client_id]) >= self.max_requests:
                return False
            
            # Add current request
            self.requests[client_id].append(now)
            return True

# ================================
# AUTHENTICATION
# ================================

class APIKeyAuth:
    """Simple API key authentication"""
    
    def __init__(self):
        # In production, store these in environment variables or database
        self.valid_keys = {
            "demo_key_12345": {"name": "demo_user", "tier": "basic"},
            "prod_key_67890": {"name": "production_user", "tier": "premium"},
        }
    
    def validate_key(self, api_key: str) -> Optional[Dict]:
        return self.valid_keys.get(api_key)

# ================================
# API APPLICATION
# ================================

class EmailClassifierAPI:
    """Main API application class"""
    
    def __init__(self, config_path: str = None):
        self.app = FastAPI(
            title="Email Classifier API",
            description="Production-ready email classification service with urgency and department detection",
            version="3.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Initialize components
        self.classifier = None
        self.rate_limiter = RateLimiter(max_requests=1000, time_window=3600)  # 1000 req/hour
        self.auth = APIKeyAuth()
        self.security = HTTPBearer()
        
        # Statistics
        self.start_time = time.time()
        self.stats = {
            "total_requests": 0,
            "urgency_counts": defaultdict(int),
            "department_counts": defaultdict(int),
            "response_times": [],
            "errors": 0
        }
        
        # Setup middleware and routes
        self._setup_middleware()
        self._setup_routes()
        
        # Initialize classifier
        self._initialize_classifier(config_path)
    
    def _setup_middleware(self):
        """Setup CORS and other middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production, specify allowed origins
            allow_credentials=True,
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
        )
        
        @self.app.middleware("http")
        async def log_requests(request, call_next):
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log request
            logger.info(
                f"{request.method} {request.url.path} "
                f"- {response.status_code} - {process_time:.3f}s"
            )
            
            return response
    
    def _initialize_classifier(self, config_path: str = None):
        """Initialize the email classifier"""
        try:
            logger.info("Initializing email classifier...")
            
            # Create sample config if it doesn't exist
            if not os.path.exists("config/classifier.yaml"):
                create_sample_config()
            
            # Use the new EmailClassifier class
            self.classifier = EmailClassifier(config_path)
            
            if not self.classifier.load_models():
                raise RuntimeError("Failed to load classification models")
            
            logger.info("Email classifier initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize classifier: {e}")
            raise RuntimeError(f"Classifier initialization failed: {e}")
    
    def _get_client_id(self, request) -> str:
        """Get client identifier for rate limiting"""
        # Use API key or IP address as client ID
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            return hashlib.md5(auth_header.encode()).hexdigest()
        
        # Fallback to IP address
        client_ip = request.client.host
        return hashlib.md5(client_ip.encode()).hexdigest()
    
    async def _authenticate(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        """Authenticate API requests"""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required"
            )
        
        user_info = self.auth.validate_key(credentials.credentials)
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        return user_info
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/", summary="Root endpoint", include_in_schema=False)
        async def root():
            return {
                "message": "Email Classifier API",
                "version": "3.0.0",
                "docs": "/docs",
                "health": "/health"
            }
        
        @self.app.get("/health", response_model=HealthResponse, summary="Health check")
        async def health():
            """Check API health and model status"""
            uptime = time.time() - self.start_time
            avg_response_time = (
                sum(self.stats["response_times"]) / len(self.stats["response_times"])
                if self.stats["response_times"] else 0
            )
            
            # Get model health from the new architecture
            model_health = self.classifier.model_manager.get_model_health() if self.classifier else {}
            working_models = model_health.get('working_models', {})
            
            return HealthResponse(
                status="healthy" if self.classifier and sum(working_models.values()) > 0 else "unhealthy",
                timestamp=datetime.utcnow(),
                uptime=uptime,
                models_loaded=working_models,
                total_requests=self.stats["total_requests"],
                average_response_time=avg_response_time
            )
        
        @self.app.get("/stats", response_model=StatsResponse, summary="API statistics")
        async def stats(user: Dict = Depends(self._authenticate)):
            """Get API usage statistics"""
            uptime = time.time() - self.start_time
            avg_response_time = (
                sum(self.stats["response_times"]) / len(self.stats["response_times"])
                if self.stats["response_times"] else 0
            )
            error_rate = (
                self.stats["errors"] / max(self.stats["total_requests"], 1) * 100
            )
            
            return StatsResponse(
                total_requests=self.stats["total_requests"],
                requests_by_urgency=dict(self.stats["urgency_counts"]),
                requests_by_department=dict(self.stats["department_counts"]),
                average_response_time=avg_response_time,
                error_rate=error_rate,
                uptime=uptime
            )
        
        @self.app.post("/classify", response_model=ClassificationResponse, summary="Classify single email")
        async def classify_email(
            email: EmailRequest,
            background_tasks: BackgroundTasks,
            user: Dict = Depends(self._authenticate)
        ):
            """
            Classify a single email for urgency and department.
            
            Returns classification results with confidence scores.
            """
            start_time = time.time()
            
            # Check rate limiting
            client_id = user.get("name", "unknown")
            if not self.rate_limiter.is_allowed(client_id):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Try again later."
                )
            
            try:
                # Prepare email data for classifier
                email_data = {
                    "subject": email.subject,
                    "testo_email": email.content,
                    "sender": email.sender or ""
                }
                
                # Use the new classify_email method
                result = self.classifier.classify_email(email_data)
                
                # Check for classification errors
                if "error" in result:
                    self.stats["errors"] += 1
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Classification failed: {result['error']}"
                    )
                
                # Prepare response
                processing_time = time.time() - start_time
                response = ClassificationResponse(
                    urgency=result["urgency"],
                    urgency_confidence=result["urgency_confidence"],
                    department=result["department"],
                    department_confidence=result["department_confidence"],
                    overall_confidence=result["overall_confidence"],
                    processing_time=processing_time,
                    timestamp=datetime.utcnow(),
                    version=result["version"]
                )
                
                # Update statistics in background
                background_tasks.add_task(
                    self._update_stats,
                    result["urgency"],
                    result["department"],
                    processing_time
                )
                
                return response
                
            except HTTPException:
                raise
            except Exception as e:
                self.stats["errors"] += 1
                logger.error(f"Classification error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Internal server error: {str(e)}"
                )
        
        @self.app.post("/classify/batch", response_model=BatchResponse, summary="Classify multiple emails")
        async def classify_batch(
            request: EmailBatchRequest,
            background_tasks: BackgroundTasks,
            user: Dict = Depends(self._authenticate)
        ):
            """
            Classify multiple emails in a single request.
            
            Limited to 50 emails per batch to prevent timeouts.
            """
            if len(request.emails) > 50:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Maximum 50 emails per batch request"
                )
            
            start_time = time.time()
            results = []
            errors = 0
            
            for email in request.emails:
                try:
                    email_data = {
                        "subject": email.subject,
                        "testo_email": email.content,
                        "sender": email.sender or ""
                    }
                    
                    # Use the new classify_email method
                    result = self.classifier.classify_email(email_data)
                    
                    if "error" in result:
                        errors += 1
                        continue
                    
                    response = ClassificationResponse(
                        urgency=result["urgency"],
                        urgency_confidence=result["urgency_confidence"],
                        department=result["department"],
                        department_confidence=result["department_confidence"],
                        overall_confidence=result["overall_confidence"],
                        processing_time=result["processing_time"],
                        timestamp=datetime.utcnow(),
                        version=result["version"]
                    )
                    
                    results.append(response)
                    
                    # Update stats for each email
                    background_tasks.add_task(
                        self._update_stats,
                        result["urgency"],
                        result["department"],
                        result["processing_time"]
                    )
                    
                except Exception as e:
                    errors += 1
                    logger.error(f"Batch classification error for email: {e}")
            
            total_processing_time = time.time() - start_time
            average_confidence = (
                sum(r.overall_confidence for r in results) / len(results)
                if results else 0
            )
            
            return BatchResponse(
                results=results,
                total_processed=len(results),
                total_processing_time=total_processing_time,
                average_confidence=average_confidence
            )
        
        @self.app.post("/config/reload", summary="Reload configuration")
        async def reload_config(user: Dict = Depends(self._authenticate)):
            """Reload classifier configuration from file"""
            try:
                if not self.classifier:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Classifier not initialized"
                    )
                
                success = self.classifier.reload_config()
                if success:
                    return {"message": "Configuration reloaded successfully"}
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to reload configuration"
                    )
            
            except Exception as e:
                logger.error(f"Config reload error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Configuration reload failed: {str(e)}"
                )
    
    def _update_stats(self, urgency: str, department: str, response_time: float):
        """Update API statistics"""
        self.stats["total_requests"] += 1
        self.stats["urgency_counts"][urgency] += 1
        self.stats["department_counts"][department] += 1
        self.stats["response_times"].append(response_time)
        
        # Keep only last 1000 response times to prevent memory issues
        if len(self.stats["response_times"]) > 1000:
            self.stats["response_times"] = self.stats["response_times"][-1000:]

# ================================
# APPLICATION FACTORY
# ================================

def create_app(config_path: str = None) -> FastAPI:
    """Create and configure the FastAPI application"""
    api = EmailClassifierAPI(config_path)
    return api.app

# ================================
# CLI RUNNER
# ================================

def run_api(
    host: str = "0.0.0.0",
    port: int = 8000,
    config_path: str = None,
    workers: int = 1,
    log_level: str = "info"
):
    """Run the API server"""
    print(f"""
🚀 Starting Email Classifier API v3.0 (Modular Architecture)
============================================================
Host: {host}:{port}
Config: {config_path or 'default'}
Workers: {workers}
Docs: http://{host}:{port}/docs
Health: http://{host}:{port}/health

API Keys for testing:
- demo_key_12345 (basic tier)
- prod_key_67890 (premium tier)
    """)
    
    app = create_app(config_path)
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        workers=workers,
        log_level=log_level
    )

if __name__ == "__main__":
    # For development
    run_api(port=8000, log_level="debug")