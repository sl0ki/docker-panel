from docker import Client
import json
import urwid

def key_press(key):
    if key in ('q', 'Q'):
        raise urwid.ExitMainLoop()


from docker import Client
api = Client(base_url='unix://var/run/docker.sock', version='auto')

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

        name = self.container[u'Names'][0]
        status = self.container[u'Status']
        command = self.container[u'Command']
        image = self.container[u'Image']

        cols = urwid.Columns( [
            # urwid.AttrWrap(urwid.Text("Weight 1", align='left', wrap='clip')),
            ('weight', 10, urwid.Text(name, align='left', wrap='clip')),
            ('weight', 7, urwid.Text(status, align='left', wrap='clip')),
            ('weight', 12, urwid.Text(image, align='left', wrap='clip')),
            ('weight', 12, urwid.Text(command , align='left', wrap='any')),
            ]),
        cols = urwid.Columns(cols, dividechars=1)
        w = urwid.AttrMap(cols, None ,'focustext')
        self.__super.__init__(w)

    def selectable (self):
        return True

    def keypress(self, size, key):
        if key == "enter":
            print "Select"
        return key

l = []

containers = api.containers(filters={'status': 'running'})
# print containers[0]
# exit()
for container in containers:
    l.append(MenuItem(container))

listbox = urwid.ListBox(urwid.SimpleFocusListWalker(l))
frame = urwid.Frame(urwid.AttrWrap(listbox, 'body'))


loop = urwid.MainLoop(frame, palette, unhandled_input=key_press)
loop.run()
