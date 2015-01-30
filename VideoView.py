#!/usr/bin/env python
# -*- coding: utf-8 -*-

#   VideoView.py por:
#   Flavio Danesse <fdanesse@gmail.com>
#   Uruguay

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os
import gtk
import gobject
import pango

from ConfigParser import SafeConfigParser

from VideoPlayer.VideoPlayer import VideoPlayer
from JAMediaImagenes.ImagePlayer import ImagePlayer

from Globales import COLORES
from Globales import get_flashcards_previews
from Globales import get_user_dict

GRADOS = ["1°", "2°", "3°", "4°", "5°", "6°"]
EDADES = range(5, 21, 1)


class VideoView(gtk.EventBox):

    __gsignals__ = {
    "flashcards": (gobject.SIGNAL_RUN_FIRST,
        gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT, )),
    "game": (gobject.SIGNAL_RUN_FIRST,
        gobject.TYPE_NONE, (gobject.TYPE_STRING, ))}

    def __init__(self):

        gtk.EventBox.__init__(self)

        self.modify_bg(gtk.STATE_NORMAL, COLORES["contenido"])
        self.set_border_width(4)

        self.full = False
        self.topic = False

        tabla = gtk.Table(rows=10, columns=5, homogeneous=True)
        tabla.set_property("column-spacing", 8)
        tabla.set_property("row-spacing", 8)
        tabla.set_border_width(8)

        self.titulo = gtk.Label("Título")
        self.titulo.modify_font(pango.FontDescription("DejaVu Sans Bold 20"))
        self.titulo.modify_fg(gtk.STATE_NORMAL, COLORES["window"])
        self.videoplayer = VideoPlayer()

        tabla.attach(self.titulo, 0, 5, 0, 1)
        tabla.attach(self.videoplayer, 0, 3, 1, 10)

        flashcards = gtk.Button()
        flashcards.set_relief(gtk.RELIEF_NONE)
        imagen = gtk.Image()
        imagen.set_from_file("Imagenes/flashcards.png")
        flashcards.modify_bg(gtk.STATE_NORMAL, COLORES["toolbar"])
        flashcards.add(imagen)

        self.imagen_juego = GameImage()
        self.flashcards_preview = FlashCardsPreview()

        tabla.attach(self.imagen_juego, 3, 5, 1, 4)
        tabla.attach(flashcards, 3, 5, 4, 6)
        tabla.attach(self.flashcards_preview, 3, 5, 6, 10)

        self.add(tabla)
        self.show_all()

        flashcards.connect("clicked", self.__emit_flashcards)
        self.imagen_juego.connect("button-press-event", self.__emit_game)
        self.videoplayer.connect("full", self.set_full)
        self.videoplayer.connect("endfile", self.__force_unfull)

    def __force_unfull(self, widget):
        if self.full:
            self.set_full(False)
        self.videoplayer.pause()

    def __emit_game(self, widget, event):
        self.emit("game", self.topic)

    def __emit_flashcards(self, widget):
        dialog = DialogLogin(self.get_toplevel())
        ret = dialog.run()
        if ret == gtk.RESPONSE_ACCEPT:
            datos = dialog.get_user_dict()
            self.emit("flashcards", (self.topic, datos))
        dialog.destroy()

    def set_full(self, widget):
        tabla = self.get_child()
        for child in tabla.children():
            child.hide()

        if self.full:
            self.videoplayer.hide()
            tabla.set_homogeneous(True)
            tabla.set_property("column-spacing", 8)
            tabla.set_property("row-spacing", 8)
            self.show_all()
            self.full = False
        else:
            tabla.set_homogeneous(False)
            tabla.set_property("column-spacing", 0)
            tabla.set_property("row-spacing", 0)
            self.videoplayer.show()
            self.full = True

        self.videoplayer.stop()
        self.videoplayer.load(os.path.join(self.topic, "video.ogv"))

    def stop(self):
        self.videoplayer.stop()
        self.imagen_juego.stop()
        self.flashcards_preview.stop()
        if self.flashcards_preview.control:
            gobject.source_remove(self.flashcards_preview.control)
            self.flashcards_preview.control = False
        self.hide()

    def run(self, topic):
        self.show()
        self.topic = topic
        self.videoplayer.load(os.path.join(self.topic, "video.ogv"))
        self.imagen_juego.load(topic)
        self.flashcards_preview.load(topic)

        parser = SafeConfigParser()
        metadata = os.path.join(topic, "topic.ini")
        parser.read(metadata)

        self.titulo.set_text("Topic: " + parser.get('topic', 'title'))
        self.full = False
        self.set_full(False)


