import torch
from transformers import pipeline
from typing import Optional, Any, Dict
import logging
from config.models import ClassifierConfig

logger = logging.getLogger(__name__)

class ModelManager:
    """Manages AI models with error handling and recovery"""
    
    def __init__(self, config: ClassifierConfig):
        self.config = config
        self.sentiment_model = None
        self.emotion_model = None
        self.bert_classifier = None
        
        self.working_models = {
            'sentiment': False,
            'emotion': False,
            'bert': False
        }
        
        self.model_failures = {
            'sentiment': 0,
            'emotion': 0,
            'bert': 0
        }
    
    def load_models(self) -> bool:
        """Load all AI models"""
        logger.info("Loading AI models...")
        logger.info(f"GPU enabled: {self.config.models.use_gpu}")
        
        device = 0 if (torch.cuda.is_available() and self.config.models.use_gpu) else -1
        
        # Load sentiment model (required)
        if not self._load_sentiment_model(device):
            return False
        
        # Load optional models
        if self.config.processing.enable_emotion_model:
            self._load_emotion_model(device)
        
        if self.config.processing.enable_bert_model:
            self._load_bert_model(device)
        
        working_count = sum(self.working_models.values())
        logger.info(f"Loaded {working_count}/3 models successfully")
        
        return True
    
    def _load_sentiment_model(self, device: int) -> bool:
        """Load sentiment analysis model (required)"""
        try:
            logger.info(f"Loading sentiment model: {self.config.models.sentiment_model}")
            self.sentiment_model = pipeline(
                "sentiment-analysis",
                model=self.config.models.sentiment_model,
                return_all_scores=True,
                device=device
            )
            # Test model
            test_result = self.sentiment_model("test message")
            self.working_models['sentiment'] = True
            logger.info("✅ Sentiment model loaded")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load sentiment model: {e}")
            self.working_models['sentiment'] = False
            return False
    
    def _load_emotion_model(self, device: int):
        """Load emotion analysis model (optional)"""
        try:
            logger.info(f"Loading emotion model: {self.config.models.emotion_model}")
            self.emotion_model = pipeline(
                "text-classification",
                model=self.config.models.emotion_model,
                return_all_scores=True,
                device=device
            )
            test_result = self.emotion_model("test message")
            self.working_models['emotion'] = True
            logger.info("✅ Emotion model loaded")
            
        except Exception as e:
            logger.warning(f"⚠️ Emotion model failed (optional): {e}")
            self.emotion_model = None
            self.working_models['emotion'] = False
    
    def _load_bert_model(self, device: int):
        """Load BERT zero-shot classifier (optional)"""
        try:
            logger.info(f"Loading BERT model: {self.config.models.bert_model}")
            self.bert_classifier = pipeline(
                "zero-shot-classification",
                model=self.config.models.bert_model,
                device=device
            )
            test_result = self.bert_classifier("test", ["positive", "negative"])
            self.working_models['bert'] = True
            logger.info("✅ BERT classifier loaded")
            
        except Exception as e:
            logger.warning(f"⚠️ BERT classifier failed (optional): {e}")
            self.bert_classifier = None
            self.working_models['bert'] = False
    
    def safe_model_call(self, model_name: str, model: Any, text: str, **kwargs) -> Optional[Any]:
        """Safely call a model with error handling"""
        if not model:
            return None
        
        try:
            # Truncate text to configured max length
            safe_text = text[:self.config.models.max_text_length]
            result = model(safe_text, **kwargs)
            return result
            
        except torch.cuda.OutOfMemoryError:
            logger.warning(f"GPU OOM in {model_name}")
            self.model_failures[model_name] += 1
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            return None
            
        except Exception as e:
            logger.warning(f"Model {model_name} failed: {e}")
            self.model_failures[model_name] += 1
            return None
    
    def get_model_health(self) -> Dict[str, Any]:
        """Get model health status"""
        return {
            'working_models': self.working_models.copy(),
            'model_failures': self.model_failures.copy(),
            'models_loaded': sum(self.working_models.values())
        }