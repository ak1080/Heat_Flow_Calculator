"""
Heat Flow Through a Composite Wall

Author: Alex Kalmbach

Description: This Python script calculates the overall R-Value and U-Value for a composite wall assembly. The total
heat flow through the wall is then calculated via Q = U*A*dT.

Modules:
material_r_values: Contains R-Values of typical wall construction materials.

Usage:
Run this script to open the GUI. Enter add wall layers as series or parallel (think insulation between studs) and
view the calculated heat transfer outputs

Version: 1.0 (completed 01/11/2025)
"""

import tkinter as tk
from tkinter import ttk, Canvas, messagebox
# Import the dictionary of materials module
from material_r_values import materials_r_values

def calculate_heat_transfer():
    """Performs the overall heat-transfer calculation based on the layers list."""
    try:
        t_inside = float(entry_t_inside.get())
        t_outside = float(entry_t_outside.get())
        r_inside_film = float(entry_r_inside_film.get())
        r_outside_film = float(entry_r_outside_film.get())
        wall_area = float(entry_wall_area.get())

        # Initialize total resistance with inside & outside film
        total_resistance = r_inside_film + r_outside_film

        # Sum up series & parallel layers
        for layer in layers:
            if layer['type'] == 'series':
                total_resistance += layer['r_value']
            elif layer['type'] == 'parallel':
                # For parallel, compute the reciprocal sum
                parallel_resistance = 0
                for path in layer['paths']:
                    r_val = path['r_value']
                    area_pct = path['area_percent']
                    parallel_resistance += (area_pct / 100) / r_val
                total_resistance += 1 / parallel_resistance

        # Compute heat-transfer quantities
        q_per_ft2 = (t_outside - t_inside) / total_resistance  # BTU/h-ft²
        q_total = q_per_ft2 * wall_area                        # BTU/h
        u_value = 1 / total_resistance

        # Update the results display
        results.set(
            f"Overall R-Value: {total_resistance:.2f} ft²·h·°F/BTU\n"
            f"Overall U-Value: {u_value:.4f} BTU/h·ft²·°F\n"
            f"Heat Flow Rate per ft²: {q_per_ft2:.1f} BTU/h·ft²\n"
            f"Total Heat Transfer: {q_total:.1f} BTU/h"
        )
    except ValueError:
        results.set("Please enter valid numeric values.")


def auto_update(*args):
    """Automatically re-calculate whenever user modifies certain fields."""
    calculate_heat_transfer()


# ------------------
# SERIES LAYER LOGIC
# ------------------

def on_typed_r_value_series(event=None):
    """
    If the user typed a non-empty R-value, disable the combobox for series.
    If typed is empty, enable the combobox (i.e. "deselect" typed).
    """
    text = entry_r_value.get().strip()
    if text == "":
        combo_material.config(state="normal")  # Re-enable dropdown
    else:
        combo_material.config(state="disabled")  # Disable dropdown
        combo_material.set("None")


def on_select_material_series(event=None):
    """
    If user picks a material, clear typed R-value and disable it.
    If user picks "None", re-enable typed R-value (deselect the dropdown).
    """
    sel = combo_material.get().strip()
    if sel == "None":
        # If "None" is selected, re-enable manual entry
        entry_r_value.config(state="normal")
    else:
        # If a material is selected, disable manual entry
        entry_r_value.delete(0, "end")
        entry_r_value.config(state="disabled")


