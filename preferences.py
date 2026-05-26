# preferences.py

import bpy
from bpy.types import AddonPreferences, Operator, PropertyGroup
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty, CollectionProperty

# ------------------------------------------------------------------------
# UI Drawing Functions
# ------------------------------------------------------------------------
def get_user_kmi_from_addon_kmi(addon_km, addon_kmi, kc_user):
    """Find the keymap item in the user preferences corresponding to the addon keymap."""
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

    # Header
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

    # Body
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
                subrow.prop(kmi, "direction")

            subrow = sub.row()
            subrow.scale_x = 0.75
            subrow.prop(kmi, "any", toggle=True)
            subrow.prop(kmi, "shift_ui", toggle=True)
            subrow.prop(kmi, "ctrl_ui", toggle=True)
            subrow.prop(kmi, "alt_ui", toggle=True)
            subrow.prop(kmi, "oskey_ui", text="Cmd", toggle=True)
            subrow.prop(kmi, "key_modifier", text="", event=True)

        # Operator Properties
        box.template_keymap_item_properties(kmi)

# ------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------
class SidebarTabFilterItem(PropertyGroup):
    name: StringProperty()
    use: BoolProperty(default=False)

def get_all_subclasses(cls):
    # Set to store unique subclasses and avoid duplicates
    subclasses = set()
    # List acts as a stack to process subclasses iteratively
    work_list = cls.__subclasses__()

    while work_list:
        # Pop a class from the list
        sub = work_list.pop()

        # If it's not already in our set, add it and append its children
        if sub not in subclasses:
            subclasses.add(sub)
            work_list.extend(sub.__subclasses__())

    return list(subclasses)

class PREFERENCES_OT_refresh_tab_filters(Operator):
    """Fetch currently available sidebar tabs"""
    bl_idname = "preferences.refresh_tab_filters"
    bl_label = "Fetch Current Tabs"

    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences

        # Find the 3D Viewport area and UI region to use for context override
        view3d_area = None
        ui_region = None
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    view3d_area = area
                    for region in area.regions:
                        if region.type == 'UI':
                            ui_region = region
                            break
                    if view3d_area:
                        break
            if view3d_area:
                break

        # Prepare kwargs for temp_override
        override_kwargs = {}
        if view3d_area:
            override_kwargs["window"] = window
            override_kwargs["area"] = view3d_area
            if ui_region:
                override_kwargs["region"] = ui_region

        tabs_set = set()
        for panel_cls in get_all_subclasses(bpy.types.Panel):
            try:
                if not panel_cls.is_registered:
                    continue
            except AttributeError:
                if not hasattr(panel_cls, "bl_rna"):
                    continue

            if getattr(panel_cls, "bl_space_type", None) == 'VIEW_3D' and \
                    getattr(panel_cls, "bl_region_type", None) == 'UI':

                category = getattr(panel_cls, "bl_category", "Unknown")

                is_visible = True

                # Check visibility using poll(), excluding basic tabs
                if category not in {"Item", "Tool", "View"} and hasattr(panel_cls, 'poll'):
                    try:
                        # Simulate 3D Viewport context to accurately test poll()
                        if override_kwargs and hasattr(context, "temp_override"):
                            with context.temp_override(**override_kwargs):
                                is_visible = panel_cls.poll(context)
                        else:
                            is_visible = False
                    except Exception:
                        is_visible = False

                if is_visible:
                    tabs_set.add(category)

        current_state = {item.name: item.use for item in prefs.filter_tabs}

        final_tabs = tabs_set.copy()
        for name, use in current_state.items():
            if use:
                final_tabs.add(name)

        prefs.filter_tabs.clear()

        for tab in sorted(final_tabs, key=lambda x: x.lower()):
            item = prefs.filter_tabs.add()
            item.name = tab
            item.use = current_state.get(tab, False)

        return {'FINISHED'}

class PREFERENCES_OT_clear_tab_filters(Operator):
    """Clear all items in the filter list"""
    bl_idname = "preferences.clear_tab_filters"
    bl_label = "Clear List"

    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        prefs.filter_tabs.clear()
        return {'FINISHED'}

class QuickSidebarSwitcherPreferences(AddonPreferences):
    bl_idname = __package__

    tab_sort_order: EnumProperty(
        name="Sort Order",
        description="How to sort the sidebar tabs in the menu",
        items=[
            ('ALPHABETICAL', "Alphabetical", "Sort tabs alphabetically"),
            ('SIDEBAR', "Sidebar Order", "Sort tabs in sidebar order"),
        ],
        default='ALPHABETICAL',
    )

    popup_columns: IntProperty(
        name="Columns",
        description="Number of columns in the popup menu",
        default=2,
        min=1,
        max=6,
        soft_min=1,
        soft_max=4
    )

    filter_mode: EnumProperty(
        name="Tab Filter",
        description="Choose how to filter the tab list",
        items=[
            ('NONE', "Show All", "Show all available tabs"),
            ('WHITELIST', "Whitelist", "Only show selected tabs"),
            ('BLACKLIST', "Blacklist", "Hide selected tabs"),
        ],
        default='NONE',
    )

    filter_tabs: CollectionProperty(type=SidebarTabFilterItem)

    def draw(self, context):
        layout = self.layout

        # 1. Native Keymap Settings
        box = layout.box()
        box.label(text="Keymap Settings:", icon='KEYINGSET')

        from . import keymap
        wm = context.window_manager
        kc = wm.keyconfigs.user

        found_kmi = False

        # keymap.py
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
        box.label(text="Filter Settings (Whitelist / Blacklist)", icon='FILTER')

        row = box.row()
        row.prop(self, "filter_mode", expand=True)

        if self.filter_mode != 'NONE':
            row = box.row()
            row.operator("preferences.refresh_tab_filters", text="Fetch Current Tabs", icon='FILE_REFRESH')
            row.operator("preferences.clear_tab_filters", text="", icon='TRASH')

            if len(self.filter_tabs) > 0:
                filter_box = box.box()
                flow = filter_box.column_flow(columns=3)
                for item in self.filter_tabs:
                    flow.prop(item, "use", text=item.name)
            else:
                box.label(text="Click 'Fetch Current Tabs' to load available tabs.", icon='INFO')

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


classes = (
    SidebarTabFilterItem,
    PREFERENCES_OT_refresh_tab_filters,
    PREFERENCES_OT_clear_tab_filters,
    QuickSidebarSwitcherPreferences,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)