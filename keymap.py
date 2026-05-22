# keymap.py
import bpy

addon_keymaps = []

def register():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')

        # Register default keymap (Ctrl + Shift + A)
        kmi = km.keymap_items.new(
            'view3d.sidebar_tab_menu',
            'A',
            'PRESS',
            ctrl=True,
            shift=True,
            alt=False
        )
        kmi.active = True
        addon_keymaps.append((km, kmi))

def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()