import asyncio
import json
import threading
import time
import tkinter as tk
from tkinter import ttk
import os

from ahttpdc.reads.interface import DatabaseInterface
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import mplcursors


class Connector:
    """
    Klasa zarządzająca połączeniem z bazą danych.
    """

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

    async def update_data(self):
        """
        Dodaje najnowszy pomiar do DataFrame i zapisuje do pliku CSV.
        """
        async with self.lock:
            row = await self.interface.query_latest()
            self.measurements = pd.concat([self.measurements, row])

            file_exists = os.path.isfile('data.csv')
            self.measurements.to_csv(
                'data.csv',
                index=True,
                header=not file_exists,
                mode='a' if file_exists else 'w',
            )
            return self.measurements


def add_interactive_annotations(ax):
    cursor = mplcursors.cursor(ax, hover=True)
    cursor.connect(
        'add',
        lambda sel: sel.annotation.set_text(
            f'{sel.artist.get_label()}: {sel.target[1]:.2f}'
        ),
    )

    def on_click(event):
        if not event.inaxes:
            cursor.remove()
            ax.figure.canvas.draw()

    ax.figure.canvas.mpl_connect('button_press_event', on_click)
    return cursor


def plot_temp_time(df, ax):
    _plot_temp_time(df, ax)
    add_interactive_annotations(ax)
    ax.figure.autofmt_xdate()


def plot_co2_temp(df, ax):
    _plot_co2_temp(df, ax)
    add_interactive_annotations(ax)
    ax.figure.autofmt_xdate()


def plot_temp_nh4(df, ax):
    _plot_temp_nh4(df, ax)
    add_interactive_annotations(ax)
    ax.figure.autofmt_xdate()


def plot_acet_alc_co_nh4_toulen(df, ax):
    _plot_acet_alc_co_nh4_toulen(df, ax)
    add_interactive_annotations(ax)
    ax.figure.autofmt_xdate()


def _plot_temp_time(df, ax):
    df = df.tail(10)
    ax.clear()
    sns.lineplot(
        data=df, x='time', y='temperature', marker='o', ax=ax, label='Temperature'
    )
    ax.set_xlabel('')
    ax.set_ylabel('Temperature')
    ax.set_title('Temperature over Time')
    ax.grid(True)
    ax.set_xticks(range(len(df['time'])))
    ax.set_xticklabels([str(time)[:19] for time in df['time']], rotation=45, ha='right')


def _plot_co2_temp(df, ax):
    df = df.tail(10)
    ax.clear()
    sns.lineplot(
        data=df, x='time', y='co2', marker='o', color='orange', ax=ax, label='co2'
    )
    ax.set_xlabel('')
    ax.set_ylabel('CO2')
    ax.set_title('CO2 vs Time')
    ax.grid(True)
    ax.set_xticks(range(len(df['time'])))
    ax.set_xticklabels([str(time)[:19] for time in df['time']], rotation=45, ha='right')


def _plot_temp_nh4(df, ax):
    df = df.tail(10)
    ax.clear()
    sns.lineplot(
        data=df, x='time', y='temperature', marker='o', ax=ax, label='Temperature'
    )
    sns.lineplot(
        data=df,
        x='time',
        y='humidity',
        marker='o',
        ax=ax,
        label='Humidity',
        color='black',
    )
    ax.set_xlabel('')
    ax.set_ylabel('Values')
    ax.set_title('Temperature and Humidity over Time')
    ax.legend()
    ax.grid(True)
    ax.set_xticks(range(len(df['time'])))
    ax.set_xticklabels([str(time)[:19] for time in df['time']], rotation=45, ha='right')


def _plot_acet_alc_co_nh4_toulen(df, ax):
    df = df.tail(10)
    ax.clear()
    sns.lineplot(data=df, x='time', y='aceton', marker='o', ax=ax, label='Aceton')
    sns.lineplot(
        data=df, x='time', y='alcohol', marker='o', ax=ax, label='Alcohol', color='blue'
    )
    sns.lineplot(data=df, x='time', y='co', marker='o', ax=ax, label='CO', color='red')
    sns.lineplot(
        data=df, x='time', y='nh4', marker='o', ax=ax, label='NH4', color='green'
    )
    sns.lineplot(
        data=df, x='time', y='toulen', marker='o', ax=ax, label='Toulen', color='purple'
    )
    ax.set_xlabel('')
    ax.set_ylabel('Values')
    ax.set_title('Aceton, Alcohol, CO, NH4, and Toulen over Time')
    ax.legend()
    ax.grid(True)
    ax.set_xticks(range(len(df['time'])))
    ax.set_xticklabels([str(time)[:19] for time in df['time']], rotation=45, ha='right')


def update_treeview(tree, df):
    for child in tree.get_children():
        tree.delete(child)

    for index, row in df.tail(10).iterrows():
        shortened_time = str(row['time'])[:19]
        row_values = list(row)
        row_values[0] = shortened_time
        tree.insert('', 'end', values=row_values)


class MyHandler(FileSystemEventHandler):
    def __init__(self, filename, tree):
        super(MyHandler, self).__init__()
        self.filename = filename
        self.tree = tree

    def on_modified(self, event):
        if event.src_path.endswith(self.filename):
            print(f'Wykryto modyfikację w {self.filename}')
            df = pd.read_csv(self.filename)
            update_treeview(self.tree, df)
            update_plots(df)


