import os
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QProgressBar, QFileDialog, QTextEdit, QLineEdit, QSpinBox, QCheckBox
)
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QIcon
from icon_data import icon_base64
from base64 import b64decode
from time import sleep


def extract_icon_tempfile():
    temp_icon_path = os.path.join(sys._MEIPASS if hasattr(sys, '_MEIPASS') else ".", "tf_icon_temp.ico")
    if not os.path.exists(temp_icon_path):
        with open(temp_icon_path, "wb") as f:
            f.write(b64decode(icon_base64))
    return temp_icon_path


class TreeWalker(QThread):
    progress = pyqtSignal(int)
    output = pyqtSignal(str)
    clear = pyqtSignal()

    def __init__(self, path, extension_filter=None, max_depth=None):
        super().__init__()
        self.path = path
        self.extension_filter = extension_filter
        self.max_depth = max_depth
        self.total_items = 0
        self.processed = 0
        self.loading_running = False
        self.show_full_path = False

    def run(self):
        self.loading_running = True
        self.loading()
        self.total_items = self.count_items(self.path, depth=0)
        self.loading_running = False
        self.clear.emit()
        self.walk_tree(self.path, depth=0)
        self.progress.emit(100)

    def count_items(self, path, depth):
        if self.max_depth is not None and depth > self.max_depth:
            return 0
        count = 0
        try:
            for item in os.listdir(path):
                full_path = os.path.join(path, item)
                if os.path.isdir(full_path):
                    count += 1
                    count += self.count_items(full_path, depth + 1)
                else:
                    count += 1
        except Exception as e:
            print(e)
        return count or 1

    def loading(self):
        def loop():
            dots = 1
            while self.loading_running:
                self.clear.emit()
                self.output.emit("⏳ Starting process. Please wait" + "." * dots)
                dots = (dots % 3) + 1
                sleep(1)

        from threading import Thread
        Thread(target=loop, daemon=True).start()

    def update_progress(self):
        self.processed += 1
        if self.total_items > 0:
            self.progress.emit(int((self.processed / self.total_items) * 100))

    def walk_tree(self, path, indent="", depth=0):
        if self.max_depth is not None and depth > self.max_depth:
            return
        try:
            for item in os.listdir(path):
                full_path = os.path.join(path, item)
                if os.path.isdir(full_path):
                    display = indent + "📁 " + item
                    if self.show_full_path:
                        display += " - " + full_path
                    self.output.emit(display)
                    self.update_progress()
                    self.walk_tree(full_path, indent + "    ", depth + 1)
                else:
                    if self.extension_filter and not any(item.lower().endswith(ext) for ext in self.extension_filter):
                        self.update_progress()
                        continue
                    display = indent + "📄 " + item
                    if self.show_full_path:
                        display += " - " + full_path
                    self.output.emit(display)
                    self.update_progress()
        except Exception as e:
            self.output.emit(f"❌ Error in {path}: {e}")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TreeFolder")
        self.setWindowIcon(QIcon(extract_icon_tempfile()))
        self.resize(600, 500)

        self.folder_path = ''

        self.layout = QVBoxLayout()
        self.btn_layout = QHBoxLayout()
        self.filter_depth_layout = QHBoxLayout()

        self.label = QLabel("No folder selected")

        self.look_button = QPushButton("Browse...")
        self.start_button = QPushButton("Start")
        self.save_button = QPushButton("Save to File")
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Extension filter: e.g., .txt,.exe,.py")

        self.depth_input = QSpinBox()
        self.depth_input.setMinimum(0)
        self.depth_input.setMaximum(100)
        self.depth_input.setValue(10)
        self.depth_input.setPrefix("Depth: ")

        self.show_fullpath_checkbox = QCheckBox("Show full path")
        self.show_fullpath_checkbox.setChecked(False)

        self.btn_layout.addWidget(self.look_button)
        self.btn_layout.addWidget(self.start_button)
        self.btn_layout.addWidget(self.save_button)

        self.filter_depth_layout.addWidget(self.filter_input)
        self.filter_depth_layout.addWidget(self.depth_input)
        self.filter_depth_layout.addWidget(self.show_fullpath_checkbox)

        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)

        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.progress.setValue(0)

        self.look_button.clicked.connect(self.choose_folder)
        self.start_button.clicked.connect(self.start_create_tree)
        self.save_button.clicked.connect(self.save_to_file)

        self.layout.addWidget(self.label)
        self.layout.addLayout(self.btn_layout)
        self.layout.addLayout(self.filter_depth_layout)
        self.layout.addWidget(self.output_area)
        self.layout.addWidget(self.progress)
        self.setLayout(self.layout)

    def choose_folder(self):
        self.folder_path = QFileDialog.getExistingDirectory()
        if self.folder_path:
            self.label.setText(f"Selected: {self.folder_path}")

    def start_create_tree(self):
        if not self.folder_path:
            self.output_area.append("❌ No folder selected")
            return
        self.progress.setValue(0)

        raw_filter = self.filter_input.text().strip()
        extensions = [ext.strip().lower() for ext in raw_filter.split(',') if ext.strip()] if raw_filter else None
        max_depth = self.depth_input.value()

        show_full_path = self.show_fullpath_checkbox.isChecked()
        self.thread = TreeWalker(self.folder_path, extensions, max_depth)
        self.thread.show_full_path = show_full_path
        self.thread.output.connect(self.append_output)
        self.thread.progress.connect(self.progress.setValue)
        self.thread.clear.connect(self.output_area.clear)
        self.thread.finished.connect(lambda: self.output_area.append("✅ Done"))
        self.thread.start()

    def append_output(self, text):
        self.output_area.append(text)

    def save_to_file(self):
        text = self.output_area.toPlainText()
        if not text:
            self.output_area.append("⚠️ No data to save.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save as", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                self.output_area.append(f"💾 Saved to: {file_path}")
            except Exception as e:
                self.output_area.append(f"❌ Error while saving: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
