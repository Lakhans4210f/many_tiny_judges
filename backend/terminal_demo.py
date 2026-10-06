import json
import urllib.request
import urllib.error

API_URL = "http://127.0.0.1:5000/api/analyze"

DEFAULT_QUESTION = (
    "If it takes 5 machines 5 minutes to make 5 widgets, "
    "how long would it take 100 machines to make 100 widgets?"
)


def call_backend(question: str):
    payload = json.dumps({"question": question}).encode("utf-8")

    request = urllib.request.Request(
        API_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw)

    except urllib.error.URLError as exc:
        print("\n[ERROR] Could not connect to the backend.")
        print("Make sure this is running in another terminal:")
        print("    python server.py")
        print(f"\nDetails: {exc}")
        return None

    except Exception as exc:
        print(f"\n[ERROR] {exc}")
        return None


def print_line(char="=", width=78):
    print(char * width)


def print_judge(role, analysis):
    print_line("-")
    print(f"  {role}")
    print_line("-")
    print(analysis if analysis else "No analysis returned.")
    print()


def main():
    print()
    print_line()
    print("              MANY TINY JUDGES")
    print("          TERMINAL DEMONSTRATION")
    print_line()

    print("\nEnter a reasoning problem.")
    print("Press ENTER without typing anything to use the demo question.\n")

    try:
        question = input("Question: ").strip()
    except KeyboardInterrupt:
        print("\nCancelled.")
        return

    if not question:
        question = DEFAULT_QUESTION

    print()
    print_line()
    print("QUESTION")
    print_line()
    print(question)

    print()
    print_line()
    print("SENDING TO MANY TINY JUDGES...")
    print_line()

    data = call_backend(question)

    if not data:
        return

    judges = data.get("judges", [])
    verdict = data.get("verdict")

    print()
    print_line()
    print(f"INDEPENDENT JUDGES ({len(judges)} AVAILABLE)")
    print_line()

    if not judges:
        print("No judge analyses were returned.")
    else:
        for judge in judges:
            role = judge.get("role", "Unknown Judge")
            assessment = judge.get("assessment") or judge.get("text") or ""
            print_judge(role, assessment)

    print_line()
    print("CHIEF ARBITER")
    print_line()

    if verdict:
        print("\nFINAL ANSWER")
        print("-" * 30)
        print(verdict.get("final_answer", "No final answer returned."))

        print("\nRESOLVED DISCREPANCIES")
        print("-" * 30)
        print(
            verdict.get(
                "resolved_discrepancies",
                "No discrepancies reported.",
            )
        )

        print("\nKEY TRAP AVOIDED")
        print("-" * 30)
        print(
            verdict.get(
                "key_trap_avoided",
                "No specific trap reported.",
            )
        )
    else:
        print("No Chief Arbiter verdict was returned.")

    print()
    print_line()
    print("DEMO COMPLETE")
    print_line()
    print()


if __name__ == "__main__":
    main()
