import bpy, json, math
from datetime import datetime, timedelta
from bpy import context

def get_object(name): return context.scene.objects.get(name)
def set_hidden(obj, vl):
    obj.hide_viewport = vl
    obj.hide_render = vl
def assign_material(mat, ob):
    if ob.data.materials:
        ob.data.materials[0] = mat
    else:
        ob.data.materials.append(mat)
def keyframe_insert_hidden(obj, frame):
    obj.keyframe_insert(data_path='hide_viewport', frame=frame)
    obj.keyframe_insert(data_path='hide_render', frame=frame)
def load_json(fp):
    with open(fp, 'r') as f: return json.load(f)
def show_from(obj, start, end):
    set_hidden(obj, True)
    keyframe_insert_hidden(obj, 0)
    keyframe_insert_hidden(obj, start - 1)
    set_hidden(obj, False)
    keyframe_insert_hidden(obj, start)
    keyframe_insert_hidden(obj, end - 1)
    set_hidden(obj, True)
    keyframe_insert_hidden(obj, end)



class Ship:
    def __init__(self, start_frame, end_frame, name):
        self.start_frame = start_frame
        self.end_frame = end_frame
        self.name = name
        # calculate using [uv.uv for uv in context.active_object.data.uv_layers.active.data]
        self.start_uv_keyframes = [(1.0938094854354858, 0.5114993453025818), (0.6424412131309509, 0.5114993453025818), (0.6424412131309509, 0.06013072654604912), (1.0938094854354858, 0.06013072654604912)]
        self.end_uv_keyframes = [(0.7325620055198669, 0.9804397225379944), (0.28119370341300964, 0.9804397225379944), (0.28119370341300964, 0.5290710926055908), (0.7325620055198669, 0.5290710926055908)]
        self.templates = {
            'map': get_object('WorldMapOverlayTemplate'),
            'steam': get_object('PhosphateSlowTemplate'),
        }
        self.mat_templates = {
            'map': bpy.data.materials.get('WorldMap'),
            'steam': bpy.data.materials.get('DarkYellow'),
        }

        self.map_layer = self.create_map_layer()
        self.steam_layer = self.create_steam_layer()

    def new_layer(self, template_type):
        template = self.templates[template_type]
        mat_template = self.mat_templates[template_type]
        layer = template.copy()
        layer.name = '%s-%s-layer' % (self.name, template_type)
        layer.data = layer.data.copy()
        layer.animation_data_clear()
        layer_mat = mat_template.copy()
        assign_material(layer_mat, layer)
        context.scene.collection.objects.link(layer)
        return layer

    def create_map_layer(self):
        map_layer = self.new_layer('map')
        self.show_only_when_sailing(map_layer)
        self.set_uv_anim_keyframes(map_layer)
        self.set_strength_keyframes(map_layer.material_slots[0].material)
        return map_layer

    def create_steam_layer(self):
        steam_layer = self.new_layer('steam')
        start = self.end_frame - 48
        end = start + 2000
        show_from(steam_layer, start, end)
        steam_layer.modifiers['Fluid'].domain_settings.cache_frame_start = start
        steam_layer.modifiers['Fluid'].domain_settings.cache_frame_end = end
        steam_layer.modifiers['Fluid'].domain_settings.cache_frame_offset = start
        return steam_layer

    def show_only_when_sailing(self, obj, duration=0):
        end_frame = self.end_frame if (duration < self.end_frame - self.start_frame) else (self.start_frame + duration)
        show_from(obj, self.start_frame, end_frame)

    def set_strength_keyframes(self, mat):
        mat.node_tree.nodes["Emission"].inputs[1].default_value = 0
        mat.node_tree.nodes["Emission"].inputs[1].keyframe_insert(data_path='default_value', frame=self.start_frame)
        mat.node_tree.nodes["Emission"].inputs[1].default_value = 2
        mat.node_tree.nodes["Emission"].inputs[1].keyframe_insert(data_path='default_value', frame=self.start_frame + 40)
        mat.node_tree.nodes["Emission"].inputs[1].default_value = 3
        mat.node_tree.nodes["Emission"].inputs[1].keyframe_insert(data_path='default_value', frame=(self.end_frame - 40))
        mat.node_tree.nodes["Emission"].inputs[1].default_value = 0
        mat.node_tree.nodes["Emission"].inputs[1].keyframe_insert(data_path='default_value', frame=self.end_frame)

    def set_uv_anim_keyframes(self, obj):
        for idx, uv in enumerate(obj.data.uv_layers.active.data):
            uv.uv = self.start_uv_keyframes[idx]
            uv.keyframe_insert(data_path='uv', frame=self.start_frame)
            uv.uv = self.end_uv_keyframes[idx]
            uv.keyframe_insert(data_path='uv', frame=self.end_frame)


class Lifecycle:
    def __init__(self, start_date, end_date, ships_fp, ports_fp):
        self.start_date = start_date
        self.end_date = end_date
        self.date_array = [self.start_date+timedelta(days=x) for x in range((self.end_date-self.start_date).days)]
        self.time_multiplier = 20
        self.last_frame = len(self.date_array) * self.time_multiplier

        self.ships = self.create_ships(ships_fp)
        self.ports = load_json(ports_fp)

    def create_ships(self, ships_fp):
        ships = load_json(ships_fp)
        edited_ships = []
        for ship in ships:
            if ship['Departure'] is not None:
                ship['Departure'] = datetime.strptime(ship['Departure'], '%Y-%m-%dT%H:%M:%S.000Z')
            if ship['Arrival'] is not None:
                ship['Arrival'] = datetime.strptime(ship['Arrival'], '%Y-%m-%dT%H:%M:%S.000Z')
            edited_ships.append(ship)
            ship['kf_start'] = math.floor(self.keyframe_from_date(ship['Departure']))
            ship['kf_end'] = math.floor(self.keyframe_from_date(ship['Arrival']))

        return edited_ships

    def keyframe_from_date(self, date):
        if date is None: return -1
        value = min(self.date_array, key=lambda d: abs(d - date))
        return self.date_array.index(value) * self.time_multiplier

    def date_from_keyframe(self, frame):
        distance_along = frame / self.last_frame
        nearest_idx = math.floor(len(self.date_array) * distance_along)
        return self.date_array[nearest_idx].strftime("%b %Y")

    def set_animations(self):
        for ship in self.ships:
            Ship(ship['kf_start'], ship['kf_end'], name=ship['Name'])


base_path = '/home/lox/Dropbox (Brown)/projects/2021_slowboil/hotwaters/'
assets_path = base_path + 'assets/'

lc = Lifecycle(
    start_date = datetime.strptime('2011-10-01T12:00:00.000Z', '%Y-%m-%dT%H:%M:%S.000Z'),
    end_date = datetime.strptime('2021-06-01T12:00:00.000Z', '%Y-%m-%dT%H:%M:%S.000Z'),
    ships_fp = assets_path+'ships.json',
    ports_fp = assets_path+'ports.json',
)

lc.set_animations()
