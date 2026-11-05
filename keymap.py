import bpy

addon_keymaps = []
POPUP_KEYMAP_NAME = 'Quick Sidebar Switcher'
POPUP_OPERATOR_ID = 'wm.quick_sidebar_switcher_panel_popup'
_owned_default_keymaps = []


def get_popup_shortcut(context):
    """Read the user binding, including edits or removal in Keymap preferences."""
    keyconfig = context.window_manager.keyconfigs.user
    km = keyconfig.keymaps.get(POPUP_KEYMAP_NAME) if keyconfig else None
    if km:
        return km, next((item for item in km.keymap_items
                         if item.idname == POPUP_OPERATOR_ID and item.active), None)
    return None, None


def is_popup_event(context, event):
    km, item = get_popup_shortcut(context)
    if not item:
        return False
    match = km.keymap_items.match_event(event)
    return match is not None and match.idname == POPUP_OPERATOR_ID and match.active


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

        # This map is evaluated only when selecting an item in the tab list.
        # Do not attach it to a viewport: Ctrl+Click must retain its normal uses.
        if wm.keyconfigs.default.keymaps.get(POPUP_KEYMAP_NAME) is None:
            default_map = wm.keyconfigs.default.keymaps.new(
                name=POPUP_KEYMAP_NAME, space_type='EMPTY',
            )
            _owned_default_keymaps.append(default_map)
        km_popup = kc.keymaps.new(name=POPUP_KEYMAP_NAME, space_type='EMPTY')
        kmi_popup = km_popup.keymap_items.new(
            POPUP_OPERATOR_ID, 'LEFTMOUSE', 'ANY', ctrl=True,
        )
        addon_keymaps.append((km_popup, kmi_popup))

def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    for km in _owned_default_keymaps:
        bpy.context.window_manager.keyconfigs.default.keymaps.remove(km)
    _owned_default_keymaps.clear()
