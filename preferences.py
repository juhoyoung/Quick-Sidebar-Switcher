# preferences.py
import bpy
from bpy.types import AddonPreferences, Operator, PropertyGroup
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty, CollectionProperty, PointerProperty

# ------------------------------------------------------------------------
# UI Drawing Functions
# ------------------------------------------------------------------------
def get_user_kmi_from_addon_kmi(addon_km, addon_kmi, kc_user):
    if addon_km.name in kc_user.keymaps:
        user_km = kc_user.keymaps[addon_km.name]
        for user_kmi in user_km.keymap_items:
            if user_kmi.idname == addon_kmi.idname:
                return user_km, user_kmi
    return None, None

def draw_kmi(kmi, layout):
    map_type = kmi.map_type
    col = layout.column()
    if kmi.show_expanded:
        col = col.column()
        box = col.box()
    else:
        box = col.column()
    box.use_property_split = False
    split = box.split(align=True)

    row = split.row(align=True)
    row.prop(kmi, "show_expanded", text="", emboss=False)
    row.prop(kmi, "active", text="", emboss=False)

    name = kmi.name if kmi.name else "Quick Sidebar Switcher"
    row.label(text=name)

    row = split.row()
    row.prop(kmi, "map_type", text="")
    if map_type == 'KEYBOARD':
        row.prop(kmi, "type", text="", full_event=True)
    elif map_type in {'MOUSE', 'NDOF'}:
        row.prop(kmi, "type", text="", full_event=True)
    elif map_type == 'TWEAK':
        subrow = row.row()
        subrow.prop(kmi, "type", text="")
        subrow.prop(kmi, "value", text="")
    elif map_type == 'TIMER':
        row.prop(kmi, "type", text="")
    else:
        row.label()

    fixed_icon = 'OPTIONS' if bpy.app.version >= (4, 3, 0) else 'REMOVE'
    row.prop(kmi, "active", text="", icon=fixed_icon if kmi.active else 'TRACKING_CLEAR_BACKWARDS', emboss=False)

    if kmi.show_expanded:
        split = box.split(factor=0.5)
        split.prop(kmi, "idname", text="")

        if map_type not in {'TEXTINPUT', 'TIMER'}:
            sub = split.column()
            subrow = sub.row(align=True)

            if map_type == 'KEYBOARD':
                subrow.prop(kmi, "type", text="", event=True)
                subrow.prop(kmi, "value", text="")
                subrow_repeat = subrow.row(align=True)
                subrow_repeat.prop(kmi, "repeat", text="Repeat")
                subrow_repeat.active = kmi.value in {'ANY', 'PRESS'}
            elif map_type in {'MOUSE', 'NDOF'}:
                subrow.prop(kmi, "type", text="")
                subrow.prop(kmi, "value", text="")

            if map_type in {'KEYBOARD', 'MOUSE'} and kmi.value == 'CLICK_DRAG':
                subrow = sub.row()
                subrow.direction(kmi, "direction")

            subrow = sub.row()
            subrow.scale_x = 0.75
            subrow.prop(kmi, "any", toggle=True)
            subrow.prop(kmi, "shift_ui", toggle=True)
            subrow.prop(kmi, "ctrl_ui", toggle=True)
            subrow.prop(kmi, "alt_ui", toggle=True)
            subrow.prop(kmi, "oskey_ui", text="Cmd", toggle=True)
            subrow.prop(kmi, "key_modifier", text="", event=True)

        box.template_keymap_item_properties(kmi)

# ------------------------------------------------------------------------
# Structural Property Groups
# ------------------------------------------------------------------------
class SidebarTabFilterItem(PropertyGroup):
    name: StringProperty()
    use: BoolProperty(default=False)

class EditorFilterSettings(PropertyGroup):
    filter_mode: EnumProperty(
        name="Tab Filter",
        items=[('NONE', "Show All", ""), ('WHITELIST', "Whitelist", ""), ('BLACKLIST', "Blacklist", "")],
        default='NONE',
    )
    show_expanded: BoolProperty(name="Show Filter Settings", default=False)
    whitelist_tabs: CollectionProperty(type=SidebarTabFilterItem)
    blacklist_tabs: CollectionProperty(type=SidebarTabFilterItem)

