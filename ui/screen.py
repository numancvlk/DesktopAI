#LIBRARIES
import threading
import datetime
from typing import List, Optional
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QVBoxLayout as QDialogVBoxLayout,
    QWidget,
)

from core import reminders, user_modes
from ui.rag_workers import RAGIndexWorker
from ui.voice_workers import VoiceListenWorker
from ui.workers import LLMWorker
from voice.stt import get_stt_model

# AYARLAR MOD DUZENLEME KISIMLARI ICIN AYARLAR KISMI BURASI
UI_SETTINGS = """ 
    QDialog {
        background-color: #0c1222;
    }

    QTabWidget::pane {
        background-color: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 14px;
        padding: 14px;
        margin-top: 6px;
    }

    QTabBar::tab {
        background-color: #1e293b;
        color: #cbd5e1;
        padding: 10px 20px;
        margin-right: 6px;
        border-radius: 10px;
        min-height: 22px;
    }

    QTabBar::tab:selected {
        background-color: #2563eb;
        color: #f8fafc;
    }

    QListWidget {
        background-color: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 10px;
        color: #e5e7eb;
    }

    QListWidget::item {
        padding: 6px 4px;
    }

    QListWidget::item:selected {
        background-color: #2563eb;
        color: #f9fafb;
    }

    QLabel {
        font-family: "Segoe UI";
        font-size: 13px;
        color: #e5e7eb;
    }

    QLineEdit {
        background-color: #0f172a;
        border-radius: 12px;
        padding: 10px 14px;
        border: 1px solid #334155;
        color: #e5e7eb;
    }

    QLineEdit:focus {
        border: 1px solid #3b82f6;
    }

    QPushButton {
        border-radius: 999px;
        padding: 8px 18px;
        font-size: 13px;
        font-weight: 500;
        border: 1px solid #334155;
        background-color: #0f172a;
        color: #e5e7eb;
    }

    QPushButton:hover:!disabled {
        background-color: #1e293b;
    }

    QPushButton#ButtonPrimary {
        background-color: qlineargradient(
            stop: 0 #2563eb,
            stop: 1 #4f46e5
        );
        border-color: #1d4ed8;
        color: #f9fafb;
    }
    
    QPushButton#ButtonPrimary:hover:!disabled {
        background-color: qlineargradient(
            stop: 0 #1d4ed8, 
            stop: 1 #4338ca
        );
    }

    QPushButton:disabled {
        color: #6b7280;
    }
"""
#AZCIK GECISLI OLSUN DIYE SOV YAPTIK BELKI CIKARABILIRIM VEYA RENGINI DEGISTRIEBILIRIM ILERIDE STOPLARIN ONLAR USTTE UNUTMA


