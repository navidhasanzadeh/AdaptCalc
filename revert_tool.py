import sys
import os
import re
import datetime

from typing import List
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLabel, QPushButton, QComboBox, QMessageBox
)
from PySide6.QtGui import QFont

def get_script_name() -> str:
    """
    Return 'adaptcalc' if we assume the main script is adaptcalc.py.
    Adjust if your main script has a different name.
    """
    return "adaptcalc"

def list_backup_files() -> List[str]:
    """
    Find all .bak files in the current directory matching:
      adaptcalc_YYYYmmdd_HHMMSS_v\d+.bak
    Sort by modification time ascending.
    """
    script_base = get_script_name()
    pattern = re.compile(rf"^{script_base}_\d{{8}}_\d{{6}}_v\d+\.bak$")
    files = []
    for f in os.listdir('.'):
        if pattern.match(f):
            files.append(f)
    files.sort(key=lambda x: os.path.getmtime(x))
    return files

def revert_backup(backup_filename: str):
    """
    Overwrite adaptcalc.py with the contents of 'backup_filename'.
    """
    script_file = f"{get_script_name()}.py"
    try:
        with open(backup_filename, 'r', encoding='utf-8') as bak, open(script_file, 'w', encoding='utf-8') as outp:
            outp.write(bak.read())
        QMessageBox.information(None, "Success", f"Reverted {script_file} to {backup_filename}.")
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Failed to revert:\n{e}")

class RevertToolWindow(QMainWindow):
    """
    A simple GUI to revert adaptcalc.py to any backup found in this directory.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AdaptCalc Revert Tool")
        font = QFont("Arial", 13)
        self.setFont(font)

        widget = QWidget(self)
        self.setCentralWidget(widget)
        layout = QVBoxLayout(widget)

        label = QLabel("Select a backup to revert AdaptCalc:")
        label.setFont(font)
        layout.addWidget(label)

        self.combo = QComboBox()
        self.combo.setFont(font)
        backups = list_backup_files()
        if backups:
            self.combo.addItems(backups)
        layout.addWidget(self.combo)

        btn_revert = QPushButton("Revert Now")
        btn_revert.setFont(font)
        btn_revert.clicked.connect(self.on_revert_clicked)
        layout.addWidget(btn_revert)

        if not backups:
            QMessageBox.information(self, "No Backups Found", "No backups found for adaptcalc.")
            btn_revert.setEnabled(False)

    def on_revert_clicked(self):
        backup_name = self.combo.currentText()
        if not backup_name:
            return
        ret = QMessageBox.question(
            self,
            "Confirm Revert",
            f"Are you sure you want to revert adaptcalc.py to:\n{backup_name}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if ret == QMessageBox.Yes:
            revert_backup(backup_name)

def main():
    app = QApplication(sys.argv)
    window = RevertToolWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
