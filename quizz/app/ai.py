"""Utility functions for AI-powered quiz generation."""

import json
import os
import random
import re

try:
    import openai
except Exception:  # pragma: no cover - openai may not be installed
    openai = None


def _fallback_questions(text, num_questions=5):
    """Generate simple fill-in-the-blank questions locally."""

    sentences = re.split(r"[\n\.]+", text)
    sentences = [s.strip() for s in sentences if len(s.split()) > 3]
    questions = []

    for _ in range(min(num_questions, len(sentences))):
        sent = random.choice(sentences)
        words = sent.split()
        if len(words) < 4:
            continue
        answer = random.choice(words)
        question = sent.replace(answer, "____", 1)
        questions.append({"question": question, "answer": answer})
    return questions


def generate_questions(text, num_questions=5):
    """Generate questions using the OpenAI API with a local fallback."""

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or openai is None:
        return _fallback_questions(text, num_questions)

    openai.api_key = api_key
    prompt = (
        "Generate {n} short-answer quiz questions based on the text below. "
        "Respond with a JSON list where each item has 'question' and 'answer'.\n".format(
            n=num_questions
        )
        + text
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You create quiz questions."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
        )
        content = response["choices"][0]["message"]["content"]
        questions = json.loads(content)
        if isinstance(questions, list):
            return questions
    except Exception:
        # Any failure falls back to the simple algorithm
        pass

    return _fallback_questions(text, num_questions)
