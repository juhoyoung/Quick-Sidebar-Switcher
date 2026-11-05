# common.py
import bpy

# Dictionary to store tabs per space type dynamically
CACHED_TABS = {}

def get_all_subclasses(cls):
    """Recursively fetch all unique subclasses of a given class."""
    subclasses = set()
    work_list = cls.__subclasses__()

    while work_list:
        sub = work_list.pop()
        if sub not in subclasses:
            subclasses.add(sub)
            work_list.extend(sub.__subclasses__())

    return list(subclasses)


def discover_sidebar_tabs(
        context,
        space_type,
        override_kwargs=None,
        poll_current_context=True,
        bypass_poll_categories=None,
        use_edit_mode_fallback=False,
):
    """Discover visible sidebar categories and their minimum panel order."""
    override_kwargs = override_kwargs or {}
    bypass_poll_categories = bypass_poll_categories or set()
    tabs_dict = {}

    for panel_cls in get_all_subclasses(bpy.types.Panel):
        try:
            if not panel_cls.is_registered:
                continue
        except AttributeError:
            if not hasattr(panel_cls, "bl_rna"):
                continue

        if (getattr(panel_cls, "bl_space_type", None) != space_type or
                getattr(panel_cls, "bl_region_type", None) != 'UI'):
            continue

        category = getattr(panel_cls, "bl_category", "Unknown")
        if not category or category == "Unknown":
            continue

        is_visible = True
        if category not in bypass_poll_categories:
            if hasattr(panel_cls, 'poll'):
                is_visible = False

                if poll_current_context:
                    try:
                        is_visible = panel_cls.poll(context)
                    except Exception:
                        is_visible = False

                if not is_visible and override_kwargs and hasattr(context, "temp_override"):
                    try:
                        with context.temp_override(**override_kwargs):
                            is_visible = panel_cls.poll(context)
                    except Exception:
                        is_visible = False
            elif use_edit_mode_fallback and category == 'Edit':
                is_visible = (getattr(context, "mode", "") == 'EDIT_MESH')

        if not is_visible:
            continue

        order = getattr(panel_cls, "bl_order", 0)
        if category not in tabs_dict or order < tabs_dict[category]:
            tabs_dict[category] = order

    return tabs_dict

def update_tabs(context, space_type):
    """Reload and cache the N-panel tab list for a specific space type."""
    CACHED_TABS[space_type] = []

    try:
        prefs = context.preferences.addons[__package__].preferences
        sort_order = prefs.tab_sort_order

        # Access the corresponding editor settings dynamically
        settings = prefs.get_editor_settings(space_type)

        if settings:
            filter_mode = settings.filter_mode
            if filter_mode == 'WHITELIST':
                active_filters = {item.name for item in settings.whitelist_tabs if item.use}
            elif filter_mode == 'BLACKLIST':
                active_filters = {item.name for item in settings.blacklist_tabs if item.use}
            else:
                active_filters = set()
        else:
            filter_mode = 'NONE'
            active_filters = set()

    except Exception:
        sort_order = 'ALPHABETICAL'
        filter_mode = 'NONE'
        active_filters = set()

    # Configure context override for safe poll checking
    override_kwargs = {}
    if getattr(context, "window", None): override_kwargs["window"] = context.window
    if getattr(context, "area", None): override_kwargs["area"] = context.area
    ui_region = next((r for r in getattr(context.area, "regions", []) if r.type == 'UI'), None)
    if ui_region: override_kwargs["region"] = ui_region

    tabs_dict = discover_sidebar_tabs(
        context,
        space_type,
        override_kwargs=override_kwargs,
        bypass_poll_categories={"Item", "Tool", "View", "Image"},
        use_edit_mode_fallback=True,
    )

    # Apply filter constraints after discovering the available categories
    if filter_mode == 'WHITELIST':
        tabs_dict = {category: order for category, order in tabs_dict.items()
                     if category in active_filters}
    elif filter_mode == 'BLACKLIST' and active_filters:
        tabs_dict = {category: order for category, order in tabs_dict.items()
                     if category not in active_filters}

    # Force default tabs for Graph Editor to always appear and apply filters
    if space_type == 'GRAPH_EDITOR':
        for forced_tab in ["F-Curve", "Modifiers", "View"]:
            # Check filter conditions before appending
            if filter_mode == 'WHITELIST' and forced_tab not in active_filters: continue
            if filter_mode == 'BLACKLIST' and active_filters and forced_tab in active_filters: continue

            if forced_tab not in tabs_dict:
                tabs_dict[forced_tab] = 0

    if sort_order == 'SIDEBAR':
        sorted_tabs = [cat for cat, _ in sorted(tabs_dict.items(), key=lambda x: x[1])]
    else:
        sorted_tabs = sorted(tabs_dict.keys())

    CACHED_TABS[space_type].extend(sorted_tabs)


