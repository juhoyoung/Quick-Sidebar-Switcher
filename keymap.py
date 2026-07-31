import bpy

addon_keymaps = []

def register():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    if kc:
        # 1. 3D View Keymap
        km_3d = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi_3d = km_3d.keymap_items.new('wm.quick_sidebar_switcher_menu', 'A', 'PRESS', ctrl=True, shift=True)
        kmi_3d.active = True
        addon_keymaps.append((km_3d, kmi_3d))

        # 2. Node Editor Keymap (Shader, Compositor, Geometry Nodes)
        km_node = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
        kmi_node = km_node.keymap_items.new('wm.quick_sidebar_switcher_menu', 'A', 'PRESS', ctrl=True, shift=True)
        kmi_node.active = True
        addon_keymaps.append((km_node, kmi_node))

        # 3. Dopesheet Keymap
        km_dope = kc.keymaps.new(name='Dopesheet', space_type='DOPESHEET_EDITOR')
        kmi_dope = km_dope.keymap_items.new('wm.quick_sidebar_switcher_menu', 'A', 'PRESS', ctrl=True, shift=True)
        kmi_dope.active = True
        addon_keymaps.append((km_dope, kmi_dope))

        # 4. Graph Editor
        km_graph = kc.keymaps.new(name='Graph Editor', space_type='GRAPH_EDITOR')
        kmi_graph = km_graph.keymap_items.new('wm.quick_sidebar_switcher_menu', 'A', 'PRESS', ctrl=True, shift=True)
        kmi_graph.active = True
        addon_keymaps.append((km_graph, kmi_graph))

        # 5. Image/UV Editor
        km_image = kc.keymaps.new(name='Image', space_type='IMAGE_EDITOR')
        kmi_image = km_image.keymap_items.new('wm.quick_sidebar_switcher_menu', 'A', 'PRESS', ctrl=True, shift=True)
        kmi_image.active = True
        addon_keymaps.append((km_image, kmi_image))

def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
