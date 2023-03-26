import json
import os, sys
import typing
import urllib.parse
from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QListView,
    QMenuBar,
    QMenu,
    QPushButton,
    QDialog,
    QLabel,
    QVBoxLayout,
    QStatusBar,
    QAbstractItemView, QFileIconProvider, QSystemTrayIcon

)
from PyQt6.QtGui import QIcon, QPixmap, QStandardItemModel, QStandardItem, QDrag
from PyQt6.QtCore import Qt, QFileInfo, QMimeData, QModelIndex, QByteArray


def getTitleFromExeName(exefilepath):
    return os.path.splitext(os.path.basename(exefilepath))[0].capitalize()


class LauncherItem:
    def __init__(self, path, **kwargs):
        self.path = path
        self.title = kwargs.get('title', getTitleFromExeName(path))
        self.small_icon_idx = kwargs.get('small_icon_idx', -1)
        self.normal_icon_idx = kwargs.get('normal_icon_idx', -1)
        self.iconfile = kwargs.get('iconfile', self.path)

    def __str__(self):
        return f"{self.title} => {self.path}"

class ListViewModelDragNdrop(QStandardItemModel):

    def __init__(self, holder,parent=None) -> None:
        #parent = parent[1:]
        super().__init__(parent)
        self.holder = holder

    # def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlag:
    #     default_args = QStringListModel.flags(index)
    #     if index.isValid():
    #         return super().flags(index) | QtCore.Qt.ItemFlag.ItemIsDragEnabled | default_args
    #     return super().flags(index) | default_args

    def mimeData(self, indexes: typing.Iterable[QtCore.QModelIndex]) -> QtCore.QMimeData:
        itemTitleDragged = indexes[0].data()
        print('mimeData',indexes[0].data())
        titles = [item.title for item in self.holder.launcheritemslist]
        idx = titles.index(itemTitleDragged)
        if idx >= 0:
            _path = self.holder.launcheritemslist[idx].path
            mimedata = QMimeData()
            mimedata.setUrls([QtCore.QUrl.fromLocalFile(_path)])
            return mimedata
        else:
            return super().mimeData(indexes)

    def canDropMimeData(self, data: 'QMimeData', action: Qt.DropAction, row: int, column: int,
                        parent: QModelIndex) -> bool:
        print('canDropMimeData',data,action,row,column,parent)
        return True
        #return super().canDropMimeData(data, action, row, column, parent)

    def dropMimeData(self, data: QtCore.QMimeData, action: QtCore.Qt.DropAction, row: int, column: int,
                     parent: QtCore.QModelIndex) -> bool:
        print('+++++++dropMimeData',data.text(),action,row,column,parent.row())
        dropped_idx = parent.row()
        paths=[item.path for item in self.holder.launcheritemslist]
        parsedfilepath = urllib.parse.urlparse(data.text())
        file=QFileInfo(parsedfilepath.path[1:])
        iconprovider = QFileIconProvider()
        if file.filePath() in paths:
            current_item_idx = paths.index(file.filePath())
            current_launcher_item = self.holder.launcheritemslist[current_item_idx]
            icon = iconprovider.icon(QFileInfo(current_launcher_item.iconfile))
            self.moveRow(parent,current_item_idx,parent,dropped_idx)
            self.insertRow(dropped_idx, QStandardItem(
                icon, current_launcher_item.title))
            # self.removeRow(current_item_idx)
        else:
            new_launcher_item = LauncherItem(file.filePath())
            self.holder.launcheritemslist.append(new_launcher_item)       
            icon = iconprovider.icon(QFileInfo(new_launcher_item.iconfile))
            self.appendRow(QStandardItem(icon,new_launcher_item.title))
        return True

        #return super().dropMimeData(data, action, row, column, parent)

    def supportedDragActions(self) -> Qt.DropAction:
        print("supportedDragActions")
        return Qt.DropAction.MoveAction
        #return super().supportedDragActions()

class LauncherListView(QListView):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.parent = parent
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
       # self.setDragDropOverwriteMode(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.parent.itemBeingDragged = event.mimeData().urls()[0].toLocalFile()
        else:       
            super().dragEnterEvent(event)
        print("dragEnterEvent",event)
        #event.accept()

    def dragMoveEvent(self, event):
        super().dragMoveEvent(event)
        print("dragMoveEvent",event)
        #event.accept()

    def dropEvent(self, event):
        # if event.mimeData().hasUrls():
        #     links = []
        #     for url in event.mimeData().urls():
        #         links.append(str(url.toLocalFile()))
        #     #self.parent.emit(QtCore.SIGNAL("dropped"), links)
        #     event.acceptProposedAction()
        # #else:
        super().dropEvent(event)
        print("dropEvent",event)
        event.accept()
    
    def dragLeaveEvent(self,event):
        super().dragLeaveEvent(event)
        print("dragLeaveEvent",event)
        if self.parent.itemBeingDragged:
            paths = [item.path for item in self.parent.launcheritemslist]
            idx = paths.index(self.parent.itemBeingDragged)
            if idx:
                print("Removing",self.parent.itemBeingDragged,"from list")
                self.parent.listModel.removeRow(idx)
                self.parent.launcheritemslist.pop(idx)
        # event.accept()

    def startDrag(self, supportedActions: Qt.DropAction) -> None:
        super().startDrag(supportedActions)
        print("startDrag",supportedActions)


