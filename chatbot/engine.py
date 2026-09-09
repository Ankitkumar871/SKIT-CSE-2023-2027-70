import json
import os
import random
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path


TOKEN_RE = re.compile(r"[a-z0-9]+")


@dataclass
class Intent:
    tag: str
    patterns: list[str]
    responses: list[str]


class ChatbotEngine:
    def __init__(self, intents: list[Intent], threshold: float = 0.42):
        self.intents = intents
        self.threshold = threshold

    @classmethod
    def from_file(cls, path: str):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        intents = [Intent(**item) for item in data["intents"]]
        return cls(intents)

    def reply(self, message: str) -> dict:
        intent, score = self._best_intent(message)
        if intent and score >= self.threshold:
            return {
                "reply": random.choice(intent.responses),
                "source": "intent",
                "tag": intent.tag,
                "confidence": round(score, 2),
            }

        gemini_reply = self._ask_gemini(message)
        if gemini_reply:
            return {
                "reply": gemini_reply,
                "source": "gemini",
                "tag": "ai_fallback",
                "confidence": round(score, 2),
            }

        return {
            "reply": "I do not have a fixed answer for that yet. Please rephrase, or add this question to the intents knowledge base.",
            "source": "fallback",
            "tag": "unknown",
            "confidence": round(score, 2),
        }

    def _best_intent(self, message: str):
        best_intent = None
        best_score = 0.0
        for intent in self.intents:
            for pattern in intent.patterns:
                score = self._score(message, pattern)
                if score > best_score:
                    best_intent = intent
                    best_score = score
        return best_intent, best_score

    def _score(self, message: str, pattern: str) -> float:
        msg = self._normalize(message)
        pat = self._normalize(pattern)
        if not msg or not pat:
            return 0.0

        msg_tokens = set(TOKEN_RE.findall(msg))
        pat_tokens = set(TOKEN_RE.findall(pat))
        token_overlap = len(msg_tokens & pat_tokens) / max(len(pat_tokens), 1)
        fuzzy = SequenceMatcher(None, msg, pat).ratio()
        return (token_overlap * 0.65) + (fuzzy * 0.35)

    def _normalize(self, value: str) -> str:
        return " ".join(TOKEN_RE.findall(value.lower()))

    def _ask_gemini(self, message: str) -> str | None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None

        model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        prompt = (
            "You are an AI linguistic chatbot for a student project. "
            "Give helpful, concise, safe answers in 2-4 sentences. "
            f"User question: {message}"
        )
        try:
            body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
            request = urllib.request.Request(
                url,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=12) as response:
                data = json.loads(response.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (KeyError, IndexError, urllib.error.URLError, TimeoutError):
            return None
