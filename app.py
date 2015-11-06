from gevent import monkey
monkey.patch_all()
# monkey patch everything
# from twisted.internet import reactor, defer
from docker import Client
import json
import urwid
import gevent


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
            widget = urwid.Overlay(widget, self.parent, 'center', width + 2, 'middle', height + 2)

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

class ContainerLogs(ModalWindow):

    overlay = False
    linebox = False

    def __init__(self, logs, loop):
        logs = urwid.Filler(urwid.Text(logs), 'bottom')
        self.__super.__init__(logs, loop)


class ContainerListItem(urwid.WidgetWrap):

    container = None

    def __init__(self, container):
        self.container = container

        name = self.container[u'Names'][0][1:]
        status = self.container[u'Status']
        command = self.container[u'Command']
        image = self.container[u'Image']

        attr = 'cnt_item_' + ('off' if 'Exit' in status else 'on')
        icon = urwid.Text(u"\u25CF ", align='center', wrap='clip')
        icon = urwid.AttrMap(icon, attr)

        name = urwid.AttrMap(urwid.Text(name, align='left', wrap='clip'), 'cnt_name');
        status = urwid.AttrMap(urwid.Text(status, align='left', wrap='clip'), 'cnt_info');
        image = urwid.AttrMap(urwid.Text(image, align='left', wrap='clip'), 'cnt_info');
        command = urwid.AttrMap(urwid.Text(command, align='left', wrap='clip'), 'cnt_info');

        cols = urwid.Columns([
            ('weight', 1, icon),
            ('weight', 8, name),
            ('weight', 6, status),
            ('weight', 12, image),
            ('weight', 12, command),
        ]),
        cols = urwid.Columns(cols, dividechars=0)
        cols = urwid.AttrMap(cols, 'cnt_item', {
            'default'   : 'cnt_item_focus',
            'cnt_name'  : 'cnt_item_focus',
            'cnt_info'  : 'cnt_item_focus',
        })
        self.__super.__init__(cols)

    def selectable(self):
        return True

    def keypress(self, size, key):
        return key


class ContainerList(urwid.ListBox):

    def __init__(self, args={}):
        super(ContainerList, self).__init__(urwid.SimpleFocusListWalker([]))

    def update(self, containers):
        l = []
        for container in containers:
            l.append(ContainerListItem(container))
        self.body[:] = urwid.SimpleFocusListWalker(l)
        self.set_focus_path(self.get_focus_path())

    def get_selected(self):
        return self.focus.container[u'Id']


#########################################################
#########################################################
#########################################################

class Ui:

    palette = [
        ('body','black','white'),
        ('border','black','white'),
        ('shadow','white','black'),
        ('selectable','black', 'dark cyan'),
        ('focus','black','dark cyan','bold'),
        ('focustext','light gray','dark blue'),
        # ('button normal','light gray', 'dark blue', 'standout'),
        ('button select','black',  'dark cyan'),

        ('cnt_item_focus', 'black', 'dark cyan'),
        ('cnt_item', 'dark gray', ''),

        ('cnt_item_on', 'dark green', ''),
        ('cnt_item_off', 'dark red', ''),

        ('cnt_name', '', ''),
        ('cnt_info', 'dark gray', ''),

        ('footer', 'dark gray', ''),
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
        status = urwid.AttrMap(urwid.Text('all/run  34/46', align='right'), 'footer_status');
        self.frame.footer = urwid.Columns([footer, status])
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
        if key in ('u', 'U'): self.update()
        # stop
        if key in ('s', 'S'): self._stop(cid)
        # run
        if key in ('r', 'R'): self._start(cid)
        # delete
        if key in ('d', 'D'): self._delete(cid)
        # delete
        if key in ('l', 'L'): self._logs(cid)
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

    def _delete(self, cid):
        modal = ModalWindow(None, self.loop, 40, 7)
        modal.add_buttons([ ("Yes", 0), ("No", 0) ])
        modal.show()
        # docker_api.delete(cid)

    def _start(self, cid):
        docker_api.start(cid)

    def _logs(self, cid):
        logs = docker_api.logs(container=cid,stdout=True,stderr=True,stream=False,tail=50)
        modal = ContainerLogs(logs, self.loop)
        modal.show()


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
