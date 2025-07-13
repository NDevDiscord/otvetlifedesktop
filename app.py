import sys
import os
import glob
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

class WebEnginePage(QWebEnginePage):
    """Custom WebEnginePage to handle JavaScript console messages"""
    def __init__(self, profile, parent):
        super().__init__(profile, parent)
        self.injected_plugins = set()  # Track injected plugins per page instance
    
    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        print(f"JS [{level.name}]: {message} (Line: {line_number}, Source: {source_id})")
    
    def inject_plugins(self, plugins):
        """Inject all plugins into the current page"""
        if not plugins:
            return
            
        print(f"→ Injecting {len(plugins)} plugins...")
        for name, script in plugins.items():
            # Only inject if not already injected
            if name not in self.injected_plugins:
                self.runJavaScript(script)
                self.injected_plugins.add(name)
                print(f"  ✓ Injected: {name}")
            else:
                print(f"  ✓ Already injected: {name}")
    
    def reset_injection_state(self):
        """Reset injection state for new page"""
        self.injected_plugins = set()
        print("↻ Plugin injection state reset for new page")

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
        self.web_page = WebEnginePage(self.profile, self)  # Use custom page
        
        # Now create web view with our custom page
        self.web_view = QWebEngineView()
        self.web_view.setPage(self.web_page)
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
        
        # Load plugins
        self.plugin_scripts = {}
        self.load_plugins()
        
        # Connect all page change signals
        self.connect_page_change_signals()
        
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
    
    def connect_page_change_signals(self):
        """Connect to all signals that indicate page content has changed"""
        # Connect to load finished signal
        self.web_view.loadFinished.connect(self.on_page_loaded)
        
        # Connect to navigation signals
        self.web_view.urlChanged.connect(self.on_url_changed)
        
        # Connect to page reload signals
        self.reload_btn.clicked.connect(self.on_reload_triggered)
    
    def on_page_loaded(self, success):
        """Handle page load completion"""
        if success:
            print("✓ Page loaded successfully")
            # Reset injection state for new page
            self.web_page.reset_injection_state()
            self.inject_plugins()
        else:
            print("✗ Page load failed")
    
    def on_url_changed(self, url):
        """Handle URL changes (navigation)"""
        print(f"→ Navigating to: {url.toString()}")
        # Reset injection state for new page
        self.web_page.reset_injection_state()
        # Inject plugins after a short delay to ensure DOM is ready
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(500, self.inject_plugins)
    
    def on_reload_triggered(self):
        """Handle explicit reloads"""
        print("↻ Reloading page...")
        # Reset injection state for reloaded page
        self.web_page.reset_injection_state()
        # Inject plugins after reload completes
        self.web_view.loadFinished.connect(self.inject_plugins_once)
    
    def inject_plugins_once(self, success):
        """Inject plugins and disconnect from the signal"""
        if success:
            self.inject_plugins()
        self.web_view.loadFinished.disconnect(self.inject_plugins_once)
    
    def load_plugins(self):
        """Load all JavaScript plugins from the plugins directory"""
        plugin_dir = os.path.join(os.getcwd(), "plugins")
        os.makedirs(plugin_dir, exist_ok=True)
        print(f"Loading plugins from: {plugin_dir}")
        
        # Clear existing plugins
        self.plugin_scripts = {}
        
        for file_path in glob.glob(os.path.join(plugin_dir, "*.js")):
            plugin_name = os.path.basename(file_path)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.plugin_scripts[plugin_name] = f.read()
                    print(f"✓ Loaded plugin: {plugin_name}")
            except Exception as e:
                print(f"✗ Error loading plugin {plugin_name}: {str(e)}")
        
        # Inject immediately if page is already loaded
        if self.web_view.url().isValid():
            self.web_page.reset_injection_state()
            self.inject_plugins()
    
    def inject_plugins(self):
        """Inject all loaded plugins into the current page"""
        if not self.plugin_scripts:
            print("! No plugins to inject")
            return
            
        print(f"→ Injecting {len(self.plugin_scripts)} plugins...")
        self.web_page.inject_plugins(self.plugin_scripts)
    
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
