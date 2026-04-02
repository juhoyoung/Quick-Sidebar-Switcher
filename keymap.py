# keymap.py
import bpy

addon_keymaps = []

def update_keymap():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    
    register_keymap()

def register_keymap():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        
        try:
            prefs = bpy.context.preferences.addons[__package__].preferences
            key = prefs.shortcut_key
            use_ctrl = prefs.use_ctrl
            use_shift = prefs.use_shift
            use_alt = prefs.use_alt
        except:
            key = 'A'
            use_ctrl = True
            use_shift = True
            use_alt = False
        
        kmi = km.keymap_items.new(
            'view3d.sidebar_tab_menu',
            key,
            'PRESS',
            ctrl=use_ctrl,
            shift=use_shift,
            alt=use_alt
        )
        kmi.active = True
        addon_keymaps.append((km, kmi))
        
def register():
    register_keymap()

def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()