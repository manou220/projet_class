import os
from matplotlib import pyplot as plt
from io import BytesIO

def save_plot(fig, name, app):
    plots_dir = app.config.get('PLOTS_DIR', os.path.join(app.static_folder, 'plots'))
    os.makedirs(plots_dir, exist_ok=True)
    path = os.path.join(plots_dir, name)
    fig.savefig(path)
    plt.close(fig)
    return path
