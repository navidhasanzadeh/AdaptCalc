# AdaptCalc

**AdaptCalc** is a self-modifying calculator written in Python. It can rewrite its own source code via the OpenAI API, allowing you to dynamically add or change features. The software automatically creates time-stamped backups of its code before and after each modification or revert, and it includes a separate tool for reverting to a previous backup if the main program becomes unusable.

> **Warning**: Because AdaptCalc can overwrite its own source code based on user prompts, it should be used cautiously. Malicious or invalid code could break or compromise your system. Only use it in a controlled environment and always keep external backups.

---

## Features

- **Calculator UI**: A very simple calculator.
- **Self-Modifying Code**: Select “Customize Entire Script” in the menu, provide a prompt and an OpenAI API key, and watch it rewrite its own Python source!
- **Backup & Revert**:  
  - Each time you update or revert, AdaptCalc creates a date- and iteration-stamped `.bak` file.  
  - If the program fails to run, use the standalone `revert_tool.py` to restore a previous backup.
- **Sharing**: Menu option to “Share Current Code,” displaying the entire script in a read-only text area.

---

## Installation

1. **Install Python**  
   Ensure you have Python 3.7+ (ideally 3.9 or newer).

2. **Clone or Download**  
   Clone this repository or download the source code (including `adaptcalc.py`, `revert_tool.py`, and the icon file `calculator.png`).

3. **Install Required Libraries**  
   ```bash
   pip install PySide6
   pip install openai
