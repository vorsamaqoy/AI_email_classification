from typing import Tuple
import logging
from core.patterns import PatternManager
from core.models import ModelManager
from config.models import ClassifierConfig

logger = logging.getLogger(__name__)

class UrgencyClassifier:
    """Classifies email urgency levels"""
    
    def __init__(self, config: ClassifierConfig, pattern_manager: PatternManager, model_manager: ModelManager):
        self.config = config
        self.patterns = pattern_manager
        self.models = model_manager
    
    def classify(self, text: str, subject: str) -> Tuple[str, float]:
        """Classify urgency level of email"""
        try:
            full_text = f"{subject} {text}".lower()
            urgency_scores = {}
            
            # Calculate pattern-based scores
            for level, pattern_config in self.patterns.urgency_patterns.items():
                score = 0
                
                # Core patterns
                score += self.patterns.calculate_pattern_score(
                    full_text,
                    pattern_config['core_patterns'],
                    self.config.weights.core_pattern_weight
                )
                
                # Secondary patterns
                if 'secondary_patterns' in pattern_config:
                    score += self.patterns.calculate_pattern_score(
                        full_text,
                        pattern_config['secondary_patterns'],
                        self.config.weights.secondary_pattern_weight
                    )
                
                # Text features
                score += self.patterns.extract_text_features(text, level)
                
                urgency_scores[level] = max(0, score)
            
            # Apply emotion analysis if available
            if self.config.processing.enable_emotion_model:
                urgency_scores = self._apply_emotion_analysis(text, urgency_scores)
            
            # Determine final urgency
            return self._determine_final_urgency(urgency_scores)
            
        except Exception as e:
            logger.error(f"Urgency classification failed: {e}")
            return self._fallback_urgency_classification(text)
    
    def _apply_emotion_analysis(self, text: str, urgency_scores: dict) -> dict:
        """Apply emotion analysis to adjust urgency scores"""
        emotion_result = self.models.safe_model_call('emotion', self.models.emotion_model, text)
        
        if emotion_result and isinstance(emotion_result, list):
            try:
                emotion_scores = {e['label']: e['score'] for e in emotion_result[0]}
                
                # Joy reduces urgency
                joy_score = emotion_scores.get('joy', 0)
                if joy_score > 0.6:
                    urgency_scores['low'] *= (1 + joy_score)
                    urgency_scores['critical'] *= (1 - joy_score * 0.5)
                
                # Anger/fear increase urgency
                anger_score = emotion_scores.get('anger', 0)
                fear_score = emotion_scores.get('fear', 0)
                if anger_score > 0.5 or fear_score > 0.5:
                    urgency_scores['high'] *= 1.3
                    urgency_scores['critical'] *= 1.2
                    
            except Exception as e:
                logger.warning(f"Emotion processing failed: {e}")
        
        return urgency_scores
    
    def _determine_final_urgency(self, urgency_scores: dict) -> Tuple[str, float]:
        """Determine final urgency based on scores and thresholds"""
        if not urgency_scores or all(score == 0 for score in urgency_scores.values()):
            return 'medium', 0.6
        
        # Apply configured thresholds
        for level in ['critical', 'high', 'medium', 'low']:
            pattern_config = self.patterns.urgency_patterns[level]
            threshold = pattern_config['threshold']
            
            if urgency_scores[level] >= threshold:
                max_conf = pattern_config['max_confidence']
                confidence = min(max_conf, 0.5 + (urgency_scores[level] / (threshold * 2)) * 0.4)
                return level, confidence
        
        # Fallback to highest score
        predicted_urgency = max(urgency_scores, key=urgency_scores.get)
        max_score = max(urgency_scores.values())
        confidence = min(0.85, 0.5 + (urgency_scores[predicted_urgency] / max_score) * 0.35)
        
        return predicted_urgency, confidence
    
    def _fallback_urgency_classification(self, text: str) -> Tuple[str, float]:
        """Fallback classification when main logic fails"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['urgent', 'critical', 'emergency', 'asap']):
            return 'high', 0.7
        elif any(word in text_lower for word in ['thank', 'thanks', 'great', 'excellent']):
            return 'low', 0.7
        else:
            return 'medium', 0.6