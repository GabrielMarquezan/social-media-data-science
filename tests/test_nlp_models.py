"""
Unit tests for nlp_models module.

Tests sentiment and emotion classification on Portuguese text,
including edge cases and known phrases.
"""

import math
from typing import List, Tuple

import pytest

from nlp_models import (
	detect_emotion,
	score_sentiment,
	_is_empty_or_nan,
	_normalize_text,
)


class TestTextNormalization:
	"""Test text normalization helper functions."""
	
	def test_is_empty_or_nan_none(self):
		assert _is_empty_or_nan(None) is True
	
	def test_is_empty_or_nan_nan(self):
		assert _is_empty_or_nan(float("nan")) is True
	
	def test_is_empty_or_nan_empty_string(self):
		assert _is_empty_or_nan("") is True
	
	def test_is_empty_or_nan_whitespace_string(self):
		assert _is_empty_or_nan("   ") is True
	
	def test_is_empty_or_nan_valid_text(self):
		assert _is_empty_or_nan("hello") is False
	
	def test_normalize_text_none(self):
		assert _normalize_text(None) == ""
	
	def test_normalize_text_nan(self):
		assert _normalize_text(float("nan")) == ""
	
	def test_normalize_text_string(self):
		assert _normalize_text("  hello world  ") == "hello world"
	
	def test_normalize_text_number(self):
		assert _normalize_text(123) == "123"


class TestSentimentClassification:
	"""Test sentiment classification on Portuguese text."""
	
	def test_sentiment_empty_text(self):
		label, score = score_sentiment("")
		assert label == "neutro"
		assert score == 0
	
	def test_sentiment_none_text(self):
		label, score = score_sentiment(None)
		assert label == "neutro"
		assert score == 0
	
	def test_sentiment_nan_text(self):
		label, score = score_sentiment(float("nan"))
		assert label == "neutro"
		assert score == 0
	
	def test_sentiment_positive_phrases(self):
		"""Test positive sentiment phrases."""
		positive_phrases = [
			"Adorei! Muito bom!",
			"Excelente vídeo, parabéns!",
			"Incrível, top demais!",
			"Perfeito e maravilhoso",
			"Que legal, me encantou!",
		]
		
		for phrase in positive_phrases:
			label, score = score_sentiment(phrase)
			assert label == "positivo", f"Expected positive for: {phrase}"
			assert 0 <= score <= 100, f"Score out of range for: {phrase}"
	
	def test_sentiment_negative_phrases(self):
		"""Test negative sentiment phrases."""
		negative_phrases = [
			"Odiei, muito ruim!",
			"Horrível, pior vídeo",
			"Que absurdo e decepcionante",
			"Péssimo e chato demais",
			"Triste e frustrante",
		]
		
		for phrase in negative_phrases:
			label, score = score_sentiment(phrase)
			assert label == "negativo", f"Expected negative for: {phrase}"
			assert -100 <= score <= 0, f"Score out of range for: {phrase}"
	
	def test_sentiment_neutral_phrases(self):
		"""Test neutral sentiment phrases."""
		neutral_phrases = [
			"Isso é um vídeo.",
			"Vi o conteúdo.",
			"Informação normal.",
			"Um texto simples sem emoção.",
		]
		
		for phrase in neutral_phrases:
			label, score = score_sentiment(phrase)
			assert label == "neutro", f"Expected neutral for: {phrase}"
			assert score == 0, f"Neutral score should be 0 for: {phrase}"
	
	def test_sentiment_return_type(self):
		"""Test that sentiment returns correct types."""
		label, score = score_sentiment("teste")
		assert isinstance(label, str)
		assert isinstance(score, int)
		assert label in ["positivo", "negativo", "neutro"]
	
	def test_sentiment_score_range(self):
		"""Test that sentiment scores are in valid range."""
		test_phrases = [
			"Bom",
			"Ruim",
			"Normal",
			"Amei demais",
			"Odiei demais",
		]
		
		for phrase in test_phrases:
			label, score = score_sentiment(phrase)
			assert -100 <= score <= 100, f"Score out of range: {score}"


