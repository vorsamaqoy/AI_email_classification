import re
from typing import Dict, List
from config.models import ClassifierConfig

class PatternManager:
    """Manages regex patterns for urgency and department classification"""
    
    def __init__(self, config: ClassifierConfig):
        self.config = config
        self.urgency_patterns = self._build_urgency_patterns()
        self.department_patterns = self._build_department_patterns()
    
    def _build_urgency_patterns(self) -> Dict:
        """Build urgency patterns using configuration"""
        return {
            'critical': {
                'core_patterns': [
                    r'\b(production|live|server|database|api).*\b(down|crashed?|dead|failed?)\b',
                    r'\b(emergency|critical).*\b(alert|issue|problem)\b',
                    r'\b(revenue|money|sales).*\b(impact|loss|losing|lost)\b',
                    r'\b(customers?|clients?).*\b(cannot|can\'t|unable).*\b(access|login|pay|order)\b'
                ],
                'secondary_patterns': [
                    r'\$\d+.*\b(loss|impact|hour)\b',
                    r'\b(all|entire|complete|whole).*\b(down|broken|failed?|stopped?)\b',
                    r'\b(security|breach|hack|attack)\b'
                ],
                'threshold': self.config.urgency.critical_threshold,
                'max_confidence': self.config.urgency.critical_max_confidence
            },
            'high': {
                'core_patterns': [
                    r'\b(urgent|asap|immediately|soon)\b',
                    r'\b(problem|issue|error|bug).*\b(major|significant|important)\b',
                    r'\b(not working|broken|malfunctioning|failing)\b',
                    r'\b(customers?|clients?).*\b(complaining|reporting|angry)\b',
                    r'\b(payment|billing).*\b(issue|problem|error|wrong)\b'
                ],
                'secondary_patterns': [
                    r'\b(affecting|impacting|blocking).*\b(business|operations|workflow)\b',
                    r'\b(multiple|many|several).*\b(customers?|users?|clients?)\b'
                ],
                'threshold': self.config.urgency.high_threshold,
                'max_confidence': self.config.urgency.high_max_confidence
            },
            'medium': {
                'core_patterns': [
                    r'\b(question|inquiry|request|ask)\b',
                    r'\b(help|support|assistance|guidance)\b',
                    r'\b(meeting|schedule|call|discuss)\b',
                    r'\b(demo|trial|evaluation|proposal)\b',
                    r'\b(improve|enhance|optimize|update)\b'
                ],
                'secondary_patterns': [
                    r'\b(next week|next month|future|planning)\b',
                    r'\b(opportunity|deal|potential)\b',
                    r'\b(feature|enhancement|improvement)\b'
                ],
                'threshold': self.config.urgency.medium_threshold,
                'max_confidence': self.config.urgency.medium_max_confidence
            },
            'low': {
                'core_patterns': [
                    r'\b(thank|thanks|appreciate|grateful)\b',
                    r'\b(info|information|fyi|notification|update)\b',
                    r'\b(newsletter|announcement|welcome)\b',
                    r'\b(feedback|suggestion|recommendation)\b'
                ],
                'secondary_patterns': [
                    r'\b(great|excellent|wonderful|amazing|love|happy)\b',
                    r'\b(congratulations|success|achievement)\b',
                    r'\b(no rush|whenever|future reference)\b'
                ],
                'threshold': self.config.urgency.low_threshold,
                'max_confidence': self.config.urgency.low_max_confidence
            }
        }
    
    def _build_department_patterns(self) -> Dict:
        """Build department patterns"""
        return {
            'technical': {
                'patterns': [
                    r'\b(server|database|api|code|sql|git)\b',
                    r'\b(bug|error|crash|timeout|502|404|500)\b',
                    r'\b(integration|deployment|infrastructure|ssl)\b',
                    r'\b(performance|loading|speed|responsive)\b'
                ],
                'context_words': ['technical', 'dev', 'engineering', 'IT'],
                'confidence_boost': 1.2
            },
            'billing': {
                'patterns': [
                    r'\b(invoice|payment|billing|subscription)\b',
                    r'\b(charge|refund|credit|debit|receipt)\b',
                    r'\b(price|cost|fee|tax|financial)\b',
                    r'\b(card|paypal|stripe|transaction)\b'
                ],
                'context_words': ['finance', 'accounting', 'billing'],
                'confidence_boost': 1.3
            },
            'sales': {
                'patterns': [
                    r'\b(demo|trial|pricing|quote|proposal)\b',
                    r'\b(purchase|buy|interested|evaluate)\b',
                    r'\b(meeting|call|presentation|opportunity)\b',
                    r'\b(partnership|collaboration|deal)\b'
                ],
                'context_words': ['sales', 'business', 'commercial'],
                'confidence_boost': 1.2
            },
            'support': {
                'patterns': [
                    r'\b(help|support|assistance|tutorial)\b',
                    r'\b(how to|documentation|manual|guide)\b',
                    r'\b(training|onboarding|setup)\b',
                    r'\b(feature|functionality|usage)\b'
                ],
                'context_words': ['support', 'help', 'customer'],
                'confidence_boost': 1.1
            }
        }
    
    def calculate_pattern_score(self, text: str, patterns: List[str], weight: float) -> float:
        """Calculate score for a set of patterns"""
        score = 0
        for pattern in patterns:
            try:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score += matches * weight
            except re.error:
                continue
        return score
    
    def extract_text_features(self, text: str, urgency_level: str) -> float:
        """Extract text-based features for urgency scoring"""
        score = 0
        
        if urgency_level == 'critical':
            caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
            exclamation_count = text.count('!')
            score += caps_ratio * self.config.weights.caps_ratio_weight
            score += exclamation_count * self.config.weights.exclamation_weight
            
        elif urgency_level == 'low':
            positive_words = len(re.findall(r'\b(thank|great|love|excellent|wonderful)\b', text.lower()))
            score += positive_words * self.config.weights.positive_words_weight
        
        return score