def add_series_layer():
    """
    Adds one series layer based on typed R-value or selected material.
    """
    entry_r_value.config(state="normal")
    combo_material.config(state="normal")

    typed_str = entry_r_value.get().strip()
    selected_mat = combo_material.get().strip()

    if typed_str:
        try:
            val = float(typed_str)
            if val <= 0:
                raise ValueError
            r_value = val
            material = "Custom R-value"
        except ValueError:
            messagebox.showerror("Input Error", "Please enter a positive numeric R-value.")
            return
    else:
        if selected_mat != "None" and selected_mat in materials_r_values:
            r_value = materials_r_values[selected_mat]
            material = selected_mat
        else:
            messagebox.showerror("Input Error", "Please type an R-value or select a material.")
            return

    # Append the series layer to the layers list
    layers.append({'type': 'series', 'r_value': r_value, 'material': material})

    # Reset the fields
    entry_r_value.delete(0, "end")
    entry_r_value.config(state="normal")
    combo_material.set("None")
    combo_material.config(state="normal")

    # Redraw the GUI immediately
    draw_layers()
    calculate_heat_transfer()

# -------------------
# PARALLEL LAYER LOGIC
# -------------------

def add_parallel_layer():
    """
    Wizard approach: user enters number of paths. Then for each path:
    - A Toplevel prompts typed R-value or dropdown (exclusively) + area percentage
    - No negative area, cannot exceed leftover area
    - The last path must exactly match leftover so total = 100%
    """
    try:
        num_paths = int(entry_num_paths.get())
        if num_paths <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Input Error", "Please enter a valid positive integer for # of parallel paths.")
        return

    paths = []
    total_area_used = 0.0

    for i in range(num_paths):
        is_last_path = (i == num_paths - 1)
        r_val, area_val, material = prompt_parallel_path(
            path_index=i + 1,
            total_paths=num_paths,
            area_used_so_far=total_area_used,
            last_path=is_last_path
        )
        paths.append({'r_value': r_val, 'area_percent': area_val, 'material': material})
        total_area_used += area_val

    if abs(total_area_used - 100) > 1e-6:
        messagebox.showerror("Area Error", f"The total area for all parallel paths is {total_area_used:.2f}%. It must sum to exactly 100%. Please re-enter.")
        return

    # Append the parallel layer to the layers list
    layers.append({'type': 'parallel', 'paths': paths})

    # Redraw the GUI immediately
    draw_layers()
    calculate_heat_transfer()

