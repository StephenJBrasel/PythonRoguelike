# PythonProjects
Tutorial Projects.

This is a follow-along project for "The Complete Roguelike Tutorial" using libtcod and pygame:
https://www.youtube.com/playlist?list=PLKUel_nHsTQ1yX7tQxR_SQRdcOFyXfNAb

Differences: 
I'm using Python 3.6 instead of the tutorial's Python 2.
I'm using tcod instead of libtcodpy. 
you can fully exit the game from within any menu. 
I'm using several different keywords for spells.
    l = lightning
    c = confusion
    f = fireball
    To exit the interface for any spell, press ESC or TAB. 
The tunneling in the tutorial had a bug that added dead ends. Fixed the bug, can create dead ends as a feature later.

ATTRIBUTIONS:
Music from Jukedeck - create your own at http://jukedeck.com.
Main Menu background: By: Tontan Travel Link: www.tontantravel.com/

TODO:
BUGFIX: If you press the Red X to close the window while using an item (scroll) from within the inventory menu, the window does not close. The window should close.