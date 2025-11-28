# Volunteer UAT Prep Instructions (For Regular Humans)

These instructions are for volunteer testers who are helping validate SquatchCut.  
You do **not** need to know GitHub, Python, or anything even remotely technical.  
If you can open FreeCAD and follow a checklist, you’re qualified.

## Before You Start

You must have:

- A computer (Windows, Mac, or Linux)
- FreeCAD **1.0 or newer** installed
- The SquatchCut add-on ZIP file provided to you
- The sample CSV file: `test_parts.csv`
- The UAT Checklist document (PDF or Markdown)

You **do not need**:
- A GitHub account  
- GitHub Desktop  
- Any coding tools  
- To install or configure Python  
- To understand what “UAT” stands for (but it’s “User Acceptance Testing”)

## How to Install SquatchCut

1. Open **FreeCAD**.
2. Go to the top menu: **Tools → Add-on Manager**.
3. In the Add-on Manager, click **Install from ZIP**.
4. Select the SquatchCut ZIP file you were given.
5. Wait for installation to finish.
6. Restart FreeCAD.

That’s it—you’re ready to test.

## Files You Will Receive

You will be provided with:

- **test_parts.csv**  
  A small cut list for testing.

- **UAT_Checklist**  
  The step-by-step process you will follow.

- **UAT_Feedback_Form.txt**  
  A simple notes file for reporting anything weird.
- Metric and Imperial test CSVs  
  If you use the imperial CSV, set CSV units to “Imperial (in)” before importing.

## How to Run the Test

1. Open the **UAT Checklist**.
2. Follow each step in order (1–22).
3. For each step, mark:
   - **Pass** → everything worked  
   - **Fail** → something didn’t behave as expected  
4. Add notes only when:
   - Something is confusing
   - Something behaves incorrectly
   - FreeCAD crashes or behaves unexpectedly

5. When finished, send back:
   - The completed checklist  
   - The feedback form  
   - Any screenshots (if applicable)

## How to Take Screenshots

If something breaks or looks strange, take a screenshot.

- **Windows:** Press `Win + Shift + S`
- **Mac:** Press `Command + Shift + 4`
- **Linux:** Try `PrintScreen` (this can vary by system)

Screenshots help tremendously.

## What NOT to Do

Please avoid the following:

- ❌ Do **not** install GitHub Desktop  
- ❌ Do **not** try to open or edit the source code  
- ❌ Do **not** rename the CSV file  
- ❌ Do **not** upload anything to GitHub  
- ❌ Do **not** contact the developer tools or open GitHub issues directly  
- ❌ Do **not** try to troubleshoot crashes (just write it down)

Your job is to run the test — not fix the test.

## When You’re Done

Email or message Steven:

- The completed checklist  
- The feedback/notes file  
- Screenshots if you took any  

Thank you for helping make SquatchCut better.
