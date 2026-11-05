"""Run with Blender --background --factory-startup --python <this file>."""
import importlib
from pathlib import Path
import sys

import bpy


root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root.parent))
addon = importlib.import_module(root.name)
addon.register()

try:
    wm = bpy.context.window_manager
    wm.keyconfigs.update()
    keymap = addon.keymap
    user_maps = wm.keyconfigs.user.keymaps
    addon_km, addon_kmi = keymap.addon_keymaps[0]
    user_km = user_maps[addon_km.name]
    item = next(kmi for kmi in user_km.keymap_items if kmi.idname == addon_kmi.idname)
    user_km.keymap_items.remove(item)
    wm.keyconfigs.update()
    assert not any(kmi.idname == addon_kmi.idname for kmi in user_maps[addon_km.name].keymap_items)

    other = user_maps[addon_km.name].keymap_items.new('wm.search_menu', 'F8', 'PRESS')
    other_id = other.id
    node_km, node_kmi = keymap.addon_keymaps[1]
    node_item = next(kmi for kmi in user_maps[node_km.name].keymap_items if kmi.idname == node_kmi.idname)
    node_item.type = 'B'
    node_item.active = False
    node_item.alt = True

    assert bpy.ops.preferences.restore_sidebar_switcher_shortcuts() == {'FINISHED'}
    wm.keyconfigs.update()
    for km, default in keymap.addon_keymaps:
        items = [item for item in user_maps[km.name].keymap_items if item.idname == default.idname]
        assert len(items) == 1, (km.name, len(items))
        item = items[0]
        assert (item.type, item.value, item.ctrl, item.shift, item.alt, item.active) == ('A', 'PRESS', 1, 1, 0, True)

    other = user_maps[addon_km.name].keymap_items.from_id(other_id)
    assert other is not None and other.type == 'F8'

    assert keymap.restore_default_shortcuts(bpy.context)
    for km, default in keymap.addon_keymaps:
        assert sum(item.idname == default.idname for item in user_maps[km.name].keymap_items) == 1
    print('PASS: deleted/modified shortcuts restored; unrelated shortcut preserved; no duplicates')
finally:
    addon.unregister()