class PREFERENCES_OT_refresh_tab_filters(Operator):
    """Fetch currently available sidebar tabs for a specific editor"""
    bl_idname = "preferences.refresh_tab_filters"
    bl_label = "Fetch Current Tabs"
    editor_type: StringProperty()

    def execute(self, context):
        # Retrieve preferences and settings for the specific editor type
        prefs = context.preferences.addons[__package__].preferences
        settings = prefs.get_editor_settings(self.editor_type)
        if not settings: return {'CANCELLED'}

        # Find the correct area and UI region to create a context override
        target_window = None
        target_area = None
        target_region = None

        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == self.editor_type:
                    target_window = window
                    target_area = area
                    for region in area.regions:
                        if region.type == 'UI':
                            target_region = region
                            break
                    if target_area: break
            if target_area: break

        # Prepare kwargs for temp_override
        override_kwargs = {}
        if target_window and target_area:
            override_kwargs["window"] = target_window
            override_kwargs["area"] = target_area
            if target_region:
                override_kwargs["region"] = target_region

        tabs_set = set()
        from .common import get_all_subclasses

        # Iterate through all panel classes
        for panel_cls in get_all_subclasses(bpy.types.Panel):
            try:
                if not panel_cls.is_registered: continue
            except AttributeError:
                if not hasattr(panel_cls, "bl_rna"): continue

            # Check if the panel belongs to the target editor and UI region
            if getattr(panel_cls, "bl_space_type", None) == self.editor_type and \
                    getattr(panel_cls, "bl_region_type", None) == 'UI':

                category = getattr(panel_cls, "bl_category", "Unknown")
                is_visible = True

                # Evaluate visibility using the poll() method
                if hasattr(panel_cls, 'poll'):
                    try:
                        # Simulate the specific editor context to accurately test poll()
                        if override_kwargs and hasattr(context, "temp_override"):
                            with context.temp_override(**override_kwargs):
                                is_visible = panel_cls.poll(context)
                        else:
                            is_visible = False
                    except Exception:
                        # Fallback to False if poll() raises an error
                        is_visible = False

                if is_visible:
                    tabs_set.add(category)

        # Store the current user-defined states
        wl_state = {item.name: item.use for item in settings.whitelist_tabs}
        bl_state = {item.name: item.use for item in settings.blacklist_tabs}

        # --- NEW: Preserve currently checked tabs regardless of poll() results ---
        # Add checked whitelist items to the set
        for name, use in wl_state.items():
            if use:
                tabs_set.add(name)

        # Add checked blacklist items to the set
        for name, use in bl_state.items():
            if use:
                tabs_set.add(name)
        # -----------------------------------------------------------------------

        settings.whitelist_tabs.clear()
        settings.blacklist_tabs.clear()

        # Rebuild the lists based on the aggregated tabs_set
        for tab in sorted(tabs_set, key=lambda x: x.lower()):
            wl_item = settings.whitelist_tabs.add()
            wl_item.name = tab
            wl_item.use = wl_state.get(tab, False)

            bl_item = settings.blacklist_tabs.add()
            bl_item.name = tab
            bl_item.use = bl_state.get(tab, False)

        return {'FINISHED'}

class PREFERENCES_OT_clear_tab_filters(Operator):
    """Clear all items in the active filter list for a specific editor"""
    bl_idname = "preferences.clear_tab_filters"
    bl_label = "Clear List"
    editor_type: StringProperty()

    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        settings = prefs.get_editor_settings(self.editor_type)
        if not settings: return {'CANCELLED'}

        if settings.filter_mode == 'WHITELIST': settings.whitelist_tabs.clear()
        elif settings.filter_mode == 'BLACKLIST': settings.blacklist_tabs.clear()
        return {'FINISHED'}

