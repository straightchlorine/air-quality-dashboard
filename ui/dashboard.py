import asyncio
import json
import tkinter as tk
from tkinter import ttk

from ahttpdc.reads.interface import DatabaseInterface
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import mplcursors
import pandas as pd
import seaborn as sns


class Connector:
    def __init__(self):
        self.lock = asyncio.Lock()

        with open('secrets/secrets.json', 'r') as f:
            secrets = json.load(f)

        sensors = {
            'bmp180': ['altitude', 'pressure', 'seaLevelPressure'],
            'mq135': ['aceton', 'alcohol', 'co', 'co2', 'nh4', 'toulen'],
            'ds18b20': ['temperature'],
            'dht22': ['humidity'],
        }

        self.interface = DatabaseInterface(
            secrets['host'],
            secrets['port'],
            secrets['token'],
            secrets['organization'],
            secrets['bucket'],
            sensors,
            secrets['dev_ip'],
            secrets['dev_port'],
            secrets['handle'],
        )

        self.measurements = pd.DataFrame()

    async def _update_data_loop(self):
        async with self.lock:
            row = await self.interface.query_latest()
            self.measurements = pd.concat([self.measurements, row])
            return self.measurements

    async def get_data(self):
        async with self.lock:
            return self.measurements


async def periodic_update(connector, interval):
    while True:
        result = await connector._update_data_loop()
        await asyncio.sleep(interval)


class UI(tk.Tk):
    def __init__(self, connector):
        super().__init__()
        self.title('UI Dane z czujnika')

        self.connector = connector
        self.df = pd.DataFrame()
        self.interval = 1

        self.tree_frame = tk.Frame(self)
        self.tree_frame.pack(pady=10)
        self.tree = ttk.Treeview(self.tree_frame)

        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack()

        self.button_frame = tk.Frame(self)
        self.button_frame.pack(pady=10)

        self.temp_time_button = tk.Button(
            self.button_frame,
            text='Wykres Temp. vs Czas',
            command=self._plot_temp_time,
        )
        self.temp_time_button.pack(side='left', padx=10)
        self.co2_temp_button = tk.Button(
            self.button_frame,
            text='Wykres CO2 vs Temp.',
            command=self._plot_co2_temp,
        )
        self.co2_temp_button.pack(side='left', padx=10)
        self.temp_nh4_button = tk.Button(
            self.button_frame,
            text='Wykres Temp. & NH4 vs Czas',
            command=self._plot_temp_nh4,
        )
        self.temp_nh4_button.pack(side='left', padx=10)

    async def update_data(self):
        while True:
            try:
                data = await self.connector.get_data()
                self.df = pd.DataFrame(data)
                self.update()

            except Exception as e:
                print(f'An error occurred while fetching data: {e}')
            await asyncio.sleep(self.interval)

    def _plot_temp_time(self):
        df = self.df.tail(10)
        self.ax.clear()
        lineplot = sns.lineplot(
            data=df, x=df.index, y='temperature', marker='o', ax=self.ax
        )
        self.ax.set_xlabel('')
        self.ax.set_ylabel('Temperature')
        self.ax.set_title('Temperature over Time')
        self.ax.grid(True)
        self.ax.set_xticks(range(len(df.index)))
        self.ax.set_xticklabels(
            [str(time)[:19] for time in df.index], rotation=45, ha='right'
        )
        self.fig.tight_layout()
        self.canvas.draw_idle()
        cursor = mplcursors.cursor(lineplot.get_lines(), hover=True)
        cursor.connect(
            'add',
            lambda sel: sel.annotation.set_text(f'Temperature: {sel.target[1]:.2f}'),
        )

    def _plot_co2_temp(self):
        df = self.df.tail(10)
        self.ax.clear()
        lineplot = sns.lineplot(
            data=df, x=df.index, y='co2', marker='o', color='orange', ax=self.ax
        )
        self.ax.set_xlabel('')
        self.ax.set_ylabel('CO2')
        self.ax.set_title('CO2 vs Time')
        self.ax.grid(True)
        self.ax.set_xticks(range(len(df.index)))
        self.ax.set_xticklabels(
            [str(time)[:19] for time in df.index], rotation=45, ha='right'
        )
        self.fig.tight_layout()
        self.canvas.draw_idle()
        cursor = mplcursors.cursor(lineplot.get_lines(), hover=True)
        cursor.connect(
            'add', lambda sel: sel.annotation.set_text(f'CO2: {sel.target[1]:.2f}')
        )

    def _plot_temp_nh4(self):
        df = self.df.tail(10)
        self.ax.clear()
        lineplot_temp = sns.lineplot(
            data=df,
            x=df.index,
            y='temperature',
            marker='o',
            ax=self.ax,
            label='Temperature',
        )
        lineplot_nh4 = sns.lineplot(
            data=df,
            x=df.index,
            y='nh4',
            marker='o',
            ax=self.ax,
            label='NH4',
            color='green',
        )
        lineplot_co = sns.lineplot(
            data=df, x=df.index, y='co', marker='o', ax=self.ax, label='CO', color='red'
        )
        self.ax.set_xlabel('')
        self.ax.set_ylabel('Values')
        self.ax.set_title('Temperature, NH4, and CO over Time')
        self.ax.legend()
        self.ax.grid(True)
        self.ax.set_xticks(range(len(df.index)))
        self.ax.set_xticklabels(
            [str(time)[:19] for time in df.index], rotation=45, ha='right'
        )
        self.fig.tight_layout()
        self.canvas.draw_idle()

        def update_annotation(sel):
            x_value = sel.target[0]
            y_value = sel.target[1]

            if sel.artist.get_label() == 'Temperature':
                value_text = f'Temperature: {y_value:.2f}'
            elif sel.artist.get_label() == 'NH4':
                value_text = f'NH4: {y_value:.2f}'
            elif sel.artist.get_label() == 'CO':
                value_text = f'CO: {y_value:.2f}'
            else:
                value_text = ''

            annotation_text = f'{value_text}'
            sel.annotation.set_text(annotation_text)

        cursor = mplcursors.cursor(
            lineplot_temp.get_lines()
            + lineplot_nh4.get_lines()
            + lineplot_co.get_lines(),
            hover=True,
        )
        cursor.connect('add', update_annotation)


def main():
    connector = Connector()
    ui = UI(connector)
    interval = 1

    loop = asyncio.new_event_loop()
    try:
        loop.create_task(periodic_update(connector, interval))
        loop.create_task(ui.update_data())

        ui.update()

        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()


if __name__ == '__main__':
    main()
