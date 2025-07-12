import sys
import os
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QFont, QPalette, QColor, QGuiApplication
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QSizePolicy
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings, QWebEnginePage

# Set Google DNS for QtWebEngine
os.environ["QTWEBENGINE_DNS_SERVER_ADDRESS"] = "8.8.8.8"

class ModernBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ответы@Live")
        self.setMinimumSize(1280, 720)  # Widescreen format
        
        # Light theme color scheme
        self.bg_color = QColor(248, 249, 250)
        self.widget_color = QColor(255, 255, 255)
        self.highlight_color = QColor(26, 115, 232)
        self.text_color = QColor(32, 33, 36)
        self.border_color = QColor(218, 220, 224)
        self.success_color = QColor(52, 168, 83)
        
        # Apply light theme palette
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, self.bg_color)
        palette.setColor(QPalette.ColorRole.WindowText, self.text_color)
        palette.setColor(QPalette.ColorRole.Base, self.widget_color)
        palette.setColor(QPalette.ColorRole.Text, self.text_color)
        palette.setColor(QPalette.ColorRole.Button, self.widget_color)
        palette.setColor(QPalette.ColorRole.ButtonText, self.text_color)
        palette.setColor(QPalette.ColorRole.Highlight, self.highlight_color)
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        self.setPalette(palette)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create compact navigation bar
        nav_bar = QFrame()
        nav_bar.setStyleSheet(f"""
            background-color: {self.widget_color.name()};
            border-bottom: 1px solid {self.border_color.name()};
            padding: 0px;
        """)
        nav_bar.setFixedHeight(40)
        nav_bar_layout = QHBoxLayout(nav_bar)
        nav_bar_layout.setContentsMargins(8, 0, 8, 0)
        nav_bar_layout.setSpacing(8)
        
        # Navigation buttons
        self.back_btn = self.create_button("←", "Navigate back")
        self.forward_btn = self.create_button("→", "Navigate forward")
        self.reload_btn = self.create_button("↻", "Reload page")
        
        # URL display
        self.url_label = QLabel()
        self.url_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.url_label.setStyleSheet(f"""
            QLabel {{
                background-color: {self.widget_color.name()};
                color: {self.text_color.name()};
                border: 1px solid {self.border_color.name()};
                padding: 4px 12px;
                font-size: 13px;
                font-weight: normal;
                margin: 0;
            }}
            QLabel:hover {{
                border-color: {self.highlight_color.name()};
            }}
        """)
        self.url_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.url_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        
        # Layout navigation bar
        nav_bar_layout.addWidget(self.back_btn)
        nav_bar_layout.addWidget(self.forward_btn)
        nav_bar_layout.addWidget(self.reload_btn)
        nav_bar_layout.addWidget(self.url_label, 1)
        
        # Configure browser profile FIRST
        self.cache_dir = os.path.join(os.getcwd(), "browser_data")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Create persistent profile with unique name
        self.profile = QWebEngineProfile("ZerkaloPersistentProfile", self)
        self.profile.setPersistentStoragePath(self.cache_dir)
        self.profile.setCachePath(self.cache_dir)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
        self.profile.setHttpCacheMaximumSize(100 * 1024 * 1024)  # 100 MB cache
        
        # Set modern user agent
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        self.profile.setHttpUserAgent(user_agent)
        
        # Create web page with our custom profile
        web_page = QWebEnginePage(self.profile, self)
        
        # Now create web view with our custom page
        self.web_view = QWebEngineView()
        self.web_view.setPage(web_page)
        self.web_view.setStyleSheet("background-color: white; border: none;")
        self.web_view.urlChanged.connect(self.update_url_display)
        self.web_view.titleChanged.connect(self.update_window_title)
        
        # Configure web view settings
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.DnsPrefetchEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
        
        # Add widgets to main layout
        main_layout.addWidget(nav_bar)
        main_layout.addWidget(self.web_view, 1)
        
        # Load initial URL
        self.load_url_from_file()
        
        # Connect signals
        self.back_btn.clicked.connect(self.web_view.back)
        self.forward_btn.clicked.connect(self.web_view.forward)
        self.reload_btn.clicked.connect(self.web_view.reload)
        self.url_label.mousePressEvent = self.copy_url_to_clipboard
        
        # Print cookie storage path for verification
        print(f"Cookie storage path: {self.profile.persistentStoragePath()}")
        print(f"Cache path: {self.profile.cachePath()}")
    
    def create_button(self, text, tooltip):
        button = QPushButton(text)
        button.setToolTip(tooltip)
        button.setFixedSize(32, 32)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.widget_color.name()};
                color: {self.text_color.name()};
                border: 1px solid {self.border_color.name()};
                font-weight: bold;
                font-size: 14px;
                padding: 0;
                margin: 0;
            }}
            QPushButton:hover {{
                background-color: #f8f9fa;
                border-color: {self.highlight_color.name()};
            }}
            QPushButton:pressed {{
                background-color: #e8eaed;
            }}
        """)
        return button
    
    def load_url_from_file(self):
        try:
            with open("zerkalo.txt", "r") as file:
                url = file.read().strip()
                if url:
                    self.web_view.load(QUrl(url))
                    self.url_label.setText(url)
        except FileNotFoundError:
            self.url_label.setText("Error: zerkalo.txt not found")
            self.setWindowTitle("Ответы@Live - Ошибка файла")
        except Exception as e:
            self.url_label.setText(f"Error: {str(e)}")
            self.setWindowTitle("Ответы@Live - Ошибка")
    
    def update_url_display(self, url):
        self.url_label.setText(url.toString())
    
    def update_window_title(self, title):
        if title:
            self.setWindowTitle(f"{title}")
        else:
            self.setWindowTitle("Ответы@Live")
    
    def copy_url_to_clipboard(self, event):
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.url_label.text())
        
        original_style = self.url_label.styleSheet()
        original_text = self.url_label.text()
        
        self.url_label.setText("✓ Copied")
        self.url_label.setStyleSheet(f"""
            QLabel {{
                background-color: #e6f4ea;
                color: {self.success_color.name()};
                border: 1px solid {self.success_color.name()};
                padding: 4px 12px;
                font-size: 13px;
                font-weight: normal;
            }}
        """)
        
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1500, lambda: [
            self.url_label.setStyleSheet(original_style),
            self.url_label.setText(original_text)
        ])

if __name__ == "__main__":
    # For Linux systems: Disable sandbox if needed
    if sys.platform.startswith('linux'):
        os.environ['QTWEBENGINE_DISABLE_SANDBOX'] = "1"
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Set optimized font
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    browser = ModernBrowser()
    browser.show()
    sys.exit(app.exec())