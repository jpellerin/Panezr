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
        print("pre close", view.file_name())
        self.views.remove(view)

    def on_activated(self, view):
        print("activated", view.file_name())
        self.views.promote(view)
        self.close_overflow(view)

    def on_modified_async(self, view):
        self.views.promote(view)

    def close_overflow(self, last):
        aw = sublime.active_window()
        ag = aw.active_group()
        w, _ = last.viewport_extent()
        maxtabs = int(w // 80)  # XXX setting

        if not self.views.diff(aw, ag):
            return

        def inner():
            if self.working:
                return
            self.working = True
            for view in self.iter_closeable(aw, ag, maxtabs):
                print("close", view.file_name())
                view.close()
            self.working = False
        sublime.set_timeout(inner, 200)

    def iter_closeable(self, aw, ag, maxtabs):
        views = aw.views_in_group(ag)
        print("views open", len(views))
        if len(views) <= maxtabs or not maxtabs:
            return
        vids = set([v.id() for v in views])
        candidates = [view for view in self.views
                      if self.closeable(view) and view.id() in vids]
        print("closeable views", len(candidates))
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

    def record_counts(self, view):
        wv = view.window()
        gp, _ = wv.get_view_index(view)
        if gp:
            self._wids.setdefault(wv.id(), {})[gp] = len(
                wv.views_in_group(gp))

    def remove(self, view):
        if view.id() in self._ids:
            self._order.remove(view)
            self._ids.remove(view.id())
        self.record_counts(view)

    def add(self, view):
        if view.id() in self._ids:
            return
        self._ids.add(view.id())
        self._order.append(view)
        self.record_counts(view)

    def diff(self, aw, gp):
        vig = len(aw.views_in_group(gp))
        last = self._wids.get(aw.id(), {}).get(gp, None)
        print("tabs: %s last: %s" % (vig, last))
        self._wids.setdefault(aw.id(), {})[gp] = vig
        if last is None:
            return False
        return vig > last

    def promote(self, view):
        self.remove(view)
        self.add(view)
