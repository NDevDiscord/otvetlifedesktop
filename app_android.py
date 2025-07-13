from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.clock import Clock, mainthread
from kivy.utils import platform
import os
import sys
import json
import time

# Android-specific imports
if platform == 'android':
    from jnius import autoclass, cast
    from android.permissions import request_permissions, Permission
    from android.storage import app_storage_path

    # Java classes
    WebView = autoclass('android.webkit.WebView')
    WebViewClient = autoclass('android.webkit.WebViewClient')
    WebSettings = autoclass('android.webkit.WebSettings')
    LayoutParams = autoclass('android.view.ViewGroup$LayoutParams')
    View = autoclass('android.view.View')
    Context = autoclass('android.content.Context')
    ValueCallback = autoclass('android.webkit.ValueCallback')
    CookieManager = autoclass('android.webkit.CookieManager')
    WebChromeClient = autoclass('android.webkit.WebChromeClient')
    Activity = autoclass('org.kivy.android.PythonActivity').mActivity
    ViewGroup = autoclass('android.view.ViewGroup')
    Gravity = autoclass('android.view.Gravity')
    RelativeLayout = autoclass('android.widget.RelativeLayout')
    RelativeLayoutParams = autoclass('android.widget.RelativeLayout$LayoutParams')
    LinearLayout = autoclass('android.widget.LinearLayout')
    LinearLayoutParams = autoclass('android.widget.LinearLayout$LayoutParams')
    TextView = autoclass('android.widget.TextView')
    OnClickListener = autoclass('android.view.View$OnClickListener')
    Color = autoclass('android.graphics.Color')
    Typeface = autoclass('android.graphics.Typeface')
    Toast = autoclass('android.widget.Toast')
    ClipboardManager = autoclass('android.content.ClipboardManager')
    ClipData = autoclass('android.content.ClipData')
    ViewGroupLayoutParams = autoclass('android.view.ViewGroup$LayoutParams')
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Handler = autoclass('android.os.Handler')
    Runnable = autoclass('java.lang.Runnable')

