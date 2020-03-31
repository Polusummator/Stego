"""
This program is an implementation of the LSB steganographic method in the Python programming language using the PyQt5 GUI
github: https://github.com/Polusummator/Stego


"""
import hashlib
import os
import random
import shutil
import sys
import tempfile
import threading
import requests

from PIL import Image
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from cryptography.fernet import Fernet
from pathlib import Path


def thread(my_func):
    """
    Starting function in the separate thread
    """
    def wrapper(*args, **kwargs):
        my_thread = threading.Thread(target=my_func, args=args, kwargs=kwargs)
        my_thread.start()
    return wrapper


class Steganography(QMainWindow):
    """
    The main class of application
    """
    my_signal1 = pyqtSignal(list, name='my_signal1')  # stego
    my_signal2 = pyqtSignal(str, name='my_signal2')   # unstego
    my_signal3 = pyqtSignal(list, name='my_signal3')  # PRNG
    my_signal4 = pyqtSignal(name='my_signal4')        # show_rgb

    def __init__(self):
        """
        Initialization of main window
        """
        super().__init__()
        self.showImage = False
        self.showBits = False
        self.initUI()

    def center(self):
        """
        Centering a window on the screen
        """
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def initUI(self):
        """
        Creating GUI
        """
        self.setFixedSize(569, 450)
        self.center()
        self.setWindowTitle('Steganography')

        # ------------------------Icon-----------------------------

        img = r'https://images.squarespace-cdn.com/content/v1/5981e865f14aa16941337125/1507228368642-3M1N4Z4KO42PGDZTMMWH/ke17ZwdGBToddI8pDm48kGDpvalPb1SqHoCn1hwN0Y57gQa3H78H3Y0txjaiv_0fDoOvxcdMmMKkDsyUqMSsMWxHk725yiiHCCLfrh8O1z5QHyNOqBUUEtDDsRWrJLTmx-YtV7KdJhhcFMxgH7DNwVWsr4BytTuzU0mdZNjZkC7ehjA8nxqmKGxR1QtMJl5J/discover.png'
        p = requests.get(img)
        some_icon_path = r".\SoMe_ApPlIcAtIoN_IcOn.png"
        out = open(some_icon_path, 'wb')
        out.write(p.content)
        self.setWindowIcon(QIcon(some_icon_path))
        out.close()
        if os.path.isfile(some_icon_path):
            os.remove(some_icon_path)

        self.tabwidget = TabWidget(self)
        self.setCentralWidget(self.tabwidget)

        self.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)

        self.bind()

        self.createWait()

        self.show()

    def createWait(self):
        """
        Creating wait-widget
        """
        self.lab = QLabel('Waiting', self)
        self.lab.setStyleSheet("""
                               font: Arial;
                               font-size: 25px;
                               color: grey;
                               """)
        self.lab.adjustSize()
        self.H()

        self.lab.move(self.rect().center() - QRect(QPoint(), self.lab.sizeHint()).center())

    def H(self):
        """
        Hide/show label "Waiting"
        """
        if self.lab.isHidden():
            self.lab.show()
        else:
            self.lab.hide()

    def bind(self):
        """
        Creating button functions
        """

        # ------------------QDialogButtonBox-----------------------

        self.tabwidget.tab1.dialog.rejected.connect(self.close)
        self.tabwidget.tab2.dialog.rejected.connect(self.close)
        self.tabwidget.tab1.dialog.accepted.connect(self.Start_e)
        self.tabwidget.tab2.dialog.accepted.connect(self.Start_d)

        # -------------Choose-file/directory-buttons---------------

        self.tabwidget.group1.buttonClicked.connect(self.getFileName)
        self.tabwidget.group2.buttonClicked.connect(self.getDirectory)

        # ----------------------CheckBoxes-------------------------

        self.tabwidget.tab1.groupbox2.check1.stateChanged.connect(self.checkbox1)
        self.tabwidget.tab1.groupbox2.check2.stateChanged.connect(self.checkbox2)

        # ------------------------Signals--------------------------

        self.my_signal1.connect(self.mySignalHandler1, Qt.QueuedConnection)
        self.my_signal2.connect(self.mySignalHandler2, Qt.QueuedConnection)
        self.my_signal3.connect(self.mySignalHandler3, Qt.QueuedConnection)
        self.my_signal4.connect(self.mySignalHandler4, Qt.QueuedConnection)

    def mySignalHandler1(self, img):
        """
        Receives a signal from the function stego and launches the function start_e_continue
        :param img: [image] or ['error']
        """
        if img == ['error']:
            self.error()
        else:
            self.start_e_continue(img[0])

    def mySignalHandler2(self, txt):
        """
        Receives a signal from the function unstego and launches the function start_d_continue
        :param txt: text or 'error'
        """
        if txt == 'error':
            self.error()
        else:
            self.start_d_continue(txt)

    def mySignalHandler3(self, prng):
        """
        Receives a signal from the function PRNG and launches the function main_continue
        :param prng: list of pseudo-random numbers or ['error']
        """
        if prng == ['error']:
            self.error()
        else:
            self.main_continue(prng)

    def mySignalHandler4(self):
        """
        Receives a signal from the function show_rgb and closes the image-file
        """
        self.closeContainer()

    def checkbox1(self, state):
        """
        Processing a check2 (self.tabwidget.tab1.groupbox2.check1) change
        :param state: the state of checkbox
        """
        if state == Qt.Checked:
            self.showImage = True
        else:
            self.showImage = False

    def checkbox2(self, state):
        """
        Processing a check2 (self.tabwidget.tab1.groupbox2.check2) change
        :param state: the state of checkbox
        """
        if state == Qt.Checked:
            self.showBits = True
        else:
            self.showBits = False

    def ProgressE(self, num):
        """
        Changing the progress bar value (encryption)
        :param num: number of pixel
        """
        if num >= self.len_prng - 1:
            self.tabwidget.tab1.pbar.setValue(100)
            return
        if not num:
            self.tabwidget.tab1.pbar.setValue(0)
            return

        if int(num // (self.len_prng / 100)) > self.tabwidget.tab1.pbar.value():
            self.tabwidget.tab1.pbar.setValue(min(100, int(num // (self.len_prng / 100))))

    def ProgressD(self, num):
        """
        Changing the progress bar value (decrypting)
        :param num: number of number in the list of pseudo-random numbers
        """
        if num >= self.len_prng - 1:
            self.tabwidget.tab2.pbar.setValue(100)
            return
        if not num:
            self.tabwidget.tab2.pbar.setValue(0)
            return

        if int(num // (self.len_prng / 100)) > self.tabwidget.tab2.pbar.value():
            self.tabwidget.tab2.pbar.setValue(min(100, int(num // (self.len_prng / 100))))

    @thread
    def stego(self, width, height, image, prng, text, signal):
        """
        Function for embedding a message in an image
        :param width: picture width
        :param height: picture height
        :param image: image-container
        :param prng: list of pseudo-random pixels
        :param text: message (list of bits)
        :return: filled container
        """
        try:
            text_i = 0
            self.H()
            self.len_prng = len(prng)
            for i in prng:
                i1, j1 = (i + image.size[1] - 1) // image.size[1] - 1, (image.size[1] - 1, i % image.size[1])[
                    bool(i % image.size[1])]
                pixel = image.getpixel((i1, j1))
                R, G, B = pixel
                cur = text[text_i]
                if len(cur) == 6:
                    R, G, B = cur[:2], cur[2:4], cur[4:]
                    r = self.change_bits(self.change_bits(pixel[0], 1, int(R[0])), 0, int(R[1]))
                    g = self.change_bits(self.change_bits(pixel[1], 1, int(G[0])), 0, int(G[1]))
                    b = self.change_bits(self.change_bits(pixel[2], 1, int(B[0])), 0, int(B[1]))
                    image.putpixel((i1, j1), (r, g, b))
                elif len(cur) == 4:
                    R, G = cur[:2], cur[2:]
                    r = self.change_bits(self.change_bits(pixel[0], 1, int(R[0])), 0, int(R[1]))
                    g = self.change_bits(self.change_bits(pixel[1], 1, int(G[0])), 0, int(G[1]))
                    image.putpixel((i1, j1), (r, g, pixel[2]))
                elif len(cur) == 2:
                    R = cur
                    r = self.change_bits(self.change_bits(pixel[0], 1, int(R[0])), 0, int(R[1]))
                    image.putpixel((i1, j1), (r, pixel[1], pixel[2]))
                self.ProgressE(text_i)
                text_i += 1
            signal.emit([image])
            return None
        except:
            signal.emit(['error'])

    @thread
    def unstego(self, image, prng, signal):
        """
        Function for extracting a message from an image
        :param image: filled container
        :param prng: list of pseudo-random pixels
        :return: message
        """
        try:
            self.len_prng = len(prng)
            self.H()
            text = ''
            prng_i = 0
            for i in prng:
                i1, j1 = (i + image.size[1] - 1) // image.size[1] - 1, (image.size[1] - 1, i % image.size[1])[bool(i % image.size[1])]
                pixel = image.getpixel((i1, j1))
                R, G, B = pixel
                text += str(self.get_bit(R, 1)) + str(self.get_bit(R, 0)) + str(self.get_bit(G, 1)) + str(self.get_bit(G, 0)) + str(self.get_bit(B, 1)) + str(self.get_bit(B, 0))
                self.ProgressD(prng_i)
                prng_i += 1
            text_group = self.group(text, 8)[0]
            text_end = ''
            for i in text_group:
                text_end += chr(int(i, 2))
            if not text_end[-1].isprintable():
                signal.emit(text_end[:-1])
            else:
                signal.emit(text_end)
            return None
        except:
            signal.emit('error')

    def group(self, string, str_len):
        """
        Function for splitting a string into blocks of a certain length
        :param string: string
        :param str_len: length of one block
        :return: list of blocks and presence of an incomplete block
        """
        l_group = []
        isMod = bool(len(string) % str_len)
        for i in range((len(string) + str_len - 1) // str_len):
            if i * str_len + str_len < len(string):
                l_group.append(string[i * str_len:i * str_len + str_len])
            else:
                l_group.append(string[i * str_len:len(string)])
        return l_group, isMod

    @thread
    def PRNG(self, *args):
        """
        The generator of pseudo-random pixels
        :param args: (width - picture width, height - picture height, number - number of pixels) or (img - filled container, ekey - key to retrieve the message)
        :return: list of pseudo-random pixels
        """
        try:
            if len(args) == 4:
                width, height, number, signal = args
                field = width * height
                rand_seed = random.randint(1, 4000000)
                just_1 = random.randint(1, 1024)
                just_2 = hashlib.sha256(str(just_1).encode('utf-8')).hexdigest()
                key = self.Encrypt(just_1, rand_seed, number, just_2)
                self.publicKey = key[0]
                self.privateKey = key[1]
                z = True
            else:
                img, ekey, signal = args
                width, height = img.size[0], img.size[1]
                t, k = ekey.split()
                key_l = self.Decrypt(t, k)
                rand_seed, number = key_l
                field = width * height
                z = False
            all_list = list(range(0, field - 1))
            random.seed(rand_seed)
            random.shuffle(all_list)
            PRNG_list = all_list[:number]
            if z:
                signal.emit(['e'] + PRNG_list)
            else:
                signal.emit(['d'] + PRNG_list)
            return None
        except:
            signal.emit(['error'])

    def change_bits(self, num, index, to):
        """
        Changing one bit in a number
        :param num: number
        :param index: bit number
        :param to: new value of the bit
        :return: number
        """
        if not to:
            return ~(1 << index) & num
        return (1 << index) | num

    def get_bit(self, num, index):
        """
        Getting the value of a number bit
        :param num: number
        :param index: bit number
        :return: bit
        """
        return int(bool(num & (1 << index)))

    def Encrypt(self, *args):
        """
        Creating a key
        :param args: a1, a7 - parameters for the test, a2-a6 - parameters for generator
        :return: encrypted key and key for decrypting
        """
        a1, a2, a3, a4, = args
        s = '{} {} {} {}'.format(a1, a2, a3, a4)
        c_key = Fernet.generate_key()
        cipher = Fernet(c_key)
        txt = bytes(s, 'utf-8')
        e_txt = cipher.encrypt(txt)
        return e_txt.decode('utf-8'), c_key.decode('utf-8')

    def Decrypt(self, *args):
        """
        Decrypting the key
        :param args: e_txt - encrypted key, c_key - key for decrypting
        :return: parameters for generator
        """
        e_txt, c_key = args
        e_txt = bytes(e_txt, 'utf-8')
        c_key = bytes(c_key, 'utf-8')
        cipher = Fernet(c_key)
        d_txt = cipher.decrypt(e_txt)
        txt = d_txt.decode('utf-8')
        txt_list = txt.split()
        z = True
        if len(txt_list) == 4:
            for i in range(3):
                if not txt_list[i].isdigit():
                    z = False
                    break
            if z:
                test_hash = hashlib.sha256(txt_list[0].encode('utf-8')).hexdigest()
                z = (False, True)[test_hash == txt_list[3]]
        else:
            z = False
        if z:
            txt_list = list(map(int, txt_list[1:3]))
            return txt_list

    def to_textb(self, text):
        """
        Converting text to binary and dividing it into blocks
        :param text: message
        :return: list of blocks in binary format
        """
        text_b = ''
        for i in text:
            text_b += bin(ord(i))[2:].rjust(8, '0')
        Group, isMod = self.group(text_b, 6)
        return Group

    @thread
    def show_rgb(self, img):
        """
        Demonstration of least significant bits of pixels
        :param img: image
        """
        self.inactive(False)
        self.H()
        w, h = img.size[0], img.size[1]
        for i in range(w):
            for j in range(h):
                pixel = img.getpixel((i, j))
                R, G, B = pixel
                r, g, b = 0, 0, 0
                if self.get_bit(R, 0):
                    r = 1
                if self.get_bit(G, 0):
                    g = 1
                if self.get_bit(B, 0):
                    b = 1
                img.putpixel((i, j), (255 * r, 255 * g, 255 * b))
        img.show()
        self.inactive(True)
        self.H()
        self.closeContainer()

    def main(self, mode, a1, a2):
        """
        Starting the algorithm
        :param mode: encrypt/decrypt ('e' or 'd')
        :param a1: image-container
        :param a2: text (mode 'e') or key (mode 'd')
        :return: filled container (mode 'e') or message (mode 'd')
        """
        img = a1
        self.H()
        if mode == 'e':
            self.mode = 'e'
            data = img.size[0] * img.size[1]
            self.size = data
            text = a2
            Group = self.to_textb(text)
            self.image = img
            self.Group = Group
            self.PRNG(img.size[0], img.size[1], len(Group), self.my_signal3)
        else:
            self.mode = 'd'
            key = a2
            self.image = img
            self.PRNG(img, key, self.my_signal3)

    def main_continue(self, prng):
        """
        Continuation of function main (starting the algorithm)
        :param prng: list of pseudo-random numbers (the first element is 'e' or 'd')
        """
        if prng[0] == 'e':
            image = self.image
            self.stego(image.size[1], image.size[0], image, prng[1:], self.Group, self.my_signal1)
        else:
            self.unstego(self.image, prng[1:], self.my_signal2)

    def error(self):
        """
        Error notification
        """
        QMessageBox.warning(self, 'Error', 'An error occurred. Check that the files you entered are correct.')
        if not self.lab.isHidden():
            self.H()
        if self.mode == 'e':
            if self.copy:
                self.container.close()
                lol = self.copyPath
                os.remove(self.copyPath)
                self.copy = False
        self.inactive(True)
        self.tabwidget.tab1.pbar.setValue(0)
        self.tabwidget.tab2.pbar.setValue(0)

    def Start_e(self):
        """
        Checking the correctness of the entered data and running the algorithm of encryption
        """
        edit1 = self.tabwidget.tab1.groupbox1.edit1.text()
        edit2 = self.tabwidget.tab1.groupbox1.edit2.text()
        edit3 = self.tabwidget.tab1.groupbox3.edit1.text()
        if os.path.isfile(edit1) and os.path.isfile(edit2) and os.path.isdir(edit3):
            correct1 = edit1[-4:] in ['.png', 'jpeg', '.bmp', '.jpg']
            correct2 = edit2[-3:] == 'txt'
            if correct1 and correct2:
                copy = False
                if edit1[-3:] != 'bmp':
                    copy = True
                    copyPath, fileName = self.convertFile(edit1)
                    self.fileName = fileName
                    self.copyPath = copyPath
                    container = Image.open(copyPath)
                else:
                    container = Image.open(edit1)
                message = open(edit2).read()
                message = message.encode('ascii', 'ignore').decode('ascii')
                self.inactive(False)
                self.copy = copy
                self.container = container
                self.edit3 = edit3
                self.edit1 = edit1
                self.main('e', container, message)
            else:
                QMessageBox.warning(self, 'Error', 'The file is not in the correct format')
        else:
            QMessageBox.warning(self, 'Error', 'File or directory not found')

    def start_e_continue(self, image_stego):
        """
        Continuation of function Start_e (writing the results to files)
        :param image_stego: filled container
        """
        self.inactive(True)
        save = self.edit3
        pathSaveDir = save + '/Steganography'
        if not os.path.isdir(pathSaveDir):
            os.mkdir(pathSaveDir)
        if not self.copy:
            self.fileName = self.file_name(self.edit1)
        image_stego.save(pathSaveDir + '/' + self.fileName)
        if self.showImage:
            image_stego.show()
        if self.copy:
            self.copy = False
            os.remove(self.copyPath)
        public_file = open(pathSaveDir + '/PublicKey.txt', 'w')
        private_file = open(pathSaveDir + '/PrivateKey.txt', 'w')
        public_file.write(self.publicKey)
        private_file.write(self.privateKey)
        public_file.close()
        private_file.close()
        if self.showBits:
            self.show_rgb(image_stego)
        else:
            self.container.close()

    def closeContainer(self):
        """
        Closing the image-file
        """
        self.container.close()

    def Start_d(self):
        """
        Checking the correctness of the entered data and running the algorithm of decryption
        """
        edit1 = self.tabwidget.tab2.groupbox1.edit1.text()
        edit2 = self.tabwidget.tab2.groupbox2.edit1.text()
        edit3 = self.tabwidget.tab2.groupbox2.edit2.text()
        edit4 = self.tabwidget.tab2.groupbox3.edit1.text()
        if os.path.isfile(edit1) and os.path.isfile(edit2) and os.path.isfile(edit3) and os.path.isdir(edit4):
            correct1 = edit1[-3:] == 'bmp'
            correct2 = edit2[-3:] == 'txt'
            correct3 = edit3[-3:] == 'txt'
            if correct1 and correct2 and correct3:
                container = Image.open(edit1)
                pub_key = open(edit2).read()
                pri_key = open(edit3).read()
                self.edit4 = edit4
                self.container = container
                self.inactive(False)
                self.main('d', container, pub_key.strip() + ' ' + pri_key.strip())
            else:
                QMessageBox.warning(self, 'Error', 'The file is not in the correct format')
        else:
            QMessageBox.warning(self, 'Error', 'File or directory not found')

    def start_d_continue(self, message):
        """
        Continuation of function Start_d (writing the results to files)
        :param message: message from container
        """
        self.inactive(True)
        save = self.edit4
        pathSaveDir = save + '/Steganography'
        if not os.path.isdir(pathSaveDir):
            os.mkdir(pathSaveDir)
        fileName = '/StegoText.txt'
        self.container.close()
        message_file = open(pathSaveDir + fileName, 'w', encoding='ascii')
        message = message.encode('ascii', 'ignore').decode('ascii')
        message_file.write(message)
        message_file.close()

    def getDirectory(self, btn):
        """
        Directory selection
        :param btn: button-object
        """
        dirlist = QFileDialog.getExistingDirectory(self, "Choose a directory", ".")
        if btn == self.tabwidget.tab1.groupbox3.but1:
            self.tabwidget.tab1.groupbox3.edit1.setText(dirlist)
        elif btn == self.tabwidget.tab2.groupbox3.but1:
            self.tabwidget.tab2.groupbox3.edit1.setText(dirlist)

    def getFileName(self, btn):
        """
        File selection
        :param btn: button-object
        """
        if btn == self.tabwidget.tab1.groupbox1.but1:
            filename = QFileDialog.getOpenFileName(self, "Choose a file", ".", "BMP Files(*.bmp);;PNG Files(*.png);;JPEG Files(*.jpeg);;JPG Files(*.jpg)")[0]
            self.tabwidget.tab1.groupbox1.edit1.setText(filename)
        elif btn == self.tabwidget.tab2.groupbox1.but1:
            filename = QFileDialog.getOpenFileName(self, "Choose a file", ".", "BMP Files(*.bmp)")[0]
            self.tabwidget.tab2.groupbox1.edit1.setText(filename)
        elif btn == self.tabwidget.tab1.groupbox1.but2:
            filename = QFileDialog.getOpenFileName(self, "Choose a file", ".", "Text Files (*.txt);")[0]
            self.tabwidget.tab1.groupbox1.edit2.setText(filename)
        elif btn == self.tabwidget.tab2.groupbox2.but1:
            filename = QFileDialog.getOpenFileName(self, "Choose a file", ".", "Text Files (*.txt);")[0]
            self.tabwidget.tab2.groupbox2.edit1.setText(filename)
        elif btn == self.tabwidget.tab2.groupbox2.but2:
            filename = QFileDialog.getOpenFileName(self, "Choose a file", ".", "Text Files (*.txt);")[0]
            self.tabwidget.tab2.groupbox2.edit2.setText(filename)

    def closeEvent(self, event):
        """
        Message about closing a window
        """
        reply = QMessageBox.question(self, 'Quit', "Are you sure to quit?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def convertFile(self, path):
        """
        Converting a file to the desired format
        :param path: file path
        :return: path to the modifies copy of the file, name of the file
        """
        temp_path, fileName = self.create_temporary_copy(path)
        point_l = temp_path.split('.')
        point_l.pop()
        path_without = '.'.join(map(str, point_l))
        new_path = path_without + '.bmp'
        p = Path(temp_path)
        p.rename(new_path)
        fileName = fileName.split('.')[0] + '.bmp'
        return new_path, fileName

    def create_temporary_copy(self, path):
        """
        Creating temporary copy of the file
        :param path: file path
        :return: path to copy, name of the file
        """
        temp_dir = tempfile.gettempdir()
        fileName = self.file_name(path)
        temp_path = os.path.join(temp_dir, fileName)
        shutil.copy2(path, temp_path)
        return temp_path, fileName

    def file_name(self, path):
        """
        Finding the file name from its path
        :param path: file path
        :return: file name
        """
        fileName = ''
        for i in path[::-1]:
            if i in ['/', '\\']:
                break
            else:
                fileName += i
        fileName = fileName[::-1]
        return fileName

    def inactive(self, mode):
        """
        Making widgets active/inactive
        :param mode: True/False
        """
        self.tabwidget.inactive(mode)


class TabWidget(QWidget):
    """
    Creating a TabWidget with 2 tabs
    """
    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()

        self.tabs.addTab(self.tab1, 'Encryption')
        self.tabs.addTab(self.tab2, 'Decryption')

        # ------------------------tab1-----------------------------

        self.tab1.layout = QVBoxLayout(self)

        self.tab1.groupbox1 = Group1(self)
        self.tab1.groupbox2 = Group2(self)
        self.tab1.groupbox3 = Group3(self)

        self.tab1.layout.addWidget(self.tab1.groupbox1)
        self.tab1.layout.addWidget(self.tab1.groupbox2)
        self.tab1.layout.addWidget(self.tab1.groupbox3)

        self.tab1.hlayout = QHBoxLayout(self)
        self.tab1.pbar = QProgressBar(self)
        self.tab1.pbar.setFixedWidth(280)

        self.tab1.dialog = QDialogButtonBox(self)
        self.tab1.dialog.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)

        self.tab1.hlayout.addWidget(self.tab1.pbar)
        self.tab1.hlayout.addStretch()
        self.tab1.hlayout.addWidget(self.tab1.dialog)

        self.tab1.layout.addStretch()
        self.tab1.layout.addLayout(self.tab1.hlayout)

        self.tab1.setLayout(self.tab1.layout)

        # ------------------------tab2-----------------------------

        self.tab2.layout = QVBoxLayout(self)

        self.tab2.groupbox1 = Group3(self)
        self.tab2.groupbox1.setTitle('Container')
        self.tab2.groupbox1.lab1.setText('Path to container:')
        self.tab2.groupbox1.but1.setText('Choose a file')

        self.tab2.groupbox2 = Group1(self)
        self.tab2.groupbox2.setTitle('Keys')
        self.tab2.groupbox2.lab1.setText('Path to public key:')
        self.tab2.groupbox2.lab2.setText('Path to private key:')

        self.tab2.groupbox3 = Group3(self)
        self.tab2.groupbox3.lab1.setText('Path to save message:')

        self.tab2.hlayout = QHBoxLayout(self)
        self.tab2.pbar = QProgressBar(self)
        self.tab2.pbar.setFixedWidth(280)

        self.tab2.dialog = QDialogButtonBox(self)
        self.tab2.dialog.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)

        self.tab2.hlayout.addWidget(self.tab2.pbar)
        self.tab2.hlayout.addStretch()
        self.tab2.hlayout.addWidget(self.tab2.dialog)

        self.tab2.layout.addWidget(self.tab2.groupbox1)
        self.tab2.layout.addWidget(self.tab2.groupbox2)
        self.tab2.layout.addWidget(self.tab2.groupbox3)
        self.tab2.layout.addStretch()
        self.tab2.layout.addLayout(self.tab2.hlayout)

        self.tab2.setLayout(self.tab2.layout)

        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

        # -------------------ButtonGroups--------------------------

        self.group1 = QButtonGroup()
        self.group1.setExclusive(True)
        self.group1.addButton(self.tab1.groupbox1.but1)
        self.group1.addButton(self.tab1.groupbox1.but2)
        self.group1.addButton(self.tab2.groupbox1.but1)
        self.group1.addButton(self.tab2.groupbox2.but1)
        self.group1.addButton(self.tab2.groupbox2.but2)

        self.group2 = QButtonGroup()
        self.group2.setExclusive(True)
        self.group2.addButton(self.tab1.groupbox3.but1)
        self.group2.addButton(self.tab2.groupbox3.but1)

    def inactive(self, mode):

        # --------------------GroupBoxes---------------------------

        self.tab1.groupbox1.inactive(mode)
        self.tab1.groupbox2.inactive(mode)
        self.tab1.groupbox3.inactive(mode)
        self.tab2.groupbox1.inactive(mode)
        self.tab2.groupbox2.inactive(mode)
        self.tab2.groupbox3.inactive(mode)

        # ----------Tabs and widgets without groupboxes------------

        self.tab1.dialog.setEnabled(mode)
        self.tab2.dialog.setEnabled(mode)
        self.tab1.setEnabled(mode)
        self.tab2.setEnabled(mode)


class Group1(QGroupBox):
    """
    Creating a GroupBox widget
    """
    def __init__(self, parent):
        super(QGroupBox, self).__init__(parent)

        self.layout = QVBoxLayout(self)

        # ---------------------HLayout1----------------------------

        self.hlayout1 = QHBoxLayout(self)
        self.lab1 = QLabel('Path to container:')
        self.font = QFont()
        self.font.setPointSize(9)
        self.lab1.setFont(self.font)

        self.hlayout1.addWidget(self.lab1)
        self.hlayout1.addStretch()

        # ---------------------HLayout2----------------------------

        self.hlayout2 = QHBoxLayout(self)
        self.edit1 = QLineEdit()
        self.but1 = QPushButton('Choose a file')

        self.hlayout2.addWidget(self.edit1)
        self.hlayout2.addWidget(self.but1)

        # ---------------------HLayout3----------------------------

        self.hlayout3 = QHBoxLayout(self)
        self.lab2 = QLabel('Path to message:')
        self.lab2.setFont(self.font)

        self.hlayout3.addWidget(self.lab2)
        self.hlayout3.addStretch()

        # ---------------------HLayout4----------------------------

        self.hlayout4 = QHBoxLayout(self)
        self.edit2 = QLineEdit()
        self.but2 = QPushButton('Choose a file')

        self.hlayout4.addWidget(self.edit2)
        self.hlayout4.addWidget(self.but2)

        self.setTitle('Container and message')

        self.layout.addLayout(self.hlayout1)
        self.layout.addLayout(self.hlayout2)
        self.layout.addLayout(self.hlayout3)
        self.layout.addLayout(self.hlayout4)

        self.setLayout(self.layout)

    def inactive(self, mode):
        """
        Making widgets active/inactive
        :param mode: True/False
        """
        self.edit1.setEnabled(mode)
        self.but1.setEnabled(mode)
        self.edit2.setEnabled(mode)
        self.but2.setEnabled(mode)


class Group2(QGroupBox):
    """
    Creating a GroupBox widget
    """
    def __init__(self, parent):
        super(QGroupBox, self).__init__(parent)

        self.layout = QVBoxLayout(self)

        self.check1 = QCheckBox('Show image', self)
        self.check2 = QCheckBox('Show least significant bits', self)

        self.layout.addWidget(self.check1)
        self.layout.addWidget(self.check2)

        self.setTitle('Options')

        self.setLayout(self.layout)

    def inactive(self, mode):
        """
        Making widgets active/inactive
        :param mode: True/False
        """
        self.check1.setEnabled(mode)
        self.check2.setEnabled(mode)


class Group3(QGroupBox):
    """
    Creating a GroupBox widget
    """
    def __init__(self, parent):
        super(QGroupBox, self).__init__(parent)

        self.layout = QVBoxLayout(self)

        self.hlayout1 = QHBoxLayout(self)
        self.lab1 = QLabel('Path to save container and keys:')
        self.font = QFont()
        self.font.setPointSize(9)
        self.lab1.setFont(self.font)

        self.hlayout1.addWidget(self.lab1)
        self.hlayout1.addStretch()

        self.hlayout2 = QHBoxLayout(self)
        self.edit1 = QLineEdit()
        self.but1 = QPushButton('Choose a directory')

        self.hlayout2.addWidget(self.edit1)
        self.hlayout2.addWidget(self.but1)

        self.setTitle('Saving')

        self.layout.addLayout(self.hlayout1)
        self.layout.addLayout(self.hlayout2)

        self.setLayout(self.layout)

    def inactive(self, mode):
        """
        Making widgets active/inactive
        :param mode: True/False
        """
        self.edit1.setEnabled(mode)
        self.but1.setEnabled(mode)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    stego = Steganography()
    sys.exit(app.exec_())