def update_plots(df):
    if current_plot == 'temperature_vs_co2':
        plot_temp_time(df, ax1)
        plot_co2_temp(df, ax2)
    elif current_plot == 'temp_nh4':
        plot_temp_nh4(df, ax3)
        plot_acet_alc_co_nh4_toulen(df, ax4)

    canvas1.draw_idle()
    canvas2.draw_idle()
    canvas3.draw_idle()
    canvas4.draw_idle()


def watch_file(filename, tree):
    event_handler = MyHandler(filename, tree)
    observer.schedule(event_handler, path='.', recursive=False)
    observer.start()
    print(f'Watching {filename} for changes...')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def switch_plot(plot_type):
    global current_plot, cursors
    current_plot = plot_type
    if plot_type == 'temperature_vs_co2':
        canvas3.get_tk_widget().pack_forget()
        canvas4.get_tk_widget().pack_forget()
        canvas1.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas2.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        plot_temp_time(df, ax1)
        plot_co2_temp(df, ax2)
    elif plot_type == 'temp_nh4':
        canvas1.get_tk_widget().pack_forget()
        canvas2.get_tk_widget().pack_forget()
        canvas3.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas4.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        plot_temp_nh4(df, ax3)
        plot_acet_alc_co_nh4_toulen(df, ax4)
    elif plot_type == 'acet_alc_co_nh4_toulen':
        canvas1.get_tk_widget().pack_forget()
        canvas2.get_tk_widget().pack_forget()
        canvas3.get_tk_widget().pack_forget()
        canvas4.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        plot_acet_alc_co_nh4_toulen(df, ax4)

    # Remove annotations on plot change
    for cursor in cursors:
        cursor.remove()

    canvas1.draw_idle()
    canvas2.draw_idle()
    canvas3.draw_idle()
    canvas4.draw_idle()


def switch_plot_others():
    global current_plot, cursors
    current_plot = 'temp_nh4'
    canvas1.get_tk_widget().pack_forget()
    canvas2.get_tk_widget().pack_forget()
    canvas4.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    canvas3.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    plot_temp_nh4(df, ax3)
    plot_acet_alc_co_nh4_toulen(df, ax4)

    # Remove annotations on plot change
    for cursor in cursors:
        cursor.remove()

    canvas1.draw_idle()
    canvas2.draw_idle()
    canvas3.draw_idle()
    canvas4.draw_idle()


def enable(connector):
    while True:
        asyncio.run(connector.update_data())


def periodic_update(connector):
    while True:
        time.sleep(60)
        asyncio.run(connector.update_data())


if __name__ == '__main__':
    connector = Connector()

    filename = 'data.csv'
    columns_order = [
        'time',
        'aceton',
        'alcohol',
        'altitude',
        'co',
        'co2',
        'humidity',
        'nh4',
        'pressure',
        'seaLevelPressure',
        'temperature',
        'toulen',
    ]
    if os.path.exists(filename):
        df = pd.read_csv(filename)
        df = df[columns_order]
    else:
        df = pd.DataFrame(columns=columns_order)
        df.to_csv(filename, index=False)

    root = tk.Tk()
    root.title('UI Dane z czujnika')

    tree_frame = tk.Frame(root)
    tree_frame.pack(pady=10)

    tree = ttk.Treeview(tree_frame)
    tree['columns'] = columns_order
    tree['show'] = 'headings'

    for column in columns_order:
        tree.heading(column, text=column)
        if column == 'time':
            tree.column(column, width=130)
        else:
            tree.column(column, width=90)

    tree.pack(side=tk.LEFT)

    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)

    temp_vs_co2_button = tk.Button(
        button_frame,
        text='Temperatura & CO2',
        command=lambda: switch_plot('temperature_vs_co2'),
    )
    temp_vs_co2_button.pack(side='left', padx=10)

    others_button = tk.Button(
        button_frame,
        text='Others',
        command=switch_plot_others,
    )
    others_button.pack(side='left', padx=10)

    current_plot = 'temperature_vs_co2'
    cursors = []

    # Kontener na wykresy
    plot_frame = tk.Frame(root)
    plot_frame.pack(pady=10, fill=tk.BOTH, expand=True)

    fig1, ax1 = plt.subplots(figsize=(8, 6))
    canvas1 = FigureCanvasTkAgg(fig1, master=plot_frame)
    canvas1.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    fig2, ax2 = plt.subplots(figsize=(8, 6))
    canvas2 = FigureCanvasTkAgg(fig2, master=plot_frame)
    canvas2.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    fig3, ax3 = plt.subplots(figsize=(8, 6))
    canvas3 = FigureCanvasTkAgg(fig3, master=plot_frame)
    canvas3.get_tk_widget().pack_forget()

    fig4, ax4 = plt.subplots(figsize=(8, 6))
    canvas4 = FigureCanvasTkAgg(fig4, master=plot_frame)
    canvas4.get_tk_widget().pack_forget()

    update_treeview(tree, df)

    # Początkowy wykres
    plot_temp_time(df, ax1)
    plot_co2_temp(df, ax2)
    canvas1.draw_idle()
    canvas2.draw_idle()

    observer = Observer()
    watch_file_thread = threading.Thread(target=watch_file, args=(filename, tree))
    watch_file_thread.start()

    root.mainloop()

