"""
Email Classifier Package
Modern, modular email classification system with configurable ML models.
"""

from .email_classifier import EmailClassifier, ConfigurableEmailClassifier
from .config.models import ClassifierConfig, create_sample_config

__version__ = "3.0.0"
__author__ = "Vincenzo Vigna"

__all__ = [
    'EmailClassifier',
    'ConfigurableEmailClassifier', 
    'ClassifierConfig',
    'create_sample_config'

]
