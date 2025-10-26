"""
Configuration dataclasses for the email classifier system.
Separates configuration logic from business logic.
"""

from dataclasses import dataclass, asdict
from typing import Optional
import yaml
import os
import logging

logger = logging.getLogger(__name__)

@dataclass
class ModelConfig:
    """Configuration for AI models"""
    sentiment_model: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    emotion_model: str = "j-hartmann/emotion-english-distilroberta-base"
    bert_model: str = "facebook/bart-large-mnli"
    use_gpu: bool = True
    max_text_length: int = 512
    model_timeout: float = 30.0

@dataclass
class UrgencyThresholds:
    """Thresholds for urgency classification"""
    critical_threshold: float = 4.0
    high_threshold: float = 2.0
    medium_threshold: float = 1.0
    low_threshold: float = 0.5
    critical_max_confidence: float = 0.95
    high_max_confidence: float = 0.90
    medium_max_confidence: float = 0.85
    low_max_confidence: float = 0.80

@dataclass
class ProcessingConfig:
    """Processing configuration"""
    max_email_length: int = 5000
    max_subject_length: int = 200
    batch_size: int = 32
    log_level: str = "INFO"
    enable_emotion_model: bool = True
    enable_bert_model: bool = True

@dataclass
class PatternWeights:
    """Weights for different pattern types"""
    core_pattern_weight: float = 2.0
    secondary_pattern_weight: float = 1.5
    caps_ratio_weight: float = 3.0
    exclamation_weight: float = 0.8
    positive_words_weight: float = 1.5
    department_signal_weight: float = 3.0

@dataclass
class ClassifierConfig:
    """Main configuration class"""
    models: ModelConfig
    urgency: UrgencyThresholds  
    processing: ProcessingConfig
    weights: PatternWeights
    version: str = "2.0"
    
    @classmethod
    def from_file(cls, config_path: str) -> 'ClassifierConfig':
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            return cls(
                models=ModelConfig(**config_data.get('models', {})),
                urgency=UrgencyThresholds(**config_data.get('urgency', {})),
                processing=ProcessingConfig(**config_data.get('processing', {})),
                weights=PatternWeights(**config_data.get('weights', {})),
                version=config_data.get('version', '2.0')
            )
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return cls.default()
        except Exception as e:
            logger.error(f"Error loading config: {e}, using defaults")
            return cls.default()
    
    @classmethod  
    def default(cls) -> 'ClassifierConfig':
        """Return default configuration"""
        return cls(
            models=ModelConfig(),
            urgency=UrgencyThresholds(),
            processing=ProcessingConfig(),
            weights=PatternWeights()
        )
    
    def save_to_file(self, config_path: str):
        """Save configuration to YAML file"""
        config_dict = {
            'models': asdict(self.models),
            'urgency': asdict(self.urgency),
            'processing': asdict(self.processing),
            'weights': asdict(self.weights),
            'version': self.version
        }
        
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)
        
        logger.info(f"Configuration saved to {config_path}")

def create_sample_config():
    """Create sample configuration files"""
    config = ClassifierConfig.default()
    
    os.makedirs("config", exist_ok=True)
    config.save_to_file("config/classifier.yaml")
    
    # Production version
    config.urgency.critical_threshold = 3.5
    config.urgency.high_threshold = 1.8
    config.processing.log_level = "WARNING"
    config.version = "2.0-production"
    
    config.save_to_file("config/classifier_production.yaml")
    
    logger.info("Sample configuration files created")