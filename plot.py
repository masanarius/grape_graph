
import pandas as pd
import matplotlib.pyplot as plt
import os
import math
from datetime import timedelta

# === グラフ設定 ===
show_title = True
title_str = "Engagement over Time"
show_xlabel = True
xlabel_str = "Time"
show_ylabel = True
ylabel_str = "Engagement Level"

# === 図のスタイル設定 ===
fig_width = 10
fig_height = 5
show_xticks = True
show_yticks = True
legend_location = 'right'

# === 各列（P_n）がすべてゼロなら描画しないオプション ===
skip_column_if_all_zero = True

# === X軸の表示モードとスタイル ===
x_axis_mode = "elapsed"   # "clock" or "elapsed"
x_axis_format = "colon"   # "colon" or "symbol"

# === X軸のカスタム設定 ===
use_custom_xlim = False
custom_xlim_start = "20:28:00.000"
custom_xlim_end   = "20:29:00.000"

# === X軸ラベルの表示間隔（秒） ===
xtick_interval_seconds = 5  # 5, 10, 15, 20, 30, 60 のみ対応

# === ファイルのプレフィックス設定 ===
input_prefix_engage = "engagement_dialog_"
input_prefix_record = "recording_dialog_"
output_prefix_width = "width_dialog_"
output_prefix_total = "total_dialog_"
output_prefix_width_player = "width_player_"
output_prefix_total_player = "total_player_"

# === 時刻目盛マップ ===
TICK_SECOND_MAP = {
    5:  [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55],
    10: [0, 10, 20, 30, 40, 50],
    15: [0, 15, 30, 45],
    20: [0, 20, 40],
    30: [0, 30],
    60: [0]
}

# === フォルダ階層 ===
root_folder = ".."
project_folder = "grape_build"
platform_folder = "win"
data_folder = "Grape_Data"
log_folder = "CsvLog_20250405202752"
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), root_folder, project_folder, platform_folder, data_folder, log_folder))
output_dir = os.path.join(os.path.dirname(__file__), log_folder)
os.makedirs(output_dir, exist_ok=True)

def extract_time_datetime(df):
    if "time" in df.columns:
        return pd.to_datetime(df["time"], format="%H:%M:%S.%f", errors="coerce")
    return pd.Series(df.index, dtype='datetime64[ns]')

def get_xlim_range():
    index = 1
    min_time, max_time = None, None
    while True:
        path = os.path.join(base_dir, f"{input_prefix_engage}{index}.csv")
        if not os.path.exists(path):
            break
        df = pd.read_csv(path)
        t = extract_time_datetime(df)
        if not t.empty:
            t_min, t_max = t.min(), t.max()
            min_time = t_min if min_time is None else min(min_time, t_min)
            max_time = t_max if max_time is None else max(max_time, t_max)
        index += 1
    if use_custom_xlim:
        x_start = pd.to_datetime(custom_xlim_start, format="%H:%M:%S.%f")
        x_end = pd.to_datetime(custom_xlim_end, format="%H:%M:%S.%f")
    else:
        min_ts = min_time.timestamp()
        max_ts = max_time.timestamp()
        x_start = pd.to_datetime(math.floor(min_ts / xtick_interval_seconds) * xtick_interval_seconds, unit='s')
        x_end = pd.to_datetime(math.ceil(max_ts / xtick_interval_seconds) * xtick_interval_seconds, unit='s')
    return x_start, x_end

def make_plot(x, ys, labels, outpath, ylimit):
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    for y, label in zip(ys, labels):
        ax.plot(x, y, label=label)
    if show_title:
        ax.set_title(title_str, fontfamily='monospace')
    if show_xlabel:
        ax.set_xlabel(xlabel_str, fontfamily='monospace')
    if show_ylabel:
        ax.set_ylabel(ylabel_str, fontfamily='monospace')
    ax.set_ylim(0, ylimit)
    ax.set_xlim(xlim_start, xlim_end)
    allowed_seconds = TICK_SECOND_MAP[xtick_interval_seconds]
    tick_times, tick_labels = [], []
    current = xlim_start
    while current <= xlim_end:
        if current.second in allowed_seconds and current.microsecond == 0:
            tick_times.append(current)
            minutes = current.strftime("%M") if x_axis_mode == "clock" else f"{(current - xlim_start).seconds // 60}"
            seconds = current.strftime("%S") if x_axis_mode == "clock" else f"{(current - xlim_start).seconds % 60:02d}"
            tick_labels.append(f"{minutes}'{seconds}\"" if x_axis_format == "symbol" else f"{minutes}:{seconds}")
        current += timedelta(seconds=1)
    ax.set_xticks(tick_times)
    ax.set_xticklabels(tick_labels, fontfamily='monospace')
    for label in ax.get_yticklabels():
        label.set_family('monospace')
    ax.tick_params(axis='x', labelbottom=show_xticks)
    ax.tick_params(axis='y', labelleft=show_yticks)
    ax.grid(True)
    if legend_location == 'right':
        ax.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), prop={'family': 'monospace'})
    else:
        ax.legend(loc=legend_location, prop={'family': 'monospace'})
    plt.tight_layout()
    plt.savefig(outpath, bbox_inches='tight')
    plt.close()
    print(f"保存しました: {outpath}")

