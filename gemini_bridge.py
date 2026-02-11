import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv

# 1. Load the secret key from the .env file
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: No Gemini API Key found in .env file. Please check your setup.")
    sys.exit(1)

# 2. Configure the Architect (Gemini)
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-pro")


def consult_architect(problem_description):
    """
    Called by the Foreman agent when the Draftsman is stuck on
    Imperial units, geometry logic, or FreeCAD API issues.
    """
    system_context = (
        "You are the Lead Architect for SquatchCut, a FreeCAD nesting add-on. "
        "The project uses STRICTLY SAE/Imperial units. Help the coding agents "
        "resolve the following technical hurdle:"
    )

    full_prompt = f"{system_context}\n\nTechnical Problem: {problem_description}"

    try:
        response = model.generate_content(full_prompt)
        # Print to stdout so the Codex Foreman can read the response
        print("-" * 30)
        print("GEMINI ARCHITECT RESPONSE:")
        print(response.text)
        print("-" * 30)
    except Exception as e:
        print(f"FAILED TO CONTACT ARCHITECT: {str(e)}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Join all arguments into one problem description string
        consult_architect(" ".join(sys.argv[1:]))
    else:
        print("Foreman provided no problem description.")
