import sublime
import sublime_plugin


class PaneTabListener(sublime_plugin.EventListener):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.views = Views(self)
        self.working = False
        self.refresh()

    def refresh(self):
        self.windows = sublime.windows()
        for window in self.windows:
            ngroups = window.num_groups()
            for gp in range(0, ngroups):
                for view in window.views_in_group(gp):
                    self.views.add(view)

    def on_close(self, view):
        self.views.remove(view)

    def on_activated(self, view):
        isnew = self.views.isnew(view)
        self.views.promote(view)
        # maybe just do a 'new' check -- is this view new?
        if isnew:
            self.close_overflow(view)

    def on_modified_async(self, view):
        self.views.promote(view)

    def close_overflow(self, last):
        aw = sublime.active_window()
        ag = aw.active_group()
        w, _ = last.viewport_extent()
        mintabwidth = aw.active_view().settings().get(
            'panezr', {}).get('min_tab_width', 80)
        maxtabs = int(w // mintabwidth)

        def inner():
            if self.working:
                return
            self.working = True
            for view in self.iter_closeable(aw, ag, maxtabs):
                self.views.remove(view)
                view.close()
            self.working = False
        sublime.set_timeout(inner, 200)

    def iter_closeable(self, aw, ag, maxtabs):
        views = aw.views_in_group(ag)
        if len(views) <= maxtabs or not maxtabs:
            return
        vids = set([v.id() for v in views])
        candidates = [view for view in self.views
                      if self.closeable(view) and view.id() in vids]
        while len(candidates) > maxtabs:
            yield candidates.pop(0)

    def closeable(self, view):
        if view.is_dirty() or view.is_scratch() or view.is_loading() \
                or self.is_preview(view):
            return False
        return True

    def is_preview(self, view):
        return sublime.active_window().get_view_index(view)[1] == -1


class Views(object):
    def __init__(self, window):
        self.window = window
        self._ids = set()
        self._order = []
        self._wids = {}

    def __iter__(self):
        return iter(self._order)

    def isnew(self, view):
        return view.id() not in self._ids

    def remove(self, view):
        if view.id() in self._ids:
            self._order.remove(view)
            self._ids.remove(view.id())

    def add(self, view):
        if view.id() in self._ids:
            return
        self._ids.add(view.id())
        self._order.append(view)

    def promote(self, view):
        self.remove(view)
        self.add(view)
