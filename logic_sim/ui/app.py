"""
MEMBER 3: User interface for the Logic Circuit Simulator.

This file only DISPLAYS things. It never computes logic itself: it asks the
backend for a circuit, wire values and a truth table, then draws them.
"""
import tkinter as tk
import traceback

from logic_sim import backend
from logic_sim.ui import builder, shapes

ON_COLOR = "#16a34a"    # green = signal is 1
OFF_COLOR = "#9ca3af"   # grey  = signal is 0
GATE_FILL = "#f3f4f6"
ROW_HIGHLIGHT = "#fde68a"   # yellow = the truth table row that matches the toggles
ROW_NORMAL = "white"
MATCH_COLOR = ON_COLOR          # green text: table and circuit agree
MISMATCH_COLOR = "#dc2626"      # red text: they disagree
GATE_W, GATE_H = shapes.GATE_W, shapes.GATE_H
INPUT_R = 14
TABLE_HEIGHT = 300       # the truth table box is as tall as the circuit canvas
TABLE_MAX_WIDTH = 420    # wider tables (many variables) scroll sideways


# The logic builder buttons. Change these lists to add or remove symbols.
BUILDER_VARIABLES = ["A", "B", "C", "D"]
BUILDER_OPERATORS = ["AND", "OR", "NOT", "->", "(", ")"]

