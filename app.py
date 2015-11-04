from gevent import monkey
monkey.patch_all()
# monkey patch everything
# from twisted.internet import reactor, defer
from docker import Client
import json
import urwid
import gevent


class ContainerListItem(urwid.WidgetWrap):

    container = None

    def __init__(self, container):
        self.container = container

        icon = u"\u25CF"
        name = self.container[u'Names'][0][1:]
        status = self.container[u'Status']
        command = self.container[u'Command']
        image = self.container[u'Image']

        attr = 'cnt_item_' + ('off' if 'Exit' in status else 'on')
        icon = urwid.Text(u"\u25CF", align='center', wrap='clip')
        icon = urwid.AttrMap(icon, attr)

        name = urwid.Text(name, align='left', wrap='clip')
        name = urwid.AttrMap(name, 'cnt_name', 'cnt_name_focus')

        command = urwid.Text(command, align='left', wrap='clip')
        # command = urwid.AttrMap(command, 'cnt_info', 'cnt_name_focus')

        cols = urwid.Columns([
            # ('weight', 1, icon),
            ('weight', 8, name),
            ('weight', 6, urwid.Text(status, align='left', wrap='clip')),
            ('weight', 12, urwid.Text(image, align='left', wrap='clip')),
            ('weight', 12, command),
        ]),
        cols = urwid.Columns(cols, dividechars=0)
        cols = urwid.AttrMap(cols, 'cnt_item', 'cnt_item_focus')
        self.__super.__init__(cols)

    def selectable(self):
        return True

    def keypress(self, size, key):
        return key

    def _start(self, id):
        pass

    def _stop(self, id):
        gevent.spawn(docker_api.stop(container=id))

    def _log(self, id):
        pass

class ContainerList(urwid.ListBox):

    def __init__(self, args={}):
        super(ContainerList, self).__init__(urwid.SimpleFocusListWalker([]))

    def update(self, containers):
        l = []
        for container in containers:
            l.append(ContainerListItem(container))
        self.body[:] = urwid.SimpleFocusListWalker(l)

    def get_selected(self):
        return self.focus.container[u'Id']


#########################################################
#########################################################
#########################################################

class Ui:

    palette = [

        ('cnt_item_focus', 'black', 'dark cyan'),
        ('cnt_item', 'dark gray', ''),

        ('cnt_item_on', 'dark green', ''),
        ('cnt_item_off', 'dark red', ''),

        ('cnt_name', '', ''),
        ('cnt_name_focus', 'black', 'dark cyan'),

        ('cnt_info', 'dark gray', ''),
        ('cnt_info_focus', 'black', 'dark cyan'),

        # ('footer', 'light gray', ''),
    ]
    filter = {'status': 'running'}

    def __init__(self):

        self.listbox = ContainerList()
        self.listbox.update(self.get_containers())

        self.frame = urwid.Frame(urwid.AttrWrap(self.listbox, 'body'))
        self.render_footer()
        self.loop = urwid.MainLoop(self.frame, self.palette, unhandled_input=self.key_press)

    def run(self):
        self.loop.run()

    def render_footer(self):
        footer_text = "r: run  s: stop  a: all s: search q: quit"
        footer = urwid.AttrMap(urwid.Text(footer_text, align='left'), 'footer')
        # footer = urwid.AttrWrap(urwid.Edit(text_edit_cap3, text_edit_text3, wrap='clip' ), 'footer'),
        footer = urwid.AttrMap(urwid.Edit(caption=u'Filter: ', edit_text=u'text', multiline=False, align='left', wrap='space'), 'footer')
        self.frame.footer = footer
        # self.frame.set_focus('footer')

    def get_containers(self):
        if self.filter['status'] == 'all':
            return docker_api.containers(all=True)
        else:
            return docker_api.containers(filters={'status': self.filter['status']})

    def switch_filter(self):
        self.filter['status'] = 'all' if self.filter['status'] == 'running' else 'running'

    def switch_focus(self):
        focused = 'body' if self.frame.get_focus() == 'footer' else 'footer'
        self.frame.set_focus(focused)

    def key_press(self, key):
        # print key
        cid = self.listbox.get_selected()
        # update
        if key in ('tab'):
            self.switch_focus()
        # update
        if key in ('u', 'U'):
            self.update()
        # stop
        if key in ('s', 'S'):
            self._stop(cid)
        # run
        if key in ('r', 'R'):
            self._start(cid)
        # show all (on/off)
        if key in ('a', 'A'):
            self.switch_filter()
            self.frame.set_focus('body')
            self.update()
        # quit
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()

    def update(self):
        self.listbox.update(self.get_containers())
        self.loop.draw_screen()

    # containers methods
    def _stop(self, cid):
        docker_api.stop(cid)

    def _start(self, cid):
        docker_api.start(cid)


def event_watcher(callback):
    # watch for docker events
    events = docker_api.events()
    for raw in events:
        e = json.loads(raw)
        callback()

docker_api = Client(base_url='unix://var/run/docker.sock', version='auto')
ui = Ui()
gevent.spawn(event_watcher, ui.update)
ui.run()
# reactor.run()