def get_visible_tabs(context, space_type):
    """Return the cached tab list, or update it if empty."""
    if space_type not in CACHED_TABS:
        update_tabs(context, space_type)
    return CACHED_TABS.get(space_type, [])


def get_popup_panels(context, space_type, tab_name):
    """Return registered top-level panels; Blender draws their children itself."""
    panels = []
    for panel in get_all_subclasses(bpy.types.Panel):
        if not getattr(panel, 'is_registered', False):
            continue
        if (getattr(panel, 'bl_space_type', None) != space_type
                or getattr(panel, 'bl_region_type', None) != 'UI'
                or getattr(panel, 'bl_category', '') != tab_name
                or getattr(panel, 'bl_parent_id', '')):
            continue
        try:
            if hasattr(panel, 'poll') and not panel.poll(context):
                continue
        except Exception:
            continue
        panels.append(panel)
    return sorted(panels, key=lambda panel: (
        getattr(panel, 'bl_order', 0), panel.bl_rna.identifier,
    ))


def open_sidebar_tab_popup(context, space_type, tab_name):
    """Use native panel popovers to preserve external panels' draw context."""
    if not context.area or context.area.type != space_type:
        return {'CANCELLED'}
    panels = get_popup_panels(context, space_type, tab_name)
    if not panels:
        return {'CANCELLED'}

    if len(panels) == 1:
        return bpy.ops.wm.call_panel(
            'INVOKE_DEFAULT', name=panels[0].bl_rna.identifier, keep_open=True,
        )

    # A category can contain several independent roots, each with its own children.
    panel_items = tuple((panel.bl_rna.identifier, panel.bl_label) for panel in panels)

    def draw_panel_choices(self, popup_context):
        self.layout.operator_context = 'INVOKE_DEFAULT'
        for panel_id, label in panel_items:
            operator = self.layout.operator('wm.call_panel', text=label)
            operator.name = panel_id
            operator.keep_open = True

    context.window_manager.popup_menu(draw_panel_choices, title=tab_name)
    return {'FINISHED'}


def switch_tab_logic(context, space_type, tab_name):
    """Core logic to reveal the sidebar and switch active category."""
    area = context.area
    if not area or area.type != space_type:
        area = next((a for a in getattr(context.screen, "areas", []) if a.type == space_type), None)

    if not area: return {'CANCELLED'}

    space = area.spaces.active
    was_closed = not getattr(space, "show_region_ui", True)

    if was_closed:
        space.show_region_ui = True

        def switch_delayed(area_ref, tab):
            def inner():
                region = next((r for r in area_ref.regions if r.type == 'UI'), None)
                if region:
                    try:
                        region.active_panel_category = tab
                        area_ref.tag_redraw()
                    except (TypeError, AttributeError):
                        pass
                return None
            return inner

        bpy.app.timers.register(switch_delayed(area, tab_name), first_interval=0.1)
        return {'FINISHED'}

    region = next((r for r in area.regions if r.type == 'UI'), None)
    if not region: return {'CANCELLED'}

    try:
        region.active_panel_category = tab_name
        area.tag_redraw()
    except (TypeError, AttributeError):
        pass

    return {'FINISHED'}
