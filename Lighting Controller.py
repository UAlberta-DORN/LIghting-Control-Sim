from numpy import *
from tkinter import *
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib import pylab as p
from matplotlib.patches import Rectangle
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.font_manager import FontProperties
fontP = FontProperties()
fontP.set_size('small')


WINDOW_WIDTH = 1.143  # m
WINDOW_HEIGHT = 1.525  # m
WINDOW_AREA = WINDOW_HEIGHT * WINDOW_WIDTH  # m^2

SW = 0.2
SH = 0.2

MAX_SENSORS = 10
MAX_LIGHT_SOURCES = 10


def cos_curve(x):
    return (1 - cos(pi * x)) / 2


def get_cloud_cover(fraction, clouds):
    num_clouds = len(clouds) - 1
    cloud_frac = fraction * num_clouds
    floor_idx = floor(cloud_frac).astype(int)
    ceil_idx = ceil(cloud_frac).astype(int)
    cloud = cos_curve(cloud_frac - floor_idx) * (clouds[ceil_idx] - clouds[floor_idx])
    return cloud + clouds[floor_idx]


def get_sunlight(t, max_sun, cloud_cover, light_pollution, sunset):
    sun = (sunset - max_sun) * cos(pi * t / 43200) + sunset
    return max((1 - cloud_cover) * sun, 0) + light_pollution


class Drag_and_Drop_Handler:
    def __init__(self, fig=None):
        if fig is None:
            fig = p.gcf()

        self.dragged_object = None
        fig.canvas.mpl_connect("pick_event", self.on_pick_event)
        fig.canvas.mpl_connect("button_release_event", self.on_release_event)

    def on_pick_event(self, event):
        self.dragged_object = event.artist
        self.pick_pos = (event.mouseevent.xdata, event.mouseevent.ydata)
        return True

    def on_release_event(self, event):
        if self.dragged_object is not None :
            old_pos = self.dragged_object.get_xy()
            new_pos = (old_pos[0] + event.xdata - self.pick_pos[0],
                       old_pos[1] + event.ydata - self.pick_pos[1])
            self.dragged_object.set_xy(new_pos)
            self.dragged_object = None
            plt.draw()
        return True


