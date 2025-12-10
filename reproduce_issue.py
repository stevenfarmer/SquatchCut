import sys
import os

# Add freecad directory to sys.path
sys.path.append(os.path.join(os.getcwd(), 'freecad'))

from SquatchCut.core.preferences import SquatchCutPreferences

def reproduce():
    prefs = SquatchCutPreferences()
    try:
        print("Attempting to call get_default_kerf_mm(system='metric')...")
        k = prefs.get_default_kerf_mm(system='metric')
        print(f"Success! Kerf: {k}")
    except TypeError as e:
        print(f"Caught expected TypeError: {e}")
    except Exception as e:
        print(f"Caught unexpected exception: {e}")

if __name__ == "__main__":
    reproduce()
