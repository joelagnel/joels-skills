# Python Diagram Generation

For complex visualizations requiring programmatic generation.

## Library Selection

| Output Format | Library | When to Use |
|---------------|---------|-------------|
| **HTML/Web** | **Bokeh** | Interactive charts, dashboards, web reports |
| **Geographic** | **Folium** | Real maps with boundaries (not grids) |
| Static PNG/SVG | Matplotlib | Print, plain-text docs, embedded images |
| Graph structures | Graphviz | Dependency trees, call graphs |

**Rule**: Prefer Bokeh for HTML output; use Matplotlib only for static images.

---

## Bokeh - Interactive Web Visualizations (Preferred for HTML)

Bokeh creates interactive, browser-native visualizations. Better than Matplotlib PNG images in HTML reports.

### Why Bokeh Over Matplotlib for HTML?

- Native HTML output renders beautifully in browsers
- Interactive (pan, zoom, hover tooltips)
- Handles large datasets efficiently
- No image quality loss at different zoom levels

### Bokeh Bar Chart (Interactive)

```python
#!/usr/bin/env python3
"""Generate interactive bar chart with hover tooltips."""
from bokeh.plotting import figure, save, output_file
from bokeh.models import HoverTool

output_file("/tmp/latency_comparison.html")

categories = ['Baseline', 'Optimization 1', 'Optimization 2']
latencies = [150, 95, 42]
colors = ['#ff6b6b', '#feca57', '#48dbfb']

p = figure(x_range=categories, height=400, width=600,
           title="Request Latency Comparison",
           toolbar_location="above")

p.vbar(x=categories, top=latencies, width=0.8, color=colors)

# Add hover tooltip
p.add_tools(HoverTool(tooltips=[("Latency", "@top us")]))

p.yaxis.axis_label = "Latency (us)"
p.xgrid.grid_line_color = None

save(p)
print("Saved to /tmp/latency_comparison.html")
```

### Bokeh Line Chart with Hover

```python
#!/usr/bin/env python3
"""Generate interactive line chart with hover details."""
from bokeh.plotting import figure, save, output_file
from bokeh.models import HoverTool, ColumnDataSource
import numpy as np

output_file("/tmp/timeseries.html")

# Sample time series data
np.random.seed(42)
x = np.arange(0, 100)
y = 50 + 20 * np.sin(x / 10) + np.random.normal(0, 5, 100)

source = ColumnDataSource(data=dict(x=x, y=y))

p = figure(height=400, width=800, title="Latency Over Time",
           x_axis_label="Time (s)", y_axis_label="Latency (us)")

p.line('x', 'y', source=source, line_width=2, color='steelblue')
p.circle('x', 'y', source=source, size=4, color='steelblue', alpha=0.5)

p.add_tools(HoverTool(tooltips=[("Time", "@x s"), ("Latency", "@y{0.1} us")]))

save(p)
print("Saved to /tmp/timeseries.html")
```

### Bokeh Histogram

```python
#!/usr/bin/env python3
"""Generate interactive histogram."""
from bokeh.plotting import figure, save, output_file
import numpy as np

output_file("/tmp/histogram.html")

np.random.seed(42)
latencies = np.concatenate([
    np.random.normal(50, 10, 800),
    np.random.normal(150, 20, 150),
    np.random.normal(500, 50, 50),
])

hist, edges = np.histogram(latencies, bins=50)

p = figure(height=400, width=700, title="Request Latency Distribution",
           x_axis_label="Latency (us)", y_axis_label="Frequency")

p.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:],
       fill_color="steelblue", line_color="black", alpha=0.7)

# Add median line
median = np.median(latencies)
p.line([median, median], [0, max(hist)], line_color="red",
       line_dash="dashed", line_width=2, legend_label=f"Median: {median:.1f}us")

p.legend.location = "top_right"
save(p)
print("Saved to /tmp/histogram.html")
```

### Bokeh Heat Map

