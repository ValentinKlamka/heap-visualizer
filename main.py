import heapq
import random
import tkinter as tk
import threading

heap = []

# Define buttons as a global variable
buttons = {}

def update_visible_values():
    """Update the values of all visible nodes."""
    global buttons  # Access the global buttons dictionary
    for idx, data in buttons.items():
        if idx in buttons:
            new_value = heap[idx] if idx < len(heap) else ""
            data["button"].config(text=str(new_value))

def create_random_heap(size: int):
    """
    Create a random heap of given size asynchronously.
    """
    def build_heap():
        for i in range(size):
            random_number = random.randint(1, 100)
            heapq.heappush(heap, random_number)

    threading.Thread(target=build_heap, daemon=True).start()

def view():
    """
    View the heap in a GUI window with interactive buttons.
    """
    root = tk.Tk()
    root.title("Heap Visualizer")

    # Create the main layout
    main_frame = tk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Create a scrollable canvas in the main frame
    frame = tk.Frame(main_frame)
    frame.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(frame, width=800, height=600, scrollregion=(0, 0, 2000, 2000))
    h_scroll = tk.Scrollbar(frame, orient=tk.HORIZONTAL, command=canvas.xview)
    v_scroll = tk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)

    canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)

    h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
    v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Add a label and input field for heap size
    heap_size_label = tk.Label(main_frame, text="Heap Size:")
    heap_size_label.pack(side=tk.LEFT, padx=5)

    heap_size_var = tk.StringVar(value="1023")
    heap_size_entry = tk.Entry(main_frame, textvariable=heap_size_var)
    heap_size_entry.pack(side=tk.LEFT, padx=5)

    # Create the root button if the heap is not empty
    def create_root_button():
        if heap:
            root_button = tk.Button(canvas, text=str(heap[0]), command=lambda: toggle_children(0, 50, 50))
            root_window_id = canvas.create_window(50, 50, window=root_button, anchor="nw")
            buttons[0] = {"window_id": root_window_id, "button": root_button, "children_visible": False}

    def reset_view():
        """Clear the canvas and reset buttons and lines."""
        canvas.delete("all")
        buttons.clear()
        lines.clear()

    # Update the on_create_random_heap function to use the input value
    def on_create_random_heap():
        try:
            size = int(heap_size_var.get())
        except ValueError:
            size = 1023  # Fallback to default if input is invalid
        reset_view()  # Clear the old view
        create_random_heap(size)
        create_root_button()
        update_visible_values()

    create_button = tk.Button(main_frame, text="Create Random Heap", command=on_create_random_heap)
    create_button.pack(side=tk.BOTTOM, pady=10)

    # Dictionary to keep track of created buttons
    global buttons
    buttons = {}

    # Dictionary to keep track of lines between nodes
    lines = {}

    def draw_line(parent_idx, child_idx):
        """Draw a line between a parent and its child if both are visible."""
        if parent_idx in buttons and child_idx in buttons:
            parent_coords = canvas.coords(buttons[parent_idx]["window_id"])
            child_coords = canvas.coords(buttons[child_idx]["window_id"])
            if parent_coords and child_coords:
                x1, y1 = parent_coords[0] + 9, parent_coords[1] + 15  # Center of parent
                x2, y2 = child_coords[0] + 9, child_coords[1] + 15  # Center of child
                line_id = canvas.create_line(x1, y1, x2, y2, fill="black", width=2)
                lines[(parent_idx, child_idx)] = line_id

    def remove_line(parent_idx, child_idx):
        """Remove the line between a parent and its child."""
        if (parent_idx, child_idx) in lines:
            canvas.delete(lines[(parent_idx, child_idx)])
            del lines[(parent_idx, child_idx)]

    def calculate_visible_subtree_width(index):
        """Recursively calculate the width of the visible subtree rooted at the given index."""
        if index >= len(heap) or index not in buttons or not buttons[index]["children_visible"]:
            return 0

        left_index = 2 * index + 1
        right_index = 2 * index + 2

        # If the node is a leaf, it has no width contribution from children
        if left_index >= len(heap) and right_index >= len(heap):
            return 0

        left_width = calculate_visible_subtree_width(left_index)
        right_width = calculate_visible_subtree_width(right_index)

        # Add a constant spacing between visible children
        return max(50, left_width + right_width + 50)

    def toggle_children(index, x, y):
        """Toggle the visibility of the children of the given index recursively."""
        left_index = 2 * index + 1
        right_index = 2 * index + 2

        def hide_children_recursive(idx):
            """Recursively hide children of the given index and remove lines."""
            left = 2 * idx + 1
            right = 2 * idx + 2

            if left in buttons:
                remove_line(idx, left)  # Remove line to left child
                hide_children_recursive(left)
                canvas.delete(buttons[left]["window_id"])
                del buttons[left]
            if right in buttons:
                remove_line(idx, right)  # Remove line to right child
                hide_children_recursive(right)
                canvas.delete(buttons[right]["window_id"])
                del buttons[right]

        def recalculate_positions():
            """Recalculate positions of all visible nodes and redraw lines."""
            # Clear all existing lines
            for line_id in lines.values():
                canvas.delete(line_id)
            lines.clear()

            def calculate_position(idx, parent_x, parent_y):
                """Calculate the position of a node based on its parent."""
                if idx not in buttons:
                    return

                left_idx = 2 * idx + 1
                right_idx = 2 * idx + 2

                left_width = calculate_visible_subtree_width(left_idx)
                right_width = calculate_visible_subtree_width(right_idx)

                if left_idx in buttons:
                    left_x = parent_x  # Align left child vertically with the parent
                    left_y = parent_y + 50
                    canvas.coords(buttons[left_idx]["window_id"], left_x, left_y)
                    draw_line(idx, left_idx)  # Draw line to left child
                    calculate_position(left_idx, left_x, left_y)

                if right_idx in buttons:
                    # Recalculate the right node's position based on the updated left subtree width
                    right_x = parent_x + (left_width + 50)  # Offset to the right of the expanded left subtree
                    right_y = parent_y + 50
                    canvas.coords(buttons[right_idx]["window_id"], right_x, right_y)
                    draw_line(idx, right_idx)  # Draw line to right child
                    calculate_position(right_idx, right_x, right_y)

            # Start recalculating from the root
            if 0 in buttons:
                canvas.coords(buttons[0]["window_id"], 50, 50)
                calculate_position(0, 50, 50)

        # If children are already visible, hide them recursively
        if index in buttons and buttons[index]["children_visible"]:
            hide_children_recursive(index)
            buttons[index]["children_visible"] = False
        else:
            # Otherwise, reveal the children
            if left_index < len(heap):
                left_button = tk.Button(canvas, text=str(heap[left_index]), command=lambda: toggle_children(left_index, x, y + 50))
                left_window_id = canvas.create_window(x - 50, y + 50, window=left_button, anchor="nw")
                buttons[left_index] = {"window_id": left_window_id, "button": left_button, "children_visible": False}

            if right_index < len(heap):
                right_button = tk.Button(canvas, text=str(heap[right_index]), command=lambda: toggle_children(right_index, x, y + 50))
                right_window_id = canvas.create_window(x + 50, y + 50, window=right_button, anchor="nw")
                buttons[right_index] = {"window_id": right_window_id, "button": right_button, "children_visible": False}

            buttons[index]["children_visible"] = True

        recalculate_positions()
        update_visible_values()

    # Create the root button
    if heap:
        create_root_button()

    root.mainloop()

if __name__ == "__main__":
    # View the heap in a GUI window
    view()

