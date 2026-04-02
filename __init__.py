# __init__.py
bl_info = {
    "name": "Quick Sidebar Switcher",
    "author": "happy Blender 😒",
    "version": (1, 0, 0),
    "blender": (5, 0, 0),
    "location": "3D Viewport > Ctrl+Shift+A",
    "description": "Quickly switch between Side Panel tabs with a popup menu",
    "warning": "",
    "doc_url": "",
    "category": "User Interface",
}

import bpy
from . import operators
from . import preferences
from . import keymap

def register():
    operators.register()
    preferences.register()
    keymap.register()

def unregister():
    keymap.unregister()
    preferences.unregister()
    operators.unregister()

if __name__ == "__main__":
    register()