class QuickSidebarSwitcherPreferences(AddonPreferences):
    bl_idname = __package__

    tab_sort_order: EnumProperty(
        name="Tab Sort Order",
        items=[('ALPHABETICAL', "Alphabetical", ""), ('SIDEBAR', "Sidebar Order", "")],
        default='ALPHABETICAL',
    )
    popup_columns: IntProperty(name="Popup Columns", default=2, min=1, max=6)

    # Isolated settings storage
    view3d_settings: PointerProperty(type=EditorFilterSettings)
    node_settings: PointerProperty(type=EditorFilterSettings)
    dopesheet_settings: PointerProperty(type=EditorFilterSettings)
    graph_settings: PointerProperty(type=EditorFilterSettings)

    def get_editor_settings(self, space_type):
        """Unified dynamic mapper to fetch specific settings without code redundancy."""
        if space_type == 'VIEW_3D': return self.view3d_settings
        if space_type == 'NODE_EDITOR': return self.node_settings
        if space_type == 'DOPESHEET_EDITOR': return self.dopesheet_settings
        if space_type == 'GRAPH_EDITOR': return self.graph_settings
        return None

    def draw(self, context):
        layout = self.layout

        # 1. Keymap Settings
        box = layout.box()
        box.label(text="Keymap Settings:", icon='KEYINGSET')
        from . import keymap
        wm = context.window_manager
        kc = wm.keyconfigs.user

        found_kmi = False
        for km_add, kmi_add in keymap.addon_keymaps:
            user_km, user_kmi = get_user_kmi_from_addon_kmi(km_add, kmi_add, kc)
            if user_km and user_kmi:
                box.context_pointer_set("keymap", user_km)
                draw_kmi(user_kmi, box)
                found_kmi = True
        if not found_kmi:
            box.label(text="Keymap is not loaded yet. Try restarting Blender.", icon='INFO')

        layout.separator()

        # 2. Filter Settings
        box = layout.box()
        box.label(text="Filter Settings (Per Editor Type)", icon='FILTER')
        self.draw_editor_ui(box, self.view3d_settings, "3D View", 'VIEW_3D')
        self.draw_editor_ui(box, self.node_settings, "Node Editor", 'NODE_EDITOR')
        self.draw_editor_ui(box, self.dopesheet_settings, "Dopesheet", 'DOPESHEET_EDITOR')
        self.draw_editor_ui(box, self.graph_settings, "Graph Editor", 'GRAPH_EDITOR')

        layout.separator()

        # 3. Display Settings
        box = layout.box()
        box.label(text="Display Settings", icon='PRESET')
        row = box.row()
        row.label(text="Tab Sort Order:")
        row.prop(self, "tab_sort_order", text="")
        row = box.row()
        row.label(text="Popup Columns:")
        row.prop(self, "popup_columns", text="")

    def draw_editor_ui(self, layout, settings, title, editor_type):
        box = layout.box()
        row = box.row(align=True)
        icon = 'TRIA_DOWN' if settings.show_expanded else 'TRIA_RIGHT'
        row.prop(settings, "show_expanded", text="", icon=icon, emboss=False)
        row.label(text=f"{title} Filter Configuration")

        if settings.show_expanded:
            row_mode = box.row()
            row_mode.prop(settings, "filter_mode", expand=True)
            if settings.filter_mode != 'NONE':
                active_list = settings.whitelist_tabs if settings.filter_mode == 'WHITELIST' else settings.blacklist_tabs
                row_btn = box.row()
                op_refresh = row_btn.operator("preferences.refresh_tab_filters", text="Fetch Current Tabs", icon='FILE_REFRESH')
                op_refresh.editor_type = editor_type
                op_clear = row_btn.operator("preferences.clear_tab_filters", text="", icon='TRASH')
                op_clear.editor_type = editor_type

                if len(active_list) > 0:
                    filter_box = box.box()
                    flow = filter_box.column_flow(columns=3)
                    for item in active_list: flow.prop(item, "use", text=item.name)
                else:
                    box.label(text="Click 'Fetch Current Tabs' to load available tabs.", icon='INFO')

classes = (
    SidebarTabFilterItem,
    EditorFilterSettings,
    PREFERENCES_OT_refresh_tab_filters,
    PREFERENCES_OT_clear_tab_filters,
    QuickSidebarSwitcherPreferences,
)

def register():
    for cls in classes: bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)