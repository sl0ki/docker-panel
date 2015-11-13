import urwid


class ModalWindow(urwid.WidgetWrap):

    parent = None
    overlay = True
    linebox = True

    def __init__(self, body, loop, width=0, height=0):

        self.body = body
        self.loop = loop
        self.parent = loop.widget

        if body is None:
            body = urwid.Filler(urwid.Divider(), 'top')

        self.frame = urwid.Frame(body, focus_part='footer')
        widget = self.frame

        # decoration
        widget = urwid.Padding(widget, ('fixed left',2), ('fixed right',2))
        widget = urwid.Filler(widget, ('fixed top',1), ('fixed bottom',1))
        if self.linebox == True:
            widget = urwid.LineBox(widget)
        if self.overlay == True:
            widget = urwid.Overlay(widget, self.parent, 'center', width + 2, ('relative', 30), height + 2)

        super(ModalWindow, self).__init__(widget)

    def add_buttons(self, buttons):
        l = []
        for name, exitcode in buttons:
            b = urwid.Button(name, self.button_press)
            b.exitcode = exitcode
            b = urwid.AttrWrap(b, 'button normal', 'button select')
            l.append(b)
        self.buttons = urwid.GridFlow(l, 10, 3, 1, 'center')
        self.frame.footer = self.buttons

    def keypress(self, size, key):
        if key in ('q', 'Q', 'esc'):
             self.hide()
        else:
            super(ModalWindow, self).keypress(size, key)

    def button_press(self, button):
        self.hide()

    def show(self):
        self.loop.widget = self

    def hide(self):
        self.loop.widget = self.parent