```python
#!/usr/bin/env python3
"""Generate interactive heat map."""
from bokeh.plotting import figure, save, output_file
from bokeh.models import LinearColorMapper, ColorBar, HoverTool
from bokeh.palettes import YlOrRd9
import numpy as np

output_file("/tmp/heatmap.html")

np.random.seed(42)
n_cpus = 8

# Simulate inter-CPU wake latencies
cpus = [f'CPU{i}' for i in range(n_cpus)]
data = {'source': [], 'target': [], 'latency': []}

for i in range(n_cpus):
    for j in range(n_cpus):
        data['source'].append(cpus[i])
        data['target'].append(cpus[j])
        if i == j:
            data['latency'].append(0)
        elif i // 4 == j // 4:  # Same NUMA node
            data['latency'].append(np.random.uniform(5, 15))
        else:  # Cross-NUMA
            data['latency'].append(np.random.uniform(40, 80))

mapper = LinearColorMapper(palette=list(reversed(YlOrRd9)), low=0, high=80)

p = figure(height=450, width=500, title="Inter-CPU Wake Latency",
           x_range=cpus, y_range=list(reversed(cpus)),
           x_axis_label="Target CPU", y_axis_label="Source CPU",
           toolbar_location="above")

p.rect(x='target', y='source', width=1, height=1, source=data,
       fill_color={'field': 'latency', 'transform': mapper},
       line_color=None)

color_bar = ColorBar(color_mapper=mapper, label_standoff=12, title="Latency (us)")
p.add_layout(color_bar, 'right')

p.add_tools(HoverTool(tooltips=[
    ("Source", "@source"), ("Target", "@target"), ("Latency", "@latency{0.1} us")
]))

save(p)
print("Saved to /tmp/heatmap.html")
```

---

## Folium - Geographic Maps

For real geographic visualizations. **Never use a square grid to represent maps.**

### US States Map

```python
#!/usr/bin/env python3
"""Generate interactive US map with state boundaries."""
import folium

# Create map centered on continental US
m = folium.Map(location=[39.8283, -98.5795], zoom_start=4)

# Add state boundaries from GeoJSON
folium.GeoJson(
    "https://raw.githubusercontent.com/python-visualization/folium/main/examples/data/us-states.json",
    name="US States",
    style_function=lambda x: {
        'fillColor': '#3186cc',
        'color': 'black',
        'weight': 1,
        'fillOpacity': 0.3
    }
).add_to(m)

folium.LayerControl().add_to(m)
m.save('/tmp/us_map.html')
print("Saved to /tmp/us_map.html")
```

### Choropleth Map (States Colored by Data)

```python
#!/usr/bin/env python3
"""Generate choropleth map with data-driven coloring."""
import folium
import pandas as pd

# Sample state data
state_data = pd.DataFrame({
    'State': ['California', 'Texas', 'Florida', 'New York', 'Pennsylvania'],
    'Value': [85, 72, 68, 91, 55]
})

m = folium.Map(location=[39.8283, -98.5795], zoom_start=4)

folium.Choropleth(
    geo_data="https://raw.githubusercontent.com/python-visualization/folium/main/examples/data/us-states.json",
    data=state_data,
    columns=['State', 'Value'],
    key_on='feature.properties.name',
    fill_color='YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Value by State'
).add_to(m)

m.save('/tmp/choropleth.html')
print("Saved to /tmp/choropleth.html")
```

### World Map with Markers

```python
#!/usr/bin/env python3
"""Generate world map with location markers."""
import folium

m = folium.Map(location=[20, 0], zoom_start=2)

# Add markers for data centers
locations = [
    (37.7749, -122.4194, "San Francisco"),
    (51.5074, -0.1278, "London"),
    (35.6762, 139.6503, "Tokyo"),
    (1.3521, 103.8198, "Singapore"),
]

for lat, lon, name in locations:
    folium.Marker(
        location=[lat, lon],
        popup=name,
        icon=folium.Icon(color='blue', icon='server', prefix='fa')
    ).add_to(m)

m.save('/tmp/world_map.html')
print("Saved to /tmp/world_map.html")
```

---

## Graphviz (DOT Language)