def prompt_parallel_path(path_index, total_paths, area_used_so_far, last_path=False):
    """
    Toplevel wizard for one parallel path:
      - typed R-value or select from combo
      - area% must be positive
      - if not the last path, area% <= leftover
      - if last path, area% == leftover
    Returns (r_value_float, area_float, material_name).
    """
    top = tk.Toplevel(root)
    top.title(f"Parallel Path {path_index} of {total_paths}")
    top.grab_set()  # modal

    frame = ttk.Frame(top, padding=10)
    frame.pack(fill="both", expand=True)

    area_left = 100 - area_used_so_far

    lbl_info = ttk.Label(
        frame,
        text=(f"Path {path_index}/{total_paths}\n"
              f"Area used so far: {area_used_so_far:.2f}%\n"
              f"Area left: {area_left:.2f}%"),
        font=("Arial", 11, "bold")
    )
    lbl_info.grid(row=0, column=0, columnspan=3, pady=5)

    # R-value typed
    ttk.Label(frame, text="Type R-value:").grid(row=1, column=0, sticky="w")
    ent_r = ttk.Entry(frame, width=10)
    ent_r.grid(row=1, column=1, padx=5, pady=5)

    # Combobox for material
    ttk.Label(frame, text="Or select material:").grid(row=2, column=0, sticky="w")
    combo_r = ttk.Combobox(
        frame,
        width=35,
        values=["None"] + list(materials_r_values.keys())
    )
    combo_r.set("None")  # Default to "None"
    combo_r.grid(row=2, column=1, columnspan=2, padx=5, pady=5)

    def on_typed_r_value_parallel(event=None):
        text = ent_r.get().strip()
        if text == "":
            combo_r.config(state="normal")
        else:
            combo_r.config(state="disabled")
            combo_r.set("None")

    def on_select_material_parallel(event=None):
        sel = combo_r.get().strip()
        if sel == "None":
            ent_r.config(state="normal")
        else:
            ent_r.delete(0, "end")
            ent_r.config(state="disabled")

    ent_r.bind("<KeyRelease>", on_typed_r_value_parallel)
    combo_r.bind("<<ComboboxSelected>>", on_select_material_parallel)

    # Area entry
    ttk.Label(frame, text="Area % for this path:").grid(row=3, column=0, sticky="w")
    ent_a = ttk.Entry(frame, width=10)
    ent_a.grid(row=3, column=1, padx=5, pady=5)

    if last_path:
        ent_a.insert(0, str(area_left))

    result = {'r_value': None, 'area': None, 'material': "Custom R-value"}

    def on_ok():
        typed_str = ent_r.get().strip()
        sel_mat = combo_r.get().strip()

        if typed_str:
            try:
                rv = float(typed_str)
                if rv <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("R-value Error", "Please enter a positive numeric R-value.")
                return
            material_name = "Custom R-value"
        else:
            if sel_mat != "None" and sel_mat in materials_r_values:
                rv = materials_r_values[sel_mat]
                material_name = sel_mat
            else:
                messagebox.showerror("Input Error", "Please type an R-value or select a material.")
                return

        try:
            a_val = float(ent_a.get().strip())
            if a_val <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Area Error", "Please enter a positive area percent.")
            return

        if not last_path:
            if a_val > area_left:
                messagebox.showerror(
                    "Area Error",
                    f"This path's area {a_val:.2f}% exceeds the remaining {area_left:.2f}%. "
                    "Please re-enter."
                )
                return
        else:
            if abs(a_val - area_left) > 1e-6:
                messagebox.showerror(
                    "Area Error",
                    f"Last path must use exactly {area_left:.2f}%. You entered {a_val:.2f}%. "
                    "Please re-enter."
                )
                return

        result['r_value'] = rv
        result['area'] = a_val
        result['material'] = material_name
        top.destroy()

    ttk.Button(frame, text="OK", command=on_ok).grid(row=4, column=0, columnspan=3, pady=10)

    root.wait_window(top)

    return result['r_value'], result['area'], result['material']

# --------------
# OTHER GUI PARTS
# --------------

def delete_last_layer():
    """Removes the most recently added layer from 'layers'."""
    if layers:
        layers.pop()
        draw_layers()
        calculate_heat_transfer()
    else:
        messagebox.showinfo("No Layers", "No layers to delete.")

def confirm_delete_layer(index):
    """Asks the user for confirmation to delete a layer (series or parallel)."""
    response = messagebox.askyesno("Delete Layer", f"Are you sure you want to delete layer {index + 1}?")
    if response:
        del layers[index]
        draw_layers()
        calculate_heat_transfer()


