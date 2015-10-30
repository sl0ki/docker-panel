from twisted.internet import reactor, defer
from threading import Thread
from docker import Client
from docker import Client
import json
import urwid


class ContainerListItem(urwid.WidgetWrap):

    container = None

    def __init__(self, container):
        self.container = container

        name = self.container[u'Names'][0][1:]
        status = self.container[u'Status']
        command = self.container[u'Command']
        image = self.container[u'Image']

        cols = urwid.Columns([
            ('weight', 10, urwid.Text(name, align='left', wrap='clip')),
            ('weight', 7, urwid.Text(status, align='left', wrap='clip')),
            ('weight', 12, urwid.Text(image, align='left', wrap='clip')),
            ('weight', 12, urwid.Text(command, align='left', wrap='clip')),
        ]),
        cols = urwid.Columns(cols, dividechars=1)
        w = urwid.AttrMap(cols, None, 'focustext')
        self.__super.__init__(w)

    def selectable(self):
        return True

    def keypress(self, size, key):
        if key == "enter":
            print "Select"
        return key


class ContainerList(urwid.ListBox):

    def __init__(self, args={}):
        super(ContainerList, self).__init__(urwid.SimpleFocusListWalker([]))
        self.update()

    def update(self):
        containers = docker_api.containers(filters={'status': 'running'})
        l = []
        for container in containers:
            l.append(ContainerListItem(container))
        self.body[:] = urwid.SimpleFocusListWalker(l)


class Ui:

    palette = [('focustext', 'light gray', 'dark cyan'), ('footer', 'light gray', 'dark cyan')]

    def __init__(self):

        self.listbox = ContainerList()
        self.frame = urwid.Frame(urwid.AttrWrap(self.listbox, 'body'))
        self.render_footer()
        self.loop = urwid.MainLoop(self.frame, self.palette, unhandled_input=self.key_press, event_loop=urwid.TwistedEventLoop(reactor=reactor)).run()

    def render_footer(self):
        footer_text = "r: run  s: stop  a: all s: search q: quit"
        footer = urwid.AttrMap(urwid.Text(footer_text, align='left'), 'footer')
        self.frame.footer = footer

    def key_press(self, key):
        if key in ('u', 'U'):
            self.update()

        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()

    def update(self):
        self.listbox.update()


def event_watcher():
        events = docker_api.events()
        for raw in events:
            evt = json.loads(raw)
            print evt
            ui.update()

docker_api = Client(base_url='unix://var/run/docker.sock', version='auto')
ui = Ui()
Thread(target=event_watcher).start()
reactor.run()
