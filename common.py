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

def update_tabs(context, space_type):
    """Reload and cache the N-panel tab list for a specific space type."""
    CACHED_TABS[space_type] = []
    tabs_dict = {}

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

    for panel_cls in get_all_subclasses(bpy.types.Panel):
        try:
            if not panel_cls.is_registered: continue
        except AttributeError:
            if not hasattr(panel_cls, "bl_rna"): continue

        if getattr(panel_cls, "bl_space_type", None) == space_type and \
                getattr(panel_cls, "bl_region_type", None) == 'UI':

            category = getattr(panel_cls, "bl_category", "Unknown")

            # Apply filter constraints
            if filter_mode == 'WHITELIST' and active_filters and category not in active_filters: continue
            if filter_mode == 'BLACKLIST' and active_filters and category in active_filters: continue

            order = getattr(panel_cls, "bl_order", 0)
            is_visible = True

            # Bypass strict poll check for default essential tabs
            if category not in {"Item", "Tool", "View", "Node", "Options", "Strip", "Modifiers"}:
                if hasattr(panel_cls, 'poll'):
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

            if not is_visible: continue

            if category not in tabs_dict or order < tabs_dict[category]:
                tabs_dict[category] = order

    if sort_order == 'SIDEBAR':
        sorted_tabs = [cat for cat, _ in sorted(tabs_dict.items(), key=lambda x: x[1])]
    else:
        sorted_tabs = sorted(tabs_dict.keys())

    CACHED_TABS[space_type].extend(sorted_tabs)


def get_visible_tabs(context, space_type, sort_order='ALPHABETICAL'):
    """Return the cached tab list, or update it if empty."""
    if space_type not in CACHED_TABS or not CACHED_TABS[space_type]:
        update_tabs(context, space_type)
    return CACHED_TABS.get(space_type, [])


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