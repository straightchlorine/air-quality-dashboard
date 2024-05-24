import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import seaborn as sns
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import mplcursors

def plot_temp_time(df):
    _plot_temp_time(df)

def _plot_temp_time(df):
    df = df.tail(10)  
    ax.clear()
    lineplot = sns.lineplot(data=df, x='time', y='temperature', marker='o', ax=ax)
    ax.set_xlabel('')
    ax.set_ylabel('Temperature')
    ax.set_title('Temperature over Time')
    ax.grid(True)
    ax.set_xticks(range(len(df['time'])))
    ax.set_xticklabels([str(time)[:19] for time in df['time']], rotation=45, ha='right')
    fig.tight_layout() 
    canvas.draw_idle()
    cursor = mplcursors.cursor(lineplot.get_lines(), hover=True)
    cursor.connect("add", lambda sel: sel.annotation.set_text(f"Temperature: {sel.target[1]:.2f}"))

def plot_co2_temp(df):
    _plot_co2_temp(df)

def _plot_co2_temp(df):
    df = df.tail(10)  
    ax.clear()
    lineplot = sns.lineplot(data=df, x='time', y='co2', marker='o', color='orange', ax=ax)
    ax.set_xlabel('')
    ax.set_ylabel('CO2')
    ax.set_title('CO2 vs Time')
    ax.grid(True)
    ax.set_xticks(range(len(df['time'])))
    ax.set_xticklabels([str(time)[:19] for time in df['time']], rotation=45, ha='right')
    fig.tight_layout()  
    canvas.draw_idle()
    cursor = mplcursors.cursor(lineplot.get_lines(), hover=True)
    cursor.connect("add", lambda sel: sel.annotation.set_text(f"CO2: {sel.target[1]:.2f}"))

def plot_temp_nh4(df):
    _plot_temp_nh4(df)

def _plot_temp_nh4(df):
    df = df.tail(10)  
    ax.clear()
    lineplot_temp = sns.lineplot(data=df, x='time', y='temperature', marker='o', ax=ax, label='Temperature')
    lineplot_nh4 = sns.lineplot(data=df, x='time', y='nh4', marker='o', ax=ax, label='NH4', color='green')
    lineplot_co = sns.lineplot(data=df, x='time', y='co', marker='o', ax=ax, label='CO', color='red')
    ax.set_xlabel('')
    ax.set_ylabel('Values')
    ax.set_title('Temperature, NH4, and CO over Time')
    ax.legend()
    ax.grid(True)
    ax.set_xticks(range(len(df['time'])))
    ax.set_xticklabels([str(time)[:19] for time in df['time']], rotation=45, ha='right')
    fig.tight_layout()  
    canvas.draw_idle()

    def update_annotation(sel):
        x_value = sel.target[0]
        y_value = sel.target[1]

        if sel.artist.get_label() == 'Temperature':
            value_text = f"Temperature: {y_value:.2f}"
        elif sel.artist.get_label() == 'NH4':
            value_text = f"NH4: {y_value:.2f}"
        elif sel.artist.get_label() == 'CO':
            value_text = f"CO: {y_value:.2f}"
        else:
            value_text = ""

        annotation_text = f"{value_text}"
        sel.annotation.set_text(annotation_text)

    cursor = mplcursors.cursor(lineplot_temp.get_lines() + lineplot_nh4.get_lines() + lineplot_co.get_lines(), hover=True)
    cursor.connect("add", update_annotation)

def update_treeview(tree, df):
    for child in tree.get_children():
        tree.delete(child)

    for index, row in df.tail(10).iterrows():
        shortened_time = str(row['time'])[:19]
        row_values = list(row)
        row_values[0] = shortened_time
        tree.insert("", "end", values=row_values)

class MyHandler(FileSystemEventHandler):
    def __init__(self, filename, tree):
        super(MyHandler, self).__init__()
        self.filename = filename
        self.tree = tree

    def on_modified(self, event):
        if event.src_path.endswith(self.filename):
            print(f"Detected modification in {self.filename}")
            df = pd.read_csv(self.filename)
            update_treeview(self.tree, df)
            if current_plot == 'temperature':
                plot_temp_time(df)
            elif current_plot == 'co2':
                plot_co2_temp(df)
            else:
                plot_temp_nh4(df)

def watch_file(filename, tree):
    event_handler = MyHandler(filename, tree)
    observer.schedule(event_handler, path='.', recursive=False)
    observer.start()
    print(f"Watching {filename} for changes...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def switch_plot(plot_type):
    global current_plot
    current_plot = plot_type
    if plot_type == 'temperature':
        plot_temp_time(df)
    elif plot_type == 'co2':
        plot_co2_temp(df)
    else:
        plot_temp_nh4(df)

if __name__ == "__main__":
    filename = "data.csv"
    df = pd.read_csv(filename)

    root = tk.Tk()
    root.title("UI Dane z czujnika")

    tree_frame = tk.Frame(root)
    tree_frame.pack(pady=10)

    tree = ttk.Treeview(tree_frame)
    tree["columns"] = list(df.columns)
    tree["show"] = "headings"

    for column in tree["columns"]:
        tree.heading(column, text=column)
        if column == 'time':
            tree.column(column, width=130)
        else:
            tree.column(column, width=90)

    tree.pack(side=tk.LEFT)

    fig, ax = plt.subplots(figsize=(8, 6))  
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack()

    update_treeview(tree, df)

    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)

    temp_time_button = tk.Button(button_frame, text="Wykres Temp. vs Czas", command=lambda: switch_plot('temperature'))
    temp_time_button.pack(side="left", padx=10)

    co2_temp_button = tk.Button(button_frame, text="Wykres CO2 vs Temp.", command=lambda: switch_plot('co2'))
    co2_temp_button.pack(side="left", padx=10)

    temp_nh4_button = tk.Button(button_frame, text="Wykres Temp. & NH4 vs Czas", command=lambda: switch_plot('temp_nh4'))
    temp_nh4_button.pack(side="left", padx=10)

    current_plot = 'temperature'
    plot_temp_time(df)

    observer = Observer()
    watch_file_thread = threading.Thread(target=watch_file, args=(filename, tree))
    watch_file_thread.start()

    root.mainloop()
