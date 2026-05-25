"""
NLP Models for Sentiment and Emotion Classification

This module provides sentiment and emotion detection using zero-shot classification
from pre-trained multilingual transformer models. It replaces the static word-based
approach with a more nuanced model-based approach.

Model: xlm-roberta-base (supports 100+ languages including Portuguese)
"""

import logging
import math
from typing import List, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

SENTIMENT_LABELS = ["positivo", "negativo", "neutro"]
EMOTION_LABELS = ["raiva", "entusiasmo", "duvida", "neutra"]

# Confidence thresholds
SENTIMENT_CONFIDENCE_THRESHOLD = 0.3
EMOTION_CONFIDENCE_THRESHOLD = 0.3

class NLPGenericProcessor:
    def __init__(self):
        self._classifier = None

    def get_classifier(self, model: str | None = None):
        """
		Lazily load the classifier pipeline.
		"""
        if self._classifier is None:
            try:
                from transformers import pipeline
                classifier = pipeline(
                    "zero-shot-classification",
                    model="joeddav/xlm-roberta-large-xnli" if model == None else model,
                    device=-1,  # -1 uses CPU, 0+ uses GPU
                )
                self._classifier = classifier
            except Exception as e:
                logger.error(f"Error instanciating classifier: {e}")
                raise
        return self._classifier
    
    def _is_empty_or_nan(self, text: str | None) -> bool:
        """Check if text is None, NaN, or empty string."""
        if text is None:
            return True
        if isinstance(text, float) and math.isnan(text):
            return True
        if isinstance(text, str) and text.strip() == "":
            return True
        return False


    def normalize_text(self, text: str | None) -> str:
        """
        Normalize text for classification.
        Handles None/NaN and converts to string.
        """
        if self._is_empty_or_nan(text):
            return ""
        return str(text).strip()
    
    def score(self, text: str | None, labels: List[str], classifier) -> Tuple[str, float]:
        """
        Classify using zero-shot classification.
        
        Args:
            text: Input text (str or None, handles None/NaN)
        
        Returns:
            Tuple of (label, confidence_score)
        """
        normalized_text = self.normalize_text(text)
        
        if not normalized_text:
            return "neutro", 0.0
        
        try:
            result = classifier(normalized_text, labels, multi_class=False)
            
            # result format: {'sequence': text, 'labels': [...], 'scores': [...]}
            label = result["labels"][0]  # Top label
            score = float(result["scores"][0])  # Top score
            return label, score
        except Exception:
            raise


class SentimentProcessor(NLPGenericProcessor):
    def __init__(self):
        super().__init__()


    def _get_sentiment_classifier(self, model: str | None = None):
        return super().get_classifier(model=model)
    

    def detect_sentiment(self, text: str | None, model: str | None = None) -> Tuple[str, int]:
        try:
            classifier = self._get_sentiment_classifier(model)
            label, score = super().score(text, SENTIMENT_LABELS, classifier)
            
            # Convert confidence (0-1) to int (0-100)
            confidence = int(round(score * 100))

            # If confidence is too low, default to neutral
            if score < SENTIMENT_CONFIDENCE_THRESHOLD:
                return "neutro", confidence
            
            # Adjust sign for sentiment scoring compatibility
            if label == "positivo":
                return label, confidence
            elif label == "negativo":
                return label, -confidence
            else:  # neutral
                return label, 0
        except Exception as e:
            logger.error(f"Error when classifying sentiment: {e}")
            return "neutro", 0.0


class EmotionProcessor(NLPGenericProcessor):
    def __init__(self):
        super().__init__()


    def _get_emotion_classifier(self, model: str | None = None):
        return super().get_classifier(model=model)


    def detect_emotion(self, text: str | None, model: str | None = None) -> str:
        """
        Detect emotion using zero-shot classification.
        
        Args:
            text: Input text (str or None, handles None/NaN)
        
        Returns:
            Emotion label: "raiva", "entusiasmo", "duvida", or "neutra"
        """  
        try:
            classifier = self._get_emotion_classifier(model)
            label, score = super().score(text, EMOTION_LABELS, classifier)
            
            # If confidence is too low, default to neutral
            if score < EMOTION_CONFIDENCE_THRESHOLD or label == "neutra":
                return "neutra"
            
            # Special case: boost "duvida" if text contains "?"
            # This preserves the original heuristic
            if "?" in super().normalize_text(text) and label != "duvida":
                # If confidence is high enough for the first label, keep it
                # Otherwise, consider "duvida" if ? is present
                if score < 0.4:  # Low confidence on first label
                    return "duvida"
            
            return label
        except Exception as e:
            logger.error(f"Error when detecting emotion: {e}")
            return "neutra"




if __name__ == "__main__":
    emotion_processor = EmotionProcessor()
    sentiment_processor = SentimentProcessor()

    # Simple test when run as script
    logging.basicConfig(level=logging.INFO)
	
    test_cases = [
		"Adorei este vídeo! Fantástico!",
		"Que horrível, simplesmente ruim",
		"Interessante, nada demais",
		"Como você fez isso?",
		"",
		None,
	]
	
    print("Testing sentiment classification:")
    for text in test_cases:
        label, score = sentiment_processor.detect_sentiment(text)
        print(f"  '{text}' -> {label} ({score})")
	
    print("\nTesting emotion detection:")
    for text in test_cases:
        emotion = emotion_processor.detect_emotion(text)
        print(f"  '{text}' -> {emotion}")
