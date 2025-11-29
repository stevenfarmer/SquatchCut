# SquatchCut UAT Prep Instructions

Audience: **Volunteer testers / UAT participants**  
Goal: Help you install SquatchCut and run a simple, repeatable test script.

You do **not** need to know how to code. You do **not** need GitHub.

---

## 1. What You’ll Need

Before you start:

- A computer with:
  - Windows, macOS, or Linux
- **FreeCAD 1.0+** installed
- The **SquatchCut add-on ZIP** file
- Test files provided to you:
  - `test_parts.csv`
  - `UAT_Checklist.md` (this file may be bundled or referenced)
  - Any feedback template your coordinator provides

---

## 2. What You Do *Not* Need

You do **not** need:

- A GitHub account
- GitHub Desktop
- A compiler
- Any knowledge of Python

Please do **not**:

- Rename the test CSV file
- Move files into the FreeCAD installation folders
- Install additional tools unless explicitly instructed

---

## 3. Install SquatchCut

1. Open **FreeCAD**.
2. Go to **Tools → Add-on Manager**.
3. Click **Install from ZIP**.
4. Choose the SquatchCut ZIP file provided to you.
5. Wait for installation to complete.
6. Close and restart FreeCAD.

After restart, confirm that:

- A **SquatchCut** toolbar or menu appears.
- You see at least:
  - A **SquatchCut** button (main panel)
  - A **Settings** button

If not, please note that as a UAT issue.

---

## 4. Files You Will Use

Your coordinator should give you:

- `test_parts.csv`  
  Sample parts list for testing.

- `UAT_Checklist.md`  
  Step-by-step script to follow inside FreeCAD.

- A feedback template (could be a text file, form, or email instructions).

Keep these together in a known folder (e.g., `Documents/SquatchCut_UAT/`).

---

## 5. How to Run the Test

1. Start **FreeCAD**.
2. Ensure the **SquatchCut** toolbar is visible.
3. Open the **UAT_Checklist.md** file in any text editor (Notepad, VS Code, etc.).
4. Follow each step in the checklist **in order**.
5. After each step, mark:
   - **Pass** – if it worked and made sense.
   - **Fail** – if it did not work, crashed, or was confusing.

Use the notes column to record:

- What you expected
- What actually happened
- Any error messages or weird behavior

You are **not** being graded. The software is.

---

## 6. Taking Screenshots (If Something Fails)

If something breaks or looks wrong:

- On **Windows**:
  - Press **Win + Shift + S** to open the Snip & Sketch / Snipping tool.
  - Drag a box around the area.
  - Save the image.

- On **macOS**:
  - Press **Command + Shift + 4**.
  - Drag a box around the area.
  - A screenshot is saved to your desktop.

- On **Linux**:
  - Use **Print Screen** or your distro’s screenshot tool.

Try to capture:

- The model tree (left panel)
- The SquatchCut UI
- The 3D view showing the layout

---

## 7. When You’re Done

When you complete the checklist:

1. Save your filled-out checklist (if it’s a file).
2. Collect:
   - The completed checklist
   - Any screenshots
   - Any test CSV variations you used (if requested)

3. Send everything to your SquatchCut contact using the method they specified:
   - Email
   - Shared folder
   - Forms, etc.

If you got stuck and couldn’t complete the script, **still** send what you have and note where you stopped.

Thank you for helping test SquatchCut!
