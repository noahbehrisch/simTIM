import matplotlib.pyplot as plt
import numpy as np

def plot_violin(data, title="Simulation Results", return_figure=False):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.violinplot(data, showmeans=True, showextrema=True, showmedians=True)
    ax.set_title(title)
    ax.set_xlabel("x")
    ax.set_ylabel("y")

    if return_figure:
        return fig
    else:
        plt.show()
        plt.close(fig)