def draw_layers():
    """Draws the layers horizontally as a cross-section of a wall, with hover effects and delete buttons."""
    canvas.delete("all")

    # Fixed layer dimensions
    fixed_layer_height = 200
    fixed_layer_width = 100
    x = 10

    # Loop through the layers
    for i, layer in enumerate(layers):
        if layer['type'] == 'series':
            color = "maroon"
            r_val = layer['r_value']
            material = layer.get('material', 'Custom R-value')

            # Draw the layer rectangle
            rect_tag = f"layer_{i}"
            rect = canvas.create_rectangle(x, 10, x + fixed_layer_width, 10 + fixed_layer_height, fill=color, outline="black", tags=rect_tag)
            canvas.create_text(x + fixed_layer_width / 2, 10 + fixed_layer_height / 2, text=f"R = {r_val:.2f}", fill="white")

            # Bind click and hover events for layer info
            canvas.tag_bind(rect_tag, "<Button-1>", lambda e, name=f"Series Layer, R={r_val:.2f}, Material: {material}": show_layer_info(name))
            canvas.tag_bind(rect_tag, "<Enter>", lambda e: canvas.config(cursor="hand2"))
            canvas.tag_bind(rect_tag, "<Leave>", lambda e: canvas.config(cursor=""))

            # Draw the "X" button for deleting the layer
            delete_tag = f"delete_{i}"
            delete_button = canvas.create_rectangle(x + fixed_layer_width - 20, 15, x + fixed_layer_width - 5, 30, fill="red", outline="black", tags=delete_tag)
            canvas.create_text(x + fixed_layer_width - 12, 22, text="X", fill="white", font=("Arial", 10, "bold"), tags=delete_tag)

            # Bind the delete button to the delete function
            canvas.tag_bind(delete_tag, "<Button-1>", lambda e, index=i: confirm_delete_layer(index))
            canvas.tag_bind(delete_tag, "<Enter>", lambda e: canvas.config(cursor="hand2"))
            canvas.tag_bind(delete_tag, "<Leave>", lambda e: canvas.config(cursor=""))

            x += fixed_layer_width + 10

        elif layer['type'] == 'parallel':
            y_start = 10
            color = "green"

            for j, path in enumerate(layer['paths']):
                r_val = path['r_value']
                pct = path['area_percent']
                material = path.get('material', 'Custom R-value')

                height = fixed_layer_height * (pct / 100)
                height = max(height, 30)

                # Draw the path rectangle
                rect_tag = f"path_{i}_{j}"
                rect = canvas.create_rectangle(x, y_start, x + fixed_layer_width, y_start + height, fill=color, outline="black", tags=rect_tag)
                canvas.create_text(x + fixed_layer_width / 2, y_start + height / 2, text=f"R = {r_val:.2f}\n{pct}%", fill="white")

                # Bind click and hover events for path info
                canvas.tag_bind(rect_tag, "<Button-1>", lambda e, name=f"Parallel Path, R={r_val:.2f}, Area={pct}%, Material: {material}": show_layer_info(name))
                canvas.tag_bind(rect_tag, "<Enter>", lambda e: canvas.config(cursor="hand2"))
                canvas.tag_bind(rect_tag, "<Leave>", lambda e: canvas.config(cursor=""))

                # Draw the "X" button for deleting the entire parallel layer
                if j == 0:
                    delete_tag = f"delete_parallel_{i}"
                    delete_button = canvas.create_rectangle(x + fixed_layer_width - 20, y_start + 5, x + fixed_layer_width - 5, y_start + 20, fill="red", outline="black", tags=delete_tag)
                    canvas.create_text(x + fixed_layer_width - 12, y_start + 12, text="X", fill="white", font=("Arial", 10, "bold"), tags=delete_tag)

                    # Bind the delete button to the delete function
                    canvas.tag_bind(delete_tag, "<Button-1>", lambda e, index=i: confirm_delete_layer(index))
                    canvas.tag_bind(delete_tag, "<Enter>", lambda e: canvas.config(cursor="hand2"))
                    canvas.tag_bind(delete_tag, "<Leave>", lambda e: canvas.config(cursor=""))

                y_start += height

            x += fixed_layer_width + 10

    # Dynamically adjust the canvas scroll region to fit all layers
    canvas_width = max(x + 20, root.winfo_width())  # Ensure the width expands with content
    canvas.config(scrollregion=(0, 0, canvas_width, 600))


def show_layer_info(name):
    """Displays the name of the clicked layer in a message box."""
    messagebox.showinfo("Layer Info", name)


# ------------------
# MAIN GUI SETUP
# ------------------
root = tk.Tk()
root.title("Composite Wall Heat Transfer")
root.geometry("800x700")
root.configure(bg="lightgray")

layers = []  # This will store the entire layer structure

# -- Inputs Frame --
frame_inputs = ttk.Frame(root, padding=10)
frame_inputs.pack(pady=10, padx=20, fill="x")

labels = [
    "Inside Temp (°F):",
    "Outside Temp (°F):",
    "Inside Air Film R-value (default 0.68):",
    "Outside Air Film R-value (default 0.17):",
    "Wall Area (ft²):"
]
entries = []
for i, text in enumerate(labels):
    ttk.Label(frame_inputs, text=text).grid(row=i, column=0, sticky="w", padx=5, pady=5)
    e = ttk.Entry(frame_inputs, width=20)
    e.grid(row=i, column=1, padx=5, pady=5)
    e.bind("<KeyRelease>", auto_update)
    entries.append(e)

entry_t_inside, entry_t_outside, entry_r_inside_film, entry_r_outside_film, entry_wall_area = entries

# -- Frame for Layers --
frame_layers = ttk.Frame(root, padding=10)
frame_layers.pack(pady=10, padx=20, fill="x")

# Series: typed or combobox
ttk.Label(frame_layers, text="Series Layer: R-value (ft²·h·°F/BTU):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
entry_r_value = ttk.Entry(frame_layers, width=10)
entry_r_value.grid(row=0, column=1, padx=5, pady=5)
# Bind to disable combobox if non-empty
entry_r_value.bind("<KeyRelease>", on_typed_r_value_series)

ttk.Label(frame_layers, text="Or Select Material:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
combo_material = ttk.Combobox(
    frame_layers,
    width=35,
    values=["None"] + list(materials_r_values.keys())
)
combo_material.set("None")  # Default to "None"
combo_material.grid(row=0, column=3, padx=5, pady=5)
combo_material.bind("<<ComboboxSelected>>", on_select_material_series)

ttk.Button(frame_layers, text="Add Series Layer", command=add_series_layer).grid(row=0, column=4, padx=5, pady=5)

# Parallel: number of paths
ttk.Label(frame_layers, text="Parallel Layer: Number of Paths:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
entry_num_paths = ttk.Entry(frame_layers, width=10)
entry_num_paths.grid(row=1, column=1, padx=5, pady=5)

ttk.Button(frame_layers, text="Add Parallel Layer", command=add_parallel_layer).grid(row=1, column=2, padx=5, pady=5)
ttk.Button(frame_layers, text="Delete Last Layer", command=delete_last_layer).grid(row=1, column=3, padx=5, pady=10)

# -- Scrollable Canvas for visualizing layers --
canvas_frame = ttk.Frame(root)
canvas_frame.pack(pady=10, padx=20, fill="both", expand=True)

# Create the canvas
canvas = Canvas(canvas_frame, bg="white", height=250)
canvas.grid(row=0, column=0, sticky="nsew")

# Add vertical scrollbar to the right of the canvas
scrollbar_y = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
scrollbar_y.grid(row=0, column=1, sticky="ns")

# Add horizontal scrollbar below the canvas
scrollbar_x = ttk.Scrollbar(canvas_frame, orient="horizontal", command=canvas.xview)
scrollbar_x.grid(row=1, column=0, sticky="ew")

# Configure the canvas to use the scrollbars
canvas.config(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

# Enable mousewheel scrolling for horizontal scrolling
def on_mousewheel(event):
    canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

canvas.bind("<Shift-MouseWheel>", on_mousewheel)

# Configure the canvas frame to expand with the window
canvas_frame.rowconfigure(0, weight=1)
canvas_frame.columnconfigure(0, weight=1)

# Initial scrollregion (will be updated dynamically)
canvas.config(scrollregion=(0, 0, 800, 250))


# -- Results section --
frame_results = ttk.Frame(root, padding=10)
frame_results.pack(pady=10, padx=20, fill="x")

results = tk.StringVar()
ttk.Label(frame_results, textvariable=results, justify="left", font=("Arial", 10, "bold")).pack()

# -- Editable Author Credit --
author_var = tk.StringVar(value="Developed By Alex Kalmbach")
ttk.Label(root, textvariable=author_var, width=40).place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

# Start
root.mainloop()