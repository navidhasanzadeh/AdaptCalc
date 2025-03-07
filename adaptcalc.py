import sys
import os
import re
import datetime
from typing import Optional, List

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QGridLayout,
    QLineEdit, QPushButton, QMenu, QMessageBox, QDialog,
    QLabel, QComboBox, QDialogButtonBox, QProgressDialog,
    QPlainTextEdit
)
from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtGui import QFont, QTextOption, QIcon

# ------------------------------------------------------------------------
# OPENAI CLIENT SETUP
# ------------------------------------------------------------------------
try:
    from openai import OpenAI
except ImportError:
    # If the user doesn't have the new-style OpenAI client, fallback or show error
    print("Error: The new OpenAI client is not installed. Install or adapt code.")
    sys.exit(1)

client = OpenAI(
    # Defaults to os.environ.get("OPENAI_API_KEY") if not provided
    api_key="private",
)

def set_api_key(key: str):
    """
    Update the OpenAI client's API key at runtime.
    """
    client.api_key = key.strip()

def chat_gpt(model: str, prompt: str) -> str:
    """
    Call the OpenAI chat completion and return the raw text response.
    """
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


# ------------------------------------------------------------------------
# UTILITY FUNCTIONS
# ------------------------------------------------------------------------
API_KEY_FILENAME = "openai_api_key.txt"