```python
#!/usr/bin/env python3
"""Generate dependency graph using graphviz."""
from graphviz import Digraph

dot = Digraph(comment='Module Dependencies')
dot.attr(rankdir='LR')  # Left to right

# Add nodes
dot.node('A', 'core_module', shape='box')
dot.node('B', 'helper_lib', shape='ellipse')
dot.node('C', 'user_api', shape='box')

# Add edges
dot.edge('C', 'A', label='uses')
dot.edge('A', 'B', label='depends')

# Render
dot.render('/tmp/dependencies', format='svg', cleanup=True)
print("Saved to /tmp/dependencies.svg")
```

---

## Matplotlib - Static Visualizations (PNG/SVG Only)

Use Matplotlib **only** when you need static PNG/SVG images (print, plain-text docs).
For HTML/web output, use Bokeh instead.

### Matplotlib Bar Chart

```python
#!/usr/bin/env python3
"""Generate performance chart (static PNG)."""
import matplotlib.pyplot as plt

# Data
categories = ['Baseline', 'Optimization 1', 'Optimization 2']
latencies = [150, 95, 42]

# Create bar chart
plt.figure(figsize=(10, 6))
bars = plt.bar(categories, latencies, color=['#ff6b6b', '#feca57', '#48dbfb'])
plt.ylabel('Latency (us)')
plt.title('Request Latency Comparison')

# Add value labels
for bar, val in zip(bars, latencies):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
             f'{val}us', ha='center', va='bottom')

plt.tight_layout()
plt.savefig('/tmp/latency_comparison.png', dpi=150)
print("Saved to /tmp/latency_comparison.png")
```

## NetworkX for Graph Analysis

```python
#!/usr/bin/env python3
"""Generate call graph visualization."""
import networkx as nx
import matplotlib.pyplot as plt

G = nx.DiGraph()

# Add function call relationships
calls = [
    ('main', 'init'),
    ('main', 'process'),
    ('process', 'validate'),
    ('process', 'transform'),
    ('transform', 'helper'),
]
G.add_edges_from(calls)

# Draw
plt.figure(figsize=(12, 8))
pos = nx.spring_layout(G, k=2)
nx.draw(G, pos, with_labels=True, node_color='lightblue',
        node_size=2000, font_size=10, font_weight='bold',
        arrows=True, arrowsize=20, edge_color='gray')

plt.title('Function Call Graph')
plt.savefig('/tmp/call_graph.png', dpi=150)
print("Saved to /tmp/call_graph.png")
```

## Histogram - Distribution Analysis

Best for: Latency distributions, frequency analysis, performance profiling.

```python
#!/usr/bin/env python3
"""Generate latency distribution histogram."""
import matplotlib.pyplot as plt
import numpy as np

# Sample latency data (microseconds)
np.random.seed(42)
latencies = np.concatenate([
    np.random.normal(50, 10, 800),   # Normal case
    np.random.normal(150, 20, 150),  # Slow path
    np.random.normal(500, 50, 50),   # Outliers
])

plt.figure(figsize=(12, 6))
plt.hist(latencies, bins=50, color='steelblue', edgecolor='black', alpha=0.7)
plt.axvline(np.median(latencies), color='red', linestyle='--', label=f'Median: {np.median(latencies):.1f}us')
plt.axvline(np.percentile(latencies, 99), color='orange', linestyle='--', label=f'P99: {np.percentile(latencies, 99):.1f}us')

plt.xlabel('Latency (us)')
plt.ylabel('Frequency')
plt.title('Request Latency Distribution')
plt.legend()
plt.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('/tmp/latency_histogram.png', dpi=150)
print("Saved to /tmp/latency_histogram.png")
```

## Box Plot - Statistical Comparison

Best for: Comparing distributions across categories, identifying outliers, showing quartiles.

