import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.animation as animation
import matplotlib.lines as mlines
import random

# Constants

STEP_SIZE = 0.5
TURN_RATIO = 0.25
ANIMATION_INTERVAL = 50
file_path = 'particle_data.xlsx'

# we'll work with some generated data in place of actual data 
# packets parameter can be set here, or the code can be modified to prompt the user for it 

def generate_data(num_cores, num_caches, total_packets):

    data = {
        'time': list(range(total_packets)),
        'source': [random.randint(0, num_cores - 1) for _ in range(total_packets)],
        'destination': [random.randint(0, num_caches - 1) for _ in range(total_packets)]
    }
    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False)


# here, we could add the ability to decide the number of packets 
# for now only prompt for cores and caches 

def get_user_input():
    num_cores = int(input("Enter number of CPU cores: "))
    num_caches = int(input("Enter number of caches: "))
    return num_cores, num_caches


def load_data(filename):
    df = pd.read_excel(filename)
    return df.sort_values(by='time').reset_index(drop=True)


# we'll keep locations in a dictionary, and draw them using add_patch from matplotlib.axes 
# one fix is the idx + 1, to go from 0 based indexing to 1 
# one problem is that the naming of the boxes is not clear when it's a large number, will search for fixes here

def create_boxes(ax, num_cores, num_caches):
    cpu_positions, cache_positions = {}, {}

    for i in range(num_cores):
        x = i * 2
        draw_box(ax, x, 8, 'CPU', i, 'lightblue', cpu_positions)

    for i in range(num_caches):
        x = i * 2
        draw_box(ax, x, 0, 'Cache', i, 'lightgreen', cache_positions)

    return cpu_positions, cache_positions


def draw_box(ax, x, y, label, idx, color, pos_dict):
    ax.add_patch(patches.Rectangle((x, y), 1.5, 1, edgecolor='black', facecolor=color))
    ax.text(x + 0.75, y + 0.5, f"{label} {idx + 1}", ha='center', va='center')
    pos_dict[idx] = (x + 0.75, y + (1 if label == 'Cache' else 0))


# animate by initializing the plot, setting limits, creating cpu and cache boxes
# also add and update the packets on the plot
# use Func animation on repeat for an infinite loop without a large excel file

def visualize(df, cpu_positions, cache_positions):
    fig, ax = plt.subplots()
    ax.set_xlim(-1, max(len(cpu_positions), len(cache_positions)) * 2)
    ax.set_ylim(-1, 10)
    ax.axis('off')

    create_boxes(ax, len(cpu_positions), len(cache_positions))

    packets, dots, paths = [], [], []

    def update(frame):
        spawn_packets(frame, df, cpu_positions, cache_positions, packets, dots, paths, ax)
        move_packets(packets, dots, paths)

    total_frames = df['time'].max() + 50
    ani = animation.FuncAnimation(fig, update, frames=range(total_frames),
                                   interval=ANIMATION_INTERVAL, repeat=True)
    plt.show()


# generate packets on the basis of frame

def spawn_packets(frame, df, cpu_positions, cache_positions, packets, dots, paths, ax):
    for _, row in df[df['time'] == frame].iterrows():
        src = cpu_positions[row['source']]
        dst = cache_positions[row['destination']]
        turn_y = src[1] + TURN_RATIO * (dst[1] - src[1])
        packet = {'pos': list(src), 'turn': (src[0], turn_y), 'end': dst, 'phase': 0}
        packets.append(packet)

        path = mlines.Line2D([src[0]], [src[1]], color='red', linewidth=1)
        ax.add_line(path)
        paths.append(path)
        dot = ax.plot(src[0], src[1], 'ro')[0]
        dots.append(dot)

def move_packets(packets, dots, paths):
    def move_coord(current, target):
        if abs(current - target) <= STEP_SIZE:
            return target, True
        return current + STEP_SIZE * (1 if target > current else -1), False

    finished = []
    for i, pkt in enumerate(packets):
        x, y = pkt['pos']
        tx, ty = pkt['turn']
        dx, dy = pkt['end']

        if pkt['phase'] == 0:  # move vertically to turn_y
            y, done = move_coord(y, ty)
            pkt['pos'][1] = y
            if done:
                pkt['phase'] = 1

        elif pkt['phase'] == 1:  # move horizontally to dest_x
            x, done = move_coord(x, dx)
            pkt['pos'][0] = x
            if done:
                pkt['phase'] = 2

        elif pkt['phase'] == 2:  # move vertically to dest_y
            y, done = move_coord(y, dy)
            pkt['pos'][1] = y
            if done:
                pkt['finished'] = True

        dots[i].set_data([pkt['pos'][0]], [pkt['pos'][1]])
        path = paths[i]
        path.set_data(list(path.get_xdata()) + [pkt['pos'][0]], list(path.get_ydata()) + [pkt['pos'][1]])

        if pkt.get('finished'):
            finished.append(i)

    for i in reversed(finished):
        dots[i].remove()
        paths[i].remove()
        del packets[i], dots[i], paths[i]



def main():
    num_cores, num_caches = get_user_input()
    generate_data(num_cores, num_caches, 40)
    df = load_data(file_path)

    fig, ax = plt.subplots()
    cpu_positions, cache_positions = create_boxes(ax, num_cores, num_caches)
    plt.close(fig)

    visualize(df, cpu_positions, cache_positions)


if __name__ == "__main__":
    main()
