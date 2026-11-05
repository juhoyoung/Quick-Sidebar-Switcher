import bpy

addon_keymaps = []


def restore_default_shortcuts(context):
    """Restore only this add-on's shortcuts, including deleted user items."""
    wm = context.window_manager
    wm.keyconfigs.update()
    kc_user = wm.keyconfigs.user
    if kc_user is None or not addon_keymaps:
        return False

    for addon_km, addon_kmi in addon_keymaps:
        user_km = kc_user.keymaps.get(addon_km.name)
        if user_km is None:
            user_km = kc_user.keymaps.new(
                name=addon_km.name,
                space_type=addon_km.space_type,
                region_type=addon_km.region_type,
            )

        matches = [
            item for item in user_km.keymap_items
            if item.idname == addon_kmi.idname
        ]
        if not matches:
            matches = [user_km.keymap_items.new(
                addon_kmi.idname, addon_kmi.type, addon_kmi.value,
            )]

        for item in matches:
            # Copy the registered defaults without resetting unrelated shortcuts.
            for attribute in (
                'map_type', 'type', 'value', 'any', 'shift', 'ctrl',
                'alt', 'oskey', 'key_modifier', 'direction', 'repeat', 'active',
            ):
                setattr(item, attribute, getattr(addon_kmi, attribute))

    context.preferences.is_dirty = True
    wm.keyconfigs.update()
    return True


def register():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    if kc:
        # 1. 3D View Keymap
        km_3d = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi_3d = km_3d.keymap_items.new('view3d.sidebar_tab_menu', 'A', 'PRESS', ctrl=True, shift=True)
        kmi_3d.active = True
        addon_keymaps.append((km_3d, kmi_3d))

        # 2. Node Editor Keymap (Shader, Compositor, Geometry Nodes)
        km_node = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
        kmi_node = km_node.keymap_items.new('node.sidebar_tab_menu', 'A', 'PRESS', ctrl=True, shift=True)
        kmi_node.active = True
        addon_keymaps.append((km_node, kmi_node))

        # 3. Dopesheet Keymap
        km_dope = kc.keymaps.new(name='Dopesheet', space_type='DOPESHEET_EDITOR')
        kmi_dope = km_dope.keymap_items.new('dopesheet.sidebar_tab_menu', 'A', 'PRESS', ctrl=True, shift=True)
        kmi_dope.active = True
        addon_keymaps.append((km_dope, kmi_dope))

        # 4. Graph Editor
        km_graph = kc.keymaps.new(name='Graph Editor', space_type='GRAPH_EDITOR')
        kmi_graph = km_graph.keymap_items.new('graph.sidebar_tab_menu', 'A', 'PRESS', ctrl=True, shift=True)
        kmi_graph.active = True
        addon_keymaps.append((km_graph, kmi_graph))

        # 5. Image/UV Editor
        km_image = kc.keymaps.new(name='Image', space_type='IMAGE_EDITOR')
        kmi_image = km_image.keymap_items.new('image.sidebar_tab_menu', 'A', 'PRESS', ctrl=True, shift=True)
        kmi_image.active = True
        addon_keymaps.append((km_image, kmi_image))

def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