```python
#!/usr/bin/env python3
"""Generate box plot for multi-configuration comparison."""
import matplotlib.pyplot as plt
import numpy as np

np.random.seed(42)
data = {
    'Baseline': np.random.normal(100, 30, 200),
    'Opt-A': np.random.normal(75, 20, 200),
    'Opt-B': np.random.normal(50, 15, 200),
    'Opt-A+B': np.random.normal(35, 10, 200),
}

fig, ax = plt.subplots(figsize=(10, 6))
bp = ax.boxplot(data.values(), labels=data.keys(), patch_artist=True)

# Color the boxes
colors = ['#ff6b6b', '#feca57', '#48dbfb', '#1dd1a1']
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)

ax.set_ylabel('Latency (us)')
ax.set_title('Latency Comparison Across Configurations')
ax.grid(axis='y', alpha=0.3)

# Add mean markers
means = [np.mean(v) for v in data.values()]
ax.scatter(range(1, len(means)+1), means, marker='D', color='black', s=50, zorder=3, label='Mean')
ax.legend()

plt.tight_layout()
plt.savefig('/tmp/latency_boxplot.png', dpi=150)
print("Saved to /tmp/latency_boxplot.png")
```

## Heat Map - Correlation and Intensity

Best for: CPU utilization matrices, correlation analysis, cache behavior, memory access patterns.

```python
#!/usr/bin/env python3
"""Generate heat map for CPU-to-CPU wake latency matrix."""
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

np.random.seed(42)
n_cpus = 8

# Simulate inter-CPU wake latencies (same NUMA node = faster)
latency_matrix = np.zeros((n_cpus, n_cpus))
for i in range(n_cpus):
    for j in range(n_cpus):
        if i == j:
            latency_matrix[i, j] = 0
        elif i // 4 == j // 4:  # Same NUMA node
            latency_matrix[i, j] = np.random.uniform(5, 15)
        else:  # Cross-NUMA
            latency_matrix[i, j] = np.random.uniform(40, 80)

plt.figure(figsize=(10, 8))
sns.heatmap(latency_matrix, annot=True, fmt='.0f', cmap='YlOrRd',
            xticklabels=[f'CPU{i}' for i in range(n_cpus)],
            yticklabels=[f'CPU{i}' for i in range(n_cpus)],
            cbar_kws={'label': 'Wake Latency (us)'})

plt.title('Inter-CPU Wake Latency Heat Map')
plt.xlabel('Target CPU')
plt.ylabel('Source CPU')

plt.tight_layout()
plt.savefig('/tmp/cpu_heatmap.png', dpi=150)
print("Saved to /tmp/cpu_heatmap.png")
```

## 3D Surface Plot - Multi-Variable Analysis

Best for: Showing relationships between three variables, performance landscapes.

```python
#!/usr/bin/env python3
"""Generate 3D surface plot for parameter sweep analysis."""
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

# Create parameter grid
batch_sizes = np.arange(1, 32, 2)
queue_depths = np.arange(1, 16, 1)
X, Y = np.meshgrid(batch_sizes, queue_depths)

# Simulate throughput as function of batch size and queue depth
Z = 1000 * (1 - np.exp(-X/10)) * (1 - np.exp(-Y/5)) + np.random.normal(0, 20, X.shape)

fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

surf = ax.plot_surface(X, Y, Z, cmap='viridis', edgecolor='none', alpha=0.8)

ax.set_xlabel('Batch Size')
ax.set_ylabel('Queue Depth')
ax.set_zlabel('Throughput (ops/sec)')
ax.set_title('Throughput vs. Batch Size and Queue Depth')

fig.colorbar(surf, shrink=0.5, aspect=10, label='Throughput')

plt.tight_layout()
plt.savefig('/tmp/3d_surface.png', dpi=150)
print("Saved to /tmp/3d_surface.png")
```

## Scatter Plot with Regression

Best for: Correlation analysis, trend identification, outlier detection.

```python
#!/usr/bin/env python3
"""Generate scatter plot with regression line."""
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

np.random.seed(42)

# Simulate concurrency vs. request latency
concurrency = np.random.uniform(10, 1000, 100)
latency = 20 + 0.05 * concurrency + np.random.normal(0, 10, 100)

# Linear regression
slope, intercept, r_value, p_value, std_err = stats.linregress(concurrency, latency)

plt.figure(figsize=(10, 6))
plt.scatter(concurrency, latency, alpha=0.6, c='steelblue', edgecolors='black')

# Regression line
x_line = np.linspace(0, 1000, 100)
plt.plot(x_line, intercept + slope * x_line, 'r-', linewidth=2,
         label=f'y = {intercept:.1f} + {slope:.3f}x (R² = {r_value**2:.3f})')

plt.xlabel('Concurrency')
plt.ylabel('Request Latency (us)')
plt.title('Concurrency vs. Request Latency')
plt.legend()
plt.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('/tmp/scatter_regression.png', dpi=150)
print("Saved to /tmp/scatter_regression.png")
```

## Violin Plot - Distribution Shape Comparison

Best for: Comparing distribution shapes across categories, showing density.

```python
#!/usr/bin/env python3
"""Generate violin plot for distribution comparison."""
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

np.random.seed(42)
data = {
    'Service A': np.concatenate([np.random.normal(50, 10, 400), np.random.normal(100, 5, 100)]),
    'Service B': np.random.normal(40, 15, 500),
    'Service C': np.random.exponential(30, 500),
}

fig, ax = plt.subplots(figsize=(10, 6))
parts = ax.violinplot(data.values(), showmeans=True, showmedians=True)

# Color the violins
colors = ['#ff6b6b', '#48dbfb', '#1dd1a1']
for pc, color in zip(parts['bodies'], colors):
    pc.set_facecolor(color)
    pc.set_alpha(0.7)

ax.set_xticks(range(1, len(data)+1))
ax.set_xticklabels(data.keys())
ax.set_ylabel('Latency (us)')
ax.set_title('Service Latency Distributions')
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('/tmp/violin_plot.png', dpi=150)
print("Saved to /tmp/violin_plot.png")
```

## Stacked Area Chart - Composition Over Time

Best for: Showing how components contribute to a total over time.

```python
#!/usr/bin/env python3
"""Generate stacked area chart for CPU time breakdown."""
import matplotlib.pyplot as plt
import numpy as np

np.random.seed(42)
time_points = np.arange(0, 100, 1)

# Simulate CPU time components
user = 30 + 10 * np.sin(time_points / 10) + np.random.normal(0, 2, len(time_points))
system = 15 + 5 * np.sin(time_points / 15 + 1) + np.random.normal(0, 1, len(time_points))
softirq = 5 + 3 * np.sin(time_points / 8 + 2) + np.random.normal(0, 0.5, len(time_points))
idle = 100 - user - system - softirq

# Ensure non-negative
user = np.maximum(user, 0)
system = np.maximum(system, 0)
softirq = np.maximum(softirq, 0)
idle = np.maximum(idle, 0)

plt.figure(figsize=(12, 6))
plt.stackplot(time_points, user, system, softirq, idle,
              labels=['User', 'System', 'Softirq', 'Idle'],
              colors=['#ff6b6b', '#feca57', '#48dbfb', '#a0a0a0'],
              alpha=0.8)

plt.xlabel('Time (seconds)')
plt.ylabel('CPU Utilization (%)')
plt.title('CPU Time Breakdown Over Time')
plt.legend(loc='upper right')
plt.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('/tmp/stacked_area.png', dpi=150)
print("Saved to /tmp/stacked_area.png")
```

## Flame Graph Generation

Best for: CPU profiling, understanding where time is spent, finding hotspots.

```bash
# Record with perf
perf record -F 99 -g -- <command>

# Generate flame graph
perf script | ~/FlameGraph/stackcollapse-perf.pl | ~/FlameGraph/flamegraph.pl > /tmp/flamegraph.svg
```

See the **perf skill** for detailed flame graph workflows.

## Installation Notes

```bash
# System packages
sudo apt install graphviz

# Interactive web visualizations (PREFERRED for HTML)
pip install bokeh

# Geographic maps
pip install folium geopandas pandas

# Static visualizations (when HTML not needed)
pip install matplotlib seaborn

# Graph structures and analysis
pip install graphviz networkx scipy numpy
```

## Best Practices

### Error Handling
When using Python scripts in production, wrap in try/except and validate inputs for error handling.

### Visualization Principles

1. **Less is more** - Fewer relevant graphs > many redundant graphs
2. **One chart, one insight** - Each visualization answers ONE question
3. **No redundancy** - Don't show same data in multiple chart types
4. **Right tool for output** - Bokeh for HTML, Matplotlib for static only
5. **Real maps** - Use Folium for geography, never grid approximations
