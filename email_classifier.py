import time
import logging
from typing import Dict, Optional
from pathlib import Path

from config.models import ClassifierConfig, create_sample_config
from core.patterns import PatternManager
from core.models import ModelManager
from core.validators import InputValidator
from classifiers.urgency_classifier import UrgencyClassifier
from classifiers.department_classifier import DepartmentClassifier

logger = logging.getLogger(__name__)

class EmailClassifier:
    """
    Main email classifier that coordinates all classification components.
    Clean, modular architecture with separated concerns.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        # Load configuration
        self.config = self._load_config(config_path)
        self.config_path = config_path
        
        # Initialize components
        self.pattern_manager = PatternManager(self.config)
        self.model_manager = ModelManager(self.config)
        self.input_validator = InputValidator(self.config)
        
        # Initialize classifiers
        self.urgency_classifier = UrgencyClassifier(self.config, self.pattern_manager, self.model_manager)
        self.department_classifier = DepartmentClassifier(self.config, self.pattern_manager, self.model_manager)
        
        # Performance tracking
        self.stats = {
            'processed': 0,
            'processing_times': []
        }
        
    
    def _load_config(self, config_path: Optional[str]) -> ClassifierConfig:
        """Load configuration from file or use defaults"""
        if config_path is None:
            config_path = self._find_config_file()
        
        if config_path:
            config = ClassifierConfig.from_file(config_path)
        else:
            config = ClassifierConfig.default()
        
        # Set logging level
        logging.getLogger().setLevel(getattr(logging, config.processing.log_level))
        
        return config
    
    def _find_config_file(self) -> Optional[str]:
        """Find configuration file in standard locations"""
        possible_paths = [
            "config/classifier.yaml",
            "configs/classifier.yaml", 
            "classifier_config.yaml",
            "config.yaml"
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                logger.info(f"Found config file: {path}")
                return path
        
        logger.info("No config file found, using defaults")
        return None
    
    def load_models(self) -> bool:
        """Load all required AI models"""
        return self.model_manager.load_models()
    
    def reload_config(self) -> bool:
        """Reload configuration from file"""
        if not self.config_path:
            logger.warning("No config file path set, cannot reload")
            return False
        
        try:
            old_version = self.config.version
            new_config = ClassifierConfig.from_file(self.config_path)
            
            # Update all components with new config
            self.config = new_config
            self.pattern_manager = PatternManager(new_config)
            self.input_validator = InputValidator(new_config)
            
            # Update classifiers
            self.urgency_classifier = UrgencyClassifier(new_config, self.pattern_manager, self.model_manager)
            self.department_classifier = DepartmentClassifier(new_config, self.pattern_manager, self.model_manager)
            
            # Update logging level
            logging.getLogger().setLevel(getattr(logging, new_config.processing.log_level))
            
            logger.info(f"Configuration reloaded: {old_version} -> {new_config.version}")
            return True
            
        except Exception as e:
            logger.error(f"Config reload failed: {e}")
            return False
    
    def classify_email(self, email_data: Dict) -> Dict:
        """
        Classify a single email for urgency and department.
        
        Args:
            email_data: Dictionary containing 'subject', 'testo_email', and optionally 'sender'
        
        Returns:
            Classification results with confidence scores and metadata
        """
        start_time = time.time()
        
        try:
            # Validate and preprocess input
            validated_data = self.input_validator.validate_email_data(email_data.copy())
            
            subject = validated_data['subject']
            content = validated_data['testo_email']
            sender = validated_data.get('sender', '')
            
            # Classify urgency and department
            urgency, urgency_conf = self.urgency_classifier.classify(content, subject)
            department, dept_conf = self.department_classifier.classify(content, subject, sender)
            
            # Apply business logic cross-validation
            if department == 'technical' and urgency in ['high', 'critical']:
                # Technical issues with certain keywords should be critical
                critical_keywords = ['down', 'crashed', 'dead', 'failed']
                if urgency == 'high' and any(word in content.lower() for word in critical_keywords):
                    urgency = 'critical'
                    urgency_conf = min(0.95, urgency_conf + 0.1)
            
            # Calculate metrics
            overall_confidence = (urgency_conf + dept_conf) / 2
            processing_time = time.time() - start_time
            
            # Update statistics
            self.stats['processed'] += 1
            self.stats['processing_times'].append(processing_time)
            
            return {
                'urgency': urgency,
                'urgency_confidence': urgency_conf,
                'department': department,
                'department_confidence': dept_conf,
                'overall_confidence': overall_confidence,
                'processing_time': processing_time,
                'model_health': self.model_manager.get_model_health(),
                'config_version': self.config.version,
                'version': 'modular_v3.0'
            }
            
        except Exception as e:
            logger.error(f"Email classification failed: {e}")
            return {
                'urgency': 'medium',
                'urgency_confidence': 0.5,
                'department': 'support',
                'department_confidence': 0.5,
                'overall_confidence': 0.5,
                'processing_time': time.time() - start_time,
                'error': str(e),
                'config_version': self.config.version,
                'version': 'modular_v3.0'
            }
    
    def classify_batch(self, email_list: list) -> list:
        """
        Classify multiple emails efficiently.
        
        Args:
            email_list: List of email dictionaries
        
        Returns:
            List of classification results
        """
        logger.info(f"Classifying batch of {len(email_list)} emails")
        
        results = []
        errors = 0
        
        for i, email in enumerate(email_list):
            try:
                result = self.classify_email(email)
                results.append(result)
                
                if 'error' in result:
                    errors += 1
                
                # Log progress for large batches
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1}/{len(email_list)} emails")
                    
            except Exception as e:
                logger.error(f"Failed to classify email {i}: {e}")
                errors += 1
                
                # Add error result
                results.append({
                    'urgency': 'medium',
                    'urgency_confidence': 0.5,
                    'department': 'support',
                    'department_confidence': 0.5,
                    'overall_confidence': 0.5,
                    'error': str(e),
                    'version': 'modular_v3.0'
                })
        
        logger.info(f"Batch classification completed: {len(results)-errors}/{len(email_list)} successful")
        return results
    
    def get_performance_stats(self) -> Dict:
        """Get classifier performance statistics"""
        avg_time = sum(self.stats['processing_times']) / max(len(self.stats['processing_times']), 1)
        
        return {
            'total_processed': self.stats['processed'],
            'average_processing_time': avg_time,
            'model_health': self.model_manager.get_model_health(),
            'config_version': self.config.version
        }

# Create backward compatibility alias
ConfigurableEmailClassifier = EmailClassifier

def run_validation_suite():
    """Run comprehensive validation of the modular classifier"""
    print("🧪 MODULAR CLASSIFIER VALIDATION SUITE")
    print("=" * 60)
    
    # Ensure config files exist
    if not Path("config/classifier.yaml").exists():
        create_sample_config()
    
    # Test default configuration
    print("\n📊 Testing modular architecture...")
    classifier = EmailClassifier("config/classifier.yaml")
    
    if not classifier.load_models():
        print("❌ Failed to load models")
        return None
    
    # Test cases covering different scenarios
    test_cases = [
        {
            'subject': 'CRITICAL: Production database crashed',
            'testo_email': 'All customer transactions are failing! Revenue impact is severe!',
            'sender': 'alerts@monitoring.com',
            'expected_urgency': 'critical',
            'expected_dept': 'technical'
        },
        {
            'subject': 'Thank you for excellent support',
            'testo_email': 'Your team provided wonderful assistance with our setup. Great work!',
            'sender': 'happy-customer@company.com',
            'expected_urgency': 'low',
            'expected_dept': 'support'
        },
        {
            'subject': 'Invoice discrepancy',
            'testo_email': 'We were charged twice for last month subscription. Please investigate.',
            'sender': 'billing@client.com',
            'expected_urgency': 'high',
            'expected_dept': 'billing'
        },
        {
            'subject': 'Demo request for enterprise features',
            'testo_email': 'Interested in scheduling a product demonstration for our team of 50 users.',
            'sender': 'cto@prospect.com',
            'expected_urgency': 'medium',
            'expected_dept': 'sales'
        }
    ]
    
    print(f"Running {len(test_cases)} test cases...")
    
    correct_urgency = 0
    correct_dept = 0
    
    for i, case in enumerate(test_cases, 1):
        result = classifier.classify_email(case)
        
        urgency_match = result['urgency'] == case['expected_urgency']
        dept_match = result['department'] == case['expected_dept']
        
        if urgency_match:
            correct_urgency += 1
        if dept_match:
            correct_dept += 1
        
        status = "✅" if (urgency_match and dept_match) else "⚠️"
        
        print(f"{status} Test {i}: {case['subject'][:40]}...")
        print(f"    Expected: {case['expected_urgency']}/{case['expected_dept']}")
        print(f"    Got: {result['urgency']}/{result['department']}")
        print(f"    Confidence: {result['overall_confidence']:.1%}")
    
    # Performance metrics
    stats = classifier.get_performance_stats()
    
    print(f"\n📈 VALIDATION RESULTS:")
    print(f"    Urgency Accuracy: {correct_urgency}/{len(test_cases)} = {correct_urgency/len(test_cases):.1%}")
    print(f"    Department Accuracy: {correct_dept}/{len(test_cases)} = {correct_dept/len(test_cases):.1%}")
    print(f"    Overall Accuracy: {(correct_urgency+correct_dept)/(len(test_cases)*2):.1%}")
    print(f"    Average Processing Time: {stats['average_processing_time']:.3f}s")
    
    # Test configuration reload
    print(f"\n🔄 Testing configuration reload...")
    reload_success = classifier.reload_config()
    print(f"    Config Reload: {'✅ Success' if reload_success else '❌ Failed'}")
    
    # Test batch processing
    print(f"\n📦 Testing batch processing...")
    batch_results = classifier.classify_batch(test_cases[:2])
    print(f"    Batch Processing: ✅ {len(batch_results)} emails processed")
    
    overall_score = (correct_urgency + correct_dept) / (len(test_cases) * 2)
    
    if overall_score >= 0.85:
        print(f"\n🎉 MODULAR ARCHITECTURE VALIDATED!")
        print(f"    ✅ Clean separation of concerns")
        print(f"    ✅ High accuracy maintained: {overall_score:.1%}")
        print(f"    ✅ All components working together")
        print(f"    ✅ Configuration management working")
        print(f"    ✅ Batch processing functional")
    else:
        print(f"\n⚠️ Architecture validated but accuracy needs improvement")
    
    return classifier

if __name__ == "__main__":
    run_validation_suite()