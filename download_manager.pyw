import datetime
import glob
import os
import random
import requests
import shutil
import sys
import time
from urllib import request
from urllib.parse import urlparse
from winreg import OpenKey, HKEY_CURRENT_USER, QueryValueEx

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot, QThread

import download  # Это наш конвертированный файл дизайна


# Основной класс, наследуется от PyQT5 - графического фреймворка.
class DownloadManager(QtWidgets.QMainWindow, download.Ui_Window):

    # Инициализация, определение основных переменных класса
    def __init__(self):
        # Это здесь нужно для доступа к переменным, методам
        # и т.д. в файле download.py
        super().__init__()

        self.setupUi(self)  # Это нужно для инициализации нашего дизайна

        self.downloadFolder = os.getcwd() + '\\downloads\\'  # Задаём дефолтную папку внутри структуры приложения

        with OpenKey(HKEY_CURRENT_USER, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders') as key:
            self.downloadFolder = QueryValueEx(key, '{374DE290-123F-4565-9164-39C4925E467B}')[0]
            # Ищем папку с загрузками указанную в компьютере по умолчанию в списке регистров

        if not os.path.exists(self.downloadFolder):
            os.mkdir(self.downloadFolder)  # Создаём её, если она не существует

        self.label_DownloadFolder.setText(f'{self.downloadFolder}')  # Указываем на рабочем окне папку, в которую
        # будут сохраняться файлы
        self.btn_OpenFolder.setEnabled(True)  # Активируем кнопку, позволяющую открыть папку, в которую будут
        # скачиваться файлы

        self.fill_download_table()  # Проверяем загрузочную папку и обновляем список файлов в таблице окна приложения

        self.action_PlaceToDownload.triggered.connect(self.browse_folder)  # Ловим событие нажатия на кнопку
        # "Изменить место сохранения"

        self.btn_Download.clicked.connect(self.download_file)  # Ловим событие нажатия на кнопку "Скачать"

        self.table_DownloadList.clicked.connect(self.select_file)  # Ловим событие нажатия на кнопку "Изменить место
        # сохранения"
        self.table_DownloadList.itemSelectionChanged.connect(self.select_file)  # Ловим событие выбора файла в таблице

        self.btn_Open.clicked.connect(self.open_file)  # Ловим событие нажатия на кнопку "Открыть"
        self.btn_Delete.clicked.connect(self.delete_file)  # Ловим событие нажатия на кнопку "Удалить"

        self.btn_OpenFolder.clicked.connect(self.open_download_folder)  # Ловим событие нажатия на кнопку "Открыть
        # папку"

        self.clear_labels()  # Чистим вспомогательные тексты в главном окне.

    def clear_labels(self):
        """ Чистка лейблов """

        self.text_File.setText("")
        self.text_Download.setText("")
        self.text_Size.setText("")
        self.text_CreateDate.setText("")

    def open_download_folder(self):
        """ Открыть выбранную для сохранения файлов папку """

        os.system(f'start {os.path.realpath(self.downloadFolder)}')

    def fill_download_table(self):
        """ Заполнение таблицы с файлами """

        self.table_DownloadList.clear()
        for filename in os.listdir(self.downloadFolder):
            f = os.path.join(self.downloadFolder.replace('/', '\\'), filename)
            if os.path.isfile(f):
                self.add_file_to_list(filename=f.split('\\')[-1])

    def browse_folder(self):
        """ Выбрать папку для сохранения файлов """

        self.downloadFolder = QtWidgets.QFileDialog.getExistingDirectory(self, "Выберите папку") + "/"
        # открыть диалог выбора директории и установить значение переменной
        # равной пути к выбранной директории

        self.label_DownloadFolder.setText(f'{self.downloadFolder}')
        self.fill_download_table()

        self.clear_labels()

    def add_file_to_list(self, filename: str = f'{random.randint(1, 999999)}.UnknownFile'):
        """ Добавить файл в таблицу в главном окне

        :param filename: Название файла (По умолчанию выставляется имя из случайного числа в диапазоне от 1 до 999999)
        """

        item = QtWidgets.QListWidgetItem()  # Создаём элемент таблицы
        try:
            item.setText(f'{filename}')  # Выставляем атрибут текста ранее созданному элементу таблицы
            self.table_DownloadList.addItem(item)  # И добавляем этот элемент таблицы в саму таблицу
        except Exception as e:
            print(str(e.with_traceback()))

    def select_file(self):
        """ Обновление текста и кнопок во время выбора файла в таблице главного окна """

        try:
            self.text_File.setText(f'{self.table_DownloadList.selectedItems()[0].text()}')  # Выставляем имя
            # выбранного файла в главное окно
            self.btn_Open.setEnabled(True)  # Активируем кнопку, позволяющую открыть файл
            self.btn_Delete.setEnabled(True)  # Активируем кнопку, позволяющую удалить файл

            dir_state = {0: 'бит', 1: 'Кб', 2: 'Мб', 3: 'Гб', 4: 'Тб'}  # Вспомогательный словарь для красивого
            # вывода размера файла
            state = 0  # Вспомогательная переменная, хранящая в себе порядок объёма файла
            size = os.stat(self.downloadFolder + "\\" + self.table_DownloadList.selectedItems()[0].text()).st_size
            # Выясняем объём файла в байтах
            if size == 0.0:
                return
            while size >= 1024:
                # Выясняем порядок размера файла, а так же приводим его к красивому виду
                size /= 1024
                state += 1

            self.text_Size.setText(f'{round(size, 2)} {dir_state[state]}')  # Выводим размер файла в главное окно
            self.text_CreateDate.setText(str(datetime.datetime.fromtimestamp(os.path.getctime(
                self.downloadFolder + "\\" + self.table_DownloadList.selectedItems()[0].text())).strftime(
                '%d.%m.%Y           %H:%M:%S')))  # Выясняем дату создания файла и в красивом виде выводим в главное
            # окно

        except Exception as e:
            print(str(e.with_traceback()))
            # При ошибке просто откатываем все действия
            self.text_File.setText('')  # Выставляем пустое имя файла
            self.btn_Open.setEnabled(False)  # Блокируем кнопку "Открыть"
            self.btn_Delete.setEnabled(False)  # Блокируем кнопку "Удалить"
            self.clear_labels()  # Удаляем информацию о выбранном файле с главного экрана

    def download_file(self):
        """ Скачать файл.

         • Проверяет ссылку на валидность, а затем пытается получить из неё данные и записать их файл."""
        try:
            if self.line_URL.text() == '':
                return  # Если ссылка не была введена, функция просто прекратит своё выполнение
            url = self.line_URL.text()  # Получаем ссылку из элемента главного экрана в отдельную переменную
            ran = random.randint(1, 999999)  # Генерируем случайно число на случай, если не сможем получить имя файла
            # из запроса

            if url.find('/'):  # Проверяем ссылку на наличие в ней имени
                filename = urlparse(url)  # Парсим ссылку
                if os.path.basename(filename.path).find('.') != -1:  # Если имя файла хранится в самой ссылке
                    filename = os.path.basename(filename.path)  # Записываем его в переменную
                else:  # Если имени файла нет в ссылке
                    filename = request.urlopen(request.Request(url)).info().get_filename()  # Пытаемся её получить из
                    # полученного ответа
                    filename = str(bytes(filename, 'iso-8859-1').decode('utf-8'))  # Далее конвертируем ответ формата
                    # iso-8859-1 в utf-8 для корректного отображения
                valid_chars = "-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" \
                              "йцукенгшщзхъэждлорпавыфячсмитьбюЙЦУКЕНГШЩЗХЪЭЖДЛОРПАВЫФЯЧСМИТЬБЮ "
                filename = ''.join(c for c in filename if c in valid_chars)  # Фильтруем запрещённые символы в
                # названии файла
            else:
                filename = str(ran) + '.downloadedFile'  # Если не получилось получить имя файла из ссылки,
                # то выставляем вместо него случайное число

            if not os.path.isdir(self.downloadFolder):
                os.mkdir(self.downloadFolder)
                # На всякий случай проверяем, существует ли до сих пор папка, в которую будет сохраняться файл

            runner = JobRunner(url, filename, self)  # Создаём объект класса, в котором и будет проходить процесс
            # загрузки файла
            runner.start()  # Запускаем процесс в отдельном потоке

            self.btn_Resume.clicked.connect(runner.resume)  # Выдаём кнопке "Продолжить" привязку к функции процесса
            # загрузки файла
            self.btn_Pause.clicked.connect(runner.pause)  # Выдаём кнопке "Пауза" привязку к функции процесса
            # загрузки файла

        except Exception as e:
            print(str(e.with_traceback()))
        finally:
            self.fill_download_table()
            # В любом случае (удачная загрузка или ошибка) мы должны обновить таблицу с файлами в главном окне
            # приложения

    def open_file(self):
        """ Открыть выбранный файл """

        os.system('"' + self.downloadFolder + "\\" + self.table_DownloadList.selectedItems()[0].text() + '"')
        # В командную строку отправляем строку формата "имя_файла"
        # По итогу открывается нужный файл программой по умолчанию установленной в системе

    def delete_file(self):
        """ Удалить выбранный файл """

        if os.path.exists(f'{self.downloadFolder}{self.table_DownloadList.selectedItems()[0].text()}'):
            # Если такой файл существует
            os.remove(f'{self.downloadFolder}{self.table_DownloadList.selectedItems()[0].text()}')
            # Просто удаляем его

            self.fill_download_table()
            self.select_file()
            # И обновляем таблицы


# Класс, в котором описана функция загрузки файла. Объект класса работает в отдельном потоке.
class JobRunner(QThread):

    # Инициализируем переменные
    def __init__(self, url: str = None, filename: str = None, obj: DownloadManager = None):
        super().__init__()

        self.is_paused = False  # По умолчанию загрузка должна быть активна, поэтому пауза = False
        self.is_killed = False  # С жизнью потока та же история, он должен изначально жить

        if url is None:
            return

        self.url = url
        self.filename = filename
        self.downloadFolder = obj.downloadFolder
        self.obj = obj

        self.obj.btn_Pause.setEnabled(True)  # Активируем кнопку "Пауза" в главном окне
        self.obj.btn_Resume.setEnabled(True)  # Активируем кнопку "Продолжить" в главном окне

    @pyqtSlot()
    def run(self):
        """ Основная рабочая функция потока.

         • Загрузка документа по URL"""
        try:
            self.obj.add_file_to_list(self.filename[:self.filename.rfind('.')] + '.DownloadManager')
            # Добавляем на главный экран временный загрузочный файл
            self.obj.table_DownloadList.clearSelection()
            # Из таблицы с файлами убираем все выделения

            current_row = self.obj.table_DownloadList.count() - 1
            # Выясняем последнюю строку в таблице с файлами
            self.obj.table_DownloadList.setCurrentRow(current_row)
            # Выделяем строку с новым временным файлом

            with open(self.downloadFolder + self.filename[:self.filename.rfind('.')] + '.DownloadManager', "wb") as f:
                # Создаём файл с временным именем и открываем его для записи
                response = requests.get(self.url, stream=True)
                # Получаем ответ по ссылке
                total_length = response.headers.get('content-length')
                # В хэдерах ответа находим полный размер ответа
                if total_length is None:
                    f.write(response.content)
                else:
                    dl = 0  # Вспомогательная переменная для подсчёта размера файла
                    total_length = int(total_length)
                    for data in response.iter_content(chunk_size=4096):
                        # Считываем данные блоками размером 4096
                        while self.is_paused:
                            # Если процесс поставили на паузу, выгоняем поток в сон
                            time.sleep(0)

                        if self.is_killed:
                            break
                            # Если процесс убили, прекращаем работу потока

                        dl += len(data)  # Обновляем размер полученных данных
                        f.write(data)  # Записываем полученные данные в файл
                        done = int(100 * dl / total_length)  # Выясняем процент загрузки документа

                        self.obj.progressBar.setValue(done)  # Выставляем процент загрузки в индикатор на главном экране
                        self.obj.text_Download.setText(f"{done}%") # Выводим процент загрузки текстом на главный экран

            for file in glob.glob(self.downloadFolder + "*.DownloadManager"):
                # Пробегаемся по загрузочной папке
                shutil.copy(file, self.downloadFolder + self.filename)
                # Копируем все файлы с расширением .DownloadManager в нужный формат
                os.remove(self.downloadFolder + self.filename[:self.filename.rfind('.')] + '.DownloadManager')
                # Удаляем лишние файлы с расшиернием .DownloadManager

            self.obj.fill_download_table()
            # Обновляем таблицу с файлами в главном окне
        except Exception as e:
            print(str(e.with_traceback()))
        finally:
            self.obj.btn_Resume.setEnabled(False)
            self.obj.btn_Pause.setEnabled(False)
            # По итогу мы должны заблокировать кнопки "Продолжить" и "Пауза" в главном окне

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False

    def kill(self):
        self.is_killed = True


def main():
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = DownloadManager()  # Создаём объект класса ExampleApp
    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение


if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    main()  # то запускаем функцию main()