class GameImage(gtk.DrawingArea):

    def __init__(self):

        gtk.DrawingArea.__init__(self)

        self.modify_bg(gtk.STATE_NORMAL, COLORES["text"])
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)

        self.imagenplayer = False
        self.path = False

        self.show_all()

    def stop(self):
        if self.imagenplayer:
            self.imagenplayer.stop()
            del(self.imagenplayer)
            self.imagenplayer = False

    def load(self, topic):
        self.stop()
        self.path = os.path.abspath("Imagenes/juego1.png")
        self.imagenplayer = ImagePlayer(self)
        self.imagenplayer.load(self.path)
        return False


class FlashCardsPreview(gtk.EventBox):

    def __init__(self):

        gtk.EventBox.__init__(self)

        self.modify_bg(gtk.STATE_NORMAL, COLORES["window"])

        self.vocabulario = []
        self.index_select = 0
        self.imagenplayer = False
        self.path = False
        self.control = False
        self.topic = False

        self.drawing = gtk.DrawingArea()
        self.label = gtk.Label("Text")
        self.drawing.modify_bg(gtk.STATE_NORMAL, COLORES["window"])
        self.label.modify_bg(gtk.STATE_NORMAL, COLORES["window"])
        self.label.modify_fg(gtk.STATE_NORMAL, COLORES["text"])
        self.label.modify_font(pango.FontDescription("DejaVu Sans 18"))

        tabla = gtk.Table(rows=1, columns=2, homogeneous=True)
        tabla.attach(self.drawing, 0, 1, 0, 1)
        tabla.attach(self.label, 1, 2, 0, 1)

        self.add(tabla)
        self.show_all()

    def __run_secuencia(self):
        self.stop()
        self.path = os.path.join(self.topic, "Imagenes",
            "%s.png" % self.vocabulario[self.index_select][0])
        self.imagenplayer = ImagePlayer(self.drawing)
        self.imagenplayer.load(self.path)
        self.label.set_text(self.vocabulario[self.index_select][1])
        if self.index_select < len(self.vocabulario) - 1:
            self.index_select += 1
        else:
            self.index_select = 0
        return True

    def stop(self):
        if self.imagenplayer:
            self.imagenplayer.stop()
            del(self.imagenplayer)
            self.imagenplayer = False

    def load(self, topic):
        self.stop()
        self.topic = topic
        self.vocabulario = get_flashcards_previews(self.topic)
        self.index_select = 0
        self.__run_secuencia()
        if not self.control:
            self.control = gobject.timeout_add(3000, self.__run_secuencia)
        return False


class DialogLogin(gtk.Dialog):

    def __init__(self, parent_window=None):

        gtk.Dialog.__init__(self, title="Loging", parent=parent_window,
            buttons= ("OK", gtk.RESPONSE_ACCEPT,
            "Cancelar", gtk.RESPONSE_CANCEL))

        # self.set_decorated(False)
        self.modify_bg(gtk.STATE_NORMAL, COLORES["window"])
        self.set_border_width(15)

        dirpath = os.path.join(os.environ["HOME"], ".Ple")
        users = []
        if os.path.exists(dirpath):
            for arch in sorted(os.listdir(dirpath)):
                newpath = os.path.join(dirpath, arch)
                if os.path.isdir(newpath):
                    users.append(os.path.basename(newpath))

        self.frame1 = Frame1(users)
        self.frame2 = Frame2()
        self.frame1.connect("user", self.__user_selected)
        self.frame1.connect("new-user", self.__new_user)
        self.frame2.connect("activar", self.__activar_ok)
        self.vbox.pack_start(self.frame1, False, False, 0)
        self.vbox.pack_start(self.frame2, False, False, 0)
        self.vbox.show_all()

        if users:
            self.frame1.show_all()
            self.frame2.set_sensitive(False)
        else:
            self.frame1.hide()
            self.frame2.set_sensitive(True)
            self.action_area.get_children()[1].set_sensitive(False)

    def __new_user(self, frame1):
        self.frame1.hide()
        self.frame2.set_sensitive(True)
        self.frame1.combo.set_active(-1)
        self.frame2.nombre.set_text("")
        self.frame2.apellido.set_text("")
        self.frame2.escuela.set_text("")
        self.frame2.grado.set_active(-1)
        self.frame2.edad.set_active(-1)

    def __user_selected(self, frame1, user):
        if user:
            self.frame2.set_user(user)

    def __activar_ok(self, widget, valor):
        self.action_area.get_children()[1].set_sensitive(valor)

    def get_user_dict(self):
        _dict = {
            "Nombre": "",
            "Apellido": "",
            "Edad": "",
            "Escuela": "",
             "Grado": ""}
        user = self.frame1.combo.get_active_text()
        if user:
            _dict = get_user_dict(user)
        else:
            _dict["Nombre"] = self.frame2.nombre.get_text()
            _dict["Apellido"] = self.frame2.apellido.get_text()
            _dict["Escuela"] = self.frame2.escuela.get_text()
            _dict["Grado"] = self.frame2.grado.get_active_text()
            _dict["Edad"] = self.frame2.edad.get_active_text()
        return _dict


class Frame1(gtk.Frame):

    __gsignals__ = {
    "user": (gobject.SIGNAL_RUN_FIRST,
        gobject.TYPE_NONE, (gobject.TYPE_STRING, )),
    "new-user": (gobject.SIGNAL_RUN_FIRST,
        gobject.TYPE_NONE, [])
        }
    def __init__(self, users):

        gtk.Frame.__init__(self)

        self.set_border_width(4)
        self.modify_bg(0, COLORES["window"])
        self.set_label(" Selecciona tu Usuario ")
        self.get_property("label-widget").modify_bg(0, COLORES["window"])
        self.set_label_align(0.5, 1.0)

        box = gtk.HBox()
        self.combo = gtk.combo_box_new_text()
        self.combo.connect('changed', self.__changed)
        button = gtk.Button("Crear Nuevo...")
        button.connect("clicked", self.__new_user)
        box.pack_start(self.combo, False, False, 5)
        box.pack_end(button, False, False, 5)

        event = gtk.EventBox()
        event.modify_bg(0, COLORES["window"])
        event.set_border_width(4)
        event.add(box)

        for user in users:
            self.combo.append_text(user)

        self.add(event)
        self.connect("realize", self.__realized)
        self.show_all()

    def __new_user(self, button):
        self.emit("new-user")

    def __realized(self, frame):
        self.combo.set_active(0)

    def __changed(self, widget):
        self.emit("user", widget.get_active_text())


class Frame2(gtk.Frame):

    __gsignals__ = {
    "activar": (gobject.SIGNAL_RUN_FIRST,
        gobject.TYPE_NONE, (gobject.TYPE_BOOLEAN, ))
        }

    def __init__(self):

        gtk.Frame.__init__(self)

        self.set_border_width(4)
        self.modify_bg(0, COLORES["window"])
        self.set_label(" Datos de Usuario ")
        self.get_property("label-widget").modify_bg(0, COLORES["window"])
        self.set_label_align(0.5, 1.0)

        tabla = gtk.Table(rows=5, columns=2, homogeneous=True)
        tabla.set_property("column-spacing", 5)
        tabla.set_property("row-spacing", 5)

        label = gtk.Label("Nombre:")
        tabla.attach(label, 0, 1, 0, 1)
        self.nombre = gtk.Entry()
        self.nombre.connect("changed", self.__update_data)
        tabla.attach(self.nombre, 1, 2, 0, 1)

        label = gtk.Label("Apellido:")
        tabla.attach(label, 0, 1, 1, 2)
        self.apellido = gtk.Entry()
        self.apellido.connect("changed", self.__update_data)
        tabla.attach(self.apellido, 1, 2, 1, 2)

        label = gtk.Label("Escuela:")
        tabla.attach(label, 0, 1, 2, 3)
        self.escuela = gtk.Entry()
        self.escuela.connect("changed", self.__update_data)
        tabla.attach(self.escuela, 1, 2, 2, 3)

        label = gtk.Label("Grado:")
        tabla.attach(label, 0, 1, 3, 4)
        self.grado = gtk.combo_box_new_text()
        self.grado.connect("changed", self.__update_data)
        for g in GRADOS:
            self.grado.append_text(g)
        tabla.attach(self.grado, 1, 2, 3, 4)

        label = gtk.Label("Edad:")
        tabla.attach(label, 0, 1, 4, 5)
        self.edad = gtk.combo_box_new_text()
        self.edad.connect("changed", self.__update_data)
        for e in EDADES:
            self.edad.append_text(str(e))
        tabla.attach(self.edad, 1, 2, 4, 5)

        event = gtk.EventBox()
        event.modify_bg(0, COLORES["window"])
        event.set_border_width(4)
        event.add(tabla)

        self.add(event)
        self.show_all()

    def __update_data(self, widget):
        nombre = self.nombre.get_text()
        apellido = self.apellido.get_text()
        escuela = self.escuela.get_text()
        grado = self.grado.get_active_text()
        edad = self.edad.get_active_text()
        if nombre and apellido and escuela and grado and edad:
            self.emit("activar", True)
        else:
            self.emit("activar", False)

    def set_user(self, user):
        _dict = get_user_dict(user)
        self.nombre.set_text(_dict.get("Nombre", ""))
        self.apellido.set_text(_dict.get("Apellido", ""))
        self.escuela.set_text(_dict.get("Escuela", ""))

        model = self.grado.get_model()
        item = model.get_iter_first()
        grado = _dict.get("Grado", "")
        while item:
            valor = model.get_value(item, 0)
            if valor == grado:
                self.grado.set_active_iter(item)
                break
            item = model.iter_next(item)

        model = self.edad.get_model()
        item = model.get_iter_first()
        edad = _dict.get("Edad", "")
        while item:
            valor = model.get_value(item, 0)
            if valor == edad:
                self.edad.set_active_iter(item)
                break
            item = model.iter_next(item)
