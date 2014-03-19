Panezr
======

A sublimetext3 plugin for automatically limiting the number of tabs open at one
time in a each pane.

Panezr works by tracking each view as it is opened. When a new view is opened,
and that results in tabs in the view's pane being less than the min_tab_width 
setting (80 pixels by default) then Panezr will close as many tabs as needed
to bring the tab width over the minimum.

However, Panezr will *never* close scratch or unsaved tabs, so if you open a lot
of those in one pane, you will still get a horrible smushed unreadable mess.
