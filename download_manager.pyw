import datetime, glob, os, random, shutil, sys, time, requests
from urllib import request
from urllib.parse import urlparse
from winreg import *
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot, QThread

import download  # Это наш конвертированный файл дизайна


class DownloadManager(QtWidgets.QMainWindow, download.Ui_Window):
    def __init__(self):
        # Это здесь нужно для доступа к переменным, методам
        # и т.д. в файле design.pyz
        super().__init__()

        self.setupUi(self)  # Это нужно для инициализации нашего дизайна

        self.downloadFolder = os.getcwd() + '\\downloads\\'  # Задаём дефолтную папку внутри структуры приложения

        with OpenKey(HKEY_CURRENT_USER, 'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders') as key:
            self.downloadFolder = QueryValueEx(key, '{374DE290-123F-4565-9164-39C4925E467B}')[0]

        if not os.path.exists(self.downloadFolder):
            os.mkdir(self.downloadFolder)  # Создаём её, если она не существует

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

        self.clear_labels()

    def clear_labels(self):
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
            f = os.path.join(self.downloadFolder.replace('/', '\\'), filename)
            if os.path.isfile(f):
                self.add_file_to_list(filename=f.split('\\')[-1])

    def browse_folder(self):

        self.downloadFolder = QtWidgets.QFileDialog.getExistingDirectory(self, "Выберите папку") + "/"
        # открыть диалог выбора директории и установить значение переменной
        # равной пути к выбранной директории

        self.label_DownloadFolder.setText(f'{self.downloadFolder}')
        self.fill_download_table()

        self.clear_labels()

    def add_file_to_list(self, filename: str = f'{random.randint(1, 999999)}.UnknownFile'):
        item = QtWidgets.QListWidgetItem()
        try:
            item.setText(f'{filename}')
            self.table_DownloadList.addItem(item)
        except Exception as e:
            print(str(e.with_traceback()))

    def select_file(self):
        try:
            self.text_File.setText(f'{self.table_DownloadList.selectedItems()[0].text()}')
            self.btn_Open.setEnabled(True)
            self.btn_Delete.setEnabled(True)

            dir_state = {0: 'бит', 1: 'Кб', 2: 'Мб', 3: 'Гб', 4: 'Тб'}
            state = 0
            size = os.stat(self.downloadFolder + "\\" + self.table_DownloadList.selectedItems()[0].text()).st_size
            if size == 0.0:
                return
            while size >= 1024:
                size /= 1024
                state += 1

            self.text_Size.setText(f'{round(size, 2)} {dir_state[state]}')
            self.text_CreateDate.setText(str(datetime.datetime.fromtimestamp(os.path.getctime(
                self.downloadFolder + "\\" + self.table_DownloadList.selectedItems()[0].text())).strftime(
                '%d.%m.%Y           %H:%M:%S')))

        except Exception as e:
            print(str(e.with_traceback()))
            self.label_SelectedFile.setText('Файл: ')
            self.btn_Open.setEnabled(False)
            self.btn_Delete.setEnabled(False)

            self.clear_labels()

    def download_file(self):
        try:
            if self.line_URL.text() == '':
                return
            url = self.line_URL.text()
            ran = random.randint(1, 999999)

            if url.find('/'):
                print(2.1)
                filename = urlparse(url)
                if os.path.basename(filename.path).find('.') != -1:
                    print(2.2)
                    filename = os.path.basename(filename.path)
                else:
                    print(2.3)
                    filename = request.urlopen(request.Request(url)).info().get_filename()
                    print(2.35)
                    filename = str(bytes(filename, 'iso-8859-1').decode('utf-8'))
                valid_chars = "-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" \
                              "йцукенгшщзхъэждлорпавыфячсмитьбюЙЦУКЕНГШЩЗХЪЭЖДЛОРПАВЫФЯЧСМИТЬБЮ "
                filename = ''.join(c for c in filename if c in valid_chars)
            else:
                filename = str(ran) + '.downloadedFile'

            if not os.path.isdir(self.downloadFolder):
                os.mkdir(self.downloadFolder)

            runner = JobRunner(url, filename, self)
            runner.start()

            self.btn_Resume.clicked.connect(runner.resume)
            self.btn_Pause.clicked.connect(runner.pause)

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


class JobRunner(QThread):
    def __init__(self, url: str = None, filename: str = None, obj: DownloadManager = None):
        super().__init__()

        self.is_paused = False
        self.is_killed = False

        if url is None:
            return

        self.url = url
        self.filename = filename
        self.downloadFolder = obj.downloadFolder
        self.obj = obj

        self.obj.btn_Pause.setEnabled(True)
        self.obj.btn_Resume.setEnabled(True)

    @pyqtSlot()
    def run(self):
        try:
            print('start download')
            self.obj.add_file_to_list(self.filename[:self.filename.rfind('.')] + '.DownloadManager')
            self.obj.table_DownloadList.clearSelection()

            current_row = self.obj.table_DownloadList.count() - 1
            self.obj.table_DownloadList.setCurrentRow(current_row)

            with open(self.downloadFolder + self.filename[:self.filename.rfind('.')] + '.DownloadManager', "wb") as f:
                print(1)
                response = requests.get(self.url, stream=True)
                print(f'response: {response}')
                total_length = response.headers.get('content-length')
                print(f'total_length: {total_length}')
                if total_length is None:  # no content length header
                    f.write(response.content)
                    print('null total lenght')
                else:
                    print(2)
                    dl = 0
                    total_length = int(total_length)
                    print(3)
                    for data in response.iter_content(chunk_size=4096):
                        while self.is_paused:
                            time.sleep(0)

                        if self.is_killed:
                            break

                        dl += len(data)
                        f.write(data)
                        done = int(100 * dl / total_length)

                        self.obj.progressBar.setValue(done)
                        self.obj.text_Download.setText(f"{done}%")
                        sys.stdout.write("\r[%s%s]" % ('=' * done, ' ' * (100 - done)))
                        sys.stdout.flush()

            for file in glob.glob(self.downloadFolder + "*.DownloadManager"):
                shutil.copy(file, self.downloadFolder + self.filename)
                os.remove(self.downloadFolder + self.filename[:self.filename.rfind('.')] + '.DownloadManager')

            self.obj.fill_download_table()

            print(f'\n{self.filename} - done')
        except Exception as e:
            print(str(e.with_traceback()))
        finally:
            self.obj.btn_Resume.setEnabled(False)
            self.obj.btn_Pause.setEnabled(False)

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
