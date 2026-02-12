import os
import sys
from google import genai
from dotenv import load_dotenv

# 1. Load the secret key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: No Gemini API Key found in .env file.")
    sys.exit(1)

# 2. Configure the New Client
# The new 2026 SDK uses a simpler Client structure
client = genai.Client(api_key=api_key)


def consult_architect(problem_description):
    system_context = (
        "You are the Lead Architect for SquatchCut, a FreeCAD nesting add-on. "
        "The project uses STRICTLY SAE/Imperial units. Help the coding agents "
        "resolve the following technical hurdle:"
    )

    try:
        # We use 'gemini-2.0-flash' or 'gemini-1.5-pro' depending on availability
        # 'gemini-2.0-flash' is usually the best default for speed/reliability now
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"{system_context}\n\nTechnical Problem: {problem_description}",
        )

        print("-" * 30)
        print("GEMINI ARCHITECT RESPONSE:")
        print(response.text)
        print("-" * 30)
    except Exception as e:
        print(f"FAILED TO CONTACT ARCHITECT: {str(e)}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        consult_architect(" ".join(sys.argv[1:]))
    else:
        print("Foreman provided no problem description.")
