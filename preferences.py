# preferences.py
import bpy
from bpy.types import AddonPreferences, Operator
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty

import bpy.utils.previews
try:
    from bl_ui.space_userpref import rna_keymap_ui
except ImportError:
    rna_keymap_ui = None


class PREFERENCES_OT_capture_keymap(Operator):
    """Click and press a key combination to set the shortcut"""
    bl_idname = "preferences.capture_keymap"
    bl_label = "Capture Keymap"
    
    current_key: StringProperty(default="Press a key combination...")
    
    def modal(self, context, event):
        prefs = context.preferences.addons[__package__].preferences
        
        if event.type not in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE', 
                              'TIMER', 'TIMER_REPORT', 'TIMERREGION'}:
            
            shortcut_display = ""
            if event.ctrl:
                shortcut_display += "Ctrl+"
            if event.shift:
                shortcut_display += "Shift+"
            if event.alt:
                shortcut_display += "Alt+"
            
            if event.type not in {'LEFT_CTRL', 'RIGHT_CTRL',
                                  'LEFT_SHIFT', 'RIGHT_SHIFT',
                                  'LEFT_ALT', 'RIGHT_ALT',
                                  'OSKEY'}:
                shortcut_display += event.type
            elif shortcut_display:
                shortcut_display = shortcut_display[:-1]
            
            self.current_key = shortcut_display if shortcut_display else "Press a key combination..."
            prefs.current_capturing_key = self.current_key
            
            for area in context.screen.areas:
                if area.type == 'PREFERENCES':
                    area.tag_redraw()
        
        if event.type == 'ESC' and event.value == 'PRESS':
            prefs.is_capturing = False
            prefs.current_capturing_key = ""
            for area in context.screen.areas:
                if area.type == 'PREFERENCES':
                    area.tag_redraw()
            return {'CANCELLED'}
        
        if event.value == 'PRESS' and event.type not in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE', 
                                                          'TIMER', 'TIMER_REPORT', 'TIMERREGION',
                                                          'LEFT_CTRL', 'RIGHT_CTRL',
                                                          'LEFT_SHIFT', 'RIGHT_SHIFT',
                                                          'LEFT_ALT', 'RIGHT_ALT',
                                                          'OSKEY', 'ESC'}:
            
            prefs.shortcut_key = event.type
            prefs.use_ctrl = event.ctrl
            prefs.use_shift = event.shift
            prefs.use_alt = event.alt
            prefs.is_capturing = False
            prefs.current_capturing_key = ""
            
            from . import keymap
            keymap.update_keymap()
            
            for area in context.screen.areas:
                if area.type == 'PREFERENCES':
                    area.tag_redraw()
            
            return {'FINISHED'}
        
        return {'RUNNING_MODAL'}
    
    def invoke(self, context, event):
        prefs = context.preferences.addons[__package__].preferences
        prefs.is_capturing = True
        prefs.current_capturing_key = "Press a key combination..."
        self.current_key = "Press a key combination..."
        context.window_manager.modal_handler_add(self)
        
        for area in context.screen.areas:
            if area.type == 'PREFERENCES':
                area.tag_redraw()
        
        return {'RUNNING_MODAL'}


class QuickSidebarSwitcherPreferences(AddonPreferences):
    bl_idname = __package__

    shortcut_key: StringProperty(
        name="Key",
        description="Shortcut key",
        default='A'
    )
    
    use_ctrl: BoolProperty(
        name="Ctrl",
        description="Use Ctrl modifier",
        default=True
    )
    
    use_shift: BoolProperty(
        name="Shift",
        description="Use Shift modifier",
        default=True
    )
    
    use_alt: BoolProperty(
        name="Alt",
        description="Use Alt modifier",
        default=False
    )
    
    is_capturing: BoolProperty(
        name="Is Capturing",
        description="Currently capturing keymap",
        default=False
    )
    
    current_capturing_key: StringProperty(
        name="Current Capturing Key",
        description="Currently pressed key combination",
        default=""
    )
    
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

    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        box.label(text="Keyboard Shortcut Settings", icon='KEYINGSET')
        
        current_shortcut = ""
        if self.use_ctrl:
            current_shortcut += "Ctrl+"
        if self.use_shift:
            current_shortcut += "Shift+"
        if self.use_alt:
            current_shortcut += "Alt+"
        current_shortcut += self.shortcut_key
        
        row = box.row(align=True)
        row.label(text="Current Shortcut:", icon='EVENT_' + self.shortcut_key if len(self.shortcut_key) == 1 else 'KEYINGSET')
        row.label(text=current_shortcut)
        
        row = box.row()
        row.scale_y = 1.5
        if self.is_capturing:
            display_text = self.current_capturing_key if self.current_capturing_key else "Press a key combination..."
            row.label(text=display_text, icon='HAND')
        else:
            row.operator("preferences.capture_keymap", text="Set Shortcut (Click & Press Key)", icon='HAND')
        
        layout.separator()
        
        box = layout.box()
        box.label(text="Display Settings", icon='PRESET')
        
        row = box.row()
        row.label(text="Tab Sort Order:")
        row.prop(self, "tab_sort_order", text="")
        
        row = box.row()
        row.label(text="Popup Columns:")
        row.prop(self, "popup_columns", text="")
        
        layout.separator()
        
        box = layout.box()
        box.label(text="Usage", icon='INFO')
        box.label(text="1. Click 'Set Shortcut' button and press your desired key combination")
        box.label(text="2. Press the shortcut in 3D Viewport to open the menu")
        box.label(text="3. Use the search box to filter tabs (optional)")
        box.label(text="4. Click on a tab name to switch to it")
        
        layout.separator()
        
        if rna_keymap_ui:
            col = layout.column()
            col.label(text="Keymap Settings:", icon='PREFERENCES')
            
            from . import keymap
            
            wm = context.window_manager
            kc = wm.keyconfigs.user
            
            old_km_name = ""
            get_kmi_l = []
            
            for km_add, kmi_add in keymap.addon_keymaps:
                for km_con in kc.keymaps:
                    if km_add.name == km_con.name:
                        km = km_con
                        break
                
                for kmi_con in km.keymap_items:
                    if kmi_add.idname == kmi_con.idname:
                        get_kmi_l.append((km, kmi_con))
            
            for km, kmi in get_kmi_l:
                if not km.name == old_km_name:
                    col.label(text=str(km.name), icon="DOT")
                
                col.context_pointer_set("keymap", km)
                rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
                col.separator()
                old_km_name = km.name


classes = (
    PREFERENCES_OT_capture_keymap,
    QuickSidebarSwitcherPreferences,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)