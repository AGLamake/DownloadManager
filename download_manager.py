import datetime
import glob
import os
import random
import shutil
import sys  # sys нужен для передачи argv в QApplication
from urllib import request
from urllib.parse import urlparse
from winreg import *

import requests
from PyQt5 import QtWidgets
import download  # Это наш конвертированный файл дизайна


class DownloadManager(QtWidgets.QMainWindow, download.Ui_Window):
    def __init__(self):
        # Это здесь нужно для доступа к переменным, методам
        # и т.д. в файле design.pyz
        super().__init__()

        self.setupUi(self)  # Это нужно для инициализации нашего дизайна

        self.downloadFolder = os.getcwd() + '\\downloads\\' # Задаём дефолтную папку внутри структуры приложения

        with OpenKey(HKEY_CURRENT_USER, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders') as key:
            self.downloadFolder = QueryValueEx(key, '{374DE290-123F-4565-9164-39C4925E467B}')[0]

        if not os.path.exists(self.downloadFolder):
            os.mkdir(self.downloadFolder) # Создаём её, если она не существует

        self.label_DownloadFolder.setText(f'{self.downloadFolder}')
        self.btn_OpenFolder.setEnabled(True)

        self.fill_download_table()

        self.action_PlaceToDownload.triggered.connect(self.browse_folder)

        self.btn_Download.clicked.connect(self.download_file)

        self.table_DownloadList.clicked.connect(self.select_file)
        self.table_DownloadList.itemSelectionChanged.connect(self.select_file)

        self.btn_Open.clicked.connect(self.open_file)
        self.btn_Delete.clicked.connect(self.delete_file)

        self.btn_OpenFolder.clicked.connect(self.open_download_folder)

        # Чистка лейблов
        self.text_File.setText("")
        self.text_Download.setText("")
        self.text_Size.setText("")
        self.text_CreateDate.setText("")

    def open_download_folder(self):
        """ Открыть выбранную для сохранения файлов папку """
        os.system(f'start {os.path.realpath(self.downloadFolder)}')

    def fill_download_table(self):
        self.table_DownloadList.clear()
        for filename in os.listdir(self.downloadFolder):
            f = os.path.join(self.downloadFolder, filename)
            if os.path.isfile(f):
                self.add_file_to_list(filename=f.split('\\')[-1])

    def browse_folder(self):

        self.downloadFolder = QtWidgets.QFileDialog.getExistingDirectory(self, "Выберите папку") + "\\"
        # открыть диалог выбора директории и установить значение переменной
        # равной пути к выбранной директории

        self.label_DownloadFolder.setText(f'{self.downloadFolder}')
        self.fill_download_table()
        self.select_file()

    def add_file_to_list(self, filename: str = f'{random.randint(1, 999999)}.UnknownFile'):
        item = QtWidgets.QListWidgetItem()
        try:
            item.setText(f'{filename}')
            self.table_DownloadList.addItem(item)
        except Exception as e:
            print(str(e))

    def select_file(self):
        try:
            self.text_File.setText(f'{self.table_DownloadList.selectedItems()[0].text()}')
            self.btn_Open.setEnabled(True)
            self.btn_Delete.setEnabled(True)

            dir_state = {0: 'b', 1: 'Kb', 2: 'Mb', 3: 'Gb', 4: 'Tb'}
            state = 0
            size = os.stat(self.downloadFolder + "\\" + self.table_DownloadList.selectedItems()[0].text()).st_size / 8
            while size / 1024 < 100:
                size /= 1024

            self.text_Size.setText(f'{size} {dir_state[state]}')
            self.text_CreateDate.setText(str(datetime.datetime.fromtimestamp(os.path.getctime(self.downloadFolder + "\\" + self.table_DownloadList.selectedItems()[0].text()))))
        except Exception as e:
            print(str(e))
            self.label_SelectedFile.setText('Файл: ')
            self.btn_Open.setEnabled(False)
            self.btn_Delete.setEnabled(False)

    def download_file(self):
        try:
            if self.line_URL.text() == '':
                return
            url = self.line_URL.text()
            ran = random.randint(1, 999999)

            if url.find('/'):
                filename = urlparse(url)
                if os.path.basename(filename.path).find('.') != -1:
                    filename = os.path.basename(filename.path)
                else:
                    filename = request.urlopen(request.Request(url)).info().get_filename()
                    filename = str(bytes(filename, 'iso-8859-1').decode('utf-8'))
                valid_chars = "-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789йцукенгшщзхъэждлорпавыфячсмитьбюЙЦУКЕНГШЩЗХЪЭЖДЛОРПАВЫФЯЧСМИТЬБЮ"
                filename = ''.join(c for c in filename if c in valid_chars)
            else:
                filename = str(ran) + '.downloadedFile'

            if not os.path.isdir(self.downloadFolder):
                os.mkdir(self.downloadFolder)

            self.add_file_to_list(filename[:filename.rfind('.')] + '.DownloadManager')
            self.table_DownloadList.clearSelection()

            CurrentRow = self.table_DownloadList.count() - 1
            self.table_DownloadList.setCurrentRow(CurrentRow)

            with open(self.downloadFolder + filename[:filename.rfind('.')] + '.DownloadManager', "wb") as f:
                response = requests.get(url, stream=True)
                total_length = response.headers.get('content-length')

                if total_length is None:  # no content length header
                    f.write(response.content)
                else:
                    dl = 0
                    total_length = int(total_length)
                    for data in response.iter_content(chunk_size=4096):
                        dl += len(data)
                        f.write(data)
                        done = int(100 * dl / total_length)
                        self.text_Download.setText(f"{done}%")
                        sys.stdout.write("\r[%s%s]" % ('=' * done, ' ' * (100 - done)))
                        sys.stdout.flush()

                        self.progressBar.setValue(done)

            for file in glob.glob(self.downloadFolder + "*.DownloadManager"):
                shutil.copy(file, self.downloadFolder + filename)
                os.remove(self.downloadFolder + filename[:filename.rfind('.')] + '.DownloadManager')

            print(f'\n{filename} - done')
        except Exception as e:
            print(str(e.with_traceback()))
        finally:
            self.fill_download_table()

    def open_file(self):
        os.system('"' + self.downloadFolder + "\\" + self.table_DownloadList.selectedItems()[0].text() + '"')

    def delete_file(self):
        if os.path.exists(f'{self.downloadFolder}{self.table_DownloadList.selectedItems()[0].text()}'):
            os.remove(f'{self.downloadFolder}{self.table_DownloadList.selectedItems()[0].text()}')

            self.fill_download_table()
            self.select_file()


def main():
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = DownloadManager()  # Создаём объект класса ExampleApp
    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение


if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    main()  # то запускаем функцию main()