class TestEmotionDetection:
	"""Test emotion detection on Portuguese text."""
	
	def test_emotion_empty_text(self):
		emotion = detect_emotion("")
		assert emotion == "neutra"
	
	def test_emotion_none_text(self):
		emotion = detect_emotion(None)
		assert emotion == "neutra"
	
	def test_emotion_nan_text(self):
		emotion = detect_emotion(float("nan"))
		assert emotion == "neutra"
	
	def test_emotion_anger_phrases(self):
		"""Test anger emotion detection."""
		anger_phrases = [
			"Que absurdo! Ódio disso!",
			"Ridículo, que raiva!",
			"Indignado com isso!",
			"Vergonha, que irritante!",
		]
		
		for phrase in anger_phrases:
			emotion = detect_emotion(phrase)
			assert emotion == "raiva", f"Expected anger for: {phrase}"
	
	def test_emotion_enthusiasm_phrases(self):
		"""Test enthusiasm emotion detection."""
		enthusiasm_phrases = [
			"Adorei, incrível!",
			"Amei demais, sensacional!",
			"Parabéns, que show!",
			"Top demais, maravilhoso!",
		]
		
		for phrase in enthusiasm_phrases:
			emotion = detect_emotion(phrase)
			assert emotion == "entusiasmo", f"Expected enthusiasm for: {phrase}"
	
	def test_emotion_doubt_questions(self):
		"""Test doubt/question emotion detection."""
		question_phrases = [
			"Como você fez isso?",
			"Qual é o segredo?",
			"Quando foi feito?",
			"Por que funciona assim?",
			"Alguém sabe como?",
		]
		
		for phrase in question_phrases:
			emotion = detect_emotion(phrase)
			assert emotion == "duvida", f"Expected doubt for: {phrase}"
	
	def test_emotion_neutral_phrases(self):
		"""Test neutral emotion detection."""
		neutral_phrases = [
			"Um vídeo normal.",
			"Conteúdo informativo.",
			"Texto comum sem sentimento.",
		]
		
		for phrase in neutral_phrases:
			emotion = detect_emotion(phrase)
			assert emotion == "neutra", f"Expected neutral for: {phrase}"
	
	def test_emotion_return_type(self):
		"""Test that emotion returns correct type."""
		emotion = detect_emotion("teste")
		assert isinstance(emotion, str)
		assert emotion in ["raiva", "entusiasmo", "duvida", "neutra"]
	
	def test_emotion_valid_labels(self):
		"""Test that emotion returns valid labels."""
		test_phrases = [
			"Adorei!",
			"Odiei!",
			"Como assim?",
			"Texto normal",
			"",
		]
		
		valid_emotions = {"raiva", "entusiasmo", "duvida", "neutra"}
		for phrase in test_phrases:
			emotion = detect_emotion(phrase)
			assert emotion in valid_emotions, f"Invalid emotion label: {emotion}"


class TestBackwardCompatibility:
	"""Test backward compatibility with existing code."""
	
	def test_sentiment_signature_compatibility(self):
		"""Test that sentiment returns (str, int) tuple."""
		result = score_sentiment("test")
		assert isinstance(result, tuple)
		assert len(result) == 2
		assert isinstance(result[0], str)
		assert isinstance(result[1], int)
	
	def test_emotion_signature_compatibility(self):
		"""Test that emotion returns str."""
		result = detect_emotion("test")
		assert isinstance(result, str)
	
	def test_sentiment_label_values(self):
		"""Test that sentiment labels match expected values."""
		test_phrases = {
			"Bom": "positivo",
			"Ruim": "negativo",
			"Normal": "neutro",
		}
		
		for phrase, expected_label in test_phrases.items():
			label, _ = score_sentiment(phrase)
			assert label == expected_label, f"Expected {expected_label} for '{phrase}', got {label}"


class TestEdgeCases:
	"""Test edge cases and special scenarios."""
	
	def test_sentiment_with_emojis(self):
		"""Test sentiment with emoji text."""
		emoji_text = "Adorei! 😍😍😍"
		label, score = score_sentiment(emoji_text)
		assert label in ["positivo", "negativo", "neutro"]
		assert -100 <= score <= 100
	
	def test_emotion_with_urls(self):
		"""Test emotion with URL text."""
		url_text = "Check out this: https://example.com muito bom!"
		emotion = detect_emotion(url_text)
		assert emotion in ["raiva", "entusiasmo", "duvida", "neutra"]
	
	def test_emotion_with_mentions(self):
		"""Test emotion with @mention text."""
		mention_text = "@usuario olhe que bom!"
		emotion = detect_emotion(mention_text)
		assert emotion in ["raiva", "entusiasmo", "duvida", "neutra"]
	
	def test_sentiment_with_accents(self):
		"""Test sentiment with accented Portuguese."""
		accented_text = "Excelente, maravilhoso e perfeito!"
		label, score = score_sentiment(accented_text)
		assert label == "positivo"
	
	def test_emotion_with_contractions(self):
		"""Test emotion with Portuguese contractions."""
		contraction_text = "Pra que serve isso? Não entendi"
		emotion = detect_emotion(contraction_text)
		assert emotion in ["raiva", "entusiasmo", "duvida", "neutra"]
	
	def test_sentiment_long_text(self):
		"""Test sentiment with longer text."""
		long_text = "Este é um vídeo muito bom, adorei! " * 10
		label, score = score_sentiment(long_text)
		assert label in ["positivo", "negativo", "neutro"]
		assert -100 <= score <= 100
	
	def test_emotion_mixed_sentiment(self):
		"""Test emotion with mixed positive and negative."""
		mixed_text = "Adorei a parte inicial, mas o final foi ruim."
		emotion = detect_emotion(mixed_text)
		assert emotion in ["raiva", "entusiasmo", "duvida", "neutra"]


if __name__ == "__main__":
	pytest.main([__file__, "-v"])
