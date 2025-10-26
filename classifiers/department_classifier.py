from typing import Tuple
import logging
from core.patterns import PatternManager
from core.models import ModelManager
from config.models import ClassifierConfig

logger = logging.getLogger(__name__)

class DepartmentClassifier:
    """Classifies emails by target department"""
    
    def __init__(self, config: ClassifierConfig, pattern_manager: PatternManager, model_manager: ModelManager):
        self.config = config
        self.patterns = pattern_manager
        self.models = model_manager
    
    def classify(self, text: str, subject: str, sender: str = "") -> Tuple[str, float]:
        """Classify target department for email"""
        try:
            full_text = f"{subject} {text} {sender}".lower()
            dept_scores = {}
            
            # Calculate pattern-based scores
            for dept, dept_config in self.patterns.department_patterns.items():
                score = self.patterns.calculate_pattern_score(
                    full_text,
                    dept_config['patterns'],
                    self.config.weights.department_signal_weight
                )
                
                # Apply context word boosters
                for word in dept_config['context_words']:
                    if word in full_text:
                        score *= dept_config['confidence_boost']
                
                dept_scores[dept] = score
            
            # Apply BERT validation if available
            if self.config.processing.enable_bert_model:
                dept_scores = self._apply_bert_validation(text, dept_scores)
            
            return self._determine_final_department(dept_scores)
            
        except Exception as e:
            logger.error(f"Department classification failed: {e}")
            return self._fallback_department_classification(text)
    
    def _apply_bert_validation(self, text: str, dept_scores: dict) -> dict:
        """Use BERT zero-shot classification to validate department scores"""
        bert_result = self.models.safe_model_call(
            'bert',
            self.models.bert_classifier,
            text,
            candidate_labels=['technical support', 'billing payment', 'sales business', 'customer support']
        )
        
        if bert_result:
            try:
                label_mapping = {
                    'technical support': 'technical',
                    'billing payment': 'billing',
                    'sales business': 'sales',
                    'customer support': 'support'
                }
                
                predicted_dept = label_mapping.get(bert_result['labels'][0], 'support')
                confidence = bert_result['scores'][0]
                
                if confidence > 0.7:
                    dept_scores[predicted_dept] += 2
                    
            except Exception as e:
                logger.warning(f"BERT validation failed: {e}")
        
        return dept_scores
    
    def _determine_final_department(self, dept_scores: dict) -> Tuple[str, float]:
        """Determine final department based on scores"""
        if not dept_scores or all(score == 0 for score in dept_scores.values()):
            return 'support', 0.7
        
        predicted_department = max(dept_scores, key=dept_scores.get)
        
        # Calculate confidence based on score separation
        score_values = sorted(dept_scores.values(), reverse=True)
        if len(score_values) > 1 and score_values[1] > 0:
            margin = (score_values[0] - score_values[1]) / score_values[0]
            confidence = 0.6 + margin * 0.35
        else:
            confidence = 0.85 if score_values[0] >= 3 else 0.75
        
        return predicted_department, min(0.95, confidence)
    
    def _fallback_department_classification(self, text: str) -> Tuple[str, float]:
        """Fallback classification when main logic fails"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['server', 'api', 'bug', 'error', 'crash']):
            return 'technical', 0.7
        elif any(word in text_lower for word in ['payment', 'billing', 'invoice', 'charge']):
            return 'billing', 0.7
        elif any(word in text_lower for word in ['demo', 'trial', 'pricing', 'buy']):
            return 'sales', 0.7
        else:
            return 'support', 0.7