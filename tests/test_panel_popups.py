"""Run with Blender --background --factory-startup --python <this file>."""
import importlib
from pathlib import Path
import sys
from types import SimpleNamespace

import bpy


root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root.parent))
addon = importlib.import_module(root.name)


class QSS_TEST_PT_root(bpy.types.Panel):
    bl_label = "Popup Test"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "QSS Popup Test"

    def draw(self, context):
        self.layout.label(text="Root")


class QSS_TEST_PT_child(bpy.types.Panel):
    bl_label = "Child"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "QSS Popup Test"
    bl_parent_id = "QSS_TEST_PT_root"

    def draw(self, context):
        self.layout.label(text="Child")


class QSS_TEST_PT_second(QSS_TEST_PT_root):
    bl_label = "Second Root"


addon.register()
registered_panels = []
try:
    common = addon.common
    operators = addon.operators
    for panel in (QSS_TEST_PT_root, QSS_TEST_PT_child):
        bpy.utils.register_class(panel)
        registered_panels.append(panel)

    panels = common.get_popup_panels(bpy.context, 'VIEW_3D', "QSS Popup Test")
    assert panels == [QSS_TEST_PT_root], panels
    assert common.get_popup_panels(bpy.context, 'NODE_EDITOR', "QSS Popup Test") == []
    assert common.get_popup_panels(bpy.context, 'VIEW_3D', "Missing") == []

    calls = []
    original_switch = operators.switch_tab_logic
    original_popup = operators.open_sidebar_tab_popup
    operators.switch_tab_logic = lambda *args: calls.append('switch') or {'FINISHED'}
    operators.open_sidebar_tab_popup = lambda *args: calls.append('popup') or {'INTERFACE'}
    keymaps = addon.keymap
    bpy.context.window_manager.keyconfigs.update()
    popup_km, popup_item = keymaps.get_popup_shortcut(bpy.context)
    assert popup_item is not None
    assert (popup_item.type, popup_item.value, popup_item.ctrl) == ('LEFTMOUSE', 'ANY', 1)
    popup_item.ctrl = False
    popup_item.alt = True
    popup_item.active = False
    assert keymaps.get_popup_shortcut(bpy.context)[1] is None
    popup_item.active = True
    assert keymaps.get_popup_shortcut(bpy.context)[1].alt
    assert 'Alt' in popup_item.to_string()
    original_event_match = keymaps.is_popup_event
    keymaps.is_popup_event = lambda ctx, event: event.alt and popup_item.active
    context = SimpleNamespace(
        area=SimpleNamespace(type='VIEW_3D'),
        window_manager=bpy.context.window_manager,
    )
    base = operators.BaseSwitchSidebarTabOp
    instance = SimpleNamespace(
        tab_name="QSS Popup Test",
        get_space_type=lambda ctx: 'VIEW_3D',
    )
    instance.execute = lambda ctx: base.execute(instance, ctx)
    event = SimpleNamespace(ctrl=False, shift=False, alt=False, oskey=False)
    base.invoke(instance, context, event)
    event.ctrl = True
    base.invoke(instance, context, event)
    base.invoke(instance, context, event)
    event.alt = True
    base.invoke(instance, context, event)
    popup_item.active = False
    base.invoke(instance, context, event)
    assert calls == ['switch', 'switch', 'switch', 'popup', 'switch'], calls
    popup_item.active = True
    description = addon.editors.WM_OT_switch_sidebar_tab.description(context, instance)
    assert 'QSS Popup Test' in description and 'Alt' in description
    assert bpy.ops.wm.quick_sidebar_switcher_switch.get_rna_type().description
    operators.switch_tab_logic = original_switch
    operators.open_sidebar_tab_popup = original_popup
    keymaps.is_popup_event = original_event_match

    # Intercept UI creation while exercising native-panel and multi-root routing.
    real_bpy = common.bpy
    calls.clear()
    def call_panel(*args, **kwargs):
        calls.append(kwargs)
        return {'INTERFACE'}
    common.bpy = SimpleNamespace(types=bpy.types, ops=SimpleNamespace(wm=SimpleNamespace(call_panel=call_panel)))
    def popup_menu(draw, **kwargs):
        items = []
        layout = SimpleNamespace(operator=lambda *args, **kwargs: items.append(SimpleNamespace()) or items[-1])
        draw(SimpleNamespace(layout=layout), context)
        calls.append([item.name for item in items])
    context.window_manager = SimpleNamespace(popup_menu=popup_menu)
    assert common.open_sidebar_tab_popup(context, 'VIEW_3D', "QSS Popup Test") == {'INTERFACE'}
    assert calls[-1] == {'name': 'QSS_TEST_PT_root', 'keep_open': True}
    bpy.utils.register_class(QSS_TEST_PT_second)
    registered_panels.append(QSS_TEST_PT_second)
    assert common.open_sidebar_tab_popup(context, 'VIEW_3D', "QSS Popup Test") == {'FINISHED'}
    assert set(calls[-1]) == {'QSS_TEST_PT_root', 'QSS_TEST_PT_second'}
    common.bpy = real_bpy
    print('PASS: modifier routing, tooltip, native panel selection, child exclusion, multi-root selection')
finally:
    for panel in reversed(registered_panels):
        bpy.utils.unregister_class(panel)
    addon.unregister()
