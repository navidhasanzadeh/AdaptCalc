# AdaptCalc

**AdaptCalc** is a self-modifying calculator written in Python. It serves as a **prototype** for **general adaptive smart applications** that can reshape themselves on demand based on user input. AdaptCalc uses **Large Language Models (LLMs)** (via the OpenAI API) for dynamic **code generation**, enabling it to evolve its own source code at runtime.

![alt text](adaptcalc.png "Adaptive Smart Applications")


The software automatically creates time-stamped backups of its code before and after each modification or revert, and it includes a separate tool for reverting to a previous backup if the main program becomes unusable.

> **Warning**: Because AdaptCalc can overwrite its own source code based on user prompts, it should be used cautiously. Malicious or invalid code could break or compromise your system. Only use it in a controlled environment and always keep external backups.

---

## Why AdaptCalc & LLMs Matter

AdaptCalc demonstrates the potential of **LLMs** in **reshaping** how future applications can be developed and maintained. Instead of static, unchanging programs, **adaptive smart software** can:

- **Evolve** based on user feedback,
- **Customize** new features on the fly,
- **Reduce** the need for frequent manual updates by developers,
- **Empower** end-users to co-create their applications.

---

## Features

- **Calculator UI**: A very simple calculator.  
- **Self-Modifying Code**: Select “Customize Entire Script” in the menu, provide a prompt and an OpenAI API key, and watch it rewrite its own Python source using **LLMs**!  
- **Backup & Revert**:  
  - Each time you update or revert, AdaptCalc creates a date- and iteration-stamped `.bak` file.  
  - If the program fails to run, use the standalone `revert_tool.py` to restore a previous backup.
- **Sharing**: Menu option to “Share Current Code,” displaying the entire script in a read-only text area for quick copy/paste.  
- **Prototype of Future**: Demonstrates a vision for adaptive, smart software that can evolve on demand, thanks to powerful LLMs.

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

4. **Run**  
   ```bash
   python adaptcalc.py
