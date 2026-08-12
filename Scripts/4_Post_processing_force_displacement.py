import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from mpl_toolkits.mplot3d import Axes3D




# ====================================================
# GLOBAL SETTINGS (defined once)
# ====================================================
model_names = ['mx_1','fl_1','wp_1']
plot_name = model_names[0] + model_names[-1]

mpl.rcParams.update({
    'font.family': 'Times New Roman',
    'font.size': 18,
    'axes.labelsize': 24,
    'xtick.labelsize': 18,
    'ytick.labelsize': 18,
    'legend.fontsize': 18,
    'lines.linewidth': 2.5,
    'grid.linestyle': '--',
    'grid.alpha': 0.7
})

colors_rgb = [
    (0/255, 0/255, 128/255),
    (196/255, 18/255, 52/255),
    (102/255, 0/255, 102/255),
    (0/255, 0/255, 0/255),
]

line_styles = ['-', '-', '-','-', '-', '-']
markers = ['o', 'o', 'o','o', 'o', 'o']


# ====================================================
# HELPER FUNCTIONS
# ====================================================

def read_data(model_name, limit=None):
    """Reads CSV and optionally clips displacement."""
    df = pd.read_csv(f'../{model_name}/force_displacement.csv')
    if limit:
        df = df[df['Displacement'] <= limit]
    return df


def plot_single_curve(ax, x, y, i, label, marker='o', linestyle='-', color=None):
    """Unified plot function for all curves."""
    if color is None:
        color = colors_rgb[i % len(colors_rgb)]
    ax.plot(
        x, y,
        color=color,
        linestyle=linestyle,
        marker=marker,
        markersize=4,
        markevery=1,
        label=label,
        zorder=10 - i
    )


def plot_3d_curve(ax, x, y, z, i, label, marker='o', linestyle='-', color=None):
    """Unified 3D curve plotting."""
    if color is None:
        color = colors_rgb[i % len(colors_rgb)]
    ax.plot(
        x, y, z,
        color=color,
        linestyle=linestyle,
        marker=marker,
        markersize=4,
        markevery=1,
        label=label,
    )

# ====================================================
# PLOT 1: FORCE – DISPLACEMENT
# ====================================================

fig, ax = plt.subplots(figsize=(8, 6))

for i, model in enumerate(model_names):
    df = read_data(model, limit=10)
    plot_single_curve(ax,
                      df['Displacement'],
                      df['Force'],
                      i,
                      model,
                      marker=markers[i],
                      linestyle=line_styles[i])

ax.set_xlabel("Displacement (mm)")
ax.set_ylabel("Force (N)")
ax.legend(frameon=False, loc='upper left')
plt.tight_layout()
plt.savefig(f"../{plot_name}_force_disp.png", dpi=600)
plt.show()



# ====================================================
# PLOT 2: COMBINED FORCE + CRACK LENGTH
# ====================================================
fig, ax1 = plt.subplots(figsize=(8, 6))
ax2 = ax1.twinx()

for i, model in enumerate(model_names):
    df = read_data(model, limit=10)

    # Force
    plot_single_curve(
        ax1,
        df['Displacement'],
        df['Force'],
        i,
        label='Force',
        marker=markers[i],
        linestyle=line_styles[i],
        color=colors_rgb[0]
    )

    # Crack length
    ax2.plot(
        df['Displacement'],
        df['crack length'],
        color=colors_rgb[1],
        linestyle='--',
        marker='s',
        markersize=4,
        markevery=1,
        linewidth=1.5,
        label='Crack length'
    )

# Axis labels
ax1.set_xlabel("Displacement (mm)")
ax1.set_ylabel("Force (N)", color=colors_rgb[0])
ax1.tick_params(axis='y', labelcolor=colors_rgb[0])

ax2.set_ylabel("Crack length (mm)", color=colors_rgb[1])
ax2.tick_params(axis='y', labelcolor=colors_rgb[1])

# Combined legend
h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, frameon=False, loc='upper left')

plt.tight_layout()
plt.savefig(f"../{plot_name}_force_crack_combined.png", dpi=600)
plt.show()



# ====================================================
# PLOT 3: CRACK LENGTH – RELEASED ENERGY
# ====================================================
fig, ax = plt.subplots(figsize=(8, 6))

for i, model in enumerate(model_names):
    df = read_data(model)

    plot_single_curve(
        ax,
        df['crack length'],
        df['released energy'],
        i,
        label='Released energy',   # <-- FIXED LABEL
        marker='^',
        linestyle='-',
        color=colors_rgb[i]
    )

# Interface marker
ax.axvline(
    x=6.7,
    linestyle='--',
    linewidth=1.5,
    label='Interface'            # <-- CORRECT LABEL
)

# Manual axis limits
ax.set_xlim(0, 15)
ax.set_ylim(0, 2)

ax.set_xlabel("Crack length (mm)")
ax.set_ylabel("Released energy (J)")
ax.legend(frameon=False, loc='upper left')

plt.tight_layout()
plt.savefig(f"../{plot_name}_crack_vs_energy.png", dpi=600)
plt.show()


