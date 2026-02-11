import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv

# Load the secret key from the .env file
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: No Gemini API Key found in .env file.")
    sys.exit(1)

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-pro")


def consult_architect(problem_description):
    # This reads the technical issue passed from the Foreman
    prompt = f"Architectural Advice Needed for SquatchCut (FreeCAD Nesting):\n\n{problem_description}"

    try:
        response = model.generate_content(prompt)
        print(response.text)
    except Exception as e:
        print(f"Connection to Gemini failed: {str(e)}")


if __name__ == "__main__":
    # This allows the Foreman to run: python gemini_bridge.py "How do I fix X?"
    if len(sys.argv) > 1:
        consult_architect(sys.argv[1])
    else:
        print("No problem description provided.")
