import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, QHBoxLayout, QCheckBox, QGridLayout
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtOpenGL import QGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *
import random
import math

# position für das Fenster
screenX = int(1920 / 2 - 400)
screenY = int(1080 / 2 - 300)

class DiceGLWidget(QGLWidget):
    def __init__(self, dice_count=1, parent=None):
        super().__init__(parent)
        self.dice_count = dice_count
        self.angles = [random.randint(0, 360) for _ in range(dice_count)]
        self.results = [1 for _ in range(dice_count)]
        self.animating = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.animation_time = 0
        self.draw_mode = 0  # 0=weiß, 1=schwarz, 2=invertiert
        # Neue Attribute für asynchrone Animation
        self.axis = [self.random_axis() for _ in range(dice_count)]
        self.speeds = [random.randint(20, 30) for _ in range(dice_count)]

    def random_axis(self):
        # Zufällige Rotationsachse (x, y, z), normiert, niemals (0,0,0)
        while True:
            x, y, z = random.uniform(-1,1), random.uniform(-1,1), random.uniform(-1,1)
            l = math.sqrt(x*x + y*y + z*z)
            if l > 0.1:  # Verhindert zu kleine oder flache Achsen
                return (x/l, y/l, z/l)

    def set_dice_count(self, count):
        self.dice_count = count
        self.angles = [random.randint(0, 360) for _ in range(count)]
        self.results = [1 for _ in range(count)]
        self.axis = [self.random_axis() for _ in range(count)]
        self.speeds = [random.randint(20, 30) for _ in range(count)]
        self.update()

    def set_draw_mode(self, mode):
        self.draw_mode = mode
        self.makeCurrent()
        if self.draw_mode == 2:
            glClearColor(1.0, 1.0, 1.0, 1.0)
        elif self.draw_mode == 3:
            glClearColor(0.07, 0.27, 0.13, 1.0)
        else:
            glClearColor(0.0, 0.0, 0.0, 1.0)
        self.update()

    def start_animation(self):
        self.animating = True
        self.animation_time = 30
        # Bei jedem Start neue Achsen und langsamere Geschwindigkeiten
        self.axis = [self.random_axis() for _ in range(self.dice_count)]
        self.speeds = [random.randint(20, 30) for _ in range(self.dice_count)]
        self.timer.start(20)  # Animation langsamer wenn wert höher

    def start_animation_locked(self, locked):
        self.animating = True
        self.animation_time = 30
        self.axis = [self.random_axis() for _ in range(self.dice_count)]
        self.speeds = [random.randint(20, 30) for _ in range(self.dice_count)]
        self.locked = locked.copy()
        self.timer.start(20)  # Animation langsamer wenn wert höher

    def animate(self):
        
        self.animation_time += 30  # Korrektes Intervall verwenden
        for i in range(self.dice_count):
            if hasattr(self, 'locked') and getattr(self, 'locked', [False]*self.dice_count)[i]:
                continue  # Festgesetzte Würfel nicht animieren
            self.angles[i] += self.speeds[i] + random.randint(-5, 5)
        self.update()
        if self.animation_time > random.randint(1000, 2000):
            self.animating = False
            self.timer.stop()
            # Nach jedem Durchgang Achsen und Winkel neu setzen
            self.axis = [self.random_axis() for _ in range(self.dice_count)]
            self.angles = [random.randint(0, 360) for _ in range(self.dice_count)]
            # Nur nicht-gesperrte Würfel neu würfeln
            if hasattr(self, 'locked'):
                for i in range(self.dice_count):
                    if not self.locked[i]:
                        self.results[i] = random.randint(1, 6)
            else:
                self.results = [random.randint(1, 6) for _ in range(self.dice_count)]
            self.update()

    def paintGL(self):
        # Hintergrundfarbe je nach Modus setzen
        if getattr(self, 'draw_mode', 0) == 2:
            glClearColor(1.0, 1.0, 1.0, 1.0)
        elif getattr(self, 'draw_mode', 0) == 3:
            glClearColor(0.07, 0.27, 0.13, 1.0)
        else:
            glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        # Positionierung der Würfel je nach Anzahl
        if self.dice_count == 1:
            positions = [(0, 0)]
        elif self.dice_count == 2:
            positions = [(-1, 0), (1, 0)]
        elif self.dice_count == 3:
            positions = [(-2, 0), (0, 0), (2, 0)]
        elif self.dice_count == 4:
            positions = [(-1, 0.7), (1, 0.7), (-1, -0.7), (1, -0.7)]
        elif self.dice_count == 5:
            positions = [(-1.5, 0.7), (0, 0.7), (1.5, 0.7), (-0.75, -0.7), (0.75, -0.7)]
        elif self.dice_count == 6:
            positions = [(-1.5, 0.7), (0, 0.7), (1.5, 0.7), (-1.5, -0.7), (0, -0.7), (1.5, -0.7)]
        else:
            positions = [(i * 2.0, 0) for i in range(self.dice_count)]
        glTranslatef(0, 0, -7.0)
        for i in range(self.dice_count):
            glPushMatrix()
            x, y = positions[i]
            glTranslatef(x, y, 0)
            self._draw_idx = i  # für locked-Overlay
            # Im Spielmodus: festgesetzte Würfel immer als Zahl anzeigen
            if self.animating and hasattr(self, 'locked') and getattr(self, 'locked', [False]*self.dice_count)[i]:
                self.draw_cube(self.results[i])
            elif self.animating:
                ax = self.axis[i]
                glRotatef(self.angles[i], ax[0], ax[1], ax[2])
                self.draw_cube(0)
            else:
                self.draw_cube(self.results[i])
            glPopMatrix()
        self._draw_idx = None

    def initializeGL(self):
        # Hintergrundfarbe je nach Modus setzen
        if getattr(self, 'draw_mode', 0) == 2:  # Invertiert
            glClearColor(1.0, 1.0, 1.0, 1.0)  # Weißer Hintergrund
        elif getattr(self, 'draw_mode', 0) == 3:  # Casino
            glClearColor(0.07, 0.27, 0.13, 1.0)  # Dunkelgrün
        else:
            glClearColor(0.0, 0.0, 0.0, 1.0)  # Schwarz
        glEnable(GL_DEPTH_TEST)

    def resizeGL(self, w, h):
        # Hintergrundfarbe je nach Modus setzen
        if getattr(self, 'draw_mode', 0) == 2:
            glClearColor(1.0, 1.0, 1.0, 1.0)
        elif getattr(self, 'draw_mode', 0) == 3:
            glClearColor(0.07, 0.27, 0.13, 1.0)
        else:
            glClearColor(0.0, 0.0, 0.0, 1.0)
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, w / float(h or 1), 1.0, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def draw_cube(self, value):
        # Farben je nach Modus
        if getattr(self, 'draw_mode', 0) == 2:  # Invertiert
            glColor3f(0, 0, 0)  # Schwarzer Würfel
        elif getattr(self, 'draw_mode', 0) == 3:  # Casino
            glColor3f(0.8, 0.1, 0.1)  # Rot
        else:
            glColor3f(1, 1, 1)  # Weiß
        glBegin(GL_QUADS)
        # Vorderseite
        glVertex3f(-0.5, -0.5, 0.5)
        glVertex3f(0.5, -0.5, 0.5)
        glVertex3f(0.5, 0.5, 0.5)
        glVertex3f(-0.5, 0.5, 0.5)
        # Rückseite
        glVertex3f(-0.5, -0.5, -0.5)
        glVertex3f(0.5, -0.5, -0.5)
        glVertex3f(0.5, 0.5, -0.5)
        glVertex3f(-0.5, 0.5, -0.5)
        # Oben
        glVertex3f(-0.5, 0.5, -0.5)
        glVertex3f(0.5, 0.5, -0.5)
        glVertex3f(0.5, 0.5, 0.5)
        glVertex3f(-0.5, 0.5, 0.5)
        # Unten
        glVertex3f(-0.5, -0.5, -0.5)
        glVertex3f(0.5, -0.5, -0.5)
        glVertex3f(0.5, -0.5, 0.5)
        glVertex3f(-0.5, -0.5, 0.5)
        # Rechts
        glVertex3f(0.5, -0.5, -0.5)
        glVertex3f(0.5, 0.5, -0.5)
        glVertex3f(0.5, 0.5, 0.5)
        glVertex3f(0.5, -0.5, 0.5)
        # Links
        glVertex3f(-0.5, -0.5, -0.5)
        glVertex3f(-0.5, 0.5, -0.5)
        glVertex3f(-0.5, 0.5, 0.5)
        glVertex3f(-0.5, -0.5, 0.5)
        glEnd()
        # Kanten zeichnen
        # Kantenfarbe je nach Modus
        if getattr(self, 'draw_mode', 0) == 2:  # Invertiert (schwarzer Würfel)
            glColor3f(1.0, 1.0, 1.0)  # weiße Kanten
        elif getattr(self, 'draw_mode', 0) == 3:  # Casino
            glColor3f(1.0, 0.84, 0.0)  # goldene Kanten
        else:  # Weißer Würfel
            glColor3f(0.0, 0.0, 0.0)  # schwarze Kanten
        glLineWidth(2)
        glBegin(GL_LINES)
        # Vorderseite
        glVertex3f(-0.5, -0.5, 0.5); glVertex3f(0.5, -0.5, 0.5)
        glVertex3f(0.5, -0.5, 0.5); glVertex3f(0.5, 0.5, 0.5)
        glVertex3f(0.5, 0.5, 0.5); glVertex3f(-0.5, 0.5, 0.5)
        glVertex3f(-0.5, 0.5, 0.5); glVertex3f(-0.5, -0.5, 0.5)
        # Rückseite
        glVertex3f(-0.5, -0.5, -0.5); glVertex3f(0.5, -0.5, -0.5)
        glVertex3f(0.5, -0.5, -0.5); glVertex3f(0.5, 0.5, -0.5)
        glVertex3f(0.5, 0.5, -0.5); glVertex3f(-0.5, 0.5, -0.5)
        glVertex3f(-0.5, 0.5, -0.5); glVertex3f(-0.5, -0.5, -0.5)
        # Verbindungen
        glVertex3f(-0.5, -0.5, 0.5); glVertex3f(-0.5, -0.5, -0.5)
        glVertex3f(0.5, -0.5, 0.5); glVertex3f(0.5, -0.5, -0.5)
        glVertex3f(0.5, 0.5, 0.5); glVertex3f(0.5, 0.5, -0.5)
        glVertex3f(-0.5, 0.5, 0.5); glVertex3f(-0.5, 0.5, -0.5)
        glEnd()
        # Punkte für die Augenzahl auf der Vorderseite (z=+0.5)
        if value > 0:
            if getattr(self, 'draw_mode', 0) == 2:
                glColor3f(1, 1, 1)  # Invertiert: weiße Augen
            elif getattr(self, 'draw_mode', 0) == 3:
                glColor3f(1.0, 0.84, 0.0)  # Casino: goldene Augen
            else:
                glColor3f(0, 0, 0)  # Normal: schwarze Augen
            points = {
                1: [(0, 0)],
                2: [(-0.2, -0.2), (0.2, 0.2)],
                3: [(-0.2, -0.2), (0, 0), (0.2, 0.2)],
                4: [(-0.2, -0.2), (0.2, -0.2), (-0.2, 0.2), (0.2, 0.2)],
                5: [(-0.2, -0.2), (0.2, -0.2), (0, 0), (-0.2, 0.2), (0.2, 0.2)],
                6: [(-0.2, -0.2), (0.2, -0.2), (-0.2, 0), (0.2, 0), (-0.2, 0.2), (0.2, 0.2)]
            }
            radius = 0.07
            glDisable(GL_DEPTH_TEST)
            for px, py in points.get(value, []):
                glBegin(GL_POLYGON)
                for i in range(24):
                    angle = 2 * math.pi * i / 24
                    dx = radius * math.cos(angle)
                    dy = radius * math.sin(angle)
                    glVertex3f(px + dx, py + dy, 0.54)
                glEnd()
            glEnable(GL_DEPTH_TEST)
        # Festgesetzte Würfel optisch hervorheben
        if hasattr(self, 'locked') and hasattr(self.parent(), 'locked'):
            idx = getattr(self, '_draw_idx', None)
            if idx is not None and self.parent().locked[idx]:
                glColor4f(0.2, 0.8, 0.2, 0.5)  # halbtransparenter grüner Overlay
                glBegin(GL_QUADS)
                glVertex3f(-0.52, -0.52, 0.55)
                glVertex3f(0.52, -0.52, 0.55)
                glVertex3f(0.52, 0.52, 0.55)
                glVertex3f(-0.52, 0.52, 0.55)
                glEnd()

    def mousePressEvent(self, event):
        # Nur im Festsetzmodus und ab 4 Würfeln
        if hasattr(self.parent(), 'current_mode') and self.parent().current_mode == 1 and self.dice_count >= 4:
            # Position im Widget
            w, h = self.width(), self.height()
            mx, my = event.x(), event.y()
            # Würfelpositionen wie in paintGL
            if self.dice_count == 1:
                positions = [(0, 0)]
            elif self.dice_count == 2:
                positions = [(-1, 0), (1, 0)]
            elif self.dice_count == 3:
                positions = [(-2, 0), (0, 0), (2, 0)]
            elif self.dice_count == 4:
                positions = [(-1, 0.7), (1, 0.7), (-1, -0.7), (1, -0.7)]
            elif self.dice_count == 5:
                positions = [(-1.5, 0.7), (0, 0.7), (1.5, 0.7), (-0.75, -0.7), (0.75, -0.7)]
            elif self.dice_count == 6:
                positions = [(-1.5, 0.7), (0, 0.7), (1.5, 0.7), (-1.5, -0.7), (0, -0.7), (1.5, -0.7)]
            else:
                positions = [(i * 2.0, 0) for i in range(self.dice_count)]
            # Umrechnung OpenGL -> Widget-Koordinaten (grob, zentriert)
            for i, (x, y) in enumerate(positions):
                # OpenGL-Koordinaten: x in [-2,2], y in [-1,1] (ca.)
                wx = int(w/2 + x * w/5)
                wy = int(h/2 - y * h/3)
                size = int(min(w, h) * 0.13)
                if (mx > wx-size and mx < wx+size and my > wy-size and my < wy+size):
                    # Festsetzen, wenn noch nicht fest und Limit nicht überschritten
                    if not self.parent().locked[i]:
                        max_lock = self.dice_count - 1
                        if self.dice_count == 4:
                            max_lock = 3
                        elif self.dice_count == 5:
                            max_lock = 4
                        elif self.dice_count == 6:
                            max_lock = 5
                        if sum(self.parent().locked) < max_lock and not self.animating:
                            self.parent().locked[i] = True
                            self.update()
                    break
        super().mousePressEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Würfel Brett")
        self.setGeometry(screenX, screenY, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Auswahl-Widgets müssen vor dem Layout erstellt werden
        self.combo = QComboBox()
        self.combo.addItems([str(i) for i in range(1, 7)])
        self.combo.currentIndexChanged.connect(self.change_dice_count)
        self.start_button = QPushButton("Würfeln")
        self.start_button.clicked.connect(self.start_animation)
        self.reset_button = QPushButton("Check Box Reset")
        self.reset_button.clicked.connect(self.reset_locked)
        self.reset_button.setVisible(False)
        # Hilfe-Button
        self.help_button = QPushButton("Hilfe")
        self.help_button.clicked.connect(self.show_help)
        self.bg_combo = QComboBox()
        self.bg_combo.addItems(["Weißer Hintergrund", "Schwarzer Hintergrund", "Farben invertieren", "Casino Style"])
        self.bg_combo.currentIndexChanged.connect(self.update_bg_color)

        # Layout für obere Steuerleiste (Würfelanzahl, Design, Modus)
        top_layout = QHBoxLayout()
        top_layout.addStretch(1)
        # Hilfe-Button links neben Würfelanzahl
        top_layout.addWidget(self.help_button)
        top_layout.addSpacing(20)
        top_layout.addWidget(QLabel("Würfelanzahl:"))
        top_layout.addWidget(self.combo)
        top_layout.addSpacing(30)
        top_layout.addWidget(QLabel("Design:"))
        top_layout.addWidget(self.bg_combo)
        top_layout.addSpacing(30)
        # Modus-Auswahl oben rechts
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Standard", "Spiel Modus"])
        self.mode_combo.currentIndexChanged.connect(self.change_mode)
        top_layout.addWidget(QLabel("Modus:"))
        top_layout.addWidget(self.mode_combo)
        top_layout.addStretch(1)
        layout.addLayout(top_layout)

        # OpenGL-Würfelanzeige
        self.dice_widget = DiceGLWidget(dice_count=1, parent=self)
        self.dice_widget.setMinimumHeight(340)  # Würfelanzeige größer machen
        layout.addWidget(self.dice_widget)

        # Layout für Checkboxen direkt unter den Würfeln (nur im Festsetzmodus)
        self.lock_checkboxes = []
        self.lock_checkbox_labels = []
        self.lock_checkbox_layout = QGridLayout()
        layout.addLayout(self.lock_checkbox_layout)

        # Layout für unteren Bereich (Start-Button zentriert, Reset-Button daneben)
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch(1)
        bottom_layout.addWidget(self.start_button)
        bottom_layout.addSpacing(20)
        bottom_layout.addWidget(self.reset_button)
        bottom_layout.addStretch(1)
        layout.addLayout(bottom_layout)

        self.current_mode = 0  # 0=Standard, 1=Würfel festsetzen
        self.locked = [False for _ in range(1)]  # Start: 1 Würfel, keiner festgesetzt
        self.bg_mode = 3  # 0=weiß, 1=schwarz, 2=invertiert, 3=casino
        self.bg_combo.setCurrentIndex(3)
        # update_lock_checkboxes erst nach Initialisierung aller Attribute aufrufen
        self.update_bg_color()
        self.update_lock_checkboxes()

    def update_lock_checkboxes(self):
        # Entferne alte Checkboxen und Labels
        for cb in self.lock_checkboxes:
            self.lock_checkbox_layout.removeWidget(cb)
            cb.deleteLater()
        for lbl in getattr(self, 'lock_checkbox_labels', []):
            self.lock_checkbox_layout.removeWidget(lbl)
            lbl.deleteLater()
        self.lock_checkboxes = []
        self.lock_checkbox_labels = []
        # Nur anzeigen, wenn Modus "Würfel festsetzen" und ab 4 Würfeln
        if self.current_mode == 1 and self.dice_widget.dice_count >= 4:
            max_lock = self.dice_widget.dice_count - 1
            if self.dice_widget.dice_count == 4:
                max_lock = 3
            elif self.dice_widget.dice_count == 5:
                max_lock = 4
            elif self.dice_widget.dice_count == 6:
                max_lock = 5
            # Grid-Positionen für Checkboxen je nach Würfelanzahl
            positions = []
            if self.dice_widget.dice_count == 4:
                positions = [(0,0), (0,1), (1,0), (1,1)]
            elif self.dice_widget.dice_count == 5:
                positions = [(0,0), (0,1), (0,2), (1,0), (1,2)]
            elif self.dice_widget.dice_count == 6:
                positions = [(0,0), (0,1), (0,2), (1,0), (1,1), (1,2)]
            else:
                positions = [(0,i) for i in range(self.dice_widget.dice_count)]
            for i in range(self.dice_widget.dice_count):
                cb = QCheckBox()
                cb.setChecked(self.locked[i])
                cb.setEnabled(not self.locked[i] and sum(self.locked) < max_lock)
                cb.stateChanged.connect(lambda state, idx=i: self.lock_checkbox_changed(idx, state, max_lock))
                label = QLabel(f"Würfel {i+1}")
                # Kompakter Stil im Spielmodus
                if self.bg_mode == 3:
                    cb.setStyleSheet("QCheckBox::indicator { border: 2px solid white; background-color: rgba(0,0,0,0); width: 14px; height: 14px; } QCheckBox::indicator:checked { background-color: white; } QCheckBox { color: white; font-weight: bold; font-size: 11px; min-width: 0px; }")
                    label.setStyleSheet("color: white; font-weight: bold; font-size: 11px; min-width: 0px; margin-left: 2px; margin-right: 4px;")
                elif self.bg_mode == 1:
                    cb.setStyleSheet("QCheckBox::indicator { border: 2px solid white; background-color: black; width: 14px; height: 14px; } QCheckBox::indicator:checked { background-color: white; } QCheckBox { color: white; font-weight: bold; font-size: 11px; min-width: 0px; }")
                    label.setStyleSheet("color: white; font-weight: bold; font-size: 11px; min-width: 0px; margin-left: 2px; margin-right: 4px;")
                else:
                    cb.setStyleSheet("QCheckBox { font-size: 11px; min-width: 0px; }")
                    label.setStyleSheet("font-size: 11px; min-width: 0px; margin-left: 2px; margin-right: 4px;")
                self.lock_checkboxes.append(cb)
                self.lock_checkbox_labels.append(label)
                row, col = positions[i]
                self.lock_checkbox_layout.addWidget(cb, row, col*2, alignment=Qt.AlignRight | Qt.AlignVCenter)
                self.lock_checkbox_layout.addWidget(label, row, col*2+1, alignment=Qt.AlignLeft | Qt.AlignVCenter)
            self.reset_button.setVisible(True)
            # Casino Style: Reset-Button weiß
            if self.bg_mode == 3:
                self.reset_button.setStyleSheet("color: white; background-color: #114422; font-weight: bold; font-size: 12px;")
            elif self.bg_mode == 1:
                self.reset_button.setStyleSheet("color: white; background-color: black; font-weight: bold; font-size: 12px;")
            else:
                self.reset_button.setStyleSheet("font-size: 12px;")
        else:
            self.reset_button.setVisible(False)

    def lock_checkbox_changed(self, idx, state, max_lock):
        if state == 2 and not self.locked[idx] and sum(self.locked) < max_lock:
            self.locked[idx] = True
            self.update_lock_checkboxes()
            self.dice_widget.update()

    def reset_locked(self):
        self.locked = [False for _ in range(self.dice_widget.dice_count)]
        self.update_lock_checkboxes()
        self.dice_widget.update()

    def change_dice_count(self):
        count = int(self.combo.currentText())
        self.dice_widget.set_dice_count(count)
        self.reset_locked()  # Immer alle Würfel entsperren beim Wechsel der Anzahl

    def change_mode(self):
        self.current_mode = self.mode_combo.currentIndex()
        self.reset_locked()
        self.update_lock_checkboxes()
        self.dice_widget.update()
        # Sicherstellen, dass auch das OpenGL-Widget keine "locked"-Würfel mehr kennt
        if hasattr(self.dice_widget, 'locked'):
            del self.dice_widget.locked

    def start_animation(self):
        if self.current_mode == 1:
            self.dice_widget.start_animation_locked(self.locked)
        else:
            self.dice_widget.start_animation()

    def update_bg_color(self):
        self.bg_mode = self.bg_combo.currentIndex()
        if self.bg_mode == 0:  # Weiß
            self.setStyleSheet("background-color: white;")
            self.centralWidget().setStyleSheet("background-color: white;")
            self.combo.setStyleSheet("color: black; background-color: white;")
            self.start_button.setStyleSheet("color: black; background-color: white;")
            self.bg_combo.setStyleSheet("color: black; background-color: white;")
            for widget in self.findChildren(QLabel):
                widget.setStyleSheet("color: black; background-color: white;")
        elif self.bg_mode == 1:  # Schwarz
            self.setStyleSheet("background-color: black;")
            self.centralWidget().setStyleSheet("background-color: black;")
            self.combo.setStyleSheet("color: white; background-color: black;")
            self.start_button.setStyleSheet("color: white; background-color: black;")
            self.bg_combo.setStyleSheet("color: white; background-color: black;")
            for widget in self.findChildren(QLabel):
                widget.setStyleSheet("color: white; background-color: black;")
        elif self.bg_mode == 2:  # Invertiert
            self.setStyleSheet("background-color: white;")
            self.centralWidget().setStyleSheet("background-color: white;")
            self.combo.setStyleSheet("color: black; background-color: white;")
            self.start_button.setStyleSheet("color: black; background-color: white;")
            self.bg_combo.setStyleSheet("color: black; background-color: white;")
            for widget in self.findChildren(QLabel):
                widget.setStyleSheet("color: black; background-color: white;")
        else:  # Casino Style
            # Dunkelgrüner Hintergrund, goldene Schrift
            self.setStyleSheet("background-color: #114422;")
            self.centralWidget().setStyleSheet("background-color: #114422;")
            self.combo.setStyleSheet("color: gold; background-color: #114422;")
            self.start_button.setStyleSheet("color: gold; background-color: #114422;")
            self.bg_combo.setStyleSheet("color: gold; background-color: #114422;")
            for widget in self.findChildren(QLabel):
                widget.setStyleSheet("color: gold; background-color: #114422;")
        self.dice_widget.set_draw_mode(self.bg_mode)

    def show_help(self):
        from PyQt5.QtWidgets import QMessageBox
        help_text = (
            # HIER HILFETEXT ANPASSEN
            "<b>Würfelbrett Hilfe</b><br><br>"
            "<b>Würfelanzahl</b> setzt die Zahl der Würfel auf 1 bis 6.<br>"
            "<b>Design</b> ändert über das Dropdown Menue das Design.<br>"
            "<b>Spiel Modus</b> ab 4 bis 6 Würfeln, werden einzelne Würfel<br> mit den Check Boxen festgesetzt.<br>"
            "<b>Würfeln</b> löst einen Würfel Wurf aus.<br>"
            "<b>Check Box Reset</b> setzt alle Festgesetzten Würfel zurück.<br>"
            "<b>Hilfe</b> zeigt diese Anleitung an."
        )
        box = QMessageBox(self)
        box.setWindowTitle("Hilfe zum Würfelbrett")
        box.setText(help_text)
        box.setTextFormat(Qt.RichText)
        # HIER HINTERGRUNDFARBE DES HILFE-FENSTERS ANPASSEN
        # Beispiel: 
        box.setStyleSheet("QLabel{background-color: #f0f0e0; color: #222;} QMessageBox{background-color: #f0f0e0;}")
        box.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