class SimulatorApp:
    def __init__(self, root):
        self.root = root
        root.title("Logic Circuit Simulator")

        self.circuit = None      # the circuit graph from the backend
        self.table = None        # the truth table from the backend
        self.toggle_vars = {}    # {"A": IntVar, ...} one per input variable
        self.values = {}         # {node_id: 0 or 1} from propagation
        self.row_labels = []     # row_labels[i] = the labels of truth table row i

        self._build_widgets()

    # ---- the widgets (layout of the window) -----------------------------
    def _build_widgets(self):
        top = tk.Frame(self.root, padx=8, pady=8)
        top.pack(fill="x")

        tk.Label(top, text="Expression:").pack(side="left")
        self.entry = tk.Entry(top, width=40)
        self.entry.pack(side="left", padx=6)
        self.entry.insert(0, "(A AND B) OR NOT C")
        tk.Button(top, text="Build circuit", command=self.on_build).pack(side="left")

                # Logic builder: click symbols instead of typing them.
        builder_row = tk.Frame(self.root, padx=8)
        builder_row.pack(fill="x")

        self.builder_buttons = {}        # {"A": Button, "AND": Button, ...}
        for group in (BUILDER_VARIABLES, BUILDER_OPERATORS):
            for token in group:
                button = tk.Button(builder_row, text=token, width=4,
                                   command=lambda t=token: self._add_token(t))
                button.pack(side="left", padx=1)
                self.builder_buttons[token] = button
            tk.Label(builder_row, text="  ").pack(side="left")    # a gap between groups

        tk.Button(builder_row, text="Backspace",
                  command=self._backspace).pack(side="left", padx=1)
        tk.Button(builder_row, text="Clear",
                  command=self._clear_expression).pack(side="left", padx=1)

        self.smart_var = tk.IntVar(value=1)
        tk.Checkbutton(builder_row, text="Smart mode", variable=self.smart_var,
                       command=self._refresh_builder).pack(side="left", padx=8)

        self.error_label = tk.Label(self.root, text="", fg="#dc2626", anchor="w", padx=8)
        self.error_label.pack(fill="x")

        self.toggle_frame = tk.Frame(self.root, padx=8, pady=4)
        self.toggle_frame.pack(fill="x")

        # Task 7: tells you whether the truth table and the circuit agree.
        self.status_label = tk.Label(self.root, text="", font=("Arial", 11, "bold"),
                                     anchor="w", padx=8)
        self.status_label.pack(fill="x")

        # The circuit on the left, the truth table on the right.
        main = tk.Frame(self.root)
        main.pack(padx=8, pady=8)

        self.canvas = tk.Canvas(main, width=600, height=300, bg="white")
        self.canvas.pack(side="left")

        # The truth table lives in a scrollable box with a fixed size, so a
        # table with 64 or 256 rows no longer stretches the window off screen.
        table_box = tk.Frame(main, padx=12)
        table_box.pack(side="left", anchor="n")
        self.table_canvas = tk.Canvas(table_box, width=200, height=TABLE_HEIGHT,
                                      highlightthickness=0)
        self.y_scroll = tk.Scrollbar(table_box, orient="vertical",
                                     command=self.table_canvas.yview)
        self.x_scroll = tk.Scrollbar(table_box, orient="horizontal",
                                     command=self.table_canvas.xview)
        self.table_canvas.configure(yscrollcommand=self.y_scroll.set,
                                    xscrollcommand=self.x_scroll.set)
        self.table_canvas.grid(row=0, column=0)
        self.y_scroll.grid(row=0, column=1, sticky="ns")
        self.x_scroll.grid(row=1, column=0, sticky="ew")

        self.table_frame = tk.Frame(self.table_canvas)    # the labels go in here
        self.table_canvas.create_window(0, 0, window=self.table_frame, anchor="nw")
        self.table_frame.bind("<Configure>", self._fit_table)
        self.root.bind_all("<MouseWheel>", self._on_mouse_wheel)

        
        # Typing in the box also updates the builder; Enter builds the circuit.
        self.entry.bind("<KeyRelease>", self._refresh_builder)
        self.entry.bind("<Return>", lambda event: self.on_build())
        self._refresh_builder()

    # ---- the logic builder ----------------------------------------------
    def _add_token(self, token):
        """Add one symbol to the end of the expression."""
        tokens = builder.tokenize(self.entry.get())
        tokens.append(token)
        self._set_expression(tokens)

    def _backspace(self):
        """Remove the last symbol."""
        tokens = builder.tokenize(self.entry.get())
        self._set_expression(tokens[:-1])

    def _clear_expression(self):
        """Empty the expression box."""
        self._set_expression([])

    def _set_expression(self, tokens):
        """Show these symbols in the box, then update the buttons."""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, " ".join(tokens))
        self._refresh_builder()

    def _refresh_builder(self, event=None):
        """In smart mode, grey out the symbols that cannot come next."""
        tokens = builder.tokenize(self.entry.get())
        smart = self.smart_var.get() == 1
        for token, button in self.builder_buttons.items():
            if smart and not builder.can_add(tokens, token):
                button.config(state="disabled")
            else:
                button.config(state="normal")

    # ---- reacting to the user -------------------------------------------
    def on_build(self):
        """Called when 'Build circuit' is clicked."""
        text = self.entry.get().strip()
        try:
            circuit = backend.get_circuit(text)
            table = backend.get_truth_table(text)
            self.circuit = circuit       # only replace the old ones once BOTH worked
            self.table = table
            self._make_toggles()
            self._build_table()
        except Exception as err:
            self._report(err, "building the circuit")
            return     # keep whatever was on screen before

        self.error_label.config(text="")
        self.update_circuit()

    def _report(self, err, doing):
        """Show an error in red. `doing` says what we were trying to do.

        Call this from inside an `except` block.
        """
        if isinstance(err, ValueError):
            message = str(err)                      # the user's input is wrong: show it as is
        elif isinstance(err, NotImplementedError):
            message = "Not built yet: " + str(err)  # a teammate's part is still a placeholder
        else:
            message = ("Unexpected error while " + doing + ": "
                       + type(err).__name__ + ": " + str(err))
            traceback.print_exc()                   # full details go to the terminal
        self.error_label.config(text=message)

    def _make_toggles(self):
        """One checkbox per input variable found in the circuit."""
        for widget in self.toggle_frame.winfo_children():
            widget.destroy()
        self.toggle_vars = {}

        for node in self.circuit["inputs"]:
            var = tk.IntVar(value=0)
            self.toggle_vars[node["id"]] = var
            tk.Checkbutton(
                self.toggle_frame, text=node["id"], variable=var,
                command=self.update_circuit,
            ).pack(side="left", padx=6)

    def update_circuit(self):
        """Read the toggles, ask the backend for wire values, then redraw."""
        assignment = {name: var.get() for name, var in self.toggle_vars.items()}
        try:
            self.values = backend.propagate(self.circuit, assignment)
            self.draw()
            self._highlight_row(assignment)
            self._update_status(assignment)
        except Exception as err:
            self._report(err, "updating the circuit")

    # ---- the truth table ------------------------------------------------
    def _build_table(self):
        """Create the table as a grid of labels. Grid row 0 is the header."""
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        self.row_labels = []

        variables = self.table["variables"]
        for col, text in enumerate(variables + ["Output"]):
            header = tk.Label(self.table_frame, text=text, width=6, bg="#e5e7eb",
                              font=("Arial", 10, "bold"), relief="solid", borderwidth=1)
            header.grid(row=0, column=col)

        for i, row in enumerate(self.table["rows"]):
            values = [row["inputs"][name] for name in variables] + [row["output"]]
            cells = []
            for col, value in enumerate(values):
                cell = tk.Label(self.table_frame, text=str(value), width=6,
                                bg=ROW_NORMAL, relief="solid", borderwidth=1)
                cell.grid(row=i + 1, column=col)      # +1 because row 0 is the header
                cells.append(cell)
            self.row_labels.append(cells)

        self.table_canvas.yview_moveto(0)     # a new table starts at the top
        self.table_canvas.xview_moveto(0)

    def _fit_table(self, event=None):
        """Size the scroll box to the table, and show scrollbars only when needed."""
        width = self.table_frame.winfo_reqwidth()
        height = self.table_frame.winfo_reqheight()
        self.table_canvas.configure(scrollregion=(0, 0, width, height),
                                    width=min(width, TABLE_MAX_WIDTH),
                                    height=min(height, TABLE_HEIGHT))
        for bar, needed in ((self.y_scroll, height > TABLE_HEIGHT),
                            (self.x_scroll, width > TABLE_MAX_WIDTH)):
            if needed:
                bar.grid()
            else:
                bar.grid_remove()

    def _on_mouse_wheel(self, event):
        """Scroll the table with the mouse wheel, but only when the mouse is over it."""
        widget = self.root.winfo_containing(event.x_root, event.y_root)
        if widget is not None and str(widget).startswith(str(self.table_canvas)):
            self.table_canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")

    def _scroll_to_row(self, index):
        """If row `index` is out of view, scroll so it sits in the middle of the box."""
        self.table_frame.update_idletasks()        # make sure the rows have positions
        total = self.table_frame.winfo_reqheight()
        if total <= TABLE_HEIGHT:
            return                                  # the whole table fits, no scrolling
        cell = self.row_labels[index][0]
        top, bottom = cell.winfo_y(), cell.winfo_y() + cell.winfo_height()
        view_top = self.table_canvas.canvasy(0)
        if top < view_top or bottom > view_top + TABLE_HEIGHT:
            self.table_canvas.yview_moveto(max(0, top - TABLE_HEIGHT / 2) / total)

    def _find_row(self, assignment):
        """Return the index of the truth table row matching `assignment`, or None."""
        for i, row in enumerate(self.table["rows"]):
            if row["inputs"] == assignment:
                return i
        return None

    def _highlight_row(self, assignment):
        """Color the row that matches the current toggles; the others stay white."""
        match = self._find_row(assignment)

        for i, cells in enumerate(self.row_labels):
            color = ROW_HIGHLIGHT if i == match else ROW_NORMAL
            for cell in cells:
                cell.config(bg=color)
        if match is not None:
            self._scroll_to_row(match)     # keep the highlighted row on screen

    def _update_status(self, assignment):
        """Compare the table's expected output with the circuit's actual output."""
        index = self._find_row(assignment)
        if index is None:
            self.status_label.config(text="No truth table row matches these inputs.",
                                     fg=MISMATCH_COLOR)
            return

        expected = self.table["rows"][index]["output"]            # from the truth table
        actual = self.values[self.circuit["output"]["id"]]        # from the circuit

        if expected == actual:
            text = "Expected " + str(expected) + " (truth table), circuit gives " + str(actual) + " - match"
            color = MATCH_COLOR
        else:
            text = "MISMATCH: truth table expects " + str(expected) + ", circuit gives " + str(actual)
            color = MISMATCH_COLOR
        self.status_label.config(text=text, fg=color)

    # ---- drawing the circuit --------------------------------------------
    def _color(self, node_id):
        return ON_COLOR if self.values[node_id] == 1 else OFF_COLOR

    def _lookup(self):
        """Map every node id to its dict, so wires can find their source."""
        nodes = {n["id"]: n for n in self.circuit["inputs"]}
        nodes.update({g["id"]: g for g in self.circuit["gates"]})
        return nodes

    def _output_point(self, node):
        """Where a wire leaves a node (right side)."""
        if "type" in node:   # gates have a "type", input nodes do not
            return node["x"] + GATE_W / 2, node["y"]
        return node["x"] + INPUT_R, node["y"]

    def _input_point(self, gate, index):
        """Where wire number `index` enters a gate (left side, spread out).

        The wire ends 8 pixels INSIDE the gate. Gates are drawn on top of the
        wires, so this hides the wire's end and closes the gap at the curved
        back of the OR gate.
        """
        count = len(gate["inputs"])
        y = gate["y"] + (index - (count - 1) / 2) * 16
        return gate["x"] - GATE_W / 2 + 8, y

    def _draw_wire(self, x1, y1, x2, y2, color):
        mid = (x1 + x2) / 2
        self.canvas.create_line(x1, y1, mid, y1, mid, y2, x2, y2, fill=color, width=3)

    def _draw_node(self, node_id, x, y, text):
        """A circle (input or output) showing `text`, colored by its value."""
        c = self.canvas
        c.create_oval(x - INPUT_R, y - INPUT_R, x + INPUT_R, y + INPUT_R,
                      fill=self._color(node_id), outline="black")
        c.create_text(x, y, text=text, fill="white", font=("Arial", 11, "bold"))

    def _draw_gate(self, gate):
        """A gate symbol (AND, OR or NOT), outlined by its value."""
        x, y = gate["x"], gate["y"]
        color = self._color(gate["id"])
        points = shapes.points_for(gate["type"], x, y)
        self.canvas.create_polygon(points, fill=GATE_FILL, outline=color, width=3)

        if gate["type"] == "NOT":
            # the small circle on the tip: center 5 pixels inside the right edge
            cx = x + GATE_W / 2 - 5
            self.canvas.create_oval(cx - 5, y - 5, cx + 5, y + 5,
                                    fill=GATE_FILL, outline=color, width=3)

    def draw(self):
        self.canvas.delete("all")   # clear, then redraw with the new values
        nodes = self._lookup()

        # Wires first, so the shapes are drawn on top of the wire ends.
        for gate in self.circuit["gates"]:
            for i, source_id in enumerate(gate["inputs"]):
                sx, sy = self._output_point(nodes[source_id])
                tx, ty = self._input_point(gate, i)
                self._draw_wire(sx, sy, tx, ty, self._color(source_id))

        out = self.circuit["output"]
        sx, sy = self._output_point(nodes[out["from"]])
        self._draw_wire(sx, sy, out["x"] - INPUT_R, out["y"], self._color(out["from"]))

        for node in self.circuit["inputs"]:
            self._draw_node(node["id"], node["x"], node["y"], node["id"])
        for gate in self.circuit["gates"]:
            self._draw_gate(gate)
        self._draw_node(out["id"], out["x"], out["y"], str(self.values[out["id"]]))


def run():
    root = tk.Tk()
    app = SimulatorApp(root)
    app.on_build()    # build the default expression right away
    root.mainloop()