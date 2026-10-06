import asyncio
import inspect
import os
from getpass import getpass

from flask import Flask, jsonify, request
from flask_cors import CORS
from google import genai

from app import evaluate_with_judges


app = Flask(__name__)
CORS(app)


# ---------------------------------------------------------
# API KEY / GEMMA CLIENT
# ---------------------------------------------------------

if not os.environ.get("GOOGLE_API_KEY"):
    print("=" * 60)
    print("MANY TINY JUDGES - BACKEND")
    print("=" * 60)

    os.environ["GOOGLE_API_KEY"] = getpass(
        "Google AI Studio API key: "
    ).strip()


API_KEY = os.environ["GOOGLE_API_KEY"]

client = genai.Client(api_key=API_KEY)


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------

@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "model": "gemma-4-26b-a4b-it"
    })


# ---------------------------------------------------------
# ANALYZE QUESTION
# ---------------------------------------------------------

@app.post("/api/analyze")
def analyze():

    data = request.get_json(silent=True) or {}

    question = str(
        data.get("question", "")
    ).strip()

    if not question:
        return jsonify({
            "error": "Question is required."
        }), 400

    print()
    print("=" * 70)
    print("GUI REQUEST")
    print("=" * 70)
    print("Question:")
    print(question)
    print("=" * 70)

    try:

        # -------------------------------------------------
        # Detect the argument structure of the existing
        # evaluate_with_judges() function.
        # -------------------------------------------------

        signature = inspect.signature(
            evaluate_with_judges
        )

        parameters = list(
            signature.parameters.values()
        )

        print(
            "evaluate_with_judges parameters:",
            [p.name for p in parameters]
        )

        # Most versions of our project use either:
        #
        # evaluate_with_judges(question)
        #
        # OR
        #
        # evaluate_with_judges(client, question)

        if len(parameters) == 1:

            result = asyncio.run(
                evaluate_with_judges(
                    question
                )
            )

        elif len(parameters) >= 2:

            result = asyncio.run(
                evaluate_with_judges(
                    client,
                    question
                )
            )

        else:

            raise RuntimeError(
                "Unexpected evaluate_with_judges() signature."
            )

        # -------------------------------------------------
        # Convert Pydantic / Python result into JSON
        # -------------------------------------------------

        if hasattr(result, "model_dump"):
            result = result.model_dump()

        elif hasattr(result, "dict"):
            result = result.dict()

        print()
        print("GUI ANALYSIS COMPLETE")
        print("=" * 70)

        return jsonify(result)

    except Exception as exc:

        print()
        print("BACKEND ERROR")
        print("=" * 70)
        print(type(exc).__name__)
        print(str(exc))
        print("=" * 70)

        return jsonify({
            "error": str(exc)
        }), 500


# ---------------------------------------------------------
# START SERVER
# ---------------------------------------------------------

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("MANY TINY JUDGES")
    print("Gemma 4 Reasoning Verification System")
    print("=" * 70)
    print()
    print("Model : gemma-4-26b-a4b-it")
    print("API   : http://127.0.0.1:5000")
    print("Health: http://127.0.0.1:5000/api/health")
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )