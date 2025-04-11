import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Tuple

import simulator
import generator

gen = generator.Generator(seed=37)
sim = simulator.Simulator(gen, channel_reserved_for_handover=1, logging=True)

sim.run(1000)

print(sim.log)

full_data_df = pd.DataFrame(None, columns=["time", "all_car_pos"])

# all car pos is an array of all cars' positions
# (car_id, car_station, car_pos, end_time)

current_cars:List[simulator.Car] = []
terminated_cars:List[simulator.Car] = []  # Keep track of terminated cars separately

time_list = []
event_list = []

# Dictionary to store last known position of each car
last_known_positions = {}  # {car_id: (x_pos, y_pos, station, slot)}

for time, event, car in sim.log:    
    event_list.append((event, car._id))

    if event == simulator.EventType.CALL_INITIATION:
        current_cars.append(car)
    elif event == simulator.EventType.CALL_HANDOVER:
        pass # There is no updates needed
    elif event == simulator.EventType.CALL_TERMINATION:
        terminated_cars.append(car)  # Add to terminated cars list when a call terminates

    time_list.append(time)

# Create DataFrame from lists
full_data_df = pd.DataFrame(
    {
        "time": time_list,
        "events": event_list
    }
)


# Parameters
station_count = 20
capacity_per_station = 10
frame_duration = 500  # Set frame duration to 500ms for playback without tweening

# Initialize Plotly figure
fig = go.Figure(
    layout=go.Layout(
        title="Station Usage Over Time",
        xaxis=dict(title="Station", range=[0, 40], dtick=1),
        yaxis=dict(title="Capacity Slot", range=[-0.5, capacity_per_station - 0.5], dtick=1),
        updatemenus=[{
            "type": "buttons",
            "buttons": [
                {
                    "label": "Play",
                    "method": "animate",
                    "args": [None, {"frame": {"duration": frame_duration, "redraw": True}, "mode": "immediate", "fromcurrent": True}]
                },
                {
                    "label": "Pause",
                    "method": "animate",
                    "args": [[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}]
                }
            ]
        }]
    )
)

# Add vertical lines for each station
for x in range(2, 40, 2):
    fig.add_shape(
        type="line",
        x0=x,
        y0=-0.5,
        x1=x,
        y1=capacity_per_station - 0.5,
        line=dict(color="gray", width=1, dash="dot")
    )

frames = []
slider_steps = []

# Build frames for each time step
for idx, row in full_data_df.iterrows():
    time = row["time"]
    event = row["events"][0]
    event_car_id = row["events"][1]

    # Track how many cars occupy each station
    station_slots = {s: 0 for s in range(station_count)}
    x_vals = []
    y_vals = []
    texts = []
    hover_texts = []
    colors = []  # Create colors list at the beginning

    # Process active cars
    for car in current_cars:
        # Check if car is still active at this time
        if not car.is_still_active(time):
            # If we have a last known position for this car, use it
            if car._id in last_known_positions:
                x_pos, y_pos, station, slot = last_known_positions[car._id]
                x_vals.append(x_pos)
                y_vals.append(y_pos)
                texts.append(" ")
                hover_texts.append(" ")
                colors.append('rgba(0,0,0,0)')
            else:
                # This should not happen if we track positions correctly
                x_vals.append(0)
                y_vals.append(0)
                texts.append("")
                hover_texts.append("")
                colors.append("lightgray")
        else:
            station = car.get_current_station(time-simulator.EPSILON)
            abs_position = car.get_abs_position(time)

            slot = station_slots[station]
            x_pos = abs_position / 1000.0
            y_pos = slot
            
            # Save the last known position
            last_known_positions[car._id] = (x_pos, y_pos, station, slot)
            
            x_vals.append(x_pos)
            y_vals.append(y_pos)
            texts.append(f"Car {car._id}<br>ET:{car.get_end_time():.1f}")
            hover_texts.append(f"Car {car._id}<br>Station: {station}<br>Position: {x_pos:.2f} km<br>End Time: {car.get_end_time():.1f}")
            
            station_slots[station] += 1

            # Determine car color (highlight car involved in the current event)
            if car._id == event_car_id:
                if event == simulator.EventType.CALL_INITIATION:
                    colors.append("green")
                elif event == simulator.EventType.CALL_HANDOVER:
                    colors.append("orange")
                elif event == simulator.EventType.CALL_TERMINATION:
                    colors.append("red")
                else:
                    colors.append("blue")
            else:
                colors.append("blue")

    frame = go.Frame(
        data=[
            go.Scatter(
                x=x_vals,
                y=y_vals,
                mode="markers+text",
                marker=dict(size=20, color=colors),
                text=texts,
                hovertext=hover_texts,
                textposition="top center"
            )
        ],
        name=f"{idx}"
    )
    frames.append(frame)

    slider_steps.append({
        "method": "animate",
        "args": [[f"{idx}"], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}],
        "label": f"{round(time, 2)}"
    })

# Initial empty scatter
fig.add_trace(go.Scatter(
    x=[],
    y=[],
    mode='markers+text',
    marker=dict(size=20),
    text=[],
    textposition="top center"
))

# Add sliders
sliders = [{
    "steps": slider_steps,
    "transition": {"duration": 150},  # Adjusted for faster playback
    "x": 0.1,
    "y": 0,
    "currentvalue": {"prefix": "Time: "}
}]

fig.frames = frames
fig.update_layout(sliders=sliders)

fig.show()
