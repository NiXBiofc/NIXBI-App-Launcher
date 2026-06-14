import os, sys, json, time, ctypes, webbrowser
from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QIcon


@dataclass
class AppEntry:
    name: str
    path: str
    run_count: int = 0
    last_run: str = ""


@dataclass
class PackEntry:
    name: str
    items: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ShortcutSlot:
    name: str = "Add App"
    path: str = ""


def get_theme_css(name):
    themes = {
        "Catppuccin Mocha": {
            'bg': '#1e1e2e', 'fg': '#cdd6f4', 'btn': '#45475a', 'btn_h': '#585b70',
            'suc': '#a6e3a1', 'acc': '#89b4fa', 'acc_h': '#b4d0fb', 'dng': '#f38ba8',
            'sec': '#313244', 'titlebar': '#181825', 'admin': '#fab387'
        },
        "Dark Green": {
            'bg': '#1b1e1b', 'fg': '#d4e4d4', 'btn': '#3a4a3a', 'btn_h': '#4a5a4a',
            'suc': '#81c784', 'acc': '#4caf50', 'acc_h': '#66bb6a', 'dng': '#e57373',
            'sec': '#2a332a', 'titlebar': '#151815', 'admin': '#ffb74d'
        },
        "Dark Blue": {
            'bg': '#1a1b2e', 'fg': '#c8d0f0', 'btn': '#2f3155', 'btn_h': '#3a3d6b',
            'suc': '#81c784', 'acc': '#5c6bc0', 'acc_h': '#7986cb', 'dng': '#e57373',
            'sec': '#252740', 'titlebar': '#12132a', 'admin': '#ffb74d'
        },
        "Dark Red": {
            'bg': '#2e1b1b', 'fg': '#f0d0d0', 'btn': '#553030', 'btn_h': '#6b3a3a',
            'suc': '#81c784', 'acc': '#c62828', 'acc_h': '#e53935', 'dng': '#ef5350',
            'sec': '#402525', 'titlebar': '#251515', 'admin': '#ffb74d'
        },
        "Gray": {
            'bg': '#2a2a2a', 'fg': '#e0e0e0', 'btn': '#484848', 'btn_h': '#585858',
            'suc': '#a5d6a7', 'acc': '#757575', 'acc_h': '#9e9e9e', 'dng': '#ef9a9a',
            'sec': '#383838', 'titlebar': '#202020', 'admin': '#ffb74d'
        }
    }
    c = themes.get(name, themes["Catppuccin Mocha"])
    return f"""
        QMainWindow{{background-color:{c['bg']};}}QLabel{{color:{c['fg']};}}
        QPushButton{{background-color:{c['btn']};color:{c['fg']};border:none;border-radius:8px;padding:10px 18px;font-weight:bold;}}
        QPushButton:hover{{background-color:{c['btn_h']};}}
        QPushButton#successBtn{{background-color:{c['suc']};color:{c['bg']};}}
        QPushButton#accentBtn{{background-color:{c['acc']};color:{c['bg']};}}
        QPushButton#accentBtn:hover{{background-color:{c['acc_h']};}}
        QPushButton#dangerBtn{{background-color:{c['dng']};color:{c['bg']};}}
        QPushButton#shortcutEmpty{{background-color:{c['btn']};color:{c['fg']};font-size:14px;border-radius:10px;padding:15px;}}
        QPushButton#shortcutEmpty:hover{{background-color:{c['btn_h']};}}
        QPushButton#shortcutSet{{background-color:{c['acc']};color:{c['bg']};font-size:14px;border-radius:10px;padding:15px;}}
        QPushButton#shortcutSet:hover{{background-color:{c['acc_h']};}}
        QPushButton#adminBtn{{background-color:{c['admin']};color:{c['bg']};}}
        QPushButton#adminBtn:hover{{background-color:{c['admin']};}}
        QPushButton#titlebarBtn{{background-color:transparent;color:{c['fg']};border:none;font-size:18px;font-weight:bold;padding:0px;}}
        QPushButton#titlebarBtn:hover{{background-color:{c['btn_h']};}}
        QPushButton#titlebarClose{{background-color:transparent;color:{c['fg']};border:none;font-size:18px;font-weight:bold;padding:0px;}}
        QPushButton#titlebarClose:hover{{background-color:{c['dng']};}}
        QLineEdit,QTextEdit,QDoubleSpinBox{{background-color:{c['sec']};color:{c['fg']};border:1px solid {c['btn']};border-radius:6px;padding:6px;}}
        QListWidget{{background-color:{c['bg']};color:{c['fg']};border:none;border-radius:8px;padding:5px;}}
        QListWidget::item{{padding:8px;border-radius:4px;}}
        QListWidget::item:selected{{background-color:{c['btn']};}}
        QListWidget::item:hover{{background-color:{c['sec']};}}
        QFrame#infoFrame{{background-color:{c['sec']};border-radius:12px;padding:15px;}}
        QComboBox{{background-color:{c['sec']};color:{c['fg']};border:1px solid {c['btn']};border-radius:6px;padding:6px;}}
        QComboBox QAbstractItemView{{background-color:{c['sec']};color:{c['fg']};selection-background-color:{c['btn']};}}
    """, c['titlebar']


class PackThread(QThread):
    log = pyqtSignal(str)

    def __init__(self, items):
        super().__init__()
        self.items = items

    def run(self):
        for i, item in enumerate(self.items):
            if i > 0 and (d := item.get('delay', 0)) > 0:
                time.sleep(d)
            try:
                os.startfile(item['path'])
                self.log.emit(f"  Launched: {item['name']}")
            except Exception as e:
                self.log.emit(f"  Error: {e}")


class PackDialog(QDialog):
    def __init__(self, pack, parent=None):
        super().__init__(parent)
        self.pack = pack
        self.setWindowTitle(f"Edit: {pack.name}")
        self.setMinimumSize(600, 500)
        l = QVBoxLayout(self)
        h = QHBoxLayout()
        h.addWidget(QLabel("Name:"))
        self.ne = QLineEdit(pack.name)
        h.addWidget(self.ne)
        l.addLayout(h)
        l.addWidget(QLabel("Items:"))
        self.lst = QListWidget()
        for i in pack.items:
            self.lst.addItem(f"{i['name']}  [delay: {i.get('delay', 0)}s]")
        l.addWidget(self.lst)
        bl = QHBoxLayout()
        ab = QPushButton("+ Add")
        ab.setObjectName("successBtn")
        ab.clicked.connect(self.add)
        bl.addWidget(ab)
        rb = QPushButton("- Remove")
        rb.setObjectName("dangerBtn")
        rb.clicked.connect(self.rem)
        bl.addWidget(rb)
        bl.addStretch()
        l.addLayout(bl)
        bl2 = QHBoxLayout()
        sb = QPushButton("Save")
        sb.setObjectName("accentBtn")
        sb.clicked.connect(self.save)
        cb = QPushButton("Cancel")
        cb.clicked.connect(self.reject)
        bl2.addStretch()
        bl2.addWidget(sb)
        bl2.addWidget(cb)
        l.addLayout(bl2)

    def add(self):
        fp, _ = QFileDialog.getOpenFileName(self, "Select File")
        if not fp:
            return
        d = QDialog(self)
        d.setWindowTitle("Delay")
        dl = QVBoxLayout(d)
        dl.addWidget(QLabel("Seconds:"))
        ds = QDoubleSpinBox()
        ds.setRange(0, 999)
        ds.setValue(0)
        dl.addWidget(ds)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(d.accept)
        bb.rejected.connect(d.reject)
        dl.addWidget(bb)
        if d.exec() == QDialog.DialogCode.Accepted:
            delay = ds.value()
            self.pack.items.append({'name': os.path.basename(fp), 'path': fp, 'delay': delay})
            self.lst.addItem(f"{os.path.basename(fp)}  [delay: {delay}s]")

    def rem(self):
        if (c := self.lst.currentRow()) >= 0:
            del self.pack.items[c]
            self.lst.takeItem(c)

    def save(self):
        self.pack.name = self.ne.text()
        self.accept()


