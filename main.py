import sys
from PyQt6.QtWidgets import QApplication, QLabel, QMenu, QFileDialog
from PyQt6.QtGui import QPixmap, QAction, QFont, QKeySequence
from PyQt6.QtCore import Qt, QByteArray, QBuffer, QIODeviceBase
import subprocess

class ScreenshotWindow(QLabel):
    def __init__(self, pixmap):
        super().__init__()

        self.pixmap_obj = pixmap
        self.scale = 0
        self.base_width = pixmap.size().width()
        self.base_height = pixmap.size().height()

        self.setWindowTitle("pinshot")
        self.setObjectName("ScreenshotWindow")

        self.setWindowFlags(
            Qt.WindowType.Dialog |                # 设置为对话框窗口
            Qt.WindowType.WindowStaysOnTopHint |  # 使其保持在其他窗口之上
            Qt.WindowType.FramelessWindowHint     # 无边框
        )

        self.resize(pixmap.size())

        self.setPixmap(pixmap)

        self.setScaledContents(True)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        self.set_shortcuts()

    def set_shortcuts(self):
        copy_shortcut = QAction("Copy", self)
        copy_shortcut.setShortcut(QKeySequence("Ctrl+C"))
        copy_shortcut.triggered.connect(self.copy_to_clipboard)
        self.addAction(copy_shortcut)

        save_shortcut = QAction("Save", self)
        save_shortcut.setShortcut(QKeySequence("Ctrl+S"))
        save_shortcut.triggered.connect(self.save_to_file)
        self.addAction(save_shortcut)

        quit_shortcut = QAction("Quit", self)
        quit_shortcut.setShortcut(QKeySequence(Qt.Key.Key_Escape))
        quit_shortcut.triggered.connect(self.close)
        self.addAction(quit_shortcut)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.copy_to_clipboard()
            self.close()

    def apply_resize(self):
        scale_factor = 1 + (self.scale * 0.05)
        new_width = int(self.base_width * scale_factor)
        new_height = int(self.base_height * scale_factor)
        subprocess.run(['hyprctl', '-q', 'dispatch', 'resizeactive', "exact", str(new_width), str(new_height)])

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.scale += 1
        else:
            if self.scale > -19:
                self.scale -= 1
        self.apply_resize()

    def edit_with_swappy(self):
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODeviceBase.OpenModeFlag.WriteOnly)
        self.pixmap().save(buffer, "PNG")

        subprocess.Popen(
            ['swappy', '-f', '-'],
            stdin=subprocess.PIPE,
            close_fds=True,
            start_new_session=True
        ).stdin.write(byte_array.data())

        sys.exit(0)

    def show_context_menu(self, pos):
        context_menu = QMenu(self)

        font = QFont()
        font.setPointSize(14)
        context_menu.setFont(font)

        copy_action = QAction("Copy to Clipboard", self)
        copy_action.triggered.connect(self.copy_to_clipboard)
        context_menu.addAction(copy_action)

        save_action = QAction("Save to File", self)
        save_action.triggered.connect(self.save_to_file)
        context_menu.addAction(save_action)

        edit_action = QAction("Edit with Swappy", self)
        edit_action.triggered.connect(self.edit_with_swappy)
        context_menu.addAction(edit_action)

        close_action = QAction("Close", self)
        close_action.triggered.connect(self.close)
        context_menu.addAction(close_action)

        context_menu.exec(self.mapToGlobal(pos))

    def copy_to_clipboard(self):
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODeviceBase.OpenModeFlag.WriteOnly)
        self.pixmap().save(buffer, "PNG")

        process = subprocess.Popen(['wl-copy', '--type', 'image/png'], stdin=subprocess.PIPE)
        process.communicate(byte_array.data())

    def save_to_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "PNG Images (*.png)")
        if file_path:
            if not file_path.lower().endswith('.png'):
                file_path += '.png'  # 确保文件以 .png 结尾
            self.pixmap().save(file_path, "PNG")


def main():
    app = QApplication(sys.argv)

    slurp_cmd = ["slurp"]
    slurp_process = subprocess.run(slurp_cmd, stdout=subprocess.PIPE)
    if slurp_process.returncode != 0:
        print("Selection was cancelled.")
        sys.exit(0)
    region = slurp_process.stdout.decode("utf-8").strip()

    grim_cmd = ["grim", "-g", region, "-"]
    grim_process = subprocess.run(grim_cmd, stdout=subprocess.PIPE)

    byte_array = QByteArray(grim_process.stdout)
    pixmap = QPixmap()
    pixmap.loadFromData(byte_array, "PNG")

    window = ScreenshotWindow(pixmap)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()