xlim_start, xlim_end = get_xlim_range()

index = 1
while True:
    epath = os.path.join(base_dir, f"{input_prefix_engage}{index}.csv")
    rpath = os.path.join(base_dir, f"{input_prefix_record}{index}.csv")
    if not os.path.exists(epath): break
    df_e = pd.read_csv(epath)
    df_r = pd.read_csv(rpath) if os.path.exists(rpath) else None
    x = extract_time_datetime(df_e)
    cols = [c for c in df_e.columns if c not in ["time", "timestamp"]]
    ys_w, ys_t, labels = [], [], []
    for i, c in enumerate(cols):
        y = pd.to_numeric(df_e[c], errors="coerce").fillna(0)
        if skip_column_if_all_zero and y.eq(0).all(): continue
        ys_w.append(y)
        labels.append(f"P_{i+1:02}")
        if df_r is not None:
            yr = pd.to_numeric(df_r[c], errors="coerce").fillna(0)
            ysum = y + yr
            if not (skip_column_if_all_zero and ysum.eq(0).all()):
                ys_t.append(ysum)
    if ys_w:
        make_plot(x, ys_w, labels, os.path.join(output_dir, f"{output_prefix_width}{index}.pdf"), ylimit=1)
    if ys_t:
        make_plot(x, ys_t, labels, os.path.join(output_dir, f"{output_prefix_total}{index}.pdf"), ylimit=2)
    index += 1

# プレイヤー別処理
player_eng, player_tot = {}, {}
index = 1
while True:
    epath = os.path.join(base_dir, f"{input_prefix_engage}{index}.csv")
    rpath = os.path.join(base_dir, f"{input_prefix_record}{index}.csv")
    if not os.path.exists(epath): break
    df_e = pd.read_csv(epath)
    df_r = pd.read_csv(rpath) if os.path.exists(rpath) else None
    t = extract_time_datetime(df_e)
    cols = [c for c in df_e.columns if c not in ["time", "timestamp"]]
    for i, c in enumerate(cols):
        y = pd.to_numeric(df_e[c], errors="coerce").fillna(0)
        if skip_column_if_all_zero and y.eq(0).all(): continue
        player_eng.setdefault(i, []).append((t, y, f"D_{index:02}"))
        if df_r is not None and c in df_r.columns:
            yr = pd.to_numeric(df_r[c], errors="coerce").fillna(0)
            yt = y + yr
            if skip_column_if_all_zero and yt.eq(0).all(): continue
            player_tot.setdefault(i, []).append((t, yt, f"D_{index:02}"))
    index += 1

def make_player_plot(pdict, outprefix, ylimit):
    for i, datalist in pdict.items():
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        for t, y, label in datalist:
            ax.plot(t, y, label=label)
        if show_title:
            ax.set_title(f"{title_str} - Player {i+1}", fontfamily='monospace')
        if show_xlabel:
            ax.set_xlabel(xlabel_str, fontfamily='monospace')
        if show_ylabel:
            ax.set_ylabel(ylabel_str, fontfamily='monospace')
        ax.set_ylim(0, ylimit)
        ax.set_xlim(xlim_start, xlim_end)
        allowed_seconds = TICK_SECOND_MAP[xtick_interval_seconds]
        tick_times, tick_labels = [], []
        current = xlim_start
        while current <= xlim_end:
            if current.second in allowed_seconds and current.microsecond == 0:
                tick_times.append(current)
                minutes = current.strftime("%M") if x_axis_mode == "clock" else f"{(current - xlim_start).seconds // 60}"
                seconds = current.strftime("%S") if x_axis_mode == "clock" else f"{(current - xlim_start).seconds % 60:02d}"
                tick_labels.append(f"{minutes}'{seconds}\"" if x_axis_format == "symbol" else f"{minutes}:{seconds}")
            current += timedelta(seconds=1)
        ax.set_xticks(tick_times)
        ax.set_xticklabels(tick_labels, fontfamily='monospace')
        for label in ax.get_yticklabels():
            label.set_family('monospace')
        ax.tick_params(axis='x', labelbottom=show_xticks)
        ax.tick_params(axis='y', labelleft=show_yticks)
        ax.grid(True)
        if legend_location == 'right':
            ax.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), prop={'family': 'monospace'})
        else:
            ax.legend(loc=legend_location, prop={'family': 'monospace'})
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f"{outprefix}{i+1}.pdf"), bbox_inches='tight')
        plt.close()
        print(f"保存しました: {outprefix}{i+1}.pdf")

make_player_plot(player_eng, output_prefix_width_player, ylimit=1)
make_player_plot(player_tot, output_prefix_total_player, ylimit=2)