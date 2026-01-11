import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button, Slider
import simpy
from typing import Dict, List, Any
import numpy as np

class Dashboard:
    def __init__(self, 
                 engine, 
                 queues_groups: Dict[str, List[Any]], 
                 duration: float, 
                 interval: int = 50):
        """
        Args:
            engine: SimulationEngine instance
            queues_groups: Dict mapping group name to list of queue objects
                          {'Processing': [q1, q2], 'Output': [q3]}
            duration: Total simulation duration
            interval: Animation update interval in ms
        """
        self.engine = engine
        self.queues_groups = queues_groups
        self.duration = duration
        self.interval = interval
        self.is_playing = False
        self.speed = 1.0
        self.current_time = 0.0
        
        # Data History
        # {group_name: {queue_idx: {'time': [], 'length': []}}}
        self.history = {}
        for group_name, queues in self.queues_groups.items():
            self.history[group_name] = {}
            for i, _ in enumerate(queues):
                self.history[group_name][i] = {'time': [], 'length': []}
        
        # Setup Plot
        self.num_groups = len(queues_groups)
        self.fig, self.axes = plt.subplots(self.num_groups, 1, figsize=(10, 3.5 * self.num_groups))
        if self.num_groups == 1:
            self.axes = [self.axes]
        
        plt.subplots_adjust(bottom=0.2, hspace=0.4)
        
        self.lines = {} # Stores Line2D objects
        self.loss_texts = {} # Stores Text objects for loss counters
        
        # Initialize plots
        colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
        
        for i, (group_name, queues) in enumerate(self.queues_groups.items()):
            ax = self.axes[i]
            self.lines[group_name] = []
            
            for j, queue in enumerate(queues):
                queue_id = getattr(queue, 'queue_id', getattr(queue, 'server_id', f'Queue {j}'))
                line, = ax.plot([], [], label=queue_id, color=colors[j % len(colors)], linewidth=2)
                self.lines[group_name].append(line)
            
            ax.set_title(group_name)
            ax.set_xlim(0, max(100, duration * 0.1)) # Initial zoom
            ax.set_ylim(0, 10)
            ax.set_xlabel('Time')
            ax.set_ylabel('Queue Length')
            ax.legend(loc='upper right')
            ax.grid(True, alpha=0.3)
            
            # Loss Info (Top Left of subplot)
            self.loss_texts[group_name] = ax.text(0.02, 0.95, '', transform=ax.transAxes, 
                                                 verticalalignment='top', 
                                                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        # Time display
        self.time_text = self.fig.text(0.5, 0.95, f'Time: 0.00 / {self.duration}', 
                                       ha='center', fontsize=12, fontweight='bold')

        # Controls
        ax_play = plt.axes([0.1, 0.05, 0.1, 0.075])
        self.btn_play = Button(ax_play, 'Play')
        self.btn_play.on_clicked(self.toggle_play)
        
        ax_speed = plt.axes([0.3, 0.05, 0.5, 0.03])
        self.slider_speed = Slider(ax_speed, 'Speed', 0.1, 50.0, valinit=1.0)
        self.slider_speed.on_changed(self.update_speed)
        
        # Animation
        self.anim = FuncAnimation(self.fig, self.update, frames=None, 
                                  interval=self.interval, blit=False, cache_frame_data=False)

    def toggle_play(self, event):
        self.is_playing = not self.is_playing
        self.btn_play.label.set_text('Pause' if self.is_playing else 'Play')
        self.fig.canvas.draw_idle()

    def update_speed(self, val):
        self.speed = val

    def _get_queue_length(self, queue):
        if hasattr(queue, 'queue_length'):
            return queue.queue_length
        elif hasattr(queue, 'resource'):
            return len(queue.resource.queue)
        elif hasattr(queue, '__len__'):
            return len(queue)
        return 0

    def _get_loss_info(self, queue):
        """Get dropped items count if available"""
        if hasattr(queue, 'rejections_queue_full'):
            return queue.rejections_queue_full
        return None

    def update(self, frame):
        if not self.is_playing:
            return
        
        if self.engine.env.now >= self.duration:
            self.is_playing = False
            self.btn_play.label.set_text('Done')
            return

        # Advance simulation
        step = self.speed * (self.interval / 1000.0)
        step = max(step, 0.01)
        
        target_time = self.engine.env.now + step
        if target_time > self.duration:
            target_time = self.duration
            
        self.engine.env.run(until=target_time)
        self.current_time = self.engine.env.now
        
        # Update UI
        self.time_text.set_text(f'Time: {self.current_time:.2f} / {self.duration}')
        
        for group_name, queues in self.queues_groups.items():
            ax = None
            for i, name in enumerate(self.queues_groups.keys()):
                if name == group_name:
                    ax = self.axes[i]
                    break
            
            max_val = 0
            loss_strings = []
            
            for j, queue in enumerate(queues):
                # Update Data
                length = self._get_queue_length(queue)
                
                # Append to history
                self.history[group_name][j]['time'].append(self.current_time)
                self.history[group_name][j]['length'].append(length)
                
                # Update Plot Data
                times = self.history[group_name][j]['time']
                lengths = self.history[group_name][j]['length']
                
                self.lines[group_name][j].set_data(times, lengths)
                
                if length > max_val:
                    max_val = length
                
                # Loss Info
                loss = self._get_loss_info(queue)
                if loss is not None and loss > 0:
                    q_id = getattr(queue, 'queue_id', f'Q{j}')
                    loss_strings.append(f"{q_id} Lost: {loss}")

            # Update View Limits
            # X Axis: Sliding window or expand? Let's expand but keep min window
            ax.set_xlim(0, max(self.current_time * 1.1, 10))
            
            # Y Axis: Dynamic with some headroom
            current_ylim = ax.get_ylim()[1]
            if max_val >= current_ylim * 0.9:
                ax.set_ylim(0, max_val * 1.2)
            
            # Update Loss Text
            if loss_strings:
                self.loss_texts[group_name].set_text("\n".join(loss_strings))
                self.loss_texts[group_name].set_color('red')
            else:
                self.loss_texts[group_name].set_text("No Loss")
                self.loss_texts[group_name].set_color('green')

    def show(self):
        plt.show()
