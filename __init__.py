# __init__.py
bl_info = {
    "name": "Quick Sidebar Switcher",
    "author": "hyeffect55",
    "version": (1, 4, 0),
    "blender": (5, 0, 1),
    "location": "3D Viewport > Ctrl+Shift+A",
    "description": "Quickly switch between Side Panel tabs with a popup menu",
    "warning": "",
    "doc_url": "",
    "category": "User Interface",
}

import bpy
from . import common
from . import ops_view3d
from . import ops_node
from . import ops_dopesheet
from . import preferences
from . import keymap

def register():
    common.CACHED_TABS.clear()
    ops_view3d.register()
    ops_node.register()
    ops_dopesheet.register()
    preferences.register()
    keymap.register()

def unregister():
    keymap.unregister()
    preferences.unregister()
    ops_dopesheet.unregister()
    ops_node.unregister()
    ops_view3d.unregister()

if __name__ == "__main__":
    register()
