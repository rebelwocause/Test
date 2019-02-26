#!/usr/bin/python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango, GObject
import sys

TEST_INFO = "\
Test of gtk3 3.22.x GtkTextView Rendering - Affects GtkSourceView -> GEdit, Xed etc...\n\
\n\
Rendering problem when height of GtkTextView gets too large - many lines/larger fonts\n\
No Text scaling is used ( default 1.0 )\n\
Once a certain 'magic' height is reached the textview renders large portions\n\
of background as black. May have to scroll up and down to see this...\n\
Approximate 'magic' height = INT_MAX / 255 = 2147483647 / 255 = 8421504\n\
\n\
Any combination of font size and number of lines that exceeds the 'magic' number\n\
appears to cause the problem\n\
lines			Monospace Font Size\n\
56200				96\n\
110900				48\n\
383000				13\n\
444000				12\n\
468000				11\n\
496000				10\n\
562000				9\n\
648000				8\n\
\n\
Problem occurs on Mint 19.0 gtk 3.22.30 , Mint 19.1 gtk 3.22.30, LMDE3 gtk 3.22.11\n\
Fine on Mint 18.2 LiveCD gtk 3.18.9\n\
Fine on Mint 17.3, Gtk 3.10.8\n\
\n\
I believe this problem is what has been referenced in:\n\
https://forums.linuxmint.com/viewtopic.php?t=272218\
"


class MyWindow(Gtk.ApplicationWindow):

    def __init__(self, app):
        gtkver = "Gtk: %s.%s.%s GtkTextView Rendering Test" % (Gtk.get_major_version(), Gtk.get_minor_version(), Gtk.get_micro_version())
        Gtk.Window.__init__(self, title=gtkver, application=app)
        self.set_default_size(1000, 700)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_border_width(5)
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        buffer1 = Gtk.TextBuffer()
        buffer1.connect('changed', self.buffer_changed)

        self.textview = Gtk.TextView(buffer=buffer1)
        self.textview.set_wrap_mode(Gtk.WrapMode.NONE)
        self.textview.set_editable(False)

        # Set border window sizes - makes no difference
        self.textview.set_border_window_size(Gtk.TextWindowType.LEFT, 20)
        self.textview.set_border_window_size(Gtk.TextWindowType.RIGHT, 20)
        self.textview.set_border_window_size(Gtk.TextWindowType.TOP, 20)
        self.textview.set_border_window_size(Gtk.TextWindowType.BOTTOM, 20)

        scrolled_window.add(self.textview)

        # Add font button so we can change fonts/size
        fontbtn = Gtk.FontButton()

        # initialize font - start with 'Monospace 12'
        font_desc = Pango.FontDescription('Monospace 12')
        self.textview.modify_font(font_desc)
        fontbtn.set_font('Monospace 12')
        fontbtn.connect('font-set', self.set_font)

        # Spin button to change number of lines
        spinadjustment = Gtk.Adjustment(450000.0, 50000.0, 700000.0, 10000.0, 100000.0, 0.0)
        self.spinlines = Gtk.SpinButton.new(spinadjustment, 0, 0)
        self.spinlines.set_update_policy(Gtk.SpinButtonUpdatePolicy.IF_VALID)
        self.spinlines.set_value(450000.0)
        self.spinlines.connect('value-changed', self.on_spinchanged)

        hbox1 = Gtk.Box()
        hbox1.set_orientation(Gtk.Orientation.HORIZONTAL)
        hbox1.pack_start(Gtk.Label('Number of Lines:'), False, False, 10)
        hbox1.pack_start(self.spinlines, False, False, 10)
        hbox1.pack_start(fontbtn, True, True, 0)

        # label for info
        self.label = Gtk.Label()
        # Spinner...
        self.spinner = Gtk.Spinner()
        self.spinner.set_size_request(24, 24)
        self.spinner.set_no_show_all(True)

        hbox2 = Gtk.Box()
        hbox2.set_orientation(Gtk.Orientation.HORIZONTAL)
        hbox2.pack_start(self.label, True, True, 0)
        hbox2.pack_start(self.spinner, False, False, 10)

        vbox = Gtk.Box()
        vbox.set_orientation(Gtk.Orientation.VERTICAL)
        vbox.pack_start(hbox1, False, False, 2)
        vbox.pack_start(hbox2, False, False, 2)
        vbox.pack_start(scrolled_window, True, True, 2)

        self.add(vbox)

        GObject.idle_add(self.loadtext)


    def loadtext(self):
        # add some test text to textview
        stext = TEST_INFO
        adj = self.spinlines.get_adjustment()
        numlines = int(adj.get_value())

        textlines = 2 * TEST_INFO.count('\n')

        for i in range(numlines - textlines - 1):
            stext += "1\n"
        stext += TEST_INFO

        self.textview.get_buffer().set_text(stext)
        return False

    def on_spinchanged(self, range):
        self.loadtext()

    def update(self):
        # update size
        iter, _ = self.textview.get_line_at_y(0)
        _, lheight = self.textview.get_line_yrange(iter)
        nlines = self.textview.get_buffer().get_line_count()
        adj = self.textview.get_vadjustment()
        stext = "Line Height: {}, # Lines: {}, Height * Lines: {}, Vadjust upper: {}".format(lheight,
            nlines, lheight * nlines, adj.get_upper())

        if (lheight * nlines > 8421504):
            self.label.set_markup("<span color='red'>" + stext + "</span>")
        else:
            self.label.set_text(stext)
        # scroll to bottom
        adj.set_value(adj.get_upper() - adj.get_page_size())


    def buffer_changed(self, notused):
        self.label.set_text("Please wait while updating...")
        self.spinner.show()
        self.spinner.start()
        while Gtk.events_pending():
            Gtk.main_iteration()
        self.update()
        self.spinner.stop()
        self.spinner.hide()


    def set_font(self, button):
        strFont = button.get_font_name()
        if strFont:
            font_desc = Pango.FontDescription(strFont)
            if font_desc:
                self.textview.modify_font(font_desc)
                self.buffer_changed(None)


class MyApplication(Gtk.Application):

    def __init__(self):
        Gtk.Application.__init__(self)

    def do_activate(self):
        win = MyWindow(self)
        win.show_all()

    def do_startup(self):
        Gtk.Application.do_startup(self)


app = MyApplication()
exit_status = app.run(sys.argv)
sys.exit(exit_status)