class BrowserApp(App):
    def build(self):
        self.layout = FloatLayout()
        Window.bind(on_keyboard=self.key_handler)
        
        # Create navigation bar
        self.nav_bar = BoxLayout(
            size_hint=(1, None),
            height=50,
            pos_hint={'top': 1}
        )
        self.nav_bar.canvas.before.add(Color(1, 1, 1, 1))
        self.nav_bar.canvas.before.add(Rectangle(size=self.nav_bar.size, pos=self.nav_bar.pos))
        
        # Navigation buttons
        self.back_btn = Button(text='←', size_hint=(None, 1), width=50)
        self.forward_btn = Button(text='→', size_hint=(None, 1), width=50)
        self.reload_btn = Button(text='↻', size_hint=(None, 1), width=50)
        self.url_label = Label(
            text='Loading...',
            size_hint_x=0.7,
            halign='left',
            valign='middle',
            padding_x=10,
            text_size=(Window.width * 0.7, None)
        )
        
        self.nav_bar.add_widget(self.back_btn)
        self.nav_bar.add_widget(self.forward_btn)
        self.nav_bar.add_widget(self.reload_btn)
        self.nav_bar.add_widget(self.url_label)
        
        self.layout.add_widget(self.nav_bar)
        
        # Request permissions on Android
        if platform == 'android':
            request_permissions([
                Permission.INTERNET,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE
            ])
            Clock.schedule_once(self.create_webview, 0)
        
        return self.layout
    
    def create_webview(self, dt):
        if platform != 'android':
            return
            
        # Create Android WebView
        self.webview = WebView(Activity)
        settings = self.webview.getSettings()
        settings.setJavaScriptEnabled(True)
        settings.setDomStorageEnabled(True)
        settings.setDatabaseEnabled(True)
        settings.setAppCacheEnabled(True)
        settings.setLoadWithOverviewMode(True)
        settings.setUseWideViewPort(True)
        settings.setSupportZoom(True)
        settings.setBuiltInZoomControls(True)
        settings.setDisplayZoomControls(False)
        settings.setUserAgentString("Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36")
        
        # Set cache paths
        cache_path = Activity.getCacheDir().getAbsolutePath()
        settings.setAppCachePath(cache_path)
        settings.setDatabasePath(cache_path)
        
        # Enable cookies
        CookieManager.getInstance().setAcceptThirdPartyCookies(self.webview, True)
        CookieManager.getInstance().setAcceptCookie(True)
        
        # Create custom WebViewClient
        class CustomWebViewClient(WebViewClient):
            def __init__(self, app):
                super().__init__()
                self.app = app
            
            def shouldOverrideUrlLoading(self, view, url):
                view.loadUrl(url)
                return True
            
            def onPageStarted(self, view, url, favicon):
                self.app.update_url(url)
                return super().onPageStarted(view, url, favicon)
            
            def onPageFinished(self, view, url):
                self.app.update_title(view.getTitle())
                return super().onPageFinished(view, url)
        
        self.webview.setWebViewClient(CustomWebViewClient(self))
        
        # Add WebView to activity
        params = ViewGroupLayoutParams(
            ViewGroupLayoutParams.MATCH_PARENT, 
            ViewGroupLayoutParams.MATCH_PARENT
        )
        Activity.addContentView(self.webview, params)
        
        # Position WebView below navigation bar
        self.position_webview()
        
        # Load initial URL
        self.load_url_from_file()
        
        # Bind buttons
        self.back_btn.bind(on_release=self.go_back)
        self.forward_btn.bind(on_release=self.go_forward)
        self.reload_btn.bind(on_release=self.reload_page)
        self.url_label.bind(on_touch_down=self.copy_url)
        
        # Bind resize event
        Window.bind(size=self.position_webview)
    
    @mainthread
    def position_webview(self, *args):
        if not hasattr(self, 'webview') or self.webview is None:
            return
            
        # Calculate positions
        nav_bar_height = self.nav_bar.height
        screen_width = Window.width
        screen_height = Window.height
        
        # Set WebView position below navigation bar
        self.webview.setX(0)
        self.webview.setY(nav_bar_height * Window._density)
        self.webview.setLayoutParams(
            ViewGroupLayoutParams(
                int(screen_width * Window._density),
                int((screen_height - nav_bar_height) * Window._density)
            )
        )
    
    def load_url_from_file(self):
        try:
            # Get path for Android storage
            if platform == 'android':
                storage_path = app_storage_path()
                file_path = os.path.join(storage_path, 'zerkalo.txt')
            else:
                file_path = 'zerkalo.txt'
            
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    url = f.read().strip()
                    if url:
                        self.load_url(url)
                        return
            
            # Fallback URL if file not found
            self.load_url("https://example.com")
        except Exception as e:
            print(f"Error loading URL: {str(e)}")
            self.load_url("https://example.com")
    
    def load_url(self, url):
        if hasattr(self, 'webview') and self.webview:
            self.webview.loadUrl(url)
    
    @mainthread
    def update_url(self, url):
        self.url_label.text = url
    
    @mainthread
    def update_title(self, title):
        if title:
            self.url_label.text = title[:50] + (title[50:] and '...')
    
    def go_back(self, instance):
        if hasattr(self, 'webview') and self.webview.canGoBack():
            self.webview.goBack()
    
    def go_forward(self, instance):
        if hasattr(self, 'webview') and self.webview.canGoForward():
            self.webview.goForward()
    
    def reload_page(self, instance):
        if hasattr(self, 'webview'):
            self.webview.reload()
    
    def copy_url(self, instance, touch):
        if instance.collide_point(*touch.pos):
            url = self.url_label.text
            self.copy_to_clipboard(url)
            self.show_toast("URL copied to clipboard")
    
    @mainthread
    def copy_to_clipboard(self, text):
        if platform != 'android':
            return
            
        clipboard = cast(
            ClipboardManager,
            Activity.getSystemService(Context.CLIPBOARD_SERVICE)
        )
        clip = ClipData.newPlainText("URL", text)
        clipboard.setPrimaryClip(clip)
    
    @mainthread
    def show_toast(self, message):
        Toast.makeText(
            Activity, 
            message, 
            Toast.LENGTH_SHORT
        ).show()
    
    def key_handler(self, window, key, *args):
        if key == 27:  # Android back button
            if hasattr(self, 'webview') and self.webview.canGoBack():
                self.webview.goBack()
                return True
        return False

if __name__ == '__main__':
    BrowserApp().run()