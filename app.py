from docker import Client
import json
import urwid
from docker import Client
from twisted.internet import pollreactor
pollreactor.install()
from twisted.internet import reactor, defer



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
            ('weight', 12, urwid.Text(command , align='left', wrap='clip')),
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

    frame = None

    def __init__(self):
        listbox = ContainerList()
        self.frame = urwid.Frame(urwid.AttrWrap(listbox, 'body'))

    def key_press(self, key):
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()


docker_api = Client(base_url='unix://var/run/docker.sock', version='auto')
palette = [ ('focustext','light gray','dark cyan') ]
ui = Ui()

urwid.MainLoop(ui.frame, palette, unhandled_input=ui.key_press, event_loop=urwid.TwistedEventLoop(reactor=reactor)).run()
reactor.run()
