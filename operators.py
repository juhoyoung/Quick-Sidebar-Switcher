# operators.py
import bpy
from bpy.types import Operator
from bpy.props import StringProperty, EnumProperty

def get_visible_sidebar_tabs(context, sort_order='ALPHABETICAL'):

    tabs_dict = {}
    
    for panel_cls in bpy.types.Panel.__subclasses__():
        if getattr(panel_cls, "bl_space_type", None) == 'VIEW_3D' and \
           getattr(panel_cls, "bl_region_type", None) == 'UI':
            if hasattr(panel_cls, 'poll'):
                try:
                    if not panel_cls.poll(context):
                        continue
                except:
                    pass  
            
            category = getattr(panel_cls, "bl_category", "Unknown")
            order = getattr(panel_cls, "bl_order", 0)
            
            if category not in tabs_dict or order < tabs_dict[category]:
                tabs_dict[category] = order
    
    if sort_order == 'SIDEBAR':
        return [cat for cat, _ in sorted(tabs_dict.items(), key=lambda x: x[1])]
    else:
        return sorted(tabs_dict.keys())


def get_tab_enum_items(self, context):
    """Generate enum items for tabs"""
    try:
        prefs = context.preferences.addons[__package__].preferences
        sort_order = prefs.tab_sort_order
    except:
        sort_order = 'ALPHABETICAL'
    
    tabs = get_visible_sidebar_tabs(context, sort_order)
    
    items = []
    for i, tab in enumerate(tabs):
        items.append((tab, tab, "", i))
    
    return items if items else [('NONE', 'No Tabs', '', 0)]


class VIEW3D_OT_switch_sidebar_tab(Operator):
    """Switch to a specific sidebar tab"""
    bl_idname = "view3d.switch_sidebar_tab"
    bl_label = "Switch Sidebar Tab"
    bl_options = set()
    
    tab_name: StringProperty()
    
    def execute(self, context):
        area = context.area
        
        if not area or area.type != 'VIEW_3D':
            area = next((a for a in context.screen.areas if a.type == 'VIEW_3D'), None)
        
        if not area:
            return {'CANCELLED'}
        
        space = area.spaces.active
        
        was_closed = not space.show_region_ui
        
        tab_name = self.tab_name
        
        if was_closed:
            space.show_region_ui = True
            
            def switch_delayed(area_ref, tab):
                def inner():
                    region = next((r for r in area_ref.regions if r.type == 'UI'), None)
                    if not region:
                        return None
                    
                    try:
                        region.active_panel_category = tab
                    except (TypeError, AttributeError):
                        pass
                    
                    area_ref.tag_redraw()
                    return None
                return inner
            
            bpy.app.timers.register(switch_delayed(area, tab_name), first_interval=0.1)
            return {'FINISHED'}
        
        return self.switch_tab_now(area, tab_name)
    
    def switch_tab_now(self, area, tab_name):
        region = next((r for r in area.regions if r.type == 'UI'), None)
        if not region:
            return {'CANCELLED'}

        try:
            region.active_panel_category = tab_name
        except (TypeError, AttributeError) as e:
            self.report({'WARNING'}, f"Could not switch tab: {tab_name}")
            return {'CANCELLED'}

        area.tag_redraw()
        return {'FINISHED'}  


class VIEW3D_OT_sidebar_tab_menu(Operator):
    """Open a popup menu to select a sidebar tab"""
    bl_idname = "view3d.sidebar_tab_menu"
    bl_label = "Select Sidebar Tab"
    
    def invoke(self, context, event):
        bpy.ops.wm.call_menu(name="VIEW3D_MT_sidebar_tab_menu")
        return {'FINISHED'}


class VIEW3D_OT_sidebar_tab_search(Operator):
    """Search and select a sidebar tab"""
    bl_idname = "view3d.sidebar_tab_search"
    bl_label = "Search Sidebar Tabs"
    bl_options = set()
    bl_property = "tab_enum"
    
    tab_enum: EnumProperty(
        name="Tab",
        description="Select a sidebar tab",
        items=get_tab_enum_items,
    )
    
    @classmethod
    def poll(cls, context):
        return context.area and context.area.type == 'VIEW_3D'
    
    def execute(self, context):
        if self.tab_enum and self.tab_enum != 'NONE':
            area = context.area
            if not area or area.type != 'VIEW_3D':
                area = next((a for a in context.screen.areas if a.type == 'VIEW_3D'), None)
            
            if not area:
                return {'CANCELLED'}
            
            space = area.spaces.active
            was_closed = not space.show_region_ui
            
            selected_tab = self.tab_enum
            
            if was_closed:
                space.show_region_ui = True
                def switch_after_open(area_ref, tab_name):
                    def inner():
                        region = next((r for r in area_ref.regions if r.type == 'UI'), None)
                        if region:
                            try:
                                region.active_panel_category = tab_name
                                area_ref.tag_redraw()
                            except:
                                pass
                        return None
                    return inner
                
                bpy.app.timers.register(switch_after_open(area, selected_tab), first_interval=0.1)
            else:
                region = next((r for r in area.regions if r.type == 'UI'), None)
                if region:
                    try:
                        region.active_panel_category = selected_tab
                        area.tag_redraw()
                    except:
                        pass
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {'CANCELLED'}


class VIEW3D_MT_sidebar_tab_menu(bpy.types.Menu):
    bl_label = "Sidebar Tabs"
    bl_idname = "VIEW3D_MT_sidebar_tab_menu"

    def draw(self, context):
        layout = self.layout

        # Search option at the top
        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("view3d.sidebar_tab_search", text="Search Tabs...", icon='VIEWZOOM')
        layout.separator()

        try:
            prefs = context.preferences.addons[__package__].preferences
            sort_order = prefs.tab_sort_order
            columns = prefs.popup_columns
        except:
            sort_order = 'ALPHABETICAL'
            columns = 2

        tabs = get_visible_sidebar_tabs(context, sort_order)

        if not tabs:
            layout.label(text="No Sidebar Tabs Found")
        else:
            # Multi-column layout
            if columns > 1:
                flow = layout.column_flow(columns=columns)
                for tab in tabs:
                    op = flow.operator("view3d.switch_sidebar_tab", text=tab)
                    op.tab_name = tab
            else:
                for tab in tabs:
                    op = layout.operator("view3d.switch_sidebar_tab", text=tab)
                    op.tab_name = tab


classes = (
    VIEW3D_OT_switch_sidebar_tab,
    VIEW3D_OT_sidebar_tab_menu,
    VIEW3D_OT_sidebar_tab_search,
    VIEW3D_MT_sidebar_tab_menu,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)