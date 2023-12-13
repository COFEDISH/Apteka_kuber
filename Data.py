import socket
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QMessageBox
subd_address = ('37.193.53.6', 31543)

token = "7HbN3P#m9e6@kT2d123dNEar"
token_admin = "R#f7GhT9@Lp2$y5BqZx!0*D"

class Get_data:
    def get_data_Pharmacy(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(subd_address)
                s.sendall(f"{token} --file Pharmacies.json --query 'GSON get'".encode()) # ???????? ?????? ?? ??????? (????? ??????????? ?? ??????, ??????? ?????? ? ??????????)
                print("Message sent successfully.")
                datas_subd = s.recv(61440)
                data_sub = datas_subd.decode()
                print(data_sub)
                return data_sub
            except ConnectionRefusedError:
                print("Connection to the server failed.")


    def get_data_Medicine(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(subd_address)
                s.sendall(f"{token} --file Medicine.json --query 'GSON get'".encode()) # ???????? ?????? ?? ??????? (????? ??????????? ?? ??????, ??????? ?????? ? ??????????)
                print("Message sent successfully.")
                datas_subd = s.recv(61440)
                data_sub = datas_subd.decode()
                print(data_sub)
                return data_sub
            except ConnectionRefusedError:
                print("Connection to the server failed.")

    def send_updated_drug_data(self, data):
        print(type(data))
        print("Data for send to SUBD: ", data)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(subd_address)
                s.sendall(f"{token_admin} --file Medicine.json --query 'GSON save {data}'".encode())
                print("Message sent successfully.")
                datas_subd = s.recv(61440)
                data_sub = datas_subd.decode()
                print(data_sub)
            except ConnectionRefusedError:
                print("Connection to the server failed.")

    def send_updated_pharmacy_data(self, data):
        print(type(data))
        print("Data for send to SUBD: ", data)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(subd_address)
                s.sendall(f"{token_admin} --file Pharmacies.json --query 'GSON save {data}'".encode())
                print("Message sent successfully.")
                datas_subd = s.recv(61440)
                data_sub = datas_subd.decode()
                print(data_sub)
            except ConnectionRefusedError:
                print("Connection to the server failed.")

    def get_password(self, login):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(subd_address)
                s.sendall(f"{token} --file passwords.data --query 'HGET Apteka_passwords {login}'".encode())
                print("Message sent successfully.")
                datas_subd = s.recv(61440)
                data_sub = datas_subd.decode()
                print(data_sub)
                return data_sub
            except ConnectionRefusedError:
                print("Connection to the server failed.")

class pharmacy():
    def __init__(self):
        self.data = Get_data.get_data_Pharmacy()

class medicine:
    def __init__(self):
        self.data = Get_data.get_data_Medicine()


class LoginWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Авторизация")

        layout = QVBoxLayout()

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Логин")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        login_button = QPushButton("Войти")
        login_button.clicked.connect(self.login)
        layout.addWidget(login_button)

        self.setLayout(layout)

    def login(self):
        # Проверка логина и пароля
        username = self.username_input.text()
        password = self.password_input.text()
        print(password)
        check_password = Get_data.get_password(self, username)

        if password == check_password:
            self.accept()  # Вход выполнен успешно
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")