# ANA UYGULAMANIN UI AYARLARI YANI SETTINGS DISINDAKI KISIMLAR ICIN
GENERAL_APP_SETTINGS = """
    QMainWindow {
        background-color: #0c1222;
    }

    QWidget {
        font-family: "Segoe UI";
        font-size: 13px;
        color: #e5e7eb;
    }

    QFrame#Chat {
        background-color: #0f172a;
        border-radius: 16px;
        border: 1px solid #1e293b;
    }

    QTextEdit {
        background-color: #0f172a;
        border-radius: 12px;
        padding: 14px 16px;
        color: #e5e7eb;
        border: 1px solid #334155;
    }

    QTextEdit:disabled {
        background-color: #0f172a;
        color: #6b7280;
    }

    QLineEdit {
        background-color: #0f172a;
        border-radius: 999px;
        padding: 10px 16px;
        border: 1px solid #334155;
        color: #e5e7eb;
    }

    QLineEdit:focus {
        border: 1px solid #3b82f6;
    }

    QLabel#MainTitle {
        color: #f8fafc;
        font-size: 22px;
        font-weight: 600;
        letter-spacing: -0.3px;
    }

    QLabel#AltTitle {
        color: #94a3b8;
        font-size: 12px;
    }

    QLabel#DurumLabel {
        color: #94a3b8;
        font-size: 12px;
    }

    QLabel#RagHintLabel {
        color: #94a3b8;
        font-size: 12px;
        padding: 4px 2px 0 2px;
    }

    QPushButton {
        border-radius: 999px;
        padding: 8px 18px;
        font-size: 13px;
        font-weight: 500;
        border: 1px solid #334155;
        background-color: #0f172a;
        color: #e5e7eb;
    }

    QPushButton:hover:!disabled {
        background-color: #1e293b;
    }

    QPushButton:pressed:!disabled {
        background-color: #0f172a;
        border-color: #475569;
    }

    QPushButton:disabled {
        color: #64748b;
        border-color: #1e293b;
        background-color: #0c1222;
    }

    QPushButton#ButtonPrimary {
        background-color: qlineargradient(
            stop: 0 #2563eb,
            stop: 1 #4f46e5
        );
        border-color: #1d4ed8;
        color: #f9fafb;
    }

    QPushButton#ButtonPrimary:hover:!disabled {
        background-color: qlineargradient(
            stop: 0 #1d4ed8,
            stop: 1 #4338ca
        );
        border-color: #1d4ed8;
    }

    QPushButton#ButtonPrimary:pressed:!disabled {
        background-color: #1d4ed8;
        border-color: #1e40af;
    }

    QPushButton#GhostButton {
        background-color: transparent;
        border-color: #334155;
        color: #cbd5e1;
    }

    QPushButton#GhostButton:hover:!disabled {
        background-color: #1e293b;
    }

    QPushButton#SesButton {
        background-color: #022c22;
        border-color: #065f46;
        color: #a7f3d0;
    }

    QPushButton#SesButton:hover:!disabled {
        background-color: #064e3b;
    }

    QPushButton#SesButton:pressed:!disabled {
        background-color: #022c22;
    }

    QPushButton#ModButonu {
        background-color: #0f172a;
        border-color: #475569;
        color: #cbd5e1;
        min-width: 88px;
        padding: 8px 16px;
    }

    QPushButton#ModButonu:checked {
        background-color: #1d4ed8;
        border-color: #3b82f6;
        color: #f8fafc;
        font-weight: 600;
    }

    QFrame#AltBar {
        background-color: #0f172a;
        border-radius: 999px;
        border: 1px solid #1e293b;
    }

    QFrame#HeaderDivider {
        color: #1e293b;
        max-height: 1px;
    }

    QScrollBar:vertical {
        background: #0f172a;
        width: 10px;
        margin: 6px 0 6px 0;
    }

    QScrollBar::handle:vertical {
        background: #334155;
        border-radius: 5px;
        min-height: 28px;
    }

    QScrollBar::handle:vertical:hover {
        background: #475569;
    }

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0px;
    }
"""

# HATIRLATICI POP UP ICIN 
class ReminderPOPUP(QDialog):
    def __init__(self, text: str, parent: QMainWindow | None = None) -> None:

        super().__init__(parent)
        self.setWindowTitle("Hatirlatici")
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setStyleSheet( #REMINDER POP UP AYARLARI BURDA USTTEDE YAZABILIRDIM ASLINDA TODO BELKI YUKARI TASIRIM KOD BUTUNLUGU ACISINDAN AMA SIMDILIK KALSIN
            """
            QDialog {
                background-color: #0c1222;
            }

            QLabel {
                font-family: "Segoe UI";
                font-size: 13px;
                color: #e5e7eb;
            }

            QPushButton {
                border-radius: 999px;
                padding: 8px 18px;
                font-size: 13px;
                font-weight: 500;
                border: 1px solid #334155;
                background-color: #0f172a;
                color: #e5e7eb;
            }

            QPushButton:hover:!disabled {
                background-color: #1e293b;
            }

            QPushButton#ButtonPrimary {
                background-color: qlineargradient(
                    stop: 0 #2563eb,
                    stop: 1 #4f46e5
                );
                border-color: #1d4ed8;
                color: #f9fafb;
            }

            QPushButton#ButtonPrimary:hover:!disabled {
                background-color: qlineargradient(
                    stop: 0 #1d4ed8,
                    stop: 1 #4338ca
                );
                border-color: #1d4ed8;
            }

            QPushButton#ButtonPrimary:pressed:!disabled {
                background-color: #1d4ed8;
                border-color: #1e40af;
            }

            QFrame#ReminderPopUP {
                background-color: #0f172a;
                border-radius: 16px;
                border: 1px solid #1e293b;
            }
            """
        )

        layout = QDialogVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        container = QFrame(self)
        container.setObjectName("ReminderPopUP")

        containerLayout = QVBoxLayout(container)
        containerLayout.setContentsMargins(20, 20, 20, 20)
        containerLayout.setSpacing(12)

        titleLabel = QLabel("Hatırlatici")
        titleLabel.setObjectName("MainTitle")
        containerLayout.addWidget(titleLabel)

        textLabel = QLabel(text)
        textLabel.setWordWrap(True)
        containerLayout.addWidget(textLabel)

        buttonRow = QHBoxLayout()
        buttonRow.setSpacing(10)

        self.okButton = QPushButton("Tamam")
        self.okButton.setObjectName("ButtonPrimary")
        self.snoozeButton = QPushButton("5 dakika ERTELE.")

        self.okButton.clicked.connect(self.accept)
        self.snoozeButton.clicked.connect(self.snooze)

        buttonRow.addStretch()
        buttonRow.addWidget(self.snoozeButton)
        buttonRow.addWidget(self.okButton)

        containerLayout.addLayout(buttonRow)
        layout.addWidget(container)

        self.snoozed = False 

    def snooze(self) -> None:
        self.snoozed = True
        self.accept()

    @property
    def snoozed(self) -> bool:
        return self.snoozed


# Mod olusturma duzenleme vs burda UI
class ModEditDialog(QDialog):
    def __init__(
        self,
        parent=None,
        modeId: Optional[int] = None,
        initial_name: str = "",
        initial_apps: Optional[List[str]] = None,
        initial_links: Optional[List[str]] = None,
        initial_browser: str = "",
    ) -> None:

        super().__init__(parent)
        self.modeId = modeId 
        self.setWindowTitle("Mod Düzenle" if modeId else "Yeni Mod")
        self.setModal(True)
        self.setMinimumWidth(460)
        self.setMinimumHeight(420)
        self.setStyleSheet(UI_SETTINGS)
        self.ui(initial_name, initial_apps or [], initial_links or [], initial_browser)

    def ui(
        self,
        initial_name: str,
        initial_apps: List[str],
        initial_links: List[str],
        initial_browser: str,
    ) -> None:

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(22, 22, 22, 22)

        layout.addWidget(QLabel("Mod adıni yaziniz:"))
        self.nameEdit = QLineEdit()
        self.nameEdit.setPlaceholderText("Örn: Oyun")
        self.nameEdit.setText(initial_name)
        layout.addWidget(self.nameEdit)

        layout.addWidget(QLabel("Çalıştırılacak Uygulamalar:"))
        self.appList = QListWidget()
        for app in initial_apps:
            self.appList.addItem(app)
        layout.addWidget(self.appList, stretch=1)

        addRow = QHBoxLayout()
        addRow.setSpacing(10)
        self.appInput = QLineEdit()
        self.appInput.setPlaceholderText("Uygulama adlarini ekle!")
        self.appInput.returnPressed.connect(self.add_app)
        addRow.addWidget(self.appInput)
        addBtn = QPushButton("Ekle")
        addBtn.setObjectName("ButtonPrimary")
        addBtn.clicked.connect(self.add_app)
        addRow.addWidget(addBtn)
        layout.addLayout(addRow)

        removeRow = QHBoxLayout()
        removeBtn = QPushButton("Sil")
        removeBtn.setToolTip("Seçilen uygulamayı listeden çıkar!")
        removeBtn.clicked.connect(self.remove_app)
        removeRow.addWidget(removeBtn)
        removeRow.addStretch()
        layout.addLayout(removeRow)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        layout.addWidget(QLabel("Açılacak Siteler:"))
        self.linkList = QListWidget()
        for link in initial_links:
            self.linkList.addItem(link)
        layout.addWidget(self.linkList, stretch=1)

        addLinkRow = QHBoxLayout()
        addLinkRow.setSpacing(10)
        self.linkInput = QLineEdit()
        self.linkInput.setPlaceholderText("Açılmasını istediğiniz sitenin URL'sini yaziniz!")
        self.linkInput.returnPressed.connect(self.add_link)
        addLinkRow.addWidget(self.linkInput)
        addLinkBtn = QPushButton("Ekle")
        addLinkBtn.setObjectName("ButtonPrimary")
        addLinkBtn.clicked.connect(self.add_link)
        addLinkRow.addWidget(addLinkBtn)
        layout.addLayout(addLinkRow)

        removeLinkRow = QHBoxLayout()
        removeLinkBtn = QPushButton("Sil")
        removeLinkBtn.setToolTip("Seçili siteyi listeden çıkar!")
        removeLinkBtn.clicked.connect(self.remove_link)
        removeLinkRow.addWidget(removeLinkBtn)
        removeLinkRow.addStretch()
        layout.addLayout(removeLinkRow)

        layout.addWidget(QLabel("Tarayıcınızın adını yaziniz:"))
        self.browserInput = QLineEdit()
        self.browserInput.setText((initial_browser or "").strip())
        layout.addWidget(self.browserInput)

        btnRow = QHBoxLayout()
        btnRow.setSpacing(10)
        btnRow.addStretch()
        cancelBtn = QPushButton("İptal")
        cancelBtn.clicked.connect(self.reject)
        saveBtn = QPushButton("Kaydet")
        saveBtn.setObjectName("ButtonPrimary")
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

    def add_link(self) -> None:
        text = self.linkInput.text().strip()
        if not text:
            return
        self.linkList.addItem(text)
        self.linkInput.clear()

    def remove_link(self) -> None:
        row = self.linkList.currentRow()
        if row >= 0:
            self.linkList.takeItem(row)

    def save(self) -> None:
        name = self.nameEdit.text().strip()
        if not name:
            QMessageBox.warning(self, "Hata", "Mod adı boş olamaz.")
            return

        apps: List[str] = []
        for i in range(self.appList.count()):
            item = self.appList.item(i)
            if item and item.text().strip():
                apps.append(item.text().strip())

        links: List[str] = []
        for i in range(self.linkList.count()):
            item = self.linkList.item(i)
            if item and item.text().strip():
                links.append(item.text().strip())
        browserName = self.browserInput.text().strip()

        try:
            if self.modeId is not None:
                user_modes.update_mode(self.modeId, name, apps, links, browserName)
            else:
                user_modes.create_mode(name, apps, links, browserName)
            self.accept()
        except RuntimeError as e:
            QMessageBox.warning(self, "Hata", "Runtime Errir")

    def mode_names(self) -> str:
        return self.nameEdit.text().strip()

    def app_names(self) -> List[str]:
        return [
            self.appList.item(i).text().strip()
            for i in range(self.appList.count())
            if self.appList.item(i) and self.appList.item(i).text().strip()
        ]

    def get_url(self) -> List[str]:
        return [
            self.linkList.item(i).text().strip()
            for i in range(self.linkList.count())
            if self.linkList.item(i) and self.linkList.item(i).text().strip()
        ]

    def browser_name(self) -> str:
        return self.browserInput.text().strip()