def load_api_key() -> str:
    """
    Load the OpenAI API key from local file if it exists.
    """
    if os.path.exists(API_KEY_FILENAME):
        try:
            with open(API_KEY_FILENAME, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception:
            return ""
    return ""

def save_api_key(key: str):
    """
    Save the given API key to local file.
    """
    try:
        with open(API_KEY_FILENAME, 'w', encoding='utf-8') as f:
            f.write(key.strip())
    except Exception as e:
        print(f"Warning: Could not write API key file: {e}")

def sanitize_script_response(script_code: str) -> str:
    """
    Remove triple backticks or disclaimers if the model includes them.
    """
    script_code = script_code.replace("```", "")
    return script_code.strip()


# ------------------------------------------------------------------------
# BACKUP / REVERT FUNCTIONS
# ------------------------------------------------------------------------
def get_script_name() -> str:
    """
    Return the base name of the current script without extension.
    e.g. "adaptcalc" for "adaptcalc.py".
    """
    script_path = os.path.abspath(sys.argv[0])
    base = os.path.basename(script_path)
    if '.' in base:
        return base.rsplit('.', 1)[0]
    return base

def list_backup_files() -> List[str]:
    """
    Find all .bak files in the current directory that match the naming pattern:
      {script_basename}_YYYYmmdd_HHMMSS_v\d+.bak
    Return them sorted by creation time (ascending).
    """
    script_base = get_script_name()
    pattern = re.compile(rf"^{script_base}_\d{{8}}_\d{{6}}_v\d+\.bak$")
    files = []
    for f in os.listdir('.'):
        if pattern.match(f):
            files.append(f)
    files.sort(key=lambda x: os.path.getmtime(x))
    return files

def get_next_backup_filename() -> str:
    """
    Generate a backup filename with current date/time and iteration ID.
    E.g. "adaptcalc_20250306_153012_v3.bak"
    We find the highest iteration among existing backups and add 1.
    """
    script_base = get_script_name()
    backups = list_backup_files()
    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    iteration = 0
    for b in backups:
        match = re.search(r"_v(\d+)\.bak$", b)
        if match:
            val = int(match.group(1))
            if val > iteration:
                iteration = val
    iteration += 1
    return f"{script_base}_{now_str}_v{iteration}.bak"

def backup_script_custom(file_path: str) -> str:
    """
    Create a time-stamped, iterated backup of the script in the same directory.
    Returns the backup file name used.
    """
    backup_path = get_next_backup_filename()
    try:
        with open(file_path, 'r', encoding='utf-8') as original, open(backup_path, 'w', encoding='utf-8') as backup:
            backup.write(original.read())
        print(f"Created backup: {backup_path}")
    except Exception as e:
        print(f"Warning: Could not create backup: {e}")
    return backup_path

def overwrite_self(new_code: str):
    """
    1) Backup the current script
    2) Overwrite with new code
    3) Restart
    """
    script_path = os.path.abspath(sys.argv[0])
    backup_script_custom(script_path)
    try:
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(new_code)

        print("Script updated. Restarting...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        msg = f"Failed to overwrite script:\n{e}"
        print(msg)
        QMessageBox.critical(None, "Error", msg)

def revert_to_backup(backup_filename: str):
    """
    1) Backup current script
    2) Overwrite with the selected backup
    3) Restart
    """
    script_path = os.path.abspath(sys.argv[0])
    backup_script_custom(script_path)
    try:
        with open(backup_filename, 'r', encoding='utf-8') as bak, open(script_path, 'w', encoding='utf-8') as curr:
            curr.write(bak.read())

        print(f"Reverted to backup: {backup_filename}. Restarting...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        msg = f"Failed to revert to backup {backup_filename}:\n{e}"
        print(msg)
        QMessageBox.critical(None, "Error", msg)


# ------------------------------------------------------------------------
# DIALOGS
# ------------------------------------------------------------------------
class CustomizeDialog(QDialog):
    """
    A dialog to get the user's prompt (multi-line), model, and API key.
    """
    def __init__(self, parent=None, initial_key: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Customize Entire Script via OpenAI")

        self.prompt_text = ""
        self.selected_model = ""
        self.api_key = initial_key

        layout = QVBoxLayout(self)
        font = QFont("Arial", 12)

        lbl_prompt = QLabel("Enter your customization prompt:")
        lbl_prompt.setFont(font)
        layout.addWidget(lbl_prompt)

        self.edit_prompt = QPlainTextEdit()
        self.edit_prompt.setFixedHeight(250)
        self.edit_prompt.setFont(font)
        self.edit_prompt.setWordWrapMode(QTextOption.WordWrap)
        layout.addWidget(self.edit_prompt)

        lbl_model = QLabel("Choose OpenAI model:")
        lbl_model.setFont(font)
        layout.addWidget(lbl_model)

        self.combo_model = QComboBox()
        self.combo_model.setFont(font)
        self.combo_model.addItems(["o1-mini", "o1-preview", "gpt-4o"])  # example
        layout.addWidget(self.combo_model)

        lbl_key = QLabel("OpenAI API Key:")
        lbl_key.setFont(font)
        layout.addWidget(lbl_key)

        self.edit_key = QLineEdit()
        self.edit_key.setPlaceholderText("Enter your OpenAI API key here")
        self.edit_key.setFont(font)
        # Hide characters (password mode)
        self.edit_key.setEchoMode(QLineEdit.Password)
        if self.api_key:
            self.edit_key.setText(self.api_key)
        layout.addWidget(self.edit_key)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self)
        buttons.setFont(font)
        buttons.accepted.connect(self.on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def on_accept(self):
        self.prompt_text = self.edit_prompt.toPlainText().strip()
        self.api_key = self.edit_key.text().strip()
        self.selected_model = self.combo_model.currentText()

        if not self.prompt_text:
            QMessageBox.warning(self, "Warning", "Please enter a prompt.")
            return
        if not self.api_key:
            QMessageBox.warning(self, "Warning", "Please enter your OpenAI API key.")
            return

        self.accept()


class RevertDialog(QDialog):
    """
    A dialog to select which backup version to revert to.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Revert to Backup Version")
        self.selected_backup = None

        layout = QVBoxLayout(self)
        font = QFont("Arial", 12)
        self.setFont(font)

        lbl = QLabel("Select a backup version:")
        lbl.setFont(font)
        layout.addWidget(lbl)

        self.combo_backups = QComboBox()
        self.combo_backups.setFont(font)

        backups = list_backup_files()
        if backups:
            self.combo_backups.addItems(backups)
        layout.addWidget(self.combo_backups)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self)
        buttons.setFont(font)
        buttons.accepted.connect(self.on_ok)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

        if not backups:
            QMessageBox.information(self, "No Backups", "No backups found.")
            self.reject()  # close if none found

    def on_ok(self):
        self.selected_backup = self.combo_backups.currentText()
        self.accept()


class ShareCodeDialog(QDialog):
    """
    Shows the entire current code in a read-only text box.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Share Current Code")

        layout = QVBoxLayout(self)
        font = QFont("Arial", 12)
        self.setFont(font)

        try:
            script_path = os.path.abspath(sys.argv[0])
            with open(script_path, 'r', encoding='utf-8') as f:
                code_text = f.read()
        except Exception as e:
            code_text = f"Error reading current code: {e}"

        text_edit = QPlainTextEdit()
        text_edit.setFont(font)
        text_edit.setReadOnly(True)
        text_edit.setPlainText(code_text)
        layout.addWidget(text_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Close, parent=self)
        buttons.setFont(font)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

        self.setLayout(layout)


# ------------------------------------------------------------------------
# MAIN CALCULATOR WINDOW
# ------------------------------------------------------------------------
class CalculatorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Change the software name
        self.setWindowTitle("AdaptCalc")

        # Set an icon (requires calculator.png in same folder)
        self.setWindowIcon(QIcon("calculator.png"))

        # Global font enlargement
        font = QFont("Arial", 13)
        self.setFont(font)

        # Central widget and layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Display line
        self.display_line = QLineEdit()
        self.display_line.setReadOnly(True)
        self.display_line.setAlignment(Qt.AlignRight)
        self.display_line.setFixedHeight(50)
        layout.addWidget(self.display_line)

        # Grid for buttons
        grid = QGridLayout()
        layout.addLayout(grid)

        buttons = [
            '7', '8', '9', '/',
            '4', '5', '6', '*',
            '1', '2', '3', '-',
            '0', '.', '=', '+'
        ]

        row = 0
        col = 0
        for btn_text in buttons:
            btn = QPushButton(btn_text)
            btn.setFixedSize(70, 70)
            btn.setFont(font)
            btn.clicked.connect(lambda _, x=btn_text: self.on_button_click(x))
            grid.addWidget(btn, row, col)
            col += 1
            if col > 3:
                col = 0
                row += 1

        # Menus
        menu_bar = self.menuBar()
        menu_bar.setFont(font)

        file_menu = QMenu("&File", self)
        file_menu.setFont(font)
        file_menu.addAction("Exit", self.close)
        file_menu.addAction("Revert to Backup", self.on_revert_to_backup)
        menu_bar.addMenu(file_menu)

        customize_menu = QMenu("&Customize", self)
        customize_menu.setFont(font)
        customize_menu.addAction("Customize Entire Script", self.customize_entire_script)
        menu_bar.addMenu(customize_menu)

        share_menu = QMenu("&Share", self)
        share_menu.setFont(font)
        share_menu.addAction("Share Current Code", self.share_current_code)
        menu_bar.addMenu(share_menu)

        help_menu = QMenu("&Help", self)
        help_menu.setFont(font)
        help_menu.addAction("About Us", self.show_about_us)
        menu_bar.addMenu(help_menu)

        # Show usage instructions immediately
        self.show_instructions()

    def show_instructions(self):
        """
        Shows a dialog with instructions on how to use AdaptCalc, 
        how to add or update features, how to revert, that an 
        OpenAI key is needed, and that it's a prototype.
        """
        instructions = (
            "<b>Welcome to AdaptCalc!</b><br><br>"
            "This calculator can modify its own code using the OpenAI API. <br><br>"
            "<u>How to Add or Update Features</u>:<br>"
            "Go to <i>Customize</i> -> <i>Customize Entire Script</i>, enter your prompt, "
            "and provide an OpenAI API key to generate new code.<br><br>"
            "<u>How to Revert to Backup Versions</u>:<br>"
            "If changes break the software, go to <i>File</i> -> <i>Revert to Backup</i> and choose a previous version.<br><br>"
            "Note: You <b>must</b> provide an OpenAI API key for code generation.<br><br>"
            "This software is a <b>prototype</b> and may be unstable. See our GitHub link for more info:<br>"
            "<a href='https://github.com/navidhasanzadeh/AdaptCalc'>https://github.com/navidhasanzadeh/AdaptCalc</a>"
        )
        msg = QMessageBox(self)
        msg.setWindowTitle("How to Use AdaptCalc")
        msg.setTextFormat(Qt.RichText)
        msg.setText(instructions)
        msg.exec()

    def on_button_click(self, char: str):
        if char == "=":
            try:
                result = str(eval(self.display_line.text()))
                self.display_line.setText(result)
            except Exception:
                self.display_line.setText("Error")
        else:
            current_val = self.display_line.text()
            new_val = current_val + char
            self.display_line.setText(new_val)

    def customize_entire_script(self):
        current_key = load_api_key()
        dialog = CustomizeDialog(self, initial_key=current_key)
        if dialog.exec() == QDialog.Accepted:
            prompt_text = dialog.prompt_text
            model_name = dialog.selected_model
            user_key = dialog.api_key

            save_api_key(user_key)
            set_api_key(user_key)

            script_path = os.path.abspath(sys.argv[0])
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    current_code = f.read()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Cannot read current script:\n{str(e)}")
                return

            system_instruction = (
                "We have a Python script for a self-modifying calculator named AdaptCalc. "
                "The user wants to add or change features. You must return the ENTIRE updated Python script, "
                "with no disclaimers or triple backticks. Provide only valid Python code."
            )
            full_prompt = (
                f"{system_instruction}\n\n"
                f"User request:\n{prompt_text}\n\n"
                f"Current Code:\n{current_code}\n\n"
                f"Please provide ONLY the complete updated Python script:\n"
            )

            progress_dialog = QProgressDialog("Waiting for model to respond...", None, 0, 0, self)
            progress_dialog.setWindowModality(Qt.WindowModal)
            progress_dialog.setMinimumDuration(0)
            progress_dialog.setValue(0)
            progress_dialog.setWindowTitle("Please wait")
            progress_dialog.show()
            QCoreApplication.processEvents()

            raw_response = chat_gpt(model_name, full_prompt)

            progress_dialog.close()
            new_code = sanitize_script_response(raw_response)

            if not new_code.strip():
                QMessageBox.critical(self, "Error", "Received empty or invalid script from model.")
                return

            overwrite_self(new_code)

    def on_revert_to_backup(self):
        dialog = RevertDialog(self)
        if dialog.exec() == QDialog.Accepted and dialog.selected_backup:
            revert_to_backup(dialog.selected_backup)

    def share_current_code(self):
        dialog = ShareCodeDialog(self)
        dialog.exec()

    def show_about_us(self):
        """
        Display 'About Us' info with clickable links.
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("About Us")
        msg.setTextFormat(Qt.RichText)
        msg.setText(
            "By Navid Hasanzadeh, "
            "<a href='https://www.linkedin.com/in/navidhasanzadeh/'>LinkedIn</a>, "
            "<a href='https://github.com/navidhasanzadeh'>GitHub</a>, "
            "March 7, 2025"
        )
        msg.exec()

def main():
    app = QApplication(sys.argv)

    # Optional: We can set an overall application font if we like
    font = QFont("Arial", 13)
    app.setFont(font)

    window = CalculatorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