class MainWin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setMinimumSize(1000, 650)
        self._drag_pos = None

        if getattr(sys, 'frozen', False):
            self.cfg = os.path.join(os.path.dirname(sys.executable), "launcher_config.json")
        else:
            self.cfg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_config.json")

        self.apps, self.packs = [], []
        self.shortcuts = [ShortcutSlot() for _ in range(5)]
        self.theme = "Catppuccin Mocha"
        self.sc_count = 5
        self.titlebar_color = "#181825"

        self.load()
        self.ui()
        self.refresh()
        self.apply_theme(self.theme)

    def load(self):
        if os.path.exists(self.cfg):
            try:
                d = json.load(open(self.cfg, 'r', encoding='utf-8'))
                self.apps = [AppEntry(**a) for a in d.get('apps', [])]
                self.packs = [PackEntry(**p) for p in d.get('packs', [])]
                if len(s := d.get('shortcuts', [])) == 5:
                    self.shortcuts = [ShortcutSlot(**x) for x in s]
                self.theme = d.get('theme', 'Catppuccin Mocha')
                self.sc_count = d.get('shortcut_count', 5)
            except:
                pass

    def save(self):
        json.dump({
            'apps': [{'name': a.name, 'path': a.path, 'run_count': a.run_count, 'last_run': a.last_run} for a in self.apps],
            'packs': [{'name': p.name, 'items': p.items} for p in self.packs],
            'shortcuts': [{'name': s.name, 'path': s.path} for s in self.shortcuts],
            'theme': self.theme,
            'shortcut_count': self.sc_count
        }, open(self.cfg, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)

    def ui(self):
        c = QWidget()
        self.setCentralWidget(c)
        ml = QVBoxLayout(c)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(0)

        self.tb = QFrame()
        self.tb.setFixedHeight(35)
        self.tbl = QHBoxLayout(self.tb)
        self.tbl.setContentsMargins(10, 0, 5, 0)

        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if os.path.exists(icon_path):
            ic = QLabel()
            ic.setPixmap(QIcon(icon_path).pixmap(20, 20))
            self.tbl.addWidget(ic)

        self.tl = QLabel("NIXBI App Launcher")
        self.tbl.addWidget(self.tl)
        self.tbl.addStretch()

        for txt, slot, style in [("─", self.showMinimized, "titlebarBtn"),
                                  ("□", self.toggle_max, "titlebarBtn"),
                                  ("✕", self.close, "titlebarClose")]:
            btn = QPushButton(txt)
            btn.setFixedSize(45, 30)
            btn.setObjectName(style)
            btn.clicked.connect(slot)
            self.tbl.addWidget(btn)

        self.tb.mousePressEvent = self._start_drag
        self.tb.mouseMoveEvent = self._do_drag
        ml.addWidget(self.tb)

        cf = QFrame()
        cl = QVBoxLayout(cf)
        cl.setContentsMargins(12, 12, 12, 12)
        cl.setSpacing(8)

        sf = QFrame()
        sf.setMaximumHeight(70)
        sf.setMinimumHeight(70)
        sl = QHBoxLayout(sf)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(6)
        self.sc_btns = []
        for i in range(5):
            b = QPushButton()
            b.setMinimumHeight(55)
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            b.clicked.connect(lambda _, idx=i: self.sc_click(idx))
            b.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            b.customContextMenuRequested.connect(lambda _, idx=i: self.sc_right(idx))
            self.sc_btns.append(b)
            sl.addWidget(b)
        cl.addWidget(sf)

        scl = QHBoxLayout()
        scl.addWidget(QLabel("Shortcuts:"))
        self.minus_btn = QPushButton("  -  ")
        self.minus_btn.setObjectName("dangerBtn")
        self.minus_btn.setFixedSize(50, 30)
        self.minus_btn.clicked.connect(self.rem_sc)
        scl.addWidget(self.minus_btn)
        self.cnt_lbl = QLabel(str(self.sc_count))
        self.cnt_lbl.setStyleSheet("font-size:16px;font-weight:bold;")
        self.cnt_lbl.setFixedWidth(30)
        self.cnt_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scl.addWidget(self.cnt_lbl)
        self.plus_btn = QPushButton("  +  ")
        self.plus_btn.setObjectName("successBtn")
        self.plus_btn.setFixedSize(50, 30)
        self.plus_btn.clicked.connect(self.add_sc)
        scl.addWidget(self.plus_btn)
        scl.addStretch()
        cl.addLayout(scl)

        tl2 = QHBoxLayout()
        tl2.addWidget(QLabel("Theme:"))
        self.tc = QComboBox()
        self.tc.addItems(list(["Catppuccin Mocha", "Dark Green", "Dark Blue", "Dark Red", "Gray"]))
        self.tc.setCurrentText(self.theme)
        self.tc.currentTextChanged.connect(self.apply_theme)
        tl2.addWidget(self.tc)
        tl2.addStretch()

        self.tg_link = QLabel("Subscribe to our Telegram channel @NiXBi_ofc")
        self.tg_link.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tg_link.mousePressEvent = lambda e: webbrowser.open("https://t.me/NiXBi_ofc")
        tl2.addWidget(self.tg_link)
        tl2.addStretch()

        tl2.addWidget(QLabel("Search:"))
        self.se = QLineEdit()
        self.se.setPlaceholderText("Search...")
        self.se.textChanged.connect(self.refresh)
        tl2.addWidget(self.se)
        self.ab = QPushButton("Get Admin")
        self.ab.setObjectName("adminBtn")
        self.ab.clicked.connect(self.req_admin)
        tl2.addWidget(self.ab)
        self.sb = QPushButton("Startup: OFF")
        self.sb.clicked.connect(self.toggle_startup)
        tl2.addWidget(self.sb)
        cl.addLayout(tl2)
        self.upd_sb()

        spl = QSplitter(Qt.Orientation.Horizontal)
        lf = QFrame()
        ll = QVBoxLayout(lf)
        ll.setContentsMargins(0, 0, 0, 0)
        self.lst = QListWidget()
        self.lst.itemDoubleClicked.connect(self.launch_sel)
        self.lst.currentItemChanged.connect(self.on_sel)
        ll.addWidget(self.lst)
        bl = QHBoxLayout()
        for t, o, c in [("Add App", "successBtn", self.add_app), ("New Pack", "accentBtn", self.mk_pack),
                        ("Delete", "dangerBtn", self.del_sel)]:
            b = QPushButton(t)
            b.setObjectName(o)
            b.clicked.connect(c)
            bl.addWidget(b)
        ll.addLayout(bl)
        spl.addWidget(lf)

        rf = QFrame()
        rf.setObjectName("infoFrame")
        rl = QVBoxLayout(rf)
        self.it = QLabel("Select an item")
        self.it.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        rl.addWidget(self.it)
        self.id = QLabel("")
        self.id.setWordWrap(True)
        rl.addWidget(self.id)
        self.al = QHBoxLayout()
        self.lpb = QPushButton("Launch Pack")
        self.lpb.setObjectName("successBtn")
        self.lpb.clicked.connect(self.launch_pack)
        self.epb = QPushButton("Edit Pack")
        self.epb.setObjectName("accentBtn")
        self.epb.clicked.connect(self.edit_pack)
        self.lab = QPushButton("Launch App")
        self.lab.setObjectName("successBtn")
        self.lab.clicked.connect(self.launch_app)
        self.eab = QPushButton("Edit App")
        self.eab.setObjectName("accentBtn")
        self.eab.clicked.connect(self.edit_app)
        for w in [self.lpb, self.epb, self.lab, self.eab]:
            self.al.addWidget(w)
        self.al.addStretch()
        rl.addLayout(self.al)
        rl.addStretch()
        rl.addWidget(QLabel("Log:"))
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(150)
        self.log.setFont(QFont("Consolas", 9))
        rl.addWidget(self.log)
        spl.addWidget(rf)
        spl.setSizes([300, 700])
        cl.addWidget(spl)

        ml.addWidget(cf)
        self.hide_all()
        self.upd_sc_vis()

    def _start_drag(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def _do_drag(self, e):
        if e.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def toggle_max(self):
        self.showNormal() if self.isMaximized() else self.showMaximized()

    def hide_all(self):
        for w in [self.lpb, self.epb, self.lab, self.eab]:
            w.hide()

    def show_pack(self):
        self.lpb.show()
        self.epb.show()
        self.lab.hide()
        self.eab.hide()

    def show_app(self):
        self.lpb.hide()
        self.epb.hide()
        self.lab.show()
        self.eab.show()

    def add_startup(self):
        import winreg
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0,
                               winreg.KEY_SET_VALUE)
            winreg.SetValueEx(k, "AppLauncher", 0, winreg.REG_SZ,
                              f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"')
            winreg.CloseKey(k)
        except:
            pass

    def rem_startup(self):
        import winreg
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0,
                               winreg.KEY_SET_VALUE)
            winreg.DeleteValue(k, "AppLauncher")
            winreg.CloseKey(k)
        except:
            pass

    def chk_startup(self):
        import winreg
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0,
                               winreg.KEY_READ)
            winreg.QueryValueEx(k, "AppLauncher")
            winreg.CloseKey(k)
            return True
        except:
            return False

    def upd_sb(self):
        if self.chk_startup():
            self.sb.setText("Startup: ON")
            self.sb.setObjectName("successBtn")
        else:
            self.sb.setText("Startup: OFF")
            self.sb.setObjectName("dangerBtn")
        self.sb.style().unpolish(self.sb)
        self.sb.style().polish(self.sb)

    def toggle_startup(self):
        if self.chk_startup():
            self.rem_startup()
        else:
            self.add_startup()
        self.upd_sb()

    def req_admin(self):
        if ctypes.windll.shell32.IsUserAnAdmin():
            QMessageBox.information(self, "Admin", "Already admin!")
            return
        if QMessageBox.question(self, "Admin", "Restart as admin?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit(0)

    def add_sc(self):
        if self.sc_count >= 5:
            return
        self.sc_count += 1
        self.cnt_lbl.setText(str(self.sc_count))
        self.save()
        self.upd_sc_vis()

    def rem_sc(self):
        if self.sc_count <= 1:
            return
        self.sc_count -= 1
        self.cnt_lbl.setText(str(self.sc_count))
        self.save()
        self.upd_sc_vis()

    def upd_sc_vis(self):
        for i, b in enumerate(self.sc_btns):
            b.setVisible(i < self.sc_count)
        self.re_sc()

    def re_sc(self):
        for i in range(self.sc_count):
            b = self.sc_btns[i]
            s = self.shortcuts[i]
            if s.path:
                b.setText(s.name)
                b.setObjectName("shortcutSet")
            else:
                b.setText(f"Add App ({i + 1})")
                b.setObjectName("shortcutEmpty")
            b.style().unpolish(b)
            b.style().polish(b)

    def sc_click(self, idx):
        s = self.shortcuts[idx]
        if s.path:
            self.launch_file(s.path)
            self.log_msg(f"Shortcut {idx + 1}: {s.name}")
        else:
            fp, _ = QFileDialog.getOpenFileName(self, "Select")
            if fp:
                s.path = fp
                s.name = os.path.basename(fp)
                self.save()
                self.re_sc()
                self.log_msg(f"Shortcut {idx + 1}: {s.name}")

    def sc_right(self, idx):
        s = self.shortcuts[idx]
        if s.path:
            s.path = ""
            s.name = "Add App"
            self.save()
            self.re_sc()
            self.log_msg(f"Shortcut {idx + 1}: reset")

    def add_app(self):
        fp, _ = QFileDialog.getOpenFileName(self, "Select")
        if fp:
            self.apps.append(AppEntry(name=os.path.basename(fp), path=fp))
            self.save()
            self.refresh()
            self.log_msg(f"Added: {os.path.basename(fp)}")

    def mk_pack(self):
        d = QDialog(self)
        d.setWindowTitle("Create Pack")
        l = QVBoxLayout(d)
        l.addWidget(QLabel("Name:"))
        ne = QLineEdit("New Pack")
        l.addWidget(ne)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(d.accept)
        bb.rejected.connect(d.reject)
        l.addWidget(bb)
        if d.exec() == QDialog.DialogCode.Accepted:
            self.packs.append(PackEntry(name=ne.text()))
            self.save()
            self.refresh()

    def edit_pack(self):
        if p := self.get_pack():
            d = PackDialog(p, self)
            if d.exec() == QDialog.DialogCode.Accepted:
                self.save()
                self.refresh()

    def edit_app(self):
        if not (a := self.get_app()):
            return
        d = QDialog(self)
        d.setWindowTitle(f"Edit: {a.name}")
        l = QFormLayout(d)
        ne = QLineEdit(a.name)
        pe = QLineEdit(a.path)
        l.addRow("Name:", ne)
        l.addRow("Path:", pe)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(d.accept)
        bb.rejected.connect(d.reject)
        l.addRow(bb)
        if d.exec() == QDialog.DialogCode.Accepted:
            a.name = ne.text()
            a.path = pe.text()
            self.save()
            self.refresh()

    def del_sel(self):
        if not (c := self.lst.currentItem()):
            return
        t = c.text()
        if t.startswith("[PACK] "):
            if (p := self.get_pack()) and QMessageBox.question(self, "Confirm", f"Delete '{p.name}'?",
                                                               QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                self.packs.remove(p)
        elif (a := self.get_app()) and QMessageBox.question(self, "Confirm", f"Delete '{a.name}'?",
                                                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.apps.remove(a)
        self.save()
        self.refresh()

    def launch_sel(self):
        if c := self.lst.currentItem():
            if c.text().startswith("[PACK] "):
                self.launch_pack()
            else:
                self.launch_app()

    def launch_pack(self):
        if not (p := self.get_pack()) or not p.items:
            return
        self.log_msg(f"Launching: {p.name}")
        self.pt = PackThread(p.items)
        self.pt.log.connect(self.log_msg)
        self.pt.start()

    def launch_app(self):
        if a := self.get_app():
            self.launch_file(a.path)
            a.run_count += 1
            a.last_run = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save()

    def launch_file(self, path):
        try:
            os.startfile(path)
            self.log_msg(f"Opened: {os.path.basename(path)}")
        except Exception as e:
            self.log_msg(f"Error: {e}")

    def get_pack(self):
        if (c := self.lst.currentItem()) and c.text().startswith("[PACK] "):
            n = c.text()[7:]
            for p in self.packs:
                if p.name == n:
                    return p
        return None

    def get_app(self):
        if (c := self.lst.currentItem()) and not c.text().startswith("[PACK] "):
            for a in self.apps:
                if a.name == c.text():
                    return a
        return None

    def on_sel(self):
        if not (c := self.lst.currentItem()):
            self.hide_all()
            return
        if c.text().startswith("[PACK] "):
            self.show_pack()
            if p := self.get_pack():
                self.it.setText(f"Pack: {p.name}")
                info = f"Items: {len(p.items)}"
                for i in p.items:
                    info += f"\n    - {i['name']}  [delay: {i.get('delay', 0)}s]"
                self.id.setText(info)
        else:
            self.show_app()
            if a := self.get_app():
                self.it.setText(f"App: {a.name}")
                self.id.setText(f"Path: {a.path}\nRuns: {a.run_count}\nLast: {a.last_run or 'Never'}")

    def refresh(self):
        self.lst.clear()
        s = self.se.text().lower()
        for p in sorted(self.packs, key=lambda x: x.name.lower()):
            if s in p.name.lower():
                self.lst.addItem(f"[PACK] {p.name}")
        for a in sorted(self.apps, key=lambda x: x.name.lower()):
            if s in a.name.lower():
                self.lst.addItem(a.name)

    def apply_theme(self, name):
        if name in ["Catppuccin Mocha", "Dark Green", "Dark Blue", "Dark Red", "Gray"]:
            self.theme = name
            css, titlebar_color = get_theme_css(name)
            self.titlebar_color = titlebar_color
            self.setStyleSheet(css)
            self.tb.setStyleSheet(f"background-color:{titlebar_color};")
            self.tl.setStyleSheet(f"color:#cdd6f4;font-weight:bold;")
            self.save()
            self.re_sc()
            self.upd_sb()

    def log_msg(self, msg):
        self.log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setFont(QFont("Segoe UI", 10))

    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    w = MainWin()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()import os, sys, json, time, ctypes, webbrowser, subprocess
from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QIcon


@dataclass
class AppEntry:
    name: str
    path: str
    run_count: int = 0
    last_run: str = ""


@dataclass
class PackEntry:
    name: str
    items: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ShortcutSlot:
    name: str = "Add App"
    path: str = ""


@dataclass
class PythonScript:
    name: str
    path: str
    use_terminal: bool = False
    presets: List[str] = field(default_factory=list)
    run_count: int = 0
    last_run: str = ""


def get_theme_css(name):
    themes = {
        "Catppuccin Mocha": {
            'bg': '#1e1e2e', 'fg': '#cdd6f4', 'btn': '#45475a', 'btn_h': '#585b70',
            'suc': '#a6e3a1', 'acc': '#89b4fa', 'acc_h': '#b4d0fb', 'dng': '#f38ba8',
            'sec': '#313244', 'titlebar': '#181825', 'admin': '#fab387'
        },
        "Dark Green": {
            'bg': '#1b1e1b', 'fg': '#d4e4d4', 'btn': '#3a4a3a', 'btn_h': '#4a5a4a',
            'suc': '#81c784', 'acc': '#4caf50', 'acc_h': '#66bb6a', 'dng': '#e57373',
            'sec': '#2a332a', 'titlebar': '#151815', 'admin': '#ffb74d'
        },
        "Dark Blue": {
            'bg': '#1a1b2e', 'fg': '#c8d0f0', 'btn': '#2f3155', 'btn_h': '#3a3d6b',
            'suc': '#81c784', 'acc': '#5c6bc0', 'acc_h': '#7986cb', 'dng': '#e57373',
            'sec': '#252740', 'titlebar': '#12132a', 'admin': '#ffb74d'
        },
        "Dark Red": {
            'bg': '#2e1b1b', 'fg': '#f0d0d0', 'btn': '#553030', 'btn_h': '#6b3a3a',
            'suc': '#81c784', 'acc': '#c62828', 'acc_h': '#e53935', 'dng': '#ef5350',
            'sec': '#402525', 'titlebar': '#251515', 'admin': '#ffb74d'
        },
        "Gray": {
            'bg': '#2a2a2a', 'fg': '#e0e0e0', 'btn': '#484848', 'btn_h': '#585858',
            'suc': '#a5d6a7', 'acc': '#757575', 'acc_h': '#9e9e9e', 'dng': '#ef9a9a',
            'sec': '#383838', 'titlebar': '#202020', 'admin': '#ffb74d'
        }
    }
    c = themes.get(name, themes["Catppuccin Mocha"])
    return f"""
        QMainWindow{{background-color:{c['bg']};}}QLabel{{color:{c['fg']};}}
        QPushButton{{background-color:{c['btn']};color:{c['fg']};border:none;border-radius:8px;padding:10px 18px;font-weight:bold;}}
        QPushButton:hover{{background-color:{c['btn_h']};}}
        QPushButton#successBtn{{background-color:{c['suc']};color:{c['bg']};}}
        QPushButton#accentBtn{{background-color:{c['acc']};color:{c['bg']};}}
        QPushButton#accentBtn:hover{{background-color:{c['acc_h']};}}
        QPushButton#dangerBtn{{background-color:{c['dng']};color:{c['bg']};}}
        QPushButton#shortcutEmpty{{background-color:{c['btn']};color:{c['fg']};font-size:14px;border-radius:10px;padding:15px;}}
        QPushButton#shortcutEmpty:hover{{background-color:{c['btn_h']};}}
        QPushButton#shortcutSet{{background-color:{c['acc']};color:{c['bg']};font-size:14px;border-radius:10px;padding:15px;}}
        QPushButton#shortcutSet:hover{{background-color:{c['acc_h']};}}
        QPushButton#adminBtn{{background-color:{c['admin']};color:{c['bg']};}}
        QPushButton#adminBtn:hover{{background-color:{c['admin']};}}
        QPushButton#titlebarBtn{{background-color:transparent;color:{c['fg']};border:none;font-size:18px;font-weight:bold;padding:0px;}}
        QPushButton#titlebarBtn:hover{{background-color:{c['btn_h']};}}
        QPushButton#titlebarClose{{background-color:transparent;color:{c['fg']};border:none;font-size:18px;font-weight:bold;padding:0px;}}
        QPushButton#titlebarClose:hover{{background-color:{c['dng']};}}
        QLineEdit,QTextEdit,QDoubleSpinBox{{background-color:{c['sec']};color:{c['fg']};border:1px solid {c['btn']};border-radius:6px;padding:6px;}}
        QListWidget{{background-color:{c['bg']};color:{c['fg']};border:none;border-radius:8px;padding:5px;}}
        QListWidget::item{{padding:8px;border-radius:4px;}}
        QListWidget::item:selected{{background-color:{c['btn']};}}
        QListWidget::item:hover{{background-color:{c['sec']};}}
        QFrame#infoFrame{{background-color:{c['sec']};border-radius:12px;padding:15px;}}
        QComboBox{{background-color:{c['sec']};color:{c['fg']};border:1px solid {c['btn']};border-radius:6px;padding:6px;}}
        QComboBox QAbstractItemView{{background-color:{c['sec']};color:{c['fg']};selection-background-color:{c['btn']};}}
    """, c['titlebar']


class PackThread(QThread):
    log = pyqtSignal(str)

    def __init__(self, items):
        super().__init__()
        self.items = items

    def run(self):
        for i, item in enumerate(self.items):
            if i > 0 and (d := item.get('delay', 0)) > 0:
                time.sleep(d)
            try:
                os.startfile(item['path'])
                self.log.emit(f"  Launched: {item['name']}")
            except Exception as e:
                self.log.emit(f"  Error: {e}")


class PackDialog(QDialog):
    def __init__(self, pack, parent=None):
        super().__init__(parent)
        self.pack = pack
        self.setWindowTitle(f"Edit: {pack.name}")
        self.setMinimumSize(600, 500)
        l = QVBoxLayout(self)
        h = QHBoxLayout()
        h.addWidget(QLabel("Name:"))
        self.ne = QLineEdit(pack.name)
        h.addWidget(self.ne)
        l.addLayout(h)
        l.addWidget(QLabel("Items:"))
        self.lst = QListWidget()
        for i in pack.items:
            self.lst.addItem(f"{i['name']}  [delay: {i.get('delay', 0)}s]")
        l.addWidget(self.lst)
        bl = QHBoxLayout()
        ab = QPushButton("+ Add")
        ab.setObjectName("successBtn")
        ab.clicked.connect(self.add)
        bl.addWidget(ab)
        rb = QPushButton("- Remove")
        rb.setObjectName("dangerBtn")
        rb.clicked.connect(self.rem)
        bl.addWidget(rb)
        bl.addStretch()
        l.addLayout(bl)
        bl2 = QHBoxLayout()
        sb = QPushButton("Save")
        sb.setObjectName("accentBtn")
        sb.clicked.connect(self.save)
        cb = QPushButton("Cancel")
        cb.clicked.connect(self.reject)
        bl2.addStretch()
        bl2.addWidget(sb)
        bl2.addWidget(cb)
        l.addLayout(bl2)

    def add(self):
        fp, _ = QFileDialog.getOpenFileName(self, "Select File")
        if not fp:
            return
        d = QDialog(self)
        d.setWindowTitle("Delay")
        dl = QVBoxLayout(d)
        dl.addWidget(QLabel("Seconds:"))
        ds = QDoubleSpinBox()
        ds.setRange(0, 999)
        ds.setValue(0)
        dl.addWidget(ds)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(d.accept)
        bb.rejected.connect(d.reject)
        dl.addWidget(bb)
        if d.exec() == QDialog.DialogCode.Accepted:
            delay = ds.value()
            self.pack.items.append({'name': os.path.basename(fp), 'path': fp, 'delay': delay})
            self.lst.addItem(f"{os.path.basename(fp)}  [delay: {delay}s]")

    def rem(self):
        if (c := self.lst.currentRow()) >= 0:
            del self.pack.items[c]
            self.lst.takeItem(c)

    def save(self):
        self.pack.name = self.ne.text()
        self.accept()


class PythonScriptDialog(QDialog):
    def __init__(self, script=None, parent=None):
        super().__init__(parent)
        self.script = script
        self.is_new = script is None
        self.setWindowTitle("Add Python Script" if self.is_new else f"Edit: {script.name}")
        self.setMinimumSize(550, 400)
        self.setup_ui()

    def setup_ui(self):
        l = QVBoxLayout(self)

        if self.is_new:
            l.addWidget(QLabel("Select Python script to add:"))
            path_layout = QHBoxLayout()
            self.path_edit = QLineEdit()
            self.path_edit.setPlaceholderText("Path to .py file...")
            path_layout.addWidget(self.path_edit)
            browse_btn = QPushButton("Browse")
            browse_btn.clicked.connect(self.browse)
            path_layout.addWidget(browse_btn)
            l.addLayout(path_layout)

        l.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit(self.script.name if not self.is_new else "")
        l.addWidget(self.name_edit)

        self.terminal_check = QCheckBox("Run in terminal")
        self.terminal_check.setChecked(self.script.use_terminal if not self.is_new else False)
        l.addWidget(self.terminal_check)

        l.addWidget(QLabel("Presets (command line arguments):"))
        self.presets_list = QListWidget()
        if not self.is_new and self.script.presets:
            for p in self.script.presets:
                self.presets_list.addItem(p if p else "(no arguments)")
        l.addWidget(self.presets_list)

        preset_input_layout = QHBoxLayout()
        self.preset_edit = QLineEdit()
        self.preset_edit.setPlaceholderText("e.g. 1000 60")
        preset_input_layout.addWidget(self.preset_edit)
        add_preset_btn = QPushButton("+")
        add_preset_btn.setObjectName("successBtn")
        add_preset_btn.clicked.connect(self.add_preset)
        preset_input_layout.addWidget(add_preset_btn)
        rem_preset_btn = QPushButton("-")
        rem_preset_btn.setObjectName("dangerBtn")
        rem_preset_btn.clicked.connect(self.rem_preset)
        preset_input_layout.addWidget(rem_preset_btn)
        l.addLayout(preset_input_layout)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setObjectName("accentBtn")
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        l.addLayout(btn_layout)

    def browse(self):
        fp, _ = QFileDialog.getOpenFileName(self, "Select Python Script", filter="Python Files (*.py)")
        if fp:
            self.path_edit.setText(fp)
            self.name_edit.setText(os.path.basename(fp))

    def add_preset(self):
        text = self.preset_edit.text().strip()
        if text:
            self.presets_list.addItem(text)
            self.preset_edit.clear()

    def rem_preset(self):
        if (c := self.presets_list.currentRow()) >= 0:
            self.presets_list.takeItem(c)

    def save(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Name is required")
            return
        path = self.path_edit.text().strip() if self.is_new else self.script.path
        if self.is_new and not path:
            QMessageBox.warning(self, "Error", "Path is required")
            return
        presets = [self.presets_list.item(i).text() for i in range(self.presets_list.count())]
        self.script = PythonScript(
            name=name,
            path=path,
            use_terminal=self.terminal_check.isChecked(),
            presets=presets,
            run_count=self.script.run_count if not self.is_new else 0,
            last_run=self.script.last_run if not self.is_new else ""
        )
        self.accept()


class MainWin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setMinimumSize(1000, 650)
        self._drag_pos = None

        if getattr(sys, 'frozen', False):
            self.cfg = os.path.join(os.path.dirname(sys.executable), "launcher_config.json")
        else:
            self.cfg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher_config.json")

        self.apps, self.packs = [], []
        self.shortcuts = [ShortcutSlot() for _ in range(5)]
        self.python_scripts: List[PythonScript] = []
        self.theme = "Catppuccin Mocha"
        self.sc_count = 5
        self.titlebar_color = "#181825"

        self.load()
        self.ui()
        self.refresh()
        self.apply_theme(self.theme)

    def load(self):
        if os.path.exists(self.cfg):
            try:
                d = json.load(open(self.cfg, 'r', encoding='utf-8'))
                self.apps = [AppEntry(**a) for a in d.get('apps', [])]
                self.packs = [PackEntry(**p) for p in d.get('packs', [])]
                if len(s := d.get('shortcuts', [])) == 5:
                    self.shortcuts = [ShortcutSlot(**x) for x in s]
                self.python_scripts = [PythonScript(**ps) for ps in d.get('python_scripts', [])]
                self.theme = d.get('theme', 'Catppuccin Mocha')
                self.sc_count = d.get('shortcut_count', 5)
            except:
                pass

    def save(self):
        json.dump({
            'apps': [{'name': a.name, 'path': a.path, 'run_count': a.run_count, 'last_run': a.last_run} for a in self.apps],
            'packs': [{'name': p.name, 'items': p.items} for p in self.packs],
            'shortcuts': [{'name': s.name, 'path': s.path} for s in self.shortcuts],
            'python_scripts': [{'name': ps.name, 'path': ps.path, 'use_terminal': ps.use_terminal,
                                'presets': ps.presets, 'run_count': ps.run_count, 'last_run': ps.last_run}
                               for ps in self.python_scripts],
            'theme': self.theme,
            'shortcut_count': self.sc_count
        }, open(self.cfg, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)

    def ui(self):
        c = QWidget()
        self.setCentralWidget(c)
        ml = QVBoxLayout(c)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(0)

        self.tb = QFrame()
        self.tb.setFixedHeight(35)
        self.tbl = QHBoxLayout(self.tb)
        self.tbl.setContentsMargins(10, 0, 5, 0)

        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if os.path.exists(icon_path):
            ic = QLabel()
            ic.setPixmap(QIcon(icon_path).pixmap(20, 20))
            self.tbl.addWidget(ic)

        self.tl = QLabel("NIXBI App Launcher")
        self.tbl.addWidget(self.tl)
        self.tbl.addStretch()

        for txt, slot, style in [("─", self.showMinimized, "titlebarBtn"),
                                  ("□", self.toggle_max, "titlebarBtn"),
                                  ("✕", self.close, "titlebarClose")]:
            btn = QPushButton(txt)
            btn.setFixedSize(45, 30)
            btn.setObjectName(style)
            btn.clicked.connect(slot)
            self.tbl.addWidget(btn)

        self.tb.mousePressEvent = self._start_drag
        self.tb.mouseMoveEvent = self._do_drag
        ml.addWidget(self.tb)

        cf = QFrame()
        cl = QVBoxLayout(cf)
        cl.setContentsMargins(12, 12, 12, 12)
        cl.setSpacing(8)

        sf = QFrame()
        sf.setMaximumHeight(70)
        sf.setMinimumHeight(70)
        sl = QHBoxLayout(sf)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(6)
        self.sc_btns = []
        for i in range(5):
            b = QPushButton()
            b.setMinimumHeight(55)
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            b.clicked.connect(lambda _, idx=i: self.sc_click(idx))
            b.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            b.customContextMenuRequested.connect(lambda _, idx=i: self.sc_right(idx))
            self.sc_btns.append(b)
            sl.addWidget(b)
        cl.addWidget(sf)

        scl = QHBoxLayout()
        scl.addWidget(QLabel("Shortcuts:"))
        self.minus_btn = QPushButton("  -  ")
        self.minus_btn.setObjectName("dangerBtn")
        self.minus_btn.setFixedSize(50, 30)
        self.minus_btn.clicked.connect(self.rem_sc)
        scl.addWidget(self.minus_btn)
        self.cnt_lbl = QLabel(str(self.sc_count))
        self.cnt_lbl.setStyleSheet("font-size:16px;font-weight:bold;")
        self.cnt_lbl.setFixedWidth(30)
        self.cnt_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scl.addWidget(self.cnt_lbl)
        self.plus_btn = QPushButton("  +  ")
        self.plus_btn.setObjectName("successBtn")
        self.plus_btn.setFixedSize(50, 30)
        self.plus_btn.clicked.connect(self.add_sc)
        scl.addWidget(self.plus_btn)
        scl.addStretch()
        cl.addLayout(scl)

        tl2 = QHBoxLayout()
        tl2.addWidget(QLabel("Theme:"))
        self.tc = QComboBox()
        self.tc.addItems(list(["Catppuccin Mocha", "Dark Green", "Dark Blue", "Dark Red", "Gray"]))
        self.tc.setCurrentText(self.theme)
        self.tc.currentTextChanged.connect(self.apply_theme)
        tl2.addWidget(self.tc)
        tl2.addStretch()

        self.tg_link = QLabel("Subscribe to our Telegram channel @NiXBi_ofc")
        self.tg_link.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tg_link.mousePressEvent = lambda e: webbrowser.open("https://t.me/NiXBi_ofc")
        tl2.addWidget(self.tg_link)
        tl2.addStretch()

        tl2.addWidget(QLabel("Search:"))
        self.se = QLineEdit()
        self.se.setPlaceholderText("Search...")
        self.se.textChanged.connect(self.refresh)
        tl2.addWidget(self.se)
        self.ab = QPushButton("Get Admin")
        self.ab.setObjectName("adminBtn")
        self.ab.clicked.connect(self.req_admin)
        tl2.addWidget(self.ab)
        self.sb = QPushButton("Startup: OFF")
        self.sb.clicked.connect(self.toggle_startup)
        tl2.addWidget(self.sb)
        cl.addLayout(tl2)
        self.upd_sb()

        spl = QSplitter(Qt.Orientation.Horizontal)
        lf = QFrame()
        ll = QVBoxLayout(lf)
        ll.setContentsMargins(0, 0, 0, 0)
        self.lst = QListWidget()
        self.lst.itemDoubleClicked.connect(self.launch_sel)
        self.lst.currentItemChanged.connect(self.on_sel)
        ll.addWidget(self.lst)
        bl = QHBoxLayout()
        for t, o, c in [("Add App", "successBtn", self.add_app),
                        ("Add Python", "successBtn", self.add_python),
                        ("New Pack", "accentBtn", self.mk_pack),
                        ("Delete", "dangerBtn", self.del_sel)]:
            b = QPushButton(t)
            b.setObjectName(o)
            b.clicked.connect(c)
            bl.addWidget(b)
        ll.addLayout(bl)
        spl.addWidget(lf)

        rf = QFrame()
        rf.setObjectName("infoFrame")
        rl = QVBoxLayout(rf)
        self.it = QLabel("Select an item")
        self.it.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        rl.addWidget(self.it)
        self.id = QLabel("")
        self.id.setWordWrap(True)
        rl.addWidget(self.id)
        self.al = QHBoxLayout()
        self.lpb = QPushButton("Launch Pack")
        self.lpb.setObjectName("successBtn")
        self.lpb.clicked.connect(self.launch_pack)
        self.epb = QPushButton("Edit Pack")
        self.epb.setObjectName("accentBtn")
        self.epb.clicked.connect(self.edit_pack)
        self.lab = QPushButton("Launch App")
        self.lab.setObjectName("successBtn")
        self.lab.clicked.connect(self.launch_app)
        self.eab = QPushButton("Edit App")
        self.eab.setObjectName("accentBtn")
        self.eab.clicked.connect(self.edit_app)
        self.lpsb = QPushButton("Launch Script")
        self.lpsb.setObjectName("successBtn")
        self.lpsb.clicked.connect(self.launch_python)
        self.epsb = QPushButton("Edit Script")
        self.epsb.setObjectName("accentBtn")
        self.epsb.clicked.connect(self.edit_python)
        for w in [self.lpb, self.epb, self.lab, self.eab, self.lpsb, self.epsb]:
            self.al.addWidget(w)
        self.al.addStretch()
        rl.addLayout(self.al)
        rl.addStretch()
        rl.addWidget(QLabel("Log:"))
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(150)
        self.log.setFont(QFont("Consolas", 9))
        rl.addWidget(self.log)
        spl.addWidget(rf)
        spl.setSizes([300, 700])
        cl.addWidget(spl)

        ml.addWidget(cf)
        self.hide_all()
        self.upd_sc_vis()

    def _start_drag(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def _do_drag(self, e):
        if e.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def toggle_max(self):
        self.showNormal() if self.isMaximized() else self.showMaximized()

    def hide_all(self):
        for w in [self.lpb, self.epb, self.lab, self.eab, self.lpsb, self.epsb]:
            w.hide()

    def show_pack(self):
        self.lpb.show(); self.epb.show()
        self.lab.hide(); self.eab.hide(); self.lpsb.hide(); self.epsb.hide()

    def show_app(self):
        self.lpb.hide(); self.epb.hide()
        self.lab.show(); self.eab.show(); self.lpsb.hide(); self.epsb.hide()

    def show_python(self):
        self.lpb.hide(); self.epb.hide(); self.lab.hide(); self.eab.hide()
        self.lpsb.show(); self.epsb.show()

    def add_startup(self):
        import winreg
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0,
                               winreg.KEY_SET_VALUE)
            winreg.SetValueEx(k, "AppLauncher", 0, winreg.REG_SZ,
                              f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"')
            winreg.CloseKey(k)
        except:
            pass

    def rem_startup(self):
        import winreg
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0,
                               winreg.KEY_SET_VALUE)
            winreg.DeleteValue(k, "AppLauncher")
            winreg.CloseKey(k)
        except:
            pass

    def chk_startup(self):
        import winreg
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0,
                               winreg.KEY_READ)
            winreg.QueryValueEx(k, "AppLauncher")
            winreg.CloseKey(k)
            return True
        except:
            return False

    def upd_sb(self):
        if self.chk_startup():
            self.sb.setText("Startup: ON")
            self.sb.setObjectName("successBtn")
        else:
            self.sb.setText("Startup: OFF")
            self.sb.setObjectName("dangerBtn")
        self.sb.style().unpolish(self.sb)
        self.sb.style().polish(self.sb)

    def toggle_startup(self):
        if self.chk_startup():
            self.rem_startup()
        else:
            self.add_startup()
        self.upd_sb()

    def req_admin(self):
        if ctypes.windll.shell32.IsUserAnAdmin():
            QMessageBox.information(self, "Admin", "Already admin!")
            return
        if QMessageBox.question(self, "Admin", "Restart as admin?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit(0)

    def add_sc(self):
        if self.sc_count >= 5:
            return
        self.sc_count += 1
        self.cnt_lbl.setText(str(self.sc_count))
        self.save()
        self.upd_sc_vis()

    def rem_sc(self):
        if self.sc_count <= 1:
            return
        self.sc_count -= 1
        self.cnt_lbl.setText(str(self.sc_count))
        self.save()
        self.upd_sc_vis()

    def upd_sc_vis(self):
        for i, b in enumerate(self.sc_btns):
            b.setVisible(i < self.sc_count)
        self.re_sc()

    def re_sc(self):
        for i in range(self.sc_count):
            b = self.sc_btns[i]
            s = self.shortcuts[i]
            if s.path:
                b.setText(s.name)
                b.setObjectName("shortcutSet")
            else:
                b.setText(f"Add App ({i + 1})")
                b.setObjectName("shortcutEmpty")
            b.style().unpolish(b)
            b.style().polish(b)

    def sc_click(self, idx):
        s = self.shortcuts[idx]
        if s.path:
            self.launch_file(s.path)
            self.log_msg(f"Shortcut {idx + 1}: {s.name}")
        else:
            fp, _ = QFileDialog.getOpenFileName(self, "Select")
            if fp:
                s.path = fp
                s.name = os.path.basename(fp)
                self.save()
                self.re_sc()
                self.log_msg(f"Shortcut {idx + 1}: {s.name}")

    def sc_right(self, idx):
        s = self.shortcuts[idx]
        if s.path:
            s.path = ""
            s.name = "Add App"
            self.save()
            self.re_sc()
            self.log_msg(f"Shortcut {idx + 1}: reset")

    def add_app(self):
        fp, _ = QFileDialog.getOpenFileName(self, "Select Application")
        if not fp:
            return
        if fp.endswith('.py'):
            reply = QMessageBox.question(self, "Python Detected",
                                         "This is a Python script. Add it as Python Script instead?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.add_python(fp)
                return
        self.apps.append(AppEntry(name=os.path.basename(fp), path=fp))
        self.save()
        self.refresh()
        self.log_msg(f"Added: {os.path.basename(fp)}")

    def add_python(self, preset_path=None):
        if not preset_path:
            fp, _ = QFileDialog.getOpenFileName(self, "Select Python Script", filter="Python Files (*.py)")
            if not fp:
                return
        else:
            fp = preset_path

        d = PythonScriptDialog(parent=self)
        d.path_edit.setText(fp)
        d.name_edit.setText(os.path.basename(fp))
        if d.exec() == QDialog.DialogCode.Accepted:
            self.python_scripts.append(d.script)
            self.save()
            self.refresh()
            self.log_msg(f"Added Python: {d.script.name}")

    def edit_python(self):
        ps = self.get_selected_python()
        if not ps:
            return
        d = PythonScriptDialog(ps, self)
        if d.exec() == QDialog.DialogCode.Accepted:
            idx = self.python_scripts.index(ps)
            self.python_scripts[idx] = d.script
            self.save()
            self.refresh()
            self.log_msg(f"Script saved: {d.script.name}")

    def launch_python(self):
        ps = self.get_selected_python()
        if not ps:
            return

        if ps.use_terminal and ps.presets:
            preset_dialog = QDialog(self)
            preset_dialog.setWindowTitle(f"Select Preset - {ps.name}")
            pl = QVBoxLayout(preset_dialog)
            pl.addWidget(QLabel("Choose preset to launch:"))
            preset_list = QListWidget()
            for p in ps.presets:
                preset_list.addItem(p if p else "(no arguments)")
            pl.addWidget(preset_list)
            btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            btn_box.accepted.connect(preset_dialog.accept)
            btn_box.rejected.connect(preset_dialog.reject)
            pl.addWidget(btn_box)
            if preset_dialog.exec() == QDialog.DialogCode.Accepted and preset_list.currentItem():
                args = preset_list.currentItem().text()
                if args == "(no arguments)":
                    args = ""
                self._launch_python_script(ps, args)
        elif ps.use_terminal:
            self._launch_python_script(ps, "")
        else:
            self.launch_file(ps.path)
            ps.run_count += 1
            ps.last_run = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save()

    def _launch_python_script(self, ps, args):
        try:
            if ps.use_terminal:
                if args:
                    cmd = f'start "{ps.name}" cmd /k "cd /d {os.path.dirname(ps.path)} && "{sys.executable}" "{ps.path}" {args}"'
                else:
                    cmd = f'start "{ps.name}" cmd /k "cd /d {os.path.dirname(ps.path)} && "{sys.executable}" "{ps.path}""'
                subprocess.Popen(cmd, shell=True, cwd=os.path.dirname(ps.path))
            else:
                cmd = [sys.executable, ps.path]
                if args:
                    cmd.extend(args.split())
                subprocess.Popen(cmd, cwd=os.path.dirname(ps.path),
                                 creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            ps.run_count += 1
            ps.last_run = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save()
            self.log_msg(f"Launched Python: {ps.name}")
        except Exception as e:
            self.log_msg(f"Error: {e}")

    def mk_pack(self):
        d = QDialog(self)
        d.setWindowTitle("Create Pack")
        l = QVBoxLayout(d)
        l.addWidget(QLabel("Name:"))
        ne = QLineEdit("New Pack")
        l.addWidget(ne)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(d.accept)
        bb.rejected.connect(d.reject)
        l.addWidget(bb)
        if d.exec() == QDialog.DialogCode.Accepted:
            self.packs.append(PackEntry(name=ne.text()))
            self.save()
            self.refresh()

    def edit_pack(self):
        if p := self.get_pack():
            d = PackDialog(p, self)
            if d.exec() == QDialog.DialogCode.Accepted:
                self.save()
                self.refresh()

    def edit_app(self):
        if not (a := self.get_app()):
            return
        d = QDialog(self)
        d.setWindowTitle(f"Edit: {a.name}")
        l = QFormLayout(d)
        ne = QLineEdit(a.name)
        pe = QLineEdit(a.path)
        l.addRow("Name:", ne)
        l.addRow("Path:", pe)
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(d.accept)
        bb.rejected.connect(d.reject)
        l.addRow(bb)
        if d.exec() == QDialog.DialogCode.Accepted:
            a.name = ne.text()
            a.path = pe.text()
            self.save()
            self.refresh()

    def del_sel(self):
        text = self.lst.currentItem().text() if self.lst.currentItem() else ""
        if text.startswith("[PACK] "):
            if (p := self.get_pack()) and QMessageBox.question(self, "Confirm", f"Delete '{p.name}'?",
                                                               QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                self.packs.remove(p)
        elif text.startswith("[APP] "):
            if (a := self.get_app()) and QMessageBox.question(self, "Confirm", f"Delete '{a.name}'?",
                                                              QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                self.apps.remove(a)
        elif text.startswith("[PY] ") or text.startswith("[PYT] "):
            if (ps := self.get_selected_python()) and QMessageBox.question(self, "Confirm", f"Delete '{ps.name}'?",
                                                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                self.python_scripts.remove(ps)
        self.save()
        self.refresh()

    def launch_sel(self):
        text = self.lst.currentItem().text() if self.lst.currentItem() else ""
        if text.startswith("[PACK] "):
            self.launch_pack()
        elif text.startswith("[APP] "):
            self.launch_app()
        elif text.startswith("[PY] ") or text.startswith("[PYT] "):
            self.launch_python()

    def launch_pack(self):
        if not (p := self.get_pack()) or not p.items:
            return
        self.log_msg(f"Launching: {p.name}")
        self.pt = PackThread(p.items)
        self.pt.log.connect(self.log_msg)
        self.pt.start()

    def launch_app(self):
        if a := self.get_app():
            self.launch_file(a.path)
            a.run_count += 1
            a.last_run = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save()

    def launch_file(self, path):
        try:
            os.startfile(path)
            self.log_msg(f"Opened: {os.path.basename(path)}")
        except Exception as e:
            self.log_msg(f"Error: {e}")

    def get_pack(self):
        text = self.lst.currentItem().text() if self.lst.currentItem() else ""
        if text.startswith("[PACK] "):
            n = text[7:]
            for p in self.packs:
                if p.name == n:
                    return p
        return None

    def get_app(self):
        text = self.lst.currentItem().text() if self.lst.currentItem() else ""
        if text.startswith("[APP] "):
            n = text[6:]
            for a in self.apps:
                if a.name == n:
                    return a
        return None

    def get_selected_python(self):
        text = self.lst.currentItem().text() if self.lst.currentItem() else ""
        if text.startswith("[PY] ") or text.startswith("[PYT] "):
            n = text[6:] if text.startswith("[PYT] ") else text[5:]
            for ps in self.python_scripts:
                if ps.name == n:
                    return ps
        return None

    def on_sel(self):
        text = self.lst.currentItem().text() if self.lst.currentItem() else ""
        if not text:
            self.hide_all()
            return
        if text.startswith("[PACK] "):
            self.show_pack()
            if p := self.get_pack():
                self.it.setText(f"Pack: {p.name}")
                info = f"Items: {len(p.items)}"
                for i in p.items:
                    info += f"\n    - {i['name']}  [delay: {i.get('delay', 0)}s]"
                self.id.setText(info)
        elif text.startswith("[APP] "):
            self.show_app()
            if a := self.get_app():
                self.it.setText(f"App: {a.name}")
                self.id.setText(f"Path: {a.path}\nRuns: {a.run_count}\nLast: {a.last_run or 'Never'}")
        elif text.startswith("[PY] ") or text.startswith("[PYT] "):
            self.show_python()
            if ps := self.get_selected_python():
                self.it.setText(f"Python: {ps.name}")
                info = f"Path: {ps.path}\nTerminal: {'Yes' if ps.use_terminal else 'No'}\nPresets: {len(ps.presets)}\nRuns: {ps.run_count}\nLast: {ps.last_run or 'Never'}"
                self.id.setText(info)

    def refresh(self):
        self.lst.clear()
        s = self.se.text().lower()

        has_packs = any(s in p.name.lower() for p in self.packs)
        has_apps = any(s in a.name.lower() for a in self.apps)
        has_py = any(s in ps.name.lower() for ps in self.python_scripts if not ps.use_terminal)
        has_pyt = any(s in ps.name.lower() for ps in self.python_scripts if ps.use_terminal)

        if has_packs:
            self.lst.addItem("--- PACKS ---")
            for p in sorted(self.packs, key=lambda x: x.name.lower()):
                if s in p.name.lower():
                    self.lst.addItem(f"[PACK] {p.name}")

        if has_apps:
            self.lst.addItem("--- APPS ---")
            for a in sorted(self.apps, key=lambda x: x.name.lower()):
                if s in a.name.lower():
                    self.lst.addItem(f"[APP] {a.name}")

        if has_py:
            self.lst.addItem("--- PYTHON SCRIPTS ---")
            for ps in sorted(self.python_scripts, key=lambda x: x.name.lower()):
                if not ps.use_terminal and s in ps.name.lower():
                    self.lst.addItem(f"[PY] {ps.name}")

        if has_pyt:
            self.lst.addItem("--- TERMINAL SCRIPTS ---")
            for ps in sorted(self.python_scripts, key=lambda x: x.name.lower()):
                if ps.use_terminal and s in ps.name.lower():
                    self.lst.addItem(f"[PYT] {ps.name}")

    def apply_theme(self, name):
        if name in ["Catppuccin Mocha", "Dark Green", "Dark Blue", "Dark Red", "Gray"]:
            self.theme = name
            css, titlebar_color = get_theme_css(name)
            self.titlebar_color = titlebar_color
            self.setStyleSheet(css)
            self.tb.setStyleSheet(f"background-color:{titlebar_color};")
            self.tl.setStyleSheet(f"color:#cdd6f4;font-weight:bold;")
            self.save()
            self.re_sc()
            self.upd_sb()

    def log_msg(self, msg):
        self.log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setFont(QFont("Segoe UI", 10))

    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    w = MainWin()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
