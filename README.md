# TreeFolder

TreeFolder is a desktop Python application built with PyQt6 that visualizes folder structures as a tree view with options for file extension filtering, depth limitation, and saving the results to a file.

## ✨ Features

- Select root folder via dialog
- Filter by extensions (e.g., `.py`, `.txt`)
- Set maximum traversal depth
- Display files and folders with icons and indentation
- Progress bar indicating traversal progress
- Optional display of full file/folder paths
- Save results to a `.txt` file
- Application icon supported in the `.exe` file via embedded base64

## 🔧 Run

```bash
python app.py
```

## 💡 Notes

- If you're using `PyInstaller`, you can build the app like this:
  ```bash
  pyinstaller --noconfirm --onefile --windowed app.py
  ```
  (The icon is embedded in the code and displayed via `QIcon(extract_icon_tempfile())`)

---

🚀 Made with ❤️ using PyQt6