class AboutWindow(QDialog):
    def __init__(self,parent):
        super().__init__(parent)
        self.initializeUI()

    def initializeUI(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setGeometry(200, 100, 200, 100)
        self.logo = QLabel(self)
        self.logo.setPixmap(QPixmap("app-menu-launcher.ico"))
        self.label = QLabel(
            """<br>
        QTLauncher v0.1<br>
        by <A href='mailto:digfish@digfish.org'>digfish@digfish.org</A><br>
        <A href='https://me.digfish.org'>https://me.digfish.org</A><br>
        """,
            self,
            
        )
        self.label.setTextFormat(Qt.TextFormat.RichText)
        self.layout.addWidget(self.logo)
        self.layout.addWidget(self.label)
        self.setWindowTitle("About QTLauncher")
        self.button = QPushButton("OK", self)
        self.layout.addWidget(self.button)
        self.button.clicked.connect(self.close)
        self.show()
        self.exec()


class QtLauncher(QWidget):
    def __init__(self):
        """Constructor for Empty Window Class"""
        super().__init__()
        self.initializeUI()

    def initializeUI(self):
        """Set up the application's GUI."""
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setGeometry(200, 100, 300, 400)

        self.menubar = QMenuBar(self)
        file_menu = QMenu("File", self.menubar)
        help_menu = QMenu("Help", self.menubar)
        view_menu = QMenu("View", self.menubar)
        view_menu.addAction("Icon", self.refreshview)
        view_menu.addAction("List", self.refreshview)
        file_menu.addAction("Exit", self.close)
        help_menu.addAction("About", self.show_about_window)
        self.menubar.addMenu(file_menu)
        self.menubar.addMenu(view_menu)
        self.menubar.addMenu(help_menu)

        self.layout.addWidget(self.menubar)

        #self.launcheritemslist = [LauncherItem("c:/windows/explorer.exe"),LauncherItem("c:/windows/notepad.exe")]
        self.launcheritemslist = []
        self.loadJson()
        self.listModel = ListViewModelDragNdrop(self)
        iconprovider = QFileIconProvider()
        for item in self.launcheritemslist:
            icon = iconprovider.icon(QFileInfo(item.iconfile))
            self.listModel.appendRow(QStandardItem(icon,item.title))
        self.listview = LauncherListView(self)
        self.listview.setAcceptDrops(True)
        self.listview.setDragEnabled(True)
        self.listview.setViewMode(QListView.ViewMode.IconMode)
        self.listview.setGeometry(0, 0, 300, 400)
        self.listview.setModel(self.listModel)
        self.listview.setDropIndicatorShown(True)
        self.listview.doubleClicked.connect(self.onListItemDoubleClicked)
        self.listview.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers) # disable item editing
        self.layout.addWidget(self.listview)
        self.statusbar = QStatusBar(self)
        self.statusbar.showMessage(f"{self.listModel.rowCount()} items loaded")
        self.layout.addWidget(self.statusbar)
        #        QMenuItem("New",file_menu)
        # self.menubar.addMenu("File")
        pdims = self.geometry()
        self.systray = QSystemTrayIcon(self)
        self.systray_menu = QMenu(self)
        self.fill_systray_menu()
        self.systray_menu.addAction("Show", self.show)
        self.systray_menu.addAction("Exit", self.close)
        self.systray.setToolTip(sys.argv[0])
        self.systray.setIcon(QIcon("app-menu-launcher.ico"))
        self.systray.setContextMenu(self.systray_menu)
        self.systray.show()
        # self.listview.setGeometry(pdims.x(), pdims.y(), pdims.width(),pdims.height())
        self.setWindowTitle("QTLauncher")
        self.setWindowIcon(QIcon("app-menu-launcher.ico"))
        self.setAcceptDrops(True)
        # self.drag = QDrag(self)
        # self.dragData = QMimeData();
        # self.dragData.setText("test")
        # self.drag.setMimeData(self.dragData)
        # self.drag.source()
        # self.drag.target()
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.show()

    def fill_systray_menu(self):
        print("fill_systray_menu")
        print(self.sender())
        iconprovider = QFileIconProvider()
        for item in self.launcheritemslist:
            icon = iconprovider.icon(QFileInfo(item.iconfile))
            self.systray_menu.addAction(icon,item.title, self.systrayClicked)
        self.systray_menu.addSeparator()

    def systrayClicked(self):
        print(self.sender().text())
        title = self.sender().text()
        idx = [item.title for item in self.launcheritemslist].index(title)
        self.launch(self.launcheritemslist[idx].path)

    def loadJson(self):
        with open('launcher.json') as json_file:
            data = json.load(json_file)
            for item in data:
                self.launcheritemslist.append(LauncherItem(**data[item]))

    def storeJson(self):
        item_dict= {}
        numberRows = self.listModel.rowCount()
        titleslist = [item.title for item in self.launcheritemslist]
        print("Number Rows: ", numberRows)
        for i in range(numberRows): #iterates through the listview datamodel to keep the order in it
            row_text_title = self.listModel.item(i).text()
            idx = titleslist.index(row_text_title)
            print(row_text_title, idx)
            launcheritem = self.launcheritemslist[idx]
            item_dict[row_text_title] = launcheritem.__dict__
        with open('launcher.json', 'w') as outfile:
            json.dump(item_dict, outfile, indent=4)

    def closeEvent(self, event):
        print("closeEvent")
        self.storeJson()
        event.accept()


    def refreshview(self):
        print("refreshview")
        action = self.sender()
        if action.text() == "Icon":
            self.listview.setViewMode(QListView.ViewMode.IconMode)
        else:
            self.listview.setViewMode(QListView.ViewMode.ListMode)

    def onListItemDoubleClicked(self, index):
        cmdline = self.launcheritemslist[index.row()].path
        self.launch(cmdline)

    def launch(self,cmdline):
        print(cmdline)
        os.system(cmdline)

    def show_about_window(self):
        about_window = AboutWindow(self)


def main():
    app = QApplication(sys.argv)
    window = QtLauncher()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
