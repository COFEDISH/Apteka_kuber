import json
from PySide6.QtWidgets import  QTableWidgetItem, QDialog, QVBoxLayout, QPushButton, QComboBox, QLabel, QLineEdit

from Data import Get_data

class AddRecordTypeDialog(QDialog):
    def __init__(self, table_drug, table_pharmacy):
        parent = None
        super().__init__(parent)
        self.setWindowTitle("Выберите тип записи")

        self.layout = QVBoxLayout()

        self.label = QLabel("Выберите тип записи:")
        self.layout.addWidget(self.label)

        self.record_type = QComboBox()
        self.record_type.addItem("Лекарство")
        self.record_type.addItem("Аптека")
        self.layout.addWidget(self.record_type)

        self.confirm_button = QPushButton("Подтвердить")
        self.confirm_button.clicked.connect(lambda: self.open_record_form(table_drug, table_pharmacy))
        self.layout.addWidget(self.confirm_button)

        self.setLayout(self.layout)

    def open_record_form(self, table_drug, table_pharmacy):
        selected_type = self.record_type.currentText()
        if selected_type == "Лекарство":
            record_form = DrugForm(table=table_drug)
            record_form.exec()
        elif selected_type == "Аптека":
            record_form = PharmacyForm(parent=self, table=table_pharmacy)
            record_form.exec()


class DrugForm(QDialog):
    def __init__(self, parent = None, table=None):
        super().__init__(parent)
        self.setWindowTitle("Форма для добавления лекарства")
        self.table = table  # Сохраняем ссылку на таблицу

        self.layout = QVBoxLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Название лекарства")
        self.layout.addWidget(self.name_input)

        self.manufacturer_input = QLineEdit()
        self.manufacturer_input.setPlaceholderText("Производитель")
        self.layout.addWidget(self.manufacturer_input)

        self.production_date_input = QLineEdit()
        self.production_date_input.setPlaceholderText("Дата производства")
        self.layout.addWidget(self.production_date_input)

        self.availability_input = QLineEdit()
        self.availability_input.setPlaceholderText("Доступность в аптеках (через пробел!)")
        self.layout.addWidget(self.availability_input)

        self.cost_input = QLineEdit()
        self.cost_input.setPlaceholderText("Цена")
        self.layout.addWidget(self.cost_input)

        self.count_input = QLineEdit()
        self.count_input.setPlaceholderText("Количество")
        self.layout.addWidget(self.count_input)

        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self.save_drug)
        self.layout.addWidget(self.save_button)

        self.setLayout(self.layout)

    def get_column_name(self, table, column, record_type):
        if record_type == "drug":
            drug_columns = ["id", "Medicine", "Manufacturer", "Production date" ,"Availability in pharmacies", "Cost", "Count"]
            return drug_columns[column]
        elif record_type == "pharmacy":
            pharmacy_columns = ["Id", "Name", "Address"]
            return pharmacy_columns[column]
        else:
            return None

    def save_drug(self):
        drug_name = self.name_input.text()
        manufacturer = self.manufacturer_input.text()
        production_date = self.production_date_input.text()
        availability = self.availability_input.text()
        cost = int(self.cost_input.text())
        count = int(self.count_input.text())

        # Создать новую запись лекарства
        new_drug_data = {
            "id": self.table.rowCount() + 1,  # Новый ID для новой записи
            "Medicine": drug_name,
            "Manufacturer": manufacturer,
            "Production date": production_date,
            "Availability in pharmacies": availability,
            "Cost": cost,
            "Count": count
        }

        # Добавить новую запись в таблицу
        if self.table:
            self.table.setRowCount(self.table.rowCount() + 1)
            for col, value in enumerate(new_drug_data.values()):
                self.table.setItem(self.table.rowCount() - 1, col, QTableWidgetItem(str(value)))

            # Отправляем данные в базу данных
            updated_data = []
            for row in range(self.table.rowCount()):
                row_data = {}
                for col in range(self.table.columnCount()):
                    column_name = self.get_column_name(self.table, col, "drug")
                    item = self.table.item(row, col)
                    if item is not None:
                        row_data[column_name] = item.text()
                    else:
                        row_data[column_name] = ''
                updated_data.append(row_data)
            print("updated_data", updated_data)
            data = Get_data()
            updated_json_data = json.dumps(updated_data)
            print("updated_json_data", updated_json_data)
            data.send_updated_drug_data(updated_json_data)

            # Закрываем окно формы
            self.close()


class PharmacyForm(QDialog):
    def __init__(self, parent=None, table=None):
        super().__init__(parent)
        self.table = table
        self.setWindowTitle("Форма для добавления аптеки")

        self.layout = QVBoxLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Название аптеки")
        self.layout.addWidget(self.name_input)

        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Адрес аптеки")
        self.layout.addWidget(self.address_input)

        # Добавьте остальные поля для аптеки

        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self.save_pharmacy)
        self.layout.addWidget(self.save_button)

        self.setLayout(self.layout)

    def get_column_name(self, table, column, record_type):
        if record_type == "drug":
            drug_columns = ["id", "Medicine", "Manufacturer", "Production date" ,"Availability in pharmacies", "Cost", "Count"]
            return drug_columns[column]
        elif record_type == "pharmacy":
            pharmacy_columns = ["Id", "Name", "Address"]
            return pharmacy_columns[column]
        else:
            return None

    def save_pharmacy(self):
        pharmacy_name = self.name_input.text()
        pharmacy_address = self.address_input.text()

        # Создать новую запись аптеки
        new_pharmacy_data = {
            "Id": self.table.rowCount() + 1,
            "Name": pharmacy_name,
            "Address": pharmacy_address
        }

        # Добавить новую запись в таблицу
        if self.table:
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            for col, value in enumerate(new_pharmacy_data.values()):
                self.table.setItem(row_position, col, QTableWidgetItem(str(value)))

            # Отправляем данные в базу данных
            updated_data = []
            for row in range(self.table.rowCount()):
                row_data = {}
                for col in range(self.table.columnCount()):
                    column_name = self.get_column_name(self.table, col, "pharmacy")
                    item = self.table.item(row, col)
                    if item is not None:
                        row_data[column_name] = item.text()
                    else:
                        row_data[column_name] = ''
                updated_data.append(row_data)

            data = Get_data()
            updated_json_data = json.dumps(updated_data)
            data.send_updated_pharmacy_data(updated_json_data)

            # Закрываем окно формы
            self.close()