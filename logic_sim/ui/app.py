"""
MEMBER 3: User interface for the Logic Circuit Simulator.

This file only DISPLAYS things. It never computes logic itself: it asks the
backend for a circuit and for wire values, then draws them.
"""
import tkinter as tk

from logic_sim import backend

ON_COLOR = "#16a34a"    # green = signal is 1
OFF_COLOR = "#9ca3af"   # grey  = signal is 0
GATE_W, GATE_H = 70, 44
INPUT_R = 14


class SimulatorApp:
    def __init__(self, root):
        self.root = root
        root.title("Logic Circuit Simulator")

        self.circuit = None      # the circuit graph from the backend
        self.toggle_vars = {}    # {"A": IntVar, ...} one per input variable
        self.values = {}         # {node_id: 0 or 1} from propagation

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

        self.error_label = tk.Label(self.root, text="", fg="#dc2626", anchor="w", padx=8)
        self.error_label.pack(fill="x")

        self.toggle_frame = tk.Frame(self.root, padx=8, pady=4)
        self.toggle_frame.pack(fill="x")

        self.canvas = tk.Canvas(self.root, width=600, height=300, bg="white")
        self.canvas.pack(padx=8, pady=8)

    # ---- reacting to the user -------------------------------------------
    def on_build(self):
        """Called when 'Build circuit' is clicked."""
        text = self.entry.get().strip()
        try:
            self.circuit = backend.get_circuit(text)
        except ValueError as err:
            self.error_label.config(text=str(err))
            return

        self.error_label.config(text="")
        self._make_toggles()
        self.update_circuit()

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
        self.values = backend.propagate(self.circuit, assignment)
        self.draw()

    # ---- drawing --------------------------------------------------------
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
        """Where wire number `index` enters a gate (left side, spread out)."""
        count = len(gate["inputs"])
        y = gate["y"] + (index - (count - 1) / 2) * 16
        return gate["x"] - GATE_W / 2, y

    def _draw_wire(self, x1, y1, x2, y2, color):
        mid = (x1 + x2) / 2
        self.canvas.create_line(x1, y1, mid, y1, mid, y2, x2, y2, fill=color, width=3)

    def draw(self):
        c = self.canvas
        c.delete("all")   # clear, then redraw everything with the new values
        nodes = self._lookup()

        # Wires first, so the nodes are drawn on top of their ends.
        for gate in self.circuit["gates"]:
            for i, source_id in enumerate(gate["inputs"]):
                sx, sy = self._output_point(nodes[source_id])
                tx, ty = self._input_point(gate, i)
                self._draw_wire(sx, sy, tx, ty, self._color(source_id))

        out = self.circuit["output"]
        sx, sy = self._output_point(nodes[out["from"]])
        self._draw_wire(sx, sy, out["x"] - INPUT_R, out["y"], self._color(out["from"]))

        for node in self.circuit["inputs"]:
            x, y = node["x"], node["y"]
            c.create_oval(x - INPUT_R, y - INPUT_R, x + INPUT_R, y + INPUT_R,
                          fill=self._color(node["id"]), outline="black")
            c.create_text(x, y, text=node["id"], fill="white", font=("Arial", 11, "bold"))

        for gate in self.circuit["gates"]:
            x, y = gate["x"], gate["y"]
            c.create_rectangle(x - GATE_W / 2, y - GATE_H / 2,
                               x + GATE_W / 2, y + GATE_H / 2,
                               fill="#f3f4f6", outline=self._color(gate["id"]), width=3)
            c.create_text(x, y, text=gate["type"], font=("Arial", 11, "bold"))

        x, y = out["x"], out["y"]
        c.create_oval(x - INPUT_R, y - INPUT_R, x + INPUT_R, y + INPUT_R,
                      fill=self._color(out["id"]), outline="black")
        c.create_text(x, y, text=str(self.values[out["id"]]), fill="white",
                      font=("Arial", 11, "bold"))
        c.create_text(x, y + 28, text="OUTPUT", font=("Arial", 9))


def run():
    root = tk.Tk()
    app = SimulatorApp(root)
    app.on_build()    # build the default expression right away
    root.mainloop()
