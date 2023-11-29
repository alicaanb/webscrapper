import sys
import requests
from bs4 import BeautifulSoup
import pandas as pd
import xml.etree.ElementTree as ET
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QFileDialog, QTextBrowser, QScrollArea, QSizePolicy, QMessageBox, QGroupBox
)
import time
import random

class WebScraperApp(QWidget):
    def __init__(self):
        super().__init__()

        self.proxy_list = [
            '188.119.49.6:19999',
            '188.132.222.43:8080',
            '194.4.153.5:8080',
            '78.188.16.111:1454',
            '185.249.202.123:3128'
        ]
        self.current_proxy_index = 0

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Web Scraper App')
        self.setGeometry(100, 100, 800, 600)

        self.url_text_edit = QTextEdit(self)
        self.url_text_edit.setPlaceholderText('Enter URLs here (one per line)')

        self.info_scroll_area = QScrollArea(self)
        self.info_group_box = QGroupBox("Selectors", self)
        self.info_group_box.setLayout(QVBoxLayout())
        self.info_scroll_area.setWidget(self.info_group_box)
        self.info_scroll_area.setWidgetResizable(True)
        self.info_scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.info_line_edits = []

        # Add initial selector input
        self.add_selector_input()

        self.run_button = QPushButton('Run', self)
        self.run_button.clicked.connect(self.run_scraper)

        self.clear_button = QPushButton('Clear', self)
        self.clear_button.clicked.connect(self.clear_table)

        self.table_widget = QTableWidget(self)
        self.copy_button = QPushButton('Copy Table', self)
        self.copy_button.clicked.connect(self.copy_table)

        self.xml_button = QPushButton('Create XML', self)
        self.xml_button.clicked.connect(self.create_xml)

        self.result_browser = QTextBrowser(self)
        self.result_browser.setVisible(False)

        scroll_area = QScrollArea(self)
        scroll_area.setWidget(self.table_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        result_scroll_area = QScrollArea(self)
        result_scroll_area.setWidget(self.result_browser)
        result_scroll_area.setWidgetResizable(True)
        result_scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QHBoxLayout()

        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel('Enter URLs:'))
        left_layout.addWidget(self.url_text_edit)
        left_layout.addWidget(self.info_scroll_area)

        # Move the creation of the "Add Selector" button outside the add_selector_input method
        add_button = QPushButton('+ Add Selector', self)
        add_button.clicked.connect(self.add_selector_input)
        left_layout.addWidget(add_button)

        left_layout.addWidget(self.run_button)
        left_layout.addWidget(self.clear_button)

        right_layout = QVBoxLayout()
        right_layout.addWidget(scroll_area)
        right_layout.addWidget(self.copy_button)
        right_layout.addWidget(self.xml_button)
        right_layout.addWidget(result_scroll_area)

        layout.addLayout(left_layout, stretch=1)
        layout.addLayout(right_layout, stretch=2)

        self.setLayout(layout)

    def add_selector_input(self):
        info_line_edit = QLineEdit(self)
        info_line_edit.setPlaceholderText('Specify information to extract (CSS selector)')
        self.info_line_edits.append(info_line_edit)
        self.info_group_box.layout().addWidget(info_line_edit)

    def run_scraper(self):
        urls = self.url_text_edit.toPlainText().split('\n')
        selectors = [info_line_edit.text() for info_line_edit in self.info_line_edits]

        results = []

        for url in urls:
            if not url:
                continue

            self.current_col = 1

            # Her 15-20 sorguda bir proxy değiştirme
            if self.current_col % 15 == 0:
                self.change_proxy()

            page_content = self.get_page_content(url)

            result = {'URL': url}
            for selector in selectors:
                if not selector:
                    continue

                info = self.extract_info(page_content, selector)
                col_key = f'{selector} - {self.current_col}'
                result[col_key] = info

                self.current_col += 1

            results.append(result)

            # İstekler arasında 3-5 saniye arasında rasgele bir gecikme ekleyin
            time.sleep(3 + random.uniform(0, 2))

        self.populate_table(results)

    def change_proxy(self):
        if self.proxy_list:
            self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
            proxy = self.proxy_list[self.current_proxy_index]
            proxies = {
                "http": f"http://{proxy}",
                "https": f"https://{proxy}"
            }
            requests.Session().proxies = proxies
            print(f"Proxy changed to: {proxy}")

    def get_page_content(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return ""

    def extract_info(self, content, selector):
        try:
            soup = BeautifulSoup(content, 'html.parser')
            is_img_selector = soup.select_one(selector).name == 'img' if soup.select_one(selector) else False

            if is_img_selector:
                result = soup.select_one(selector)['src']
            else:
                result = soup.select_one(selector).text if soup.select_one(selector) else 'Not Found'

            return result
        except Exception as e:
            print(f"Error extracting info: {e}")
            return 'Error'

    def populate_table(self, results):
        self.table_widget.clear()
        self.table_widget.setColumnCount(0)
        self.table_widget.setRowCount(0)

        if not results:
            return

        headers = list(results[0].keys())
        self.table_widget.setColumnCount(len(headers))
        self.table_widget.setHorizontalHeaderLabels(headers)

        for result in results:
            row_position = self.table_widget.rowCount()
            self.table_widget.insertRow(row_position)
            for col, key in enumerate(headers):
                self.table_widget.setItem(row_position, col, QTableWidgetItem(result[key]))

        df = pd.DataFrame(results)
        self.result_browser.setPlainText(df.to_html(index=False))

    def clear_table(self):
        reply = QMessageBox.question(
            self, 'Clear Table', 'Are you sure you want to clear the table?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.table_widget.clear()
            self.table_widget.setColumnCount(0)
            self.table_widget.setRowCount(0)
            self.result_browser.clear()

    def copy_table(self):
        self.result_browser.selectAll()
        self.result_browser.copy()

    def create_xml(self):
        file_path, _ = QFileDialog.getSaveFileName(self, 'Save XML File', '', 'XML Files (*.xml);;All Files (*)')

        if file_path:
            root = ET.Element("data")

            for row in range(self.table_widget.rowCount()):
                url = self.table_widget.item(row, 0).text()

                entry = ET.SubElement(root, "entry")
                url_elem = ET.SubElement(entry, "url")
                url_elem.text = url

                for col in range(1, self.table_widget.columnCount()):
                    info = self.table_widget.item(row, col).text()
                    header = self.table_widget.horizontalHeaderItem(col).text()
                    selector, col_num = header.split(" - ")
                    col_elem = ET.SubElement(entry, f"{selector}_{col_num}")
                    col_elem.text = info

            tree = ET.ElementTree(root)
            tree.write(file_path, encoding="utf-8", xml_declaration=True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = WebScraperApp()
    window.show()
    sys.exit(app.exec_())
