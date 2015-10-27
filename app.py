from docker import Client
import json
import urwid

def key_press(key):
    if key in ('q', 'Q'):
        raise urwid.ExitMainLoop()


from docker import Client
api = Client(base_url='unix://docker.sock', version='auto')

palette = [
    # ('body','black','light gray', 'standout'),
    # ('border','black','dark blue'),
    # ('shadow','white','black'),
    # ('selectable','black', 'dark cyan'),
    # ('focus','white','dark blue','bold'),
    ('focustext','light gray','dark cyan'),
    ]


class MenuItem(urwid.WidgetWrap):

    container = None

    def __init__(self, container):
        self.container = container
        col = urwid.Columns([urwid.Text(self.container[u'Names'][0]), urwid.Text("testc dc ds")])
        w = urwid.AttrMap(col, None ,'focustext')
        self.__super.__init__(w)

    def selectable (self):
        return True

    def keypress(self, size, key):
        if key == "enter":
            print "Select"
        return key

l = []

containers = api.containers(filters={'status': 'running'})
for container in containers:
    l.append(MenuItem(container))

listbox = urwid.ListBox(urwid.SimpleFocusListWalker(l))
frame = urwid.Frame(urwid.AttrWrap(listbox, 'body'))


loop = urwid.MainLoop(frame, palette, unhandled_input=key_press)
loop.run()