# Kulalncii Modlarini listeleyen kisim ayalr vs
class SettingsDialog(QDialog):
    def __init__(self, parent=None) -> None:

        super().__init__(parent)
        self.setWindowTitle("Ayarlar")
        self.setModal(True)
        self.setMinimumSize(520, 440)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setStyleSheet(UI_SETTINGS)
        self.ui()

    def ui(self) -> None:
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(16)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.mod(), "Mod Ayarları")  # TODO sekmeleri burdan ekliyoruz ileride ekelrsem kalsin
        layout.addWidget(self.tabs)

        closeBtn = QPushButton("Kapat")
        closeBtn.setObjectName("ButtonPrimary")
        closeBtn.clicked.connect(self.accept)
        btnRow = QHBoxLayout()
        btnRow.addStretch()
        btnRow.addWidget(closeBtn)
        layout.addLayout(btnRow)

    def mod(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(14)
        layout.setContentsMargins(4, 8, 4, 4)

        layout.addWidget(QLabel("Modlariniz:"))
        self.modList = QListWidget()
        self.modList.itemSelectionChanged.connect(self.mod_selection_changed)
        layout.addWidget(self.modList, stretch=1)

        self.appPreviewLabel = QLabel("Modun Uygulamalari:")
        self.appPreviewLabel.setObjectName("DurumLabel")
        self.appPreviewLabel.setStyleSheet("color: #94a3b8; font-size: 12px;")
        layout.addWidget(self.appPreviewLabel)
        self.linkPreviewLabel = QLabel("Modun Siteleri:")
        self.linkPreviewLabel.setObjectName("DurumLabel")
        self.linkPreviewLabel.setStyleSheet("color: #94a3b8; font-size: 12px;")
        layout.addWidget(self.linkPreviewLabel)
        self.browserPreviewLabel = QLabel("Modun Tarayicisi:")
        self.browserPreviewLabel.setObjectName("DurumLabel")
        self.browserPreviewLabel.setStyleSheet("color: #94a3b8; font-size: 12px;")
        layout.addWidget(self.browserPreviewLabel)

        btnRow = QHBoxLayout()
        btnRow.setSpacing(10)
        self.addBtn = QPushButton("Ekle")
        self.addBtn.setObjectName("ButtonPrimary")
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

    def refresh_mods(self) -> None: #Modlarin listesini gunvellemek icin

        self.modList.clear()
        try:
            for mode in user_modes.modes():
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
            self.appPreviewLabel.setText("Modun Uygulamalari:")
            self.linkPreviewLabel.setText("Modun Siteleri:")
            self.browserPreviewLabel.setText("Modun Tarayicisi:")
            return

        modeId = current.data(Qt.ItemDataRole.UserRole)
        try:
            mode = user_modes.mode_id(modeId)
            if mode:
                apps = mode.get("app_names", [])
                links = mode.get("link_urls", [])
                browserName = mode.get("browser_name", "") or "(belirtilmedi)"
                self.appPreviewLabel.setText(
                    f"Seçili modun uygulamaları: {', '.join(apps) if apps else '(yok)'}"
                )
                self.linkPreviewLabel.setText(
                    f"Seçili modun siteleri: {', '.join(links) if links else '(yok)'}"
                )
                self.browserPreviewLabel.setText(f"Seçili modun tarayıcısı: {browserName}")
            else:
                self.appPreviewLabel.setText("Modun Uygulamalari:")
                self.linkPreviewLabel.setText("Modun Siteleri:")
                self.browserPreviewLabel.setText("Modun Tarayicisi:")
        except RuntimeError:
            self.appPreviewLabel.setText("Modun Uygulamalari:")
            self.linkPreviewLabel.setText("Modun Siteleri:")
            self.browserPreviewLabel.setText("Modun Tarayicisi:")

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
            mode = user_modes.mode_id(modeId)
            if not mode:
                return
            dlg = ModEditDialog(
                parent=self,
                modeId=modeId,
                initial_name=mode.get("name", ""),
                initial_apps=mode.get("app_names", []),
                initial_links=mode.get("link_urls", []),
                initial_browser=mode.get("browser_name", ""),
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
            user_modes.delete_mode(modeId)
            self.refresh_mods()
        except RuntimeError as e:
            QMessageBox.warning(self, "Hata", "Mod Silinemedi")


# Ana UI ayalra kismi degilde obur taraflar iste
class MainScreen(QMainWindow):
    def __init__(self, parent=None):

        super().__init__(parent)
        self.worker = None  
        self.voiceWorker = None  
        self.ragWorker = None 
        self.currentMode = "assistant"  
        self.reminderTimer = None
        self.ui()
        threading.Thread(target=get_stt_model, daemon=True).start()

    def ui(self):
        self.setWindowTitle("LOCAL DESKTOP ASSISTANT")
        self.setMinimumSize(720, 520)
        self.resize(920, 640)

        self.setStyleSheet(GENERAL_APP_SETTINGS)

        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(18)

        headerRow = QHBoxLayout()
        headerRow.setSpacing(20)

        titleColumn = QVBoxLayout()
        titleColumn.setSpacing(6)
        titleLabel = QLabel("LOCAL DESKTOP ASSISTANT")
        titleLabel.setObjectName("MainTitle")
        titleColumn.addWidget(titleLabel)

        headerRow.addLayout(titleColumn)

        modeRow = QHBoxLayout()
        modeRow.setSpacing(10)
        self.assistantModeButton = QPushButton("Asistan")
        self.assistantModeButton.setObjectName("ModButonu")
        self.assistantModeButton.setCheckable(True)
        self.assistantModeButton.setChecked(True)
        self.assistantModeButton.clicked.connect(self.mode_assistant_clicked)
        modeRow.addWidget(self.assistantModeButton)

        self.ragModeButton = QPushButton("RAG")
        self.ragModeButton.setObjectName("ModButonu")
        self.ragModeButton.setCheckable(True)
        self.ragModeButton.setChecked(False)
        self.ragModeButton.clicked.connect(self.mode_rag_clicked)
        modeRow.addWidget(self.ragModeButton)

        headerRow.addLayout(modeRow)
        headerRow.addStretch()

        self.settingsButton = QPushButton("Ayarlar")
        self.settingsButton.setObjectName("GhostButton")
        self.settingsButton.setToolTip("Ayarları aç")
        self.settingsButton.clicked.connect(self.settings_clicked)
        headerRow.addWidget(self.settingsButton, alignment=Qt.AlignRight | Qt.AlignVCenter)

        self.statusLabel = QLabel("Mod: Asistan")
        self.statusLabel.setObjectName("DurumLabel")
        headerRow.addWidget(self.statusLabel, alignment=Qt.AlignRight | Qt.AlignVCenter)

        root.addLayout(headerRow)

        divider = QFrame()
        divider.setObjectName("HeaderDivider")
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: #1e293b; border: none;")
        root.addWidget(divider)

        chatCard = QFrame()
        chatCard.setObjectName("Chat")
        chatLayout = QVBoxLayout(chatCard)
        chatLayout.setContentsMargins(14, 14, 14, 14)
        chatLayout.setSpacing(0)

        self.chatArea = QTextEdit()
        self.chatArea.setReadOnly(True)
        chatLayout.addWidget(self.chatArea, stretch=1)

        root.addWidget(chatCard, stretch=1)

        self.ragInfoLabel = QLabel("RAG: Henüz PDF yüklenmedi")
        self.ragInfoLabel.setObjectName("RagHintLabel")
        root.addWidget(self.ragInfoLabel)

        bottomFrame = QFrame()
        bottomFrame.setObjectName("AltBar")
        bottomLayout = QHBoxLayout(bottomFrame)
        bottomLayout.setContentsMargins(14, 12, 14, 12)
        bottomLayout.setSpacing(12)

        self.inputLine = QLineEdit()
        self.inputLine.setPlaceholderText("Mesajınızı yazın veya söyleyin...")
        self.inputLine.returnPressed.connect(self.send_clicked)
        bottomLayout.addWidget(self.inputLine, stretch=1)

        self.voiceButton = QPushButton("Ses")
        self.voiceButton.setObjectName("SesButton")
        self.voiceButton.setToolTip("Mikrofon ile konuş")
        self.voiceButton.clicked.connect(self.voice_clicked)
        bottomLayout.addWidget(self.voiceButton)

        self.pdfButton = QPushButton("PDF Yükle")
        self.pdfButton.setToolTip("RAG için PDF dosyası ekle")
        self.pdfButton.clicked.connect(self.pdf_clicked)
        self.pdfButton.setEnabled(False)
        bottomLayout.addWidget(self.pdfButton)

        self.sendButton = QPushButton("Gönder")
        self.sendButton.setObjectName("ButtonPrimary")
        self.sendButton.setToolTip("Mesajı gönder")
        self.sendButton.clicked.connect(self.send_clicked)
        bottomLayout.addWidget(self.sendButton)

        root.addWidget(bottomFrame)
        self.refresh_ui()

        self.reminderTimer = QTimer(self)
        self.reminderTimer.setInterval(5000)
        self.reminderTimer.timeout.connect(self.check_reminders)
        self.reminderTimer.start()

    def check_reminders(self):
        try:
            due_list = reminders.get_due_reminders()
        except RuntimeError:
            return

        if not due_list:
            return

        for item in due_list:
            text = item.get("text") or ""
            reminderId = item.get("id")

            if reminderId is None:
                continue

            dialog = ReminderPOPUP(text, parent=self)
            result = dialog.exec()

            if result != QDialog.Accepted:
                continue

            try:
                if dialog.snoozed:
                    newDue = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
                    reminders.reschedule_reminder(int(reminderId), newDue)
                    self.chatArea.append(
                        f"<span style='color: #a5b4fc;'><b>Hatırlatma ertelendi:</b> {text} (5 dakika sonra)</span>"
                    )
                else:
                    reminders.mark_reminder_done(int(reminderId))
                    self.chatArea.append(
                        f"<span style='color: #fde68a;'><b>Hatırlatma:</b> {text}</span>"
                    )
            except RuntimeError:
                continue

    def mode_names(self) -> str:
        return "RAG" if self.currentMode == "rag" else "Asistan"

    def refresh_ui(self):
        isRag = self.currentMode == "rag"
        self.assistantModeButton.setChecked(not isRag)
        self.ragModeButton.setChecked(isRag)
        self.pdfButton.setEnabled(isRag)

        if isRag:
            if "PDF yüklendi" not in self.ragInfoLabel.text():
                self.ragInfoLabel.setText("RAG: Aktif")
        else:
            self.ragInfoLabel.setText("RAG: Pasif (Asistan modu)")

        self.statusLabel.setText(f"Mod: {self.mode_names()}")

    def send_clicked(self):
        text = self.inputLine.text().strip()

        if not text:
            return

        self.inputLine.clear()
        self.chatArea.append(f"<b>Sen:</b> {text}")
        self.sendButton.setEnabled(False)
        self.statusLabel.setText(f"Mod: {self.mode_names()} - Düşünüyor…")
        self.worker = LLMWorker(text, mode=self.currentMode)
        self.worker.startedProcessing.connect(self.started)
        self.worker.newMessage.connect(self.message)
        self.worker.errorOccured.connect(self.error)
        self.worker.finishedProcessing.connect(self.finished)
        self.worker.start()

    def started(self):
        pass

    def message(self, text: str):
        safeText = (text or "").replace("\n", "<br>")
        self.chatArea.append(f"<b>Asistan:</b> {safeText}")

    def error(self, message: str):
        self.chatArea.append(f"<span style='color: red;'><b>Hata:</b> {message}</span>")

    def finished(self):
        self.statusLabel.setText(f"Mod: {self.mode_names()}")
        self.sendButton.setEnabled(True)
        self.worker = None

    def voice_clicked(self):
        if self.voiceWorker is not None:
            return

        self.voiceButton.setEnabled(False)
        self.statusLabel.setText(f"Mod: {self.mode_names()} - Dinliyor…")

        self.voiceWorker = VoiceListenWorker()
        self.voiceWorker.transcriptReady.connect(self.voice_transcript)
        self.voiceWorker.errorOccured.connect(self.voice_error)
        self.voiceWorker.finished.connect(self.voice_finished)
        self.voiceWorker.start()

    def voice_transcript(self, text: str):
        if not text:
            self.statusLabel.setText(f"Mod: {self.mode_names()}")
            self.voiceButton.setEnabled(True)
            return

        self.inputLine.setText(text)
        self.send_clicked()

    def voice_error(self, message: str):
        self.chatArea.append(
            f"<span style='color: red;'><b>Ses Hatası:</b> {message}</span>"
        )

    def voice_finished(self):
        self.statusLabel.setText(f"Mod: {self.mode_names()}")
        self.voiceButton.setEnabled(True)
        self.voiceWorker = None

    def pdf_clicked(self):
        if self.ragWorker is not None:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "PDF Seç",
            "",
            "PDF Dosyaları (*.pdf)",
        )

        if not file_path:
            return

        self.pdfButton.setEnabled(False)
        self.statusLabel.setText("Mod: RAG - PDF indeksleniyor.")

        self.ragWorker = RAGIndexWorker(file_path)
        self.ragWorker.indexingFinished.connect(self.pdf_index)
        self.ragWorker.errorOccured.connect(self.pdf_error)
        self.ragWorker.finished.connect(self.pdf_finished)
        self.ragWorker.start()

    def pdf_index(self, doc_id: str):
        self.ragInfoLabel.setText("RAG: En az bir PDF yüklendi")
        self.chatArea.append(
            "<span style='color: #6ee7b7;'><b>RAG:</b> PDF indeksleme tamamlandı.</span>"
        )

    def pdf_error(self, message: str):
        self.chatArea.append(
            f"<span style='color: red;'><b>RAG Hatası:</b> {message}</span>"
        )

    def pdf_finished(self):
        self.statusLabel.setText(f"Mod: {self.mode_names()} - Hazır")
        self.pdfButton.setEnabled(True)
        self.ragWorker = None

    def settings_clicked(self) -> None:
        dlg = SettingsDialog(parent=self)
        dlg.exec()

    def mode_assistant_clicked(self):
        if self.currentMode == "assistant":
            return

        self.currentMode = "assistant"
        self.refresh_ui()

    def mode_rag_clicked(self):
        if self.currentMode == "rag":
            return

        self.currentMode = "rag"
        self.refresh_ui()
