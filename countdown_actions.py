
# Countdown Actions — updates a text source with mm:ss and triggers actions on finish
import obspython as obs
import time

TEXT_SOURCE = ""
DURATION_SEC = 300
TARGET_SCENE = ""
SHOW_SOURCE = ""
HIDE_SOURCE = ""

remaining = 0
active = False

def script_description():
    return "Timer regressivo que atualiza uma fonte de texto e executa ações ao terminar."

def script_properties():
    p = obs.obs_properties_create()
    list_text = obs.obs_properties_add_list(p, "TEXT_SOURCE", "Fonte de texto para o timer",
                                            obs.OBS_COMBO_TYPE_EDITABLE, obs.OBS_COMBO_FORMAT_STRING)
    populate_text_sources(list_text)

    obs.obs_properties_add_int(p, "DURATION_SEC", "Duração (segundos)", 5, 36000, 1)

    list_scene = obs.obs_properties_add_list(p, "TARGET_SCENE", "Cena ao terminar (opcional)",
                                             obs.OBS_COMBO_TYPE_EDITABLE, obs.OBS_COMBO_FORMAT_STRING)
    populate_scenes(list_scene)

    list_show = obs.obs_properties_add_list(p, "SHOW_SOURCE", "Mostrar fonte ao terminar (opcional)",
                                            obs.OBS_COMBO_TYPE_EDITABLE, obs.OBS_COMBO_FORMAT_STRING)
    populate_all_sources(list_show)

    list_hide = obs.obs_properties_add_list(p, "HIDE_SOURCE", "Ocultar fonte ao terminar (opcional)",
                                            obs.OBS_COMBO_TYPE_EDITABLE, obs.OBS_COMBO_FORMAT_STRING)
    populate_all_sources(list_hide)

    obs.obs_properties_add_button(p, "start_btn", "Iniciar", start_btn)
    obs.obs_properties_add_button(p, "stop_btn", "Parar", stop_btn)
    return p

def script_defaults(s):
    obs.obs_data_set_default_int(s, "DURATION_SEC", 300)

def script_update(s):
    global TEXT_SOURCE, DURATION_SEC, TARGET_SCENE, SHOW_SOURCE, HIDE_SOURCE
    TEXT_SOURCE = obs.obs_data_get_string(s, "TEXT_SOURCE")
    DURATION_SEC = obs.obs_data_get_int(s, "DURATION_SEC")
    TARGET_SCENE = obs.obs_data_get_string(s, "TARGET_SCENE")
    SHOW_SOURCE = obs.obs_data_get_string(s, "SHOW_SOURCE")
    HIDE_SOURCE = obs.obs_data_get_string(s, "HIDE_SOURCE")

def start_btn(props, prop):
    start_timer()

def stop_btn(props, prop):
    stop_timer()

def start_timer():
    global remaining, active
    remaining = max(1, DURATION_SEC)
    active = True
    obs.timer_remove(tick)
    obs.timer_add(tick, 1000)

def stop_timer():
    global active
    active = False
    obs.timer_remove(tick)

def tick():
    global remaining
    if not active:
        return
    update_text(remaining)
    remaining -= 1
    if remaining < 0:
        stop_timer()
        on_finish()

def update_text(sec):
    name = TEXT_SOURCE
    if not name:
        return
    src = obs.obs_get_source_by_name(name)
    if src is not None:
        s = obs.obs_data_create()
        mm = sec // 60
        ss = sec % 60
        text = f"{mm:02d}:{ss:02d}"
        obs.obs_data_set_string(s, "text", text)
        obs.obs_source_update(src, s)
        obs.obs_data_release(s)
        obs.obs_source_release(src)

def on_finish():
    # switch scene
    if TARGET_SCENE:
        scn = obs.obs_get_source_by_name(TARGET_SCENE)
        if scn:
            obs.obs_frontend_set_current_scene(scn)
            obs.obs_source_release(scn)
    # show/hide sources in current scene
    cur = obs.obs_frontend_get_current_scene()
    if cur:
        scene = obs.obs_scene_from_source(cur)
        if scene:
            if SHOW_SOURCE:
                toggle_source_visibility(scene, SHOW_SOURCE, True)
            if HIDE_SOURCE:
                toggle_source_visibility(scene, HIDE_SOURCE, False)
        obs.obs_source_release(cur)

def toggle_source_visibility(scene, name, vis):
    item = obs.obs_scene_find_source(scene, name)
    if item:
        obs.obs_sceneitem_set_visible(item, vis)

# Helpers to populate combo lists
def populate_text_sources(prop):
    populate_sources_by_kind(prop, ["text_gdiplus", "text_ft2_source_v2"])

def populate_scenes(prop):
    scenes = obs.obs_frontend_get_scenes()
    if scenes is not None:
        for s in scenes:
            obs.obs_property_list_add_string(prop, obs.obs_source_get_name(s), obs.obs_source_get_name(s))
        obs.source_list_release(scenes)

def populate_all_sources(prop):
    populate_sources_by_kind(prop, None)

def populate_sources_by_kind(prop, kinds):
    sources = obs.obs_enum_sources()
    if sources is not None:
        for s in sources:
            kind = obs.obs_source_get_id(s)
            name = obs.obs_source_get_name(s)
            if kinds is None or kind in kinds:
                obs.obs_property_list_add_string(prop, name, name)
        obs.source_list_release(sources)
