#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from gevent import monkey
monkey.patch_all()

from docker import Client
import json
import urwid
import gevent

from modal import ModalWindow
import config


class ErrorWindow(ModalWindow):

    def __init__(self, loop, msg):
        self.__super.__init__(self.get_body(msg), loop, 80, 5)
        self.show()

    def get_body(self, msg):
        msg = urwid.Text(('text_danged', msg))
        msg = urwid.Filler(msg)
        return msg

class HelpWindow(ModalWindow):

    def __init__(self, loop):
        self.__super.__init__(self.get_body(), loop, 50, 10)
        self.show()

    def get_body(self):
        l = []
        for i in config.hotkey:
            key = urwid.Text(['"', ('help_key', i['key']), '": '], align='right')
            dscr = urwid.Text(('help_dscr', i['dscr']), align='left')
            row = urwid.Columns([
                ('weight', 2, key),
                ('weight', 4, dscr)
            ])
            l.append(row)
        return urwid.ListBox(urwid.SimpleFocusListWalker(l))

#-------------------------------------------------------------------------------

class ContainerLogs(ModalWindow):

    overlay = False
    linebox = False

    def __init__(self, logs, loop):
        logs = urwid.Filler(urwid.Text(logs), 'bottom')
        self.__super.__init__(logs, loop)
        self.show()


#-------------------------------------------------------------------------------

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

#-------------------------------------------------------------------------------

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
        return self.focus.container[u'Id'] if hasattr(self.focus, 'container') else None


#-------------------------------------------------------------------------------

class Ui:

    filter = {'status': 'running'}

    def __init__(self):

        self.listbox = ContainerList()
        self.listbox.update(self.get_containers())

        self.frame = urwid.Frame(urwid.AttrWrap(self.listbox, 'body'))
        self.render_footer()
        self.loop = urwid.MainLoop(self.frame, config.palette, handle_mouse=False, unhandled_input=self.key_press)

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
        # show all (on/off)
        if key in ('a', 'A'):
            self.switch_filter()
            self.update()
            self.frame.set_focus('body')
        # update
        #if key in ('tab'): self.switch_focus()
        # help window
        if key in ('h', 'H'): HelpWindow(self.loop)
        # update
        if key in ('u', 'U'): self.update()
        # quit
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()

        # get selected container ID
        cid = self.listbox.get_selected()
        if cid == None: return
        # stop
        if key in ('s', 'S'): self._stop(cid)
        # run
        if key in ('r', 'R'): self._start(cid)
        # delete
        if key in ('d', 'D'): self._delete(cid)
        # delete
        if key in ('l', 'L'): self._logs(cid)

    def update(self):
        self.listbox.update(self.get_containers())
        self.loop.draw_screen()

    # containers methods
    def _stop(self, cid):
        docker_api.stop(cid)

    def _delete(self, cid):
        body = urwid.Text(('text_danged', 'Are you sure to delete this container ? '), align='center');
        body = urwid.Filler(body)
        modal = ModalWindow(body, self.loop, 45, 7)
        modal.add_buttons([ ("Yes", 0), ("No", 0) ])
        modal.show()
        # docker_api.delete(cid)

    def _start(self, cid):
        try:
            docker_api.start(cid)
        except BaseException as e:
            ErrorWindow(self.loop, str(e))
            # self.frame.footer = urwid.Text(str(e))

    def _logs(self, cid):
        logs = docker_api.logs(container=cid,stdout=True,stderr=True,stream=False,tail=50)
        modal = ContainerLogs(logs, self.loop)


def event_watcher(callback):
    # watch for docker events
    events = docker_api.events()
    for raw in events:
        e = json.loads(raw)
        callback()

#-------------------------------------------------------------------------------

docker_api = None

def main():
    global docker_api
    docker_api = Client(base_url='unix://var/run/docker.sock', version='auto')
    ui = Ui()
    gevent.spawn(event_watcher, ui.update)
    ui.run()

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
