# LIBRARIES
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QWidget,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QMessageBox,
    QLineEdit,
    QFrame,
)

from core import userModes


SETTINGS_STYLESHEET = """
    QDialog {
        background-color: #020617;
    }

    QTabWidget::pane {
        background-color: #020617;
        border: 1px solid #111827;
        border-radius: 10px;
        padding: 8px;
    }

    QTabBar::tab {
        background-color: #111827;
        color: #e5e7eb;
        padding: 8px 16px;
        margin-right: 4px;
        border-radius: 8px;
    }

    QTabBar::tab:selected {
        background-color: #1d4ed8;
        color: #f9fafb;
    }

    QListWidget {
        background-color: #020617;
        border: 1px solid #111827;
        border-radius: 8px;
        padding: 6px;
        color: #e5e7eb;
    }

    QListWidget::item:selected {
        background-color: #1d4ed8;
        color: #f9fafb;
    }

    QLabel {
        font-family: "Segoe UI", Arial;
        font-size: 13px;
        color: #e5e7eb;
    }

    QLineEdit {
        background-color: #020617;
        border-radius: 8px;
        padding: 8px 12px;
        border: 1px solid #1e293b;
        color: #e5e7eb;
    }

    QLineEdit:focus {
        border: 1px solid #2563eb;
    }

    QPushButton {
        border-radius: 999px;
        padding: 7px 16px;
        font-size: 13px;
        font-weight: 500;
        border: 1px solid #1f2937;
        background-color: #020617;
        color: #e5e7eb;
    }

    QPushButton:hover:!disabled {
        background-color: #111827;
    }

    QPushButton#PrimaryButton {
        background-color: qlineargradient(
            x1: 0, y1: 0, x2: 1, y2: 0,
            stop: 0 #2563eb,
            stop: 1 #4f46e5
        );
        border-color: #1d4ed8;
        color: #f9fafb;
    }

    QPushButton#PrimaryButton:hover:!disabled {
        background-color: qlineargradient(
            x1: 0, y1: 0, x2: 1, y2: 0,
            stop: 0 #1d4ed8,
            stop: 1 #4338ca
        );
    }

    QPushButton:disabled {
        color: #6b7280;
    }
"""


class ModEditDialog(QDialog):
    def __init__(
        self,
        parent=None,
        modeId: Optional[int] = None,
        initial_name: str = "",
        initial_apps: Optional[List[str]] = None,
    ) -> None:
        super().__init__(parent)
        self.modeId = modeId
        self.setWindowTitle("Mod Düzenle" if modeId else "Yeni Mod")
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setStyleSheet(SETTINGS_STYLESHEET)
        self.build_ui(initial_name, initial_apps or [])

    def build_ui(self, initial_name: str, initial_apps: List[str]) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(18, 18, 18, 18)

        layout.addWidget(QLabel("Mod adı:"))
        self.nameEdit = QLineEdit()
        self.nameEdit.setPlaceholderText("Örn: çalışma modu")
        self.nameEdit.setText(initial_name)
        layout.addWidget(self.nameEdit)

        layout.addWidget(QLabel("Uygulamalar:"))
        self.appList = QListWidget()
        for app in initial_apps:
            self.appList.addItem(app)
        layout.addWidget(self.appList, stretch=1)

        addRow = QHBoxLayout()
        self.appInput = QLineEdit()
        self.appInput.setPlaceholderText("Uygulama adı ekle...")
        self.appInput.returnPressed.connect(self.add_app)
        addRow.addWidget(self.appInput)
        addBtn = QPushButton("Ekle")
        addBtn.setObjectName("PrimaryButton")
        addBtn.clicked.connect(self.add_app)
        addRow.addWidget(addBtn)
        layout.addLayout(addRow)

        removeRow = QHBoxLayout()
        removeBtn = QPushButton("Sil")
        removeBtn.setToolTip("Seçili uygulamayı listeden çıkar")
        removeBtn.clicked.connect(self.remove_app)
        removeRow.addWidget(removeBtn)
        removeRow.addStretch()
        layout.addLayout(removeRow)

        btnRow = QHBoxLayout()
        btnRow.addStretch()
        cancelBtn = QPushButton("İptal")
        cancelBtn.clicked.connect(self.reject)
        saveBtn = QPushButton("Kaydet")
        saveBtn.setObjectName("PrimaryButton")
        saveBtn.clicked.connect(self.save)
        btnRow.addWidget(cancelBtn)
        btnRow.addWidget(saveBtn)
        layout.addLayout(btnRow)

    def add_app(self) -> None:
        text = self.appInput.text().strip()
        if not text:
            return
        self.appList.addItem(text)
        self.appInput.clear()

    def remove_app(self) -> None:
        row = self.appList.currentRow()
        if row >= 0:
            self.appList.takeItem(row)

    def save(self) -> None:
        name = self.nameEdit.text().strip()
        if not name:
            QMessageBox.warning(self, "Hata", "Mod adı bos olamaz.")
            return

        apps: List[str] = []
        for i in range(self.appList.count()):
            item = self.appList.item(i)
            if item and item.text().strip():
                apps.append(item.text().strip())

        try:
            if self.modeId is not None:
                userModes.update_mode(self.modeId, name, apps)
            else:
                userModes.create_mode(name, apps)
            self.accept()
        except RuntimeError as e:
            QMessageBox.warning(self, "Hata", str(e))

    def get_name(self) -> str:
        return self.nameEdit.text().strip()

    def get_app_names(self) -> List[str]:
        return [
            self.appList.item(i).text().strip()
            for i in range(self.appList.count())
            if self.appList.item(i) and self.appList.item(i).text().strip()
        ]


class SettingsDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ayarlar")
        self.setModal(True)
        self.setMinimumSize(480, 380)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setStyleSheet(SETTINGS_STYLESHEET)
        self.build_ui()

    def build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.build_mod_tab(), "Mod Ayarları")
        layout.addWidget(self.tabs)

        closeBtn = QPushButton("Kapat")
        closeBtn.setObjectName("PrimaryButton")
        closeBtn.clicked.connect(self.accept)
        btnRow = QHBoxLayout()
        btnRow.addStretch()
        btnRow.addWidget(closeBtn)
        layout.addLayout(btnRow)

    def build_mod_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Tanımlı modlar:"))
        self.modList = QListWidget()
        self.modList.itemSelectionChanged.connect(self.mod_selection_changed)
        layout.addWidget(self.modList, stretch=1)

        self.appPreviewLabel = QLabel("Seçili modun uygulamaları: -")
        self.appPreviewLabel.setObjectName("StatusLabel")
        self.appPreviewLabel.setStyleSheet("color: #9ca3af; font-size: 11px;")
        layout.addWidget(self.appPreviewLabel)

        btnRow = QHBoxLayout()
        self.addBtn = QPushButton("Ekle")
        self.addBtn.setObjectName("PrimaryButton")
        self.addBtn.clicked.connect(self.add_mode)
        self.editBtn = QPushButton("Düzenle")
        self.editBtn.clicked.connect(self.edit_mode)
        self.editBtn.setEnabled(False)
        self.deleteBtn = QPushButton("Sil")
        self.deleteBtn.clicked.connect(self.delete_mode)
        self.deleteBtn.setEnabled(False)
        btnRow.addWidget(self.addBtn)
        btnRow.addWidget(self.editBtn)
        btnRow.addWidget(self.deleteBtn)
        btnRow.addStretch()
        layout.addLayout(btnRow)

        self.refresh_mods()
        return tab

    def refresh_mods(self) -> None:
        self.modList.clear()
        try:
            for mode in userModes.get_modes():
                item = QListWidgetItem(mode.get("name", ""))
                item.setData(Qt.ItemDataRole.UserRole, mode.get("id"))
                self.modList.addItem(item)
        except RuntimeError:
            pass
        self.mod_selection_changed()

    def mod_selection_changed(self) -> None:
        current = self.modList.currentItem()
        hasSelect = current is not None
        self.editBtn.setEnabled(hasSelect)
        self.deleteBtn.setEnabled(hasSelect)

        if not hasSelect:
            self.appPreviewLabel.setText("Seçili modun uygulamaları: -")
            return

        modeId = current.data(Qt.ItemDataRole.UserRole)
        try:
            mode = userModes.get_mode_id(modeId)
            if mode:
                apps = mode.get("app_names", [])
                self.appPreviewLabel.setText(
                    f"Seçili modun uygulamaları: {', '.join(apps) if apps else '(yok)'}"
                )
            else:
                self.appPreviewLabel.setText("Seçili modun uygulamaları: -")
        except RuntimeError:
            self.appPreviewLabel.setText("Seçili modun uygulamaları: -")

    def add_mode(self) -> None:
        dlg = ModEditDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            self.refresh_mods()

    def edit_mode(self) -> None:
        current = self.modList.currentItem()
        if not current:
            return
        modeId = current.data(Qt.ItemDataRole.UserRole)
        try:
            mode = userModes.get_mode_id(modeId)
            if not mode:
                return
            dlg = ModEditDialog(
                parent=self,
                modeId=modeId,
                initial_name=mode.get("name", ""),
                initial_apps=mode.get("app_names", []),
            )
            if dlg.exec() == QDialog.Accepted:
                self.refresh_mods()
        except RuntimeError:
            pass

    def delete_mode(self) -> None:
        current = self.modList.currentItem()
        if not current:
            return

        name = current.text()
        reply = QMessageBox.question(
            self,
            "Modu Sil",
            f"'{name}' modunu silmek istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        modeId = current.data(Qt.ItemDataRole.UserRole)
        try:
            userModes.delete_mode(modeId)
            self.refresh_mods()
        except RuntimeError as e:
            QMessageBox.warning(self, "Hata", str(e))
