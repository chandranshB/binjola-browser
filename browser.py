import sys
import requests
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QTabWidget, QShortcut, QPushButton, \
    QProgressBar, QMenu, QAction, QHBoxLayout, QListView
from PyQt5.QtCore import QUrl, QThread, pyqtSignal, Qt, QSettings
from PyQt5.QtGui import QKeySequence, QStandardItemModel, QStandardItem
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings


class GoogleSearchThread(QThread):
    results = pyqtSignal(list)

    def __init__(self, query):
        super().__init__()
        self.query = query

    def run(self):
        try:
            url = f"https://suggestqueries.google.com/complete/search?client=firefox&q={self.query}"
            response = requests.get(url)
            suggestions = response.json()[1]
            self.results.emit(suggestions)
        except Exception as e:
            self.results.emit([])


class WebKitBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Binjola Browser")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: #f0f0f0; color: #333;")

        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        central_widget.setLayout(layout)
        layout.addWidget(self.tabs)

        # Last closed tab
        self.last_closed_tabs = []

        # Add initial tab (homepage)
        self.add_new_tab()

        # Setup keyboard shortcuts
        self._setup_shortcuts()

        # Dark theme flag
        self.is_dark_theme = self.get_theme_preference()

    def add_new_tab(self):
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)

        # Browser widget
        browser = QWebEngineView()
        tab_layout.addWidget(browser)

        # Progress bar
        progress_bar = QProgressBar(self)
        progress_bar.setRange(0, 100)
        progress_bar.setTextVisible(False)
        tab_layout.addWidget(progress_bar)

        # Address bar layout
        address_bar_layout = QHBoxLayout()
        address_bar = QLineEdit(self)
        address_bar.setPlaceholderText("Enter URL or search karo bheji...")
        address_bar.setAlignment(Qt.AlignCenter)
        address_bar.returnPressed.connect(lambda: self.load_url(browser, address_bar))

        # Navigation buttons
        back_button = QPushButton("<", self)
        back_button.clicked.connect(browser.back)
        reload_button = QPushButton("↻", self)
        reload_button.clicked.connect(browser.reload)
        forward_button = QPushButton(">", self)
        forward_button.clicked.connect(browser.forward)

        menu_button = QPushButton("⋮", self)
        menu = QMenu(self)
        toggle_theme_action = QAction("Toggle Theme", self)
        toggle_theme_action.triggered.connect(self.toggle_theme)
        menu.addAction(toggle_theme_action)
        menu_button.setMenu(menu)

        address_bar_layout.addWidget(back_button)
        address_bar_layout.addWidget(reload_button)
        address_bar_layout.addWidget(address_bar)
        address_bar_layout.addWidget(forward_button)
        address_bar_layout.addWidget(menu_button)
        tab_layout.addLayout(address_bar_layout)

        # Suggestions list
        suggestions_list = QListView(self)
        suggestions_list.setVisible(False)
        tab_layout.addWidget(suggestions_list)

        self.tabs.addTab(tab, "New Tab")

        address_bar.setFocus()
        browser.setUrl(QUrl("https://github.com/chandransh186"))

        tab.browser = browser
        tab.address_bar = address_bar
        tab.suggestions_list = suggestions_list
        tab.progress_bar = progress_bar

        browser.loadStarted.connect(lambda: self.on_load_started(tab))
        browser.loadProgress.connect(lambda progress: self.on_load_progress(progress, tab))
        browser.loadFinished.connect(lambda success: self.on_load_finished(success, tab))

    def load_url(self, browser, address_bar):
        url = address_bar.text().strip()

        if not url.startswith(("http://", "https://", "www.")):
            if "." in url:
                url = f"http://{url}"
            else:
                self.search_google(url, browser)
                return

        browser.setUrl(QUrl(url))
        address_bar.setText(url)

    def search_google(self, query, browser):
        google_search_url = f"https://www.google.com/search?q={query}"
        browser.setUrl(QUrl(google_search_url))

    def _setup_shortcuts(self):
        self._add_shortcut("Ctrl+T", self.add_new_tab)
        self._add_shortcut("Ctrl+W", self.close_current_tab)
        self._add_shortcut("Ctrl+Shift+T", self.reopen_last_closed_tab)
        self._add_shortcut("Ctrl+N", self.open_new_window)
        self._add_shortcut("Ctrl+R", self.reload_current_page)
        self._add_shortcut("Ctrl+L", self.focus_address_bar)
        self._add_shortcut("Alt+D", self.focus_address_bar)
        self._add_shortcut("Ctrl+Shift+M", self.toggle_theme)
        self._add_shortcut("F11", self.toggle_fullscreen)

    def _add_shortcut(self, key_sequence, function):
        shortcut = QShortcut(QKeySequence(key_sequence), self)
        shortcut.activated.connect(function)

    def close_tab(self, index):
        if self.tabs.count() > 0:
            current_tab = self.tabs.widget(index)
            self.last_closed_tabs.append(current_tab)  # Save the tab for reopening
            self.tabs.removeTab(index)
            if self.tabs.count() == 0:
                self.close()  # Close the window if no tabs are open

    def close_current_tab(self):
        current_index = self.tabs.currentIndex()
        self.close_tab(current_index)

    def reopen_last_closed_tab(self):
        if self.last_closed_tabs:
            last_tab = self.last_closed_tabs.pop()
            self.tabs.addTab(last_tab, "Restored Tab")
            last_tab.browser.setUrl(QUrl("http://google.com"))

    def open_new_window(self):
        new_window = WebKitBrowser()
        new_window.show()

    def reload_current_page(self):
        current_browser = self.tabs.widget(self.tabs.currentIndex()).browser
        current_browser.reload()

    def focus_address_bar(self):
        current_address_bar = self.tabs.widget(self.tabs.currentIndex()).address_bar
        current_address_bar.setFocus()

    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        if self.is_dark_theme:
            self.setStyleSheet("background-color: #2E2E2E; color: white;")
        else:
            self.setStyleSheet("background-color: #f0f0f0; color: #333;")
        self.save_theme_preference()

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def on_load_started(self, tab):
        tab.progress_bar.setVisible(True)
        tab.progress_bar.setValue(0)

    def on_load_progress(self, progress, tab):
        tab.progress_bar.setValue(progress)

    def on_load_finished(self, success, tab):
        tab.progress_bar.setVisible(False)

    def get_theme_preference(self):
        settings = QSettings("MyApp", "WebKitBrowser")
        return settings.value("theme", False, type=bool)

    def save_theme_preference(self):
        settings = QSettings("MyApp", "WebKitBrowser")
        settings.setValue("theme", self.is_dark_theme)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    browser = WebKitBrowser()
    browser.show()
    sys.exit(app.exec_())
