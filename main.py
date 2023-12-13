import sys
import json
from PySide6 import QtCore
from PySide6.QtCore import QEvent, Qt, QTimer, QItemSelectionModel
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QDialog, QVBoxLayout, QPushButton, QComboBox, QLabel, QLineEdit, QListView
from Data import Get_data, LoginWindow
from Add_table import AddRecordTypeDialog
from PySide6.QtGui import QIcon, QStandardItemModel, QStandardItem
class CheckBoxComboBox(QComboBox):
    def __init__(self, main_window, column_index, column_names):
        super().__init__()
        self.column_index = column_index
        self.main_window = main_window
        self.column_names = column_names  # Сохраняем имена столбцов для заголовков
        self.header_text = column_names[column_index]  # Сохраняем текст заголовка
        self._prevent_hiding = False
        self.setView(QListView())
        self.setModel(QStandardItemModel())
        self.setMinimumWidth(150)
        self.setMinimumHeight(30)

        header_items = [QStandardItem(name) for name in column_names]  # Создаем элементы для заголовков
        for item in header_items:
            item.setCheckable(False)
            item.setSelectable(False)

        self.addItems(column_names)  # Добавляем все имена столбцов в выпадающий список

        self.currentTextChanged.connect(self.handle_current_text_changed)  # Обработчик изменения текста

        self.view().pressed.connect(self.handle_item_pressed)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.WindowDeactivate and not self.view().underMouse():
            self.hidePopup()
        return super().eventFilter(obj, event)

    def hidePopup(self):
        if self._prevent_hiding:
            self._prevent_hiding = False
            return
        super().hidePopup()

    def handle_item_pressed(self, index):
        item = self.model().itemFromIndex(index)
        if item.flags() & Qt.ItemIsUserCheckable:
            state = item.checkState()
            item.setCheckState(Qt.Unchecked if state == Qt.Checked else Qt.Checked)
            self._prevent_hiding = True
            QTimer.singleShot(0, self.showPopup)
            self.main_window.handle_combo_pressed(self)
        else:
            QTimer.singleShot(0, self.showPopup)  # Показываем выпадающий список при выборе нового значения
            self.view().selectionModel().setCurrentIndex(index, QItemSelectionModel.Select)  # Выбираем элемент
            self.view().selectionModel().clearSelection()  # Очищаем выделение
            self.view().setCurrentIndex(index)  # Устанавливаем текущий индекс

    def handle_current_text_changed(self, text):
        if text != self.header_text:
            self.setCurrentText(self.header_text)

    def showPopup(self):
        # Восстанавливаем текст заголовка после закрытия списка
        super().showPopup()
        self.view().model().item(0).setText(self.header_text)

    def setItems(self, items):
        model = QStandardItemModel()
        for text in items:
            item = QStandardItem(text)
            item.setCheckable(
                text not in self.column_names)  # Устанавливаем чекбокс только если элемент не является столбцом
            if text in self.column_names:
                item.setSelectable(False)  # Отключаем выбор для исходных имен столбцов
            model.appendRow(item)
        self.setModel(model)

    def checkedItems(self):
        return [self.model().item(index).text() for index in range(self.count()) if
                self.model().item(index).checkState() == Qt.Checked]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Поиск лекарств и аптек")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.AVAILABILITY_COLUMN_INDEX = 5
        self.PRICE_COLUMN_INDEX = 6
        self.layout = QVBoxLayout()

        self.authenticated = False  # Флаг аутентификации

        # Строка поиска лекарств
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите название препарата")
        self.search_layout = QHBoxLayout()
        self.search_layout.addWidget(self.search_input)
        self.search_input.textChanged.connect(self.filter_drugs)

        # Размещение кнопки "Войти" в правом верхнем углу окна
        self.login_button = QPushButton("Войти")
        self.login_button.clicked.connect(self.show_login_window)

        # Размещение виджетов поиска и кнопки входа
        self.layout.addWidget(self.login_button, alignment=Qt.AlignRight)
        self.layout.addLayout(self.search_layout)

        # Кнопки для управления записями
        self.add_button = QPushButton()
        self.add_button.setIcon(QIcon(r"icons\plus.png"))
        self.add_button.setIconSize(QtCore.QSize(24, 24))
        self.add_button.clicked.connect(self.add_record)

        self.edit_button = QPushButton()
        self.edit_button.setIcon(QIcon(r"icons\pencil.png"))
        self.edit_button.setIconSize(QtCore.QSize(24, 24))
        self.edit_button.clicked.connect(self.edit_record)

        self.delete_button = QPushButton()
        self.delete_button.setIcon(QIcon(r"icons\сrash.png"))
        self.delete_button.setIconSize(QtCore.QSize(24, 24))
        self.delete_button.clicked.connect(self.delete_record)

        # Скрываем кнопки
        self.add_button.setVisible(False)
        self.edit_button.setVisible(False)
        self.delete_button.setVisible(False)

        # Добавление кнопок в основной layout
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.setAlignment(Qt.AlignRight)

        self.layout.addLayout(buttons_layout)
        self.layout.addLayout(self.search_layout)

        # Таблица лекарств
        self.drug_table = QTableWidget()
        self.drug_table.setColumnCount(8)
        self.drug_table.setHorizontalHeaderLabels(
            ["По действию", "По целевой системе или органу", "Лекарство", "Производитель", "Дата производства", "Доступность в аптеках", "Цена", "Количество"]
        )
        self.drug_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.drug_table)

        # Строка поиска для аптек
        self.search_input_pharm = QLineEdit()
        self.search_input_pharm.setPlaceholderText("Введите название аптеки")
        self.search_layout_pharm = QHBoxLayout()
        self.search_layout_pharm.addWidget(self.search_input_pharm)
        self.search_input_pharm.textChanged.connect(self.filter_pharmacies)
        self.layout.addLayout(self.search_layout_pharm)

        # Таблица аптек
        self.pharmacy_table = QTableWidget()
        self.pharmacy_table.setColumnCount(3)
        self.pharmacy_table.setHorizontalHeaderLabels(["Id Аптеки", "Название", "Адрес"])
        self.pharmacy_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.pharmacy_table)

        self.central_widget.setLayout(self.layout)

        # Загрузка данных о лекарствах и аптеках
        data = Get_data()

        data = Get_data()
        print("pharm", data.get_data_Pharmacy())
        print("med", data.get_data_Medicine())
        pharmacy_data = json.loads(data.get_data_Pharmacy())
        medicine_data = json.loads(data.get_data_Medicine())


        # Отображение данных в таблицах
        self.populate_drug_table(medicine_data)
        self.populate_pharmacy_table(pharmacy_data)

        self.filter_boxes = []  # Список для хранения фильтров

        # Добавление фильтров
        self.add_column_filters()  # Вызов метода для добавления выпадающих списков
        self.apply_initial_filters()  # Вызов метода для начальной фильтрации данных

        # Установка стилей для улучшения внешнего вида
        self.setStyleSheet("""
            QPushButton {
                background-color: #2ECC71;
                border: none;
                color: white;
                padding: 8px 12px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 14px;
                margin: 4px 2px;
                transition-duration: 0.4s;
                cursor: pointer;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #58D68D;
                color: white;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QTableWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #E8DDB5;
                padding: 4px;
            }
        """)
        self.drug_table.itemSelectionChanged.connect(self.on_table_selection_changed)
        self.pharmacy_table.itemSelectionChanged.connect(self.on_table_selection_changed)

        self.availability_filter = None  # Атрибут для фильтра доступности

    def populate_drug_table(self, data):
        self.drug_table.setRowCount(len(data))
        for row, item in enumerate(data):
            self.drug_table.setItem(row, 0, QTableWidgetItem(item.get('Category by action')))
            self.drug_table.setItem(row, 1, QTableWidgetItem(item.get('Category by system')))
            self.drug_table.setItem(row, 2, QTableWidgetItem(item.get('Medicine')))
            self.drug_table.setItem(row, 3, QTableWidgetItem(item.get('Manufacturer')))
            self.drug_table.setItem(row, 4, QTableWidgetItem(item.get('Production date')))
            self.drug_table.setItem(row, 5, QTableWidgetItem(''.join(map(str, item.get('Availability in pharmacies')))))
            self.drug_table.setItem(row, 6, QTableWidgetItem(str(item.get('Cost'))))
            self.drug_table.setItem(row, 7, QTableWidgetItem(str(item.get('Count'))))

    def populate_pharmacy_table(self, data):
        self.pharmacy_table.setRowCount(len(data))
        for row, item in enumerate(data):
            self.pharmacy_table.setItem(row, 0, QTableWidgetItem(str(item.get('Id'))))
            self.pharmacy_table.setItem(row, 1, QTableWidgetItem(item.get('Name')))
            self.pharmacy_table.setItem(row, 2, QTableWidgetItem(item.get('Address')))

    def filter_drugs(self):
        search_text = self.search_input.text().lower()
        for row in range(self.drug_table.rowCount()):
            should_show_row = False
            for col in range(self.drug_table.columnCount()):
                cell_text = self.drug_table.item(row, col).text().lower()
                if search_text in cell_text:
                    should_show_row = True
                    break
            self.drug_table.setRowHidden(row, not should_show_row)

    def filter_pharmacies(self):
        search_text = self.search_input_pharm.text().lower()
        for row in range(self.pharmacy_table.rowCount()):
            should_show_row = False
            for col in range(self.pharmacy_table.columnCount()):
                cell_text = self.pharmacy_table.item(row, col).text().lower()
                if search_text in cell_text:
                    should_show_row = True
                    break
            self.pharmacy_table.setRowHidden(row, not should_show_row)

    def add_column_filters(self):
        self.filter_boxes = []  # Создаем список для хранения фильтров
        column_names = ["По действию", "По целевой системе или органу", "Лекарство", "Производитель",
                        "Дата производства", "Доступность в аптеках", "Цена"]
        for col in range(self.drug_table.columnCount() - 1):
            if self.drug_table.horizontalHeaderItem(col).text() == "Цена":
                self.add_price_filter()
            elif self.drug_table.horizontalHeaderItem(col).text() == "Доступность в аптеках":
                filter_box = CheckBoxComboBox(main_window=self, column_index=col, column_names=column_names)
                item = self.extract_numbers_from_column(self.drug_table, 5)
                items = [str(num) for num in item]
                filter_box.setItems([self.drug_table.horizontalHeaderItem(col).text()] + items)
                availability_filter = filter_box
                filter_box.view().pressed.connect(lambda event, box=filter_box: self.apply_availability_filter(availability_filter))
                  # Присваиваем созданный фильтр доступности self.availability_filter
                self.search_layout.addWidget(filter_box)
                self.filter_boxes.append(filter_box)
            else:
                filter_box = CheckBoxComboBox(main_window=self, column_index=col, column_names=column_names)
                items = sorted(set(self.drug_table.item(row, col).text() for row in range(self.drug_table.rowCount())))
                filter_box.setItems([self.drug_table.horizontalHeaderItem(col).text()] + items)
                filter_box.view().pressed.connect(lambda event, box=filter_box: self.handle_combo_pressed(box))
                self.search_layout.addWidget(filter_box)
                self.filter_boxes.append(filter_box)

    def handle_combo_pressed(self, combo_box):
        checked_items = [box.checkedItems() for box in self.filter_boxes]

        price_filters = False
        min_price_text = self.min_price_input.text()
        max_price_text = self.max_price_input.text()

        # Check if price filters are active
        if min_price_text or max_price_text:
            price_filters = True

        for row in range(self.drug_table.rowCount()):
            should_show_row = True

            # Check price filter
            if price_filters:
                price_text = self.drug_table.item(row, self.PRICE_COLUMN_INDEX).text()
                try:
                    price = float(price_text)
                    min_price = float(min_price_text) if min_price_text else float("-inf")
                    max_price = float(max_price_text) if max_price_text else float("inf")

                    if not (min_price <= price <= max_price):
                        should_show_row = False
                        print(f"Row {row}: Price filter - Hiding row")
                except ValueError:
                    pass  # Handle conversion errors

            # Check other filters
            for col, items in enumerate(checked_items):
                if col != self.PRICE_COLUMN_INDEX:  # Skip price column
                    cell_text = self.drug_table.item(row, col).text().lower()
                    if items and not any(item.lower() in cell_text for item in items):
                        should_show_row = False
                        print(f"Row {row}: Other filters - Hiding row")
                        break

            # Set row visibility based on combined filters
            self.drug_table.setRowHidden(row, not should_show_row)

    def apply_initial_filters(self):
        for row in range(self.drug_table.rowCount()):
            should_show_row = False
            for col, filter_box in enumerate(self.filter_boxes):
                if col >= self.drug_table.columnCount():
                    break  # Прерываем цикл, если индекс столбца превышает количество столбцов в таблице
                cell_text = self.drug_table.item(row, col).text().lower()
                filter_text = filter_box.currentText().lower()
                if filter_text == "all" or filter_text in cell_text:
                    should_show_row = True
                    break
                else:
                    should_show_row = True  # Показать строку, если фильтр не "all"
            self.drug_table.setRowHidden(row, not should_show_row)

    def add_price_filter(self):
        price_filter_widget = QWidget()  # Creating a widget to contain the layout
        price_filter_layout = QHBoxLayout(price_filter_widget)  # Adding the layout to the widget

        self.min_price_input = QLineEdit()
        self.max_price_input = QLineEdit()
        self.min_price_input.setPlaceholderText("Min")
        self.max_price_input.setPlaceholderText("Max")
        self.min_price_input.textChanged.connect(self.apply_price_filter)
        self.max_price_input.textChanged.connect(self.apply_price_filter)

        price_filter_layout.addWidget(QLabel("Цена:"))
        price_filter_layout.addWidget(self.min_price_input)
        price_filter_layout.addWidget(self.max_price_input)

        self.search_layout.addWidget(price_filter_widget)  # Adding the widget to the layout

    def apply_price_filter(self):
        min_price_text = self.min_price_input.text()
        max_price_text = self.max_price_input.text()

        checked_items = [box.checkedItems() for box in self.filter_boxes]

        for row in range(self.drug_table.rowCount()):
            should_show_row = True

            # Check price filter
            price_text = self.drug_table.item(row, self.PRICE_COLUMN_INDEX).text()
            try:
                price = float(price_text)
                min_price = float(min_price_text) if min_price_text else float("-inf")
                max_price = float(max_price_text) if max_price_text else float("inf")

                if not (min_price <= price <= max_price):
                    should_show_row = False
            except ValueError:
                pass  # Handle conversion errors

            # Check other filters
            for col, items in enumerate(checked_items):
                if col != self.PRICE_COLUMN_INDEX:  # Skip price column
                    cell_text = self.drug_table.item(row, col).text().lower()
                    if items and not any(item.lower() in cell_text for item in items):
                        should_show_row = False
                        break

            self.drug_table.setRowHidden(row, not should_show_row)

    def apply_availability_filter(self, availability_filter):
        selected_nums = {int(num) for num in availability_filter.checkedItems()}

        for row in range(self.drug_table.rowCount()):
            availability_text = self.drug_table.item(row, self.AVAILABILITY_COLUMN_INDEX).text()

            try:
                availabilities = {int(num) for num in availability_text.split() if num.isdigit()}
                should_show_row = not selected_nums or any(num in availabilities for num in selected_nums)
            except ValueError:
                should_show_row = False

            self.drug_table.setRowHidden(row, not should_show_row)

    def show_login_window(self):
        login_window = LoginWindow(self)
        if login_window.exec() == QDialog.Accepted:
            self.authenticated = True
            self.login_button.setVisible(False)  # Скрыть кнопку Войти при успешной аутентификации
            # Показать кнопки Добавить, Изменить, Удалить
            self.add_button.setVisible(True)
            self.edit_button.setVisible(True)
            self.delete_button.setVisible(True)

        else:
            self.authenticated = False

    def get_column_name(self, table, column, record_type):
        if record_type == "drug":
            drug_columns = ["Category by action", "Category by system", "Medicine", "Manufacturer", "Production date", "Availability in pharmacies", "Cost", "Count"]
            return drug_columns[column]
        elif record_type == "pharmacy":
            pharmacy_columns = ["Id", "Name", "Address"]
            return pharmacy_columns[column]
        else:
            return None

    def on_table_selection_changed(self):
        sender_table = self.sender()  # Определение таблицы, вызвавшей событие

        if sender_table == self.drug_table:
            other_table = self.pharmacy_table
        else:
            other_table = self.drug_table

        if sender_table.selectedItems():
            other_table.clearSelection()

    def extract_numbers_from_column(self, table, column_index):
        numbers_set = set()
        for row in range(table.rowCount()):
            cell_text = table.item(row, column_index).text()
            numbers = [int(num) for num in cell_text.split() if num.isdigit()]
            numbers_set.update(numbers)
        print(numbers_set)
        return list(numbers_set)

    def edit_record(self):
        drug_row = self.drug_table.currentRow()
        pharmacy_row = self.pharmacy_table.currentRow()

        if self.drug_table.selectedItems():
            row = drug_row
            if row >= 0:
                dialog = QDialog(self)
                dialog.setWindowTitle("Изменить запись")

                # Получаем данные из выбранной строки таблицы
                current_values = [self.drug_table.item(row, col).text() for col in range(self.drug_table.columnCount())]

                # Создаем поля для ввода данных
                input_widgets = []
                for value in current_values:
                    line_edit = QLineEdit()
                    line_edit.setText(value)
                    input_widgets.append(line_edit)

                layout = QVBoxLayout()
                for widget in input_widgets:
                    layout.addWidget(widget)

                save_button = QPushButton("Сохранить")
                save_button.clicked.connect(lambda: self.save_edited_record(row, input_widgets, self.drug_table, "drug"))

                layout.addWidget(save_button)

                dialog.setLayout(layout)
                dialog.exec()

        elif self.pharmacy_table.selectedItems():
            row = pharmacy_row
            if row >= 0:
                dialog = QDialog(self)
                dialog.setWindowTitle("Изменить запись")

                # Получаем данные из выбранной строки таблицы
                current_values = [self.pharmacy_table.item(row, col).text() for col in range(self.pharmacy_table.columnCount())]

                # Создаем поля для ввода данных
                input_widgets = []
                for value in current_values:
                    line_edit = QLineEdit()
                    line_edit.setText(value)
                    input_widgets.append(line_edit)

                layout = QVBoxLayout()
                for widget in input_widgets:
                    layout.addWidget(widget)

                save_button = QPushButton("Сохранить")
                save_button.clicked.connect(lambda: self.save_edited_record(row, input_widgets, self.pharmacy_table, "pharmacy"))

                layout.addWidget(save_button)

                dialog.setLayout(layout)
                dialog.exec()

    def save_edited_record(self, row, widgets, table, record_type):
        new_values = [widget.text() for widget in widgets]

        updated_row = {}
        for col, value in enumerate(new_values):
            column_name = self.get_column_name(table, col, record_type)
            updated_row[column_name] = value

        # Получение текущих значений строки таблицы
        current_row_values = {}
        for col in range(table.columnCount()):
            column_name = self.get_column_name(table, col, record_type)
            current_row_values[column_name] = table.item(row, col).text()

        # Проверка, изменились ли значения в строке
        if updated_row != current_row_values:
            # Обновляем данные в таблице
            for col, value in enumerate(new_values):
                table.setItem(row, col, QTableWidgetItem(value))

            # Отправляем изменения в базу данных
            updated_data = []
            for row in range(table.rowCount()):
                row_data = {}
                for col in range(table.columnCount()):
                    column_name = self.get_column_name(table, col, record_type)
                    item = table.item(row, col)
                    if item is not None:
                        row_data[column_name] = item.text()
                    else:
                        row_data[column_name] = ''
                updated_data.append(row_data)

            updated_json_data = json.dumps(updated_data)
            data = Get_data()
            if record_type == "drug":
                data.send_updated_drug_data(updated_json_data)
            elif record_type == "pharmacy":
                data.send_updated_pharmacy_data(updated_json_data)

    def add_record(self):
        add_type_dialog = AddRecordTypeDialog(self.drug_table, self.pharmacy_table)
        add_type_dialog.exec()

    def save_added_record(self, widgets, table, record_type):
        row_position = table.rowCount()
        table.insertRow(row_position)

        new_values = [widget.text() for widget in widgets]
        for col, value in enumerate(new_values):
            table.setItem(row_position, col, QTableWidgetItem(value))

        updated_data = []
        for row in range(table.rowCount()):
            row_data = {}
            for col in range(table.columnCount()):
                column_name = self.get_column_name(table, col, record_type)
                item = table.item(row, col)
                if item is not None:
                    row_data[column_name] = item.text()
                else:
                    row_data[column_name] = ''
            updated_data.append(row_data)

        updated_json_data = json.dumps(updated_data)
        data = Get_data()
        if table == self.drug_table:
            data.send_updated_drug_data(updated_json_data)
        elif table == self.pharmacy_table:
            data.send_updated_pharmacy_data(updated_json_data)

    def delete_record(self):
        drug_row = self.drug_table.currentRow()
        pharmacy_row = self.pharmacy_table.currentRow()

        if self.drug_table.selectedItems():
            reply = QMessageBox.question(self, 'Удаление записи',
                                         'Вы уверены, что хотите удалить запись из таблицы лекарств?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.drug_table.removeRow(drug_row)
                self.save_deleted_record(self.drug_table)
        elif self.pharmacy_table.selectedItems():
            reply = QMessageBox.question(self, 'Удаление записи',
                                         'Вы уверены, что хотите удалить запись из таблицы аптек?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.pharmacy_table.removeRow(pharmacy_row)
                self.save_deleted_record(self.pharmacy_table)

    def save_deleted_record(self, table):
        updated_data = []
        for row in range(table.rowCount()):
            row_data = {}
            for col in range(table.columnCount()):
                item = table.item(row, col)
                column_name = self.get_column_name(table, col, "drug" if table == self.drug_table else "pharmacy")
                if item is not None:
                    row_data[column_name] = item.text()
                else:
                    row_data[column_name] = ''
            updated_data.append(row_data)

        updated_json_data = json.dumps(updated_data)
        data = Get_data()
        if table == self.drug_table:
            data.send_updated_drug_data(updated_json_data)
        elif table == self.pharmacy_table:
            data.send_updated_pharmacy_data(updated_json_data)

    def show_detailed_info(self):
        row = self.drug_table.currentRow()
        drug_id = int(self.drug_table.item(row, 0).text())

        # Ваш код для отображения подробной информации о лекарстве по ID
        # Создаем диалоговое окно с информацией о выбранном лекарстве
        dialog = QDialog(self)
        dialog.setWindowTitle("Подробная информация о лекарстве")

        # Здесь вы можете отображать информацию о лекарстве в соответствии с вашими данными
        # Например:
        info_label = QLabel(f"Подробная информация о лекарстве с ID {drug_id}")
        layout = QVBoxLayout()
        layout.addWidget(info_label)
        dialog.setLayout(layout)

        dialog.exec()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.setWindowIcon(QIcon(r'icons\plus_icon.ico'))  # Установка иконки окна
    window.showMaximized()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()