class Root(Tk):
    def __init__(self):
        super(Root, self).__init__()
        self.title("Lighting Simulator")
        self.minsize(800, 675)

        self.max_brightness = StringVar()
        self.max_brightness.set(1600)
        self.max_sun = StringVar()
        self.max_sun.set(15000)
        self.light_pollution = StringVar()
        self.light_pollution.set(500)
        self.sunset = StringVar()
        self.sunset.set(400)
        self.cloud = StringVar()
        self.cloud.set('0,30,15')
        self.start_time = StringVar()
        self.start_time.set(6)
        self.duration = StringVar()
        self.duration.set(12)
        self.max_lux_str = StringVar()
        self.max_lux_str.set(2000)
        self.height_step_size = StringVar()
        self.height_step_size.set(0.05)
        self.tilt_step_size = StringVar()
        self.tilt_step_size.set(0.05)
        self.sample_period = StringVar()
        self.sample_period.set(60)
        self.err_thresh = StringVar()
        self.err_thresh.set(0.1)
        self.timeout = StringVar()
        self.timeout.set(10)
        self.use_response = BooleanVar()
        self.use_response.set(False)
        self.refs = StringVar()
        self.refs.set('25,50,25')

        self.initialize_layout()
        self.initialize_sim_parameters()
        self.initialize_controller_parameters()
        self.initialize_sensor_frame()
        self.initialize_light_source_frame()

        self.sim_button = Button(self,
                                 text="Run Simulation",
                                 command=self.simulate)
        self.sim_button.grid(row=0,
                             column=2)

        self.num_sensors = 0
        self.sensor_ids = []
        self.sensor_tabs = []

        self.num_light_source = 0
        self.light_source_ids = []
        self.light_source_tabs = []

        self.update_ui()

    def initialize_layout(self):
        self.fig = plt.figure(figsize=(4, 4), dpi=100)
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.axis('equal')
        self.ax.set_xlim(-2.5, 2.5)
        self.ax.set_ylim(-2.5, 2.5)
        self.canvas = FigureCanvasTkAgg(figure=self.fig, master=self)
        self.canvas.get_tk_widget().grid(column=0,
                                         columnspan=2,
                                         row=1,
                                         rowspan=2,
                                         padx=20,
                                         pady=20)
        self.drag_handler = Drag_and_Drop_Handler(self.fig)
        ww = WINDOW_WIDTH
        wh = 0.1
        window = Rectangle((-ww / 2, 2.5 - wh), width=ww, height=wh, lw=1, fc='k', ec='k', gid=0)
        self.ax.add_patch(window)

    def initialize_sim_parameters(self):
        self.sim_parameters_frame = LabelFrame(self,
                                               text="Simulation Parameters")
        self.sim_parameters_frame.grid(column=2,
                                       row=1,
                                       padx=20,
                                       pady=20)

        self.max_sunlight_label = Label(self.sim_parameters_frame,
                                        text="Max Sunlight Illuminance [lux]")
        self.max_sunlight_label.grid(row=0,
                                       column=0)
        self.max_sunlight_entry = Entry(self.sim_parameters_frame,
                                          textvariable=self.max_sun,
                                          width=10,
                                          justify="center")
        self.max_sunlight_entry.grid(column=1,
                                       row=0)

        self.max_brightness_label = Label(self.sim_parameters_frame,
                                          text="Max Light Source Luminosity [lm]")
        self.max_brightness_label.grid(row=1,
                                       column=0)
        self.max_brightness_entry = Entry(self.sim_parameters_frame,
                                          textvariable=self.max_brightness,
                                          width=10,
                                          justify="center")
        self.max_brightness_entry.grid(column=1,
                                       row=1)

        self.light_pollution_label = Label(self.sim_parameters_frame,
                                           text="Light Pollution [lux]")
        self.light_pollution_label.grid(row=2,
                                       column=0)
        self.light_pollution_entry = Entry(self.sim_parameters_frame,
                                           textvariable=self.light_pollution,
                                           width=10,
                                           justify="center")
        self.light_pollution_entry.grid(column=1,
                                        row=2)

        self.sunset_label = Label(self.sim_parameters_frame,
                                  text="Illuminance at Sunset/Sunrise [lux]")
        self.sunset_label.grid(row=3,
                               column=0)
        self.sunset_entry = Entry(self.sim_parameters_frame,
                                  textvariable=self.sunset,
                                  width=10,
                                  justify="center")
        self.sunset_entry.grid(column=1,
                               row=3)

        self.cloud_label = Label(self.sim_parameters_frame,
                                 text="Cloud Coverage [%]")
        self.cloud_label.grid(row=4,
                              column=0)
        self.cloud_entry = Entry(self.sim_parameters_frame,
                                 textvariable=self.cloud,
                                 width=10,
                                 justify="center")
        self.cloud_entry.grid(column=1,
                              row=4)

        self.start_time_label = Label(self.sim_parameters_frame,
                                      text="Start Time [hr]")
        self.start_time_label.grid(row=5,
                                   column=0)
        self.start_time_entry = Entry(self.sim_parameters_frame,
                                      textvariable=self.start_time,
                                      width=10,
                                      justify="center")
        self.start_time_entry.grid(column=1,
                                   row=5)

        self.duration_label = Label(self.sim_parameters_frame,
                                    text="Sim Duration [hr]")
        self.duration_label.grid(row=6,
                                 column=0)
        self.duration_entry = Entry(self.sim_parameters_frame,
                                    textvariable=self.duration,
                                    width=10,
                                    justify="center")
        self.duration_entry.grid(column=1,
                                 row=6)

    def initialize_controller_parameters(self):
        self.control_frame = LabelFrame(self,
                                        text="Controller Parameters")
        self.control_frame.grid(column=2,
                                row=2,
                                padx=20,
                                pady=20)

        self.max_lux_label = Label(self.control_frame,
                                   text="Illuminance at 100% [lux]")
        self.max_lux_label.grid(row=0,
                                column=0)
        self.max_lux_entry = Entry(self.control_frame,
                                   textvariable=self.max_lux_str,
                                   width=10,
                                   justify="center")
        self.max_lux_entry.grid(column=1,
                                row=0)

        self.height_step_label = Label(self.control_frame,
                                       text="Height Step Size")
        self.height_step_label.grid(row=1,
                                    column=0)
        self.height_step_entry = Entry(self.control_frame,
                                       textvariable=self.height_step_size,
                                       width=10,
                                       justify="center")
        self.height_step_entry.grid(column=1,
                                    row=1)

        self.tilt_step_label = Label(self.control_frame,
                                       text="Tilt Step Size")
        self.tilt_step_label.grid(row=2,
                                  column=0)
        self.tilt_step_entry = Entry(self.control_frame,
                                     textvariable=self.tilt_step_size,
                                     width=10,
                                     justify="center")
        self.tilt_step_entry.grid(column=1,
                                  row=2)

        self.sample_label = Label(self.control_frame,
                                  text="Sample Period [s]")
        self.sample_label.grid(row=3,
                               column=0)
        self.sample_entry = Entry(self.control_frame,
                                  textvariable=self.sample_period,
                                  width=10,
                                  justify="center")
        self.sample_entry.grid(column=1,
                               row=3)

        self.error_label = Label(self.control_frame,
                                 text="Error Threshold [%]")
        self.error_label.grid(row=4,
                              column=0)
        self.error_entry = Entry(self.control_frame,
                                 textvariable=self.err_thresh,
                                 width=10,
                                 justify="center")
        self.error_entry.grid(column=1,
                              row=4)

        self.timeout_label = Label(self.control_frame,
                                   text="Timeout")
        self.timeout_label.grid(row=5,
                                column=0)
        self.timeout_entry = Entry(self.control_frame,
                                   textvariable=self.timeout,
                                   width=10,
                                   justify="center")
        self.timeout_entry.grid(column=1,
                                row=5)

        self.response_checkbutton = Checkbutton(self.control_frame,
                                                text='Use Call/Response With Battery Powered Devices',
                                                variable=self.use_response)
        self.response_checkbutton.grid(column=0,
                                       columnspan=2,
                                       row=7)

        self.ref_label = Label(self.control_frame,
                               text="Reference Brightness [%]")
        self.ref_label.grid(row=6,
                            column=0)
        self.ref_entry = Entry(self.control_frame,
                               textvariable=self.refs,
                               width=10,
                               justify="center")
        self.ref_entry.grid(column=1,
                            row=6)


    def initialize_sensor_frame(self):
        self.sensor_frame = LabelFrame(self,
                                       text="Sensors")
        self.sensor_frame.grid(column=0,
                               row=0,
                               padx=20,
                               pady=20)
        self.add_sensor_button = Button(self.sensor_frame,
                                        text="Add Sensor",
                                        command=self.add_sensor)
        self.add_sensor_button.grid(column=0,
                                    row=0)
        self.delete_sensor_button = Button(self.sensor_frame,
                                           text="Delete Sensor",
                                           command=self.delete_sensor)
        self.delete_sensor_button.grid(column=1,
                                       row=0)
        self.sensor_notebook = ttk.Notebook(self.sensor_frame)
        self.sensor_notebook.grid(column=0,
                                  row=1,
                                  columnspan=2)

    def add_sensor(self):
        if self.num_sensors >= MAX_SENSORS:
            return
        if len(self.sensor_ids) == 0:
            gid = 1
        else:
            gid = self.sensor_ids[-1] + 2
        self.sensor_ids.append(gid)
        r = Rectangle((-SW / 2, -SH / 2), width=SW, height=SH, fc='r', gid=gid, picker=True)
        self.ax.add_patch(r)
        self.create_sensor_tab(gid)
        plt.draw()

    def create_sensor_tab(self, gid):
        self.num_sensors += 1
        tab = Frame(self.sensor_notebook)
        x_label = Label(tab,
                        text="X =")
        x_label.grid(row=0,
                     column=0)
        y_label = Label(tab,
                        text="Y =")
        y_label.grid(row=1,
                     column=0)
        use_battery = BooleanVar()
        battery_checkbutton = Checkbutton(tab,
                                          text='Battery Powered',
                                          variable=use_battery)
        battery_checkbutton.grid(row=0,
                                 rowspan=2,
                                 column=1)
        self.sensor_notebook.add(tab, text="{}".format(int((gid - 1) / 2)))
        self.sensor_tabs.append([gid, x_label, y_label, use_battery])

    def update_sensor_notebook(self):
        gid_data = []
        tab_data = []
        for patch in self.ax.patches:
            gid = patch.get_gid()
            if gid % 2 == 1:
                x, y = patch.get_xy()
                gid_data.append(gid)
                tab_data.append([x + SW / 2, y + SH / 2])
        for t in self.sensor_tabs:
            tab_gid, x_label, y_label, _ = t
            idx = argwhere(array(gid_data) == tab_gid).squeeze()
            x, y = tab_data[idx]
            x_label['text'] = "X = {}".format(round(x, 5))
            y_label['text'] = "Y = {}".format(round(2.5 - y, 5))

    def delete_sensor(self):
        if len(self.sensor_tabs) == 0:
            return
        tab_name = self.sensor_notebook.select()
        tab_gid = 2 * int(self.sensor_notebook.tab(tab_name)['text']) + 1
        for patch in self.ax.patches:
            if tab_gid == patch.get_gid():
                self.ax.patches.remove(patch)
                plt.draw()
                break
        idx = argwhere(array(self.sensor_ids) == tab_gid).squeeze()
        self.sensor_tabs.pop(idx)
        self.sensor_ids.remove(tab_gid)
        self.num_sensors -= 1
        self.sensor_notebook.forget(tab_name)

    def initialize_light_source_frame(self):
        self.light_source_frame = LabelFrame(self,
                                             text="Light Sources")
        self.light_source_frame.grid(column=1,
                                     row=0,
                                     padx=20,
                                     pady=20)
        self.add_light_source_button = Button(self.light_source_frame,
                                              text="Add Light Source",
                                              command=self.add_light_source)
        self.add_light_source_button.grid(column=0,
                                          row=0)
        self.delete_light_source_button = Button(self.light_source_frame,
                                                 text="Delete Light Source",
                                                 command=self.delete_light_source)
        self.delete_light_source_button.grid(column=1,
                                             row=0)
        self.light_source_notebook = ttk.Notebook(self.light_source_frame)
        self.light_source_notebook.grid(column=0,
                                        row=1,
                                        columnspan=2)

    def add_light_source(self):
        if self.num_light_source >= MAX_LIGHT_SOURCES:
            return
        if len(self.light_source_ids) == 0:
            gid = 2
        else:
            gid = self.light_source_ids[-1] + 2
        self.light_source_ids.append(gid)
        r = Rectangle((-SW / 2, -SH / 2), width=SW, height=SH, fc='b', gid=gid, picker=True)
        self.ax.add_patch(r)
        self.create_light_source_tab(gid)
        plt.draw()

    def create_light_source_tab(self, gid):
        self.num_light_source += 1
        tab = Frame(self.light_source_notebook)
        x_label = Label(tab,
                        text="X =")
        x_label.grid(row=0,
                     column=0)
        y_label = Label(tab,
                        text="Y =")
        y_label.grid(row=1,
                     column=0)
        light_label = Label(tab,
                            text='Brightness [%]')
        light_label.grid(row=0,
                         column=1)
        brightness = StringVar()
        brightness.set('50,100')
        light_entry = Entry(tab,
                            textvariable=brightness,
                            width=10,
                            justify="center")
        light_entry.grid(row=1,
                         column=1)
        self.light_source_notebook.add(tab, text="{}".format(int((gid - 2) / 2)))
        self.light_source_tabs.append([gid, x_label, y_label, brightness])

    def update_light_source_notebook(self):
        gid_data = []
        tab_data = []
        for patch in self.ax.patches:
            gid = patch.get_gid()
            if gid % 2 == 0 and gid != 0:
                x, y = patch.get_xy()
                gid_data.append(gid)
                tab_data.append([x + SW / 2, y + SH / 2])
        for t in self.light_source_tabs:
            tab_gid, x_label, y_label, _ = t
            idx = argwhere(array(gid_data) == tab_gid).squeeze()
            x, y = tab_data[idx]
            x_label['text'] = "X = {}".format(round(x, 5))
            y_label['text'] = "Y = {}".format(round(2.5 - y, 5))

    def delete_light_source(self):
        if len(self.light_source_tabs) == 0:
            return
        tab_name = self.light_source_notebook.select()
        tab_gid = 2 * int(self.light_source_notebook.tab(tab_name)['text']) + 2
        for patch in self.ax.patches:
            if tab_gid == patch.get_gid():
                self.ax.patches.remove(patch)
                plt.draw()
                break
        idx = argwhere(array(self.light_source_ids) == tab_gid).squeeze()
        self.light_source_tabs.pop(idx)
        self.light_source_ids.remove(tab_gid)
        self.num_light_source -= 1
        self.light_source_notebook.forget(tab_name)

    def simulate(self):
        ref_str = self.refs.get().split(",")
        refs = [float(i) / 100 for i in ref_str]

        cloud_str = self.cloud.get().split(",")
        clouds = [float(i) / 100 for i in cloud_str]

        light_sources = []
        for i in range(self.num_light_source):
            light_str = self.light_source_tabs[i][3].get().split(",")
            light = [float(i) / 100 for i in light_str]
            light_sources.append(light)

        start_time = int(3600 * float(self.start_time.get()))
        duration = int(3600 * float(self.duration.get())) + 1

        self.max_lux = float(self.max_lux_str.get())
        ref_freq = int(ceil(duration / len(refs)))
        ref_idx = -1
        self.ref = 0
        timeout = int(self.timeout.get())
        self.err = 0
        self.thresh = float(self.err_thresh.get()) / 100
        use_battery = self.use_response.get()

        measure_freq = int(self.sample_period.get())
        self.measured_light = zeros(self.num_sensors + 1)
        self.alpha_h = float(self.height_step_size.get())
        self.alpha_theta = float(self.tilt_step_size.get())
        self.initialize_sensors_and_lights()

        max_sun = float(self.max_sun.get())
        light_pollution = float(self.light_pollution.get())
        sunset = float(self.sunset.get())

        self.h = 0
        self.theta = pi / 4

        self.time = []
        self.outside_light = []
        self.reference_light = []
        self.room_light = []
        self.m_light = []

        for s in range(duration):
            t = start_time + s
            fraction = s / duration

            cloud_cover = get_cloud_cover(fraction, clouds)
            sunlight = get_sunlight(t, max_sun, cloud_cover, light_pollution, sunset)

            if s % ref_freq == 0:
                ref_idx += 1
                self.ref = refs[ref_idx]
            if s % measure_freq == 0:
                self.measure_light(fraction, sunlight)
                self.control()
            elif s % measure_freq < timeout and abs(self.err) > self.thresh:
                if use_battery:
                    self.measure_light(fraction, sunlight)
                else:
                    self.partial_measure_light(fraction, sunlight)
                self.control()

            room = self.get_room_light(fraction, sunlight)

            self.time.append(t / 3600)
            self.outside_light.append(sunlight)
            self.reference_light.append(self.ref * self.max_lux)
            self.room_light.append(room)
            self.m_light.append(mean(self.measured_light[1:]))

        self.open_plot_window()

    def measure_light(self, fraction, sunlight):
        self.measured_light[0] = random.normal(sunlight, 0.01)
        window_light = WINDOW_AREA * (1 - self.h * cos(self.theta)) * sunlight
        for i in range(self.num_sensors):
            dst = self.sensor_x[i] ** 2 + (self.sensor_y[i] - 2.5) ** 2
            lux = random.normal(window_light, 0.01) / dst
            for j in range(self.num_light_source):
                dst_x = (self.sensor_x[i] - self.light_source_x[j]) ** 2
                dst_y = (self.sensor_y[i] - self.light_source_y[j]) ** 2
                dst = dst_x + dst_y
                idx = floor(fraction * len(self.light_source_level[j])).astype(int)
                lum = self.light_source_level[j][idx]
                lux += random.normal(lum, 0.01) / dst
            self.measured_light[i + 1] = lux

    def partial_measure_light(self, fraction, sunlight):
        window_light = WINDOW_AREA * (1 - self.h * cos(self.theta)) * sunlight
        for i in range(self.num_sensors):
            if not self.sensor_battery:
                dst = self.sensor_x[i] ** 2 + (self.sensor_y[i] - 2.5) ** 2
                lux = random.normal(window_light, 0.01) / dst
                for j in range(self.num_light_source):
                    dst_x = (self.sensor_x[i] - self.light_source_x[j]) ** 2
                    dst_y = (self.sensor_y[i] - self.light_source_y[j]) ** 2
                    dst = dst_x + dst_y
                    idx = floor(fraction * len(self.light_source_level[j])).astype(int)
                    lum = self.light_source_level[j][idx]
                    lux += random.normal(lum, 0.01) / dst
                self.measured_light[i + 1] = lux

    def control(self):
        if self.num_sensors == 0:
            return
        window = clip(self.measured_light[0] / self.max_lux, 0, 1)
        room = clip(mean(self.measured_light[1:]) / self.max_lux, 0, 1)
        self.err = self.ref - room
        dh = -self.alpha_h * self.err * window * cos(self.theta)
        dtheta = self.alpha_theta * self.err * window * self.h * sin(self.theta)
        self.h = clip(self.h + dh, 0, 1)
        self.theta = clip(self.theta + dtheta, pi / 180, pi / 2)

    def initialize_sensors_and_lights(self):
        max_lux = float(self.max_brightness.get())
        self.sensor_x = []
        self.sensor_y = []
        self.sensor_battery = []
        self.light_source_x = []
        self.light_source_y = []
        self.light_source_level = []
        s_idx = 0
        l_idx = 0
        for patch in self.ax.patches:
            gid = patch.get_gid()
            if gid % 2 == 1:
                x, y = patch.get_xy()
                self.sensor_x.append(x + SW / 2)
                self.sensor_y.append(y + SH / 2)
                self.sensor_battery.append(self.sensor_tabs[s_idx][3].get())
                s_idx += 1
            elif gid % 2 == 0 and gid != 0:
                x, y = patch.get_xy()
                self.light_source_x.append(x + SW / 2)
                self.light_source_y.append(y + SH / 2)
                light_str = self.light_source_tabs[l_idx][3].get().split(",")
                light = [max_lux * float(i) / 100 for i in light_str]
                self.light_source_level.append(light)
                l_idx += 1

    def get_room_light(self, fraction, sunlight):
        if self.num_sensors == 0:
            return 0
        window_light = WINDOW_AREA * (1 - self.h * cos(self.theta)) * sunlight
        luxs = []
        for i in range(self.num_sensors):
            dst = self.sensor_x[i] ** 2 + (self.sensor_y[i] - 2.5) ** 2
            lux = window_light / dst
            for j in range(self.num_light_source):
                dst_x = (self.sensor_x[i] - self.light_source_x[j]) ** 2
                dst_y = (self.sensor_y[i] - self.light_source_y[j]) ** 2
                dst = dst_x + dst_y
                idx = floor(fraction * len(self.light_source_level[j])).astype(int)
                lum = self.light_source_level[j][idx]
                lux += lum / dst
            luxs.append(lux)
        return mean(luxs)

    def open_plot_window(self):
        self.plot_outside = BooleanVar()
        self.plot_outside.set(False)
        self.plot_ref = BooleanVar()
        self.plot_ref.set(True)
        self.plot_room = BooleanVar()
        self.plot_room.set(True)
        self.plot_measured = BooleanVar()
        self.plot_measured.set(False)

        self.plot_window = Toplevel(self)
        self.plot_window.title('Lighting Plot')
        plot = plt.figure(figsize=(8, 6), dpi=100)
        self.canvas2 = FigureCanvasTkAgg(figure=plot, master=self.plot_window)
        self.canvas2.get_tk_widget().grid(column=1,
                                          columnspan=2,
                                          row=0,
                                          rowspan=5,
                                          padx=20,
                                          pady=20)
        toolbar = NavigationToolbar2Tk(self.canvas2, self.plot_window, pack_toolbar=False)
        toolbar.update()
        toolbar.grid(column=1,
                     columnspan=1,
                     row=5)

        plt.plot(self.time, self.reference_light, 'r', label='Reference', linewidth=2, linestyle=':')
        plt.plot(self.time, self.room_light, 'b', label='Room', linewidth=0.5)
        plt.xlim(self.time[0], self.time[-1])
        plt.xlabel('Time [hr]')
        plt.ylabel('Illuminance [lux]')
        plt.legend(bbox_to_anchor=(0.5, 1.1), loc='upper center', ncol=4, prop=fontP)
        self.canvas2.draw()

        self.outside_checkbutton = Checkbutton(self.plot_window,
                                               text='Outside',
                                               variable=self.plot_outside)
        self.outside_checkbutton.grid(row=0,
                                      column=0)
        self.ref_checkbutton = Checkbutton(self.plot_window,
                                           text='Reference',
                                           variable=self.plot_ref)
        self.ref_checkbutton.grid(row=1,
                                  column=0)
        self.room_checkbutton = Checkbutton(self.plot_window,
                                            text='Room',
                                            variable=self.plot_room)
        self.room_checkbutton.grid(row=2,
                                   column=0)
        self.measure_checkbutton = Checkbutton(self.plot_window,
                                               text='Measure',
                                               variable=self.plot_measured)
        self.measure_checkbutton.grid(row=3,
                                      column=0)
        self.update_button = Button(self.plot_window,
                                    text='Refresh Plot',
                                    command=self.update_plot)
        self.update_button.grid(row=4,
                                column=0)


    def update_plot(self):
        plt.cla()
        if self.plot_outside.get():
            plt.plot(self.time, self.outside_light, 'k', label='Outside', linestyle='--')
        if self.plot_ref.get():
            plt.plot(self.time, self.reference_light, 'r', label='Reference', linewidth=2, linestyle=':')
        if self.plot_room.get():
            plt.plot(self.time, self.room_light, 'b', label='Room', linewidth=0.5)
        if self.plot_measured.get():
            plt.plot(self.time, self.m_light, 'g', label='Measured', linewidth=0.75, linestyle='-.')
        plt.xlim(self.time[0], self.time[-1])
        plt.xlabel('Time [hr]')
        plt.ylabel('Illuminance [lux]')
        plt.legend(bbox_to_anchor=(0.5, 1.1), loc='upper center', ncol=4, prop=fontP)
        self.canvas2.draw()

    def update_ui(self):
        if self.num_sensors > 0:
            self.update_sensor_notebook()
        if self.num_light_source > 0:
            self.update_light_source_notebook()
        self.after(100, self.update_ui)


if __name__ == '__main__':
    root = Root()
    root.mainloop()
    root.quit()