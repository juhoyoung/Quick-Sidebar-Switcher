# operators.py
import bpy
from bpy.types import Operator
from bpy.props import StringProperty, EnumProperty

# 단축키 실행 시점의 탭 목록을 저장할 전역 리스트
CURRENT_TABS = []

def update_current_tabs(context):
    """단축키 실행 시점에서 N패널 탭 목록을 다시 리로드하여 캐싱합니다."""
    global CURRENT_TABS
    CURRENT_TABS.clear()

    tabs_dict = {}

    try:
        prefs = context.preferences.addons[__package__].preferences
        sort_order = prefs.tab_sort_order
        filter_mode = prefs.filter_mode
        # 체크된 탭들의 이름만 모아서 세트(Set)로 만듦
        active_filters = {item.name for item in prefs.filter_tabs if item.use}
    except:
        sort_order = 'ALPHABETICAL'
        filter_mode = 'NONE'
        active_filters = set()

    # 현재 컨텍스트에서 UI(N패널) 영역 찾기
    ui_region = None
    if context.area:
        ui_region = next((r for r in context.area.regions if r.type == 'UI'), None)

    # 안전한 temp_override를 위한 딕셔너리 구성
    override_kwargs = {}
    if getattr(context, "window", None): override_kwargs["window"] = context.window
    if getattr(context, "area", None): override_kwargs["area"] = context.area
    if ui_region: override_kwargs["region"] = ui_region

    for panel_cls in bpy.types.Panel.__subclasses__():
        if getattr(panel_cls, "bl_space_type", None) == 'VIEW_3D' and \
                getattr(panel_cls, "bl_region_type", None) == 'UI':

            category = getattr(panel_cls, "bl_category", "Unknown")

            # 화이트리스트 / 블랙리스트 필터링 적용
            if filter_mode == 'WHITELIST' and active_filters:
                if category not in active_filters:
                    continue
            elif filter_mode == 'BLACKLIST' and active_filters:
                if category in active_filters:
                    continue

            order = getattr(panel_cls, "bl_order", 0)
            is_visible = True

            # 블렌더 기본 탭(Item, Tool, View)은 poll 검사를 생략하고 항상 리스트에 포함
            if category not in {"Item"} and hasattr(panel_cls, 'poll'):
                try:
                    # 1차 시도: 현재 컨텍스트로 활성화 여부 확인
                    is_visible = panel_cls.poll(context)
                except Exception:
                    is_visible = False

                # 2차 시도: 일반 컨텍스트에서 실패했을 경우, N패널 컨텍스트로 오버라이드하여 재검사
                if not is_visible and override_kwargs and hasattr(context, "temp_override"):
                    try:
                        with context.temp_override(**override_kwargs):
                            is_visible = panel_cls.poll(context)
                    except Exception:
                        is_visible = False

            if not is_visible:
                continue

            if category not in tabs_dict or order < tabs_dict[category]:
                tabs_dict[category] = order

    if sort_order == 'SIDEBAR':
        sorted_tabs = [cat for cat, _ in sorted(tabs_dict.items(), key=lambda x: x[1])]
    else:
        sorted_tabs = sorted(tabs_dict.keys())

    CURRENT_TABS.extend(sorted_tabs)


def get_visible_sidebar_tabs(context, sort_order='ALPHABETICAL'):
    """캐싱된 탭 목록 반환"""
    if not CURRENT_TABS:
        update_current_tabs(context)
    return CURRENT_TABS


def get_tab_enum_items(self, context):
    """Generate enum items for tabs"""
    items = []
    for i, tab in enumerate(CURRENT_TABS):
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
        # 단축키 실행 시점에 강제로 탭 목록을 갱신합니다.
        update_current_tabs(context)
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


class VIEW3D_OT_open_addon_prefs(Operator):
    """Open Preferences for Quick Sidebar Switcher"""
    bl_idname = "view3d.open_sidebar_switcher_prefs"
    bl_label = "Open Settings"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
        context.window_manager.addon_search = "Quick Sidebar Switcher"
        context.preferences.active_section = 'ADDONS'
        return {'FINISHED'}


class VIEW3D_MT_sidebar_tab_menu(bpy.types.Menu):
    bl_label = "Sidebar Tabs"
    bl_idname = "VIEW3D_MT_sidebar_tab_menu"

    def draw(self, context):
        layout = self.layout

        # 상단 레이아웃을 확실히 고정하기 위해 column을 사용하고 버튼들을 각각의 줄로 분리
        top_col = layout.column()

        # 첫 번째 줄: 환경 설정 버튼
        top_col.operator("view3d.open_sidebar_switcher_prefs", text="Open Settings", icon='PREFERENCES')

        # 두 번째 줄: 검색 탭
        top_col.operator_context = 'INVOKE_DEFAULT'
        top_col.operator("view3d.sidebar_tab_search", text="Search Tabs...", icon='VIEWZOOM')

        top_col.separator()

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
    VIEW3D_OT_open_addon_prefs,
    VIEW3D_MT_sidebar_tab_menu,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)