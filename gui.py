import os
import tkinter as tk
import threading
import concurrent.futures
from tkinter import ttk, filedialog
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from colored_graph import ColoredGraph
from graph_generator import GraphGenerator
from ramsey_solver import RamseySolver

matplotlib.use("Agg")

all_colorings_exit_flag = False
# TODO UPDATEEEEE
HELP_TEXT = """
This is a general overview for using Ordered Ramsey numbers utility!
This tool should help a researcher in finding Ramsey numbers for given two ordered graphs (2 color case).

On the left, there are two Graph Builders for the two graphs. The 'New graph' button is used to create a chosen graph
of a chosen size. The main tool for fine-tuning the graph is the 'Edge +-er'. By writing the corresponding space-separated
indices of an edge, this edge is added to the graph (or removed, if it exists).

Then specify the Avoiding graph size, chosen solver and special requirements - the button 'Create new SAT formula' makes use of all
of these, and it takes the current red and blue graphs (because it has to create a static SAT solver problem).
In short, the button takes the two specified graphs along with the specified underlying SAT solver and special conditions 
and prompts you to choose the buttons on the right.

Clicking 'Find next solution' tries to find a solution to the SAT problem and display you an avoiding colouring you haven't seen yet,
if there is any. 'Copy graph as text' overwrites your clipboard with the currently displayed avoiding graph in the format
'1 2 r, 1 3 b, ..', which is exactly the format used in the Special conditions entry. It serves for advanced uses, when you e.g. want to 
expand the current colouring by enforcing a part of it. You can also save the current figures to a chosen folder by the last button.

Note that clicking 'Create new SAT formula' resets these already found solutions and starts searching for them from scratch.
Also note that before clicking 'Create new SAT formula', the newly built graphs in the builders don't matter, as the previous
(SAT) problem is still active while clicking 'Find next solution'.

For advanced uses (e.g. when you want to exhaustively search for all possible solutions to a given SAT problem and
view them with another tool), you can use the button 'Find all solutions in a separate thread'. This also creates a new formula
for itself and saves all found avoiding colourings until they run out.

Please note that (depending on you PC specifications) you may encounter difficulties when trying to look for large avoiding graphs (of size ~16 and more).
"""


class GraphBuilder:
    """
    A class serving as a tkinter frame for building, GUI-displaying and maintaining a graph.
    """

    def __init__(self, master_frame, graph, color):
        """
        :param master_frame: The frame where the GraphBuilder will be placed
        :param graph: ColoredGraph data structure - the underlying graph
        :param color: The enforced color of this graph, either 'r' or 'b'
        """
        self.master_frame = master_frame
        self.graph = graph
        self.color = color
        self.color_full_name = 'red' if color == 'r' else 'blue'
        self._initialize_control_frame()
        self.width = 20
        self.update_graph()

    def _initialize_control_frame(self):
        """
        Places all the necessary controls in their respective places, prepares the layout.
        """
        self.control_frame = tk.Frame(self.master_frame)
        self.control_frame.grid(rowspan=2, column=0)
        info1 = tk.Label(self.control_frame, text="Graph size:")
        info1.grid(row=0, column=0, sticky='N')
        self.vertex_num_textbox = tk.Spinbox(self.control_frame, from_=3, to=15, width=4)
        self.vertex_num_textbox.grid(row=1, column=0)
        info2 = tk.Label(self.control_frame, text="Graph type:")
        info2.grid(row=2, column=0)
        self.graph_type = ttk.Combobox(self.control_frame,
                                       values=[
                                           "Complete",
                                           "Path",
                                           "Alt path",
                                           "Left star",
                                           "Empty"],
                                       width=9)
        self.graph_type.grid(row=3, column=0)
        self.graph_type.current(0)
        self.new_graph_button = tk.Button(self.control_frame, text="New graph", width=10, command=self._reset_graph)
        self.new_graph_button.grid(row=4, column=0)
        info3 = tk.Label(self.control_frame, text="Edge +-er:")
        info3.grid(row=5, column=0)
        self.edge_adder = tk.Entry(self.control_frame, width=8)
        self.edge_adder.grid(row=6, column=0, sticky='N')
        self.edge_adder.bind("<Return>", self.update_graph)

    def update_graph(self, event=None):
        """
        Processes  textbox input and adds/removes edges accordingly from the underlying graph. The behaviour is -
        if the edge is present in the graph, remove it, otherwise add it. The only allowed text is in the form of two
        separated integers denoting the new edge.
        """
        self._show_graph()
        adder_content = self.edge_adder.get()
        self.edge_adder.delete(0, 100)
        if adder_content == "":
            return
        tokens = adder_content.split()
        if len(tokens) != 2:
            tk.messagebox.showerror("Error", "Only 2 space separated integers are allowed here.")
            return
        v1, v2 = tokens[0], tokens[1]
        # TODO catch exception
        v1, v2 = int(v1), int(v2)
        if v1 > v2:
            v1, v2 = v2, v1
        if 0 < v1 <= self.graph.size and 0 < v2 <= self.graph.size and v1 != v2:
            edge = (v1, v2)
            if not self.graph.edge_exists(edge):
                self.graph.add_edge((v1, v2), color=self.color)
            else:
                self.graph.remove_edge(edge)
        else:
            tk.messagebox.showerror("Error", "The numbers should be between 1 and " + str(
                self.graph.size) + " without self-loops.")
            return
        self._show_graph()
        self.master_frame.after(100, lambda: self.edge_adder.focus())

    def _show_graph(self):
        """
        Displays the underlying graph in the Tkinter Canvas.
        """
        fig, _ = self.graph.get_visualization()
        label_red = tk.Label(self.master_frame, text="Current " + self.color_full_name + " graph:",
                             fg=self.color_full_name)
        label_red.grid(row=0, column=1, sticky='N')
        canvas_red = FigureCanvasTkAgg(fig, master=self.master_frame)
        canvas_red.draw()
        canvas_red.get_tk_widget().grid(row=1, column=1, sticky='N')

    def _reset_graph(self):
        """
        Creates a new underlying graph and calls _show_graph.
        """
        graph_type = self.graph_type.get()
        graph_size = int(self.vertex_num_textbox.get())
        if graph_type == "Empty":
            self.graph = ColoredGraph(graph_size, [], {})
        elif graph_type == "Complete":
            self.graph = ColoredGraph.create_colored_graph_from_adj_list(GraphGenerator.full(graph_size), self.color)
        elif graph_type == "Path":
            self.graph = ColoredGraph.create_colored_graph_from_adj_list(GraphGenerator.monotone_path(graph_size),
                                                                         self.color)
        elif graph_type == "Alt path":
            self.graph = ColoredGraph.create_colored_graph_from_adj_list(GraphGenerator.alternating_path(graph_size),
                                                                         self.color)
        elif graph_type == "Left star":
            self.graph = ColoredGraph.create_colored_graph_from_adj_list(GraphGenerator.star(1, graph_size), self.color)

        self._show_graph()


# Graphs which appear first in the GUI as an example
G_DEFAULT_RED = ColoredGraph(3, [(1, 2), (2, 3), (1, 3)], {(1, 2): 'r', (2, 3): 'r', (1, 3): 'r'})
G_DEFAULT_BLUE = ColoredGraph(4, [(1, 2), (2, 3), (3, 4)], {(1, 2): 'b', (2, 3): 'b', (3, 4): 'b'})
G_DEFAULT_RED.color_edges_monochromatic('r')
G_DEFAULT_BLUE.color_edges_monochromatic('b')

# Global variables keeping track of the current program state
ramsey_solver = RamseySolver(5, G_DEFAULT_RED, G_DEFAULT_BLUE)
current_avoiding_graph = None
current_graph_viz = None
current_matrix_viz = None


def general_help_popup():
    help_popup = tk.Toplevel(root)
    help_label = tk.Label(master=help_popup, text=HELP_TEXT)
    help_label.grid(row=0, column=0)


# Create the main window
root = tk.Tk()
root.title("Ordered Ramsey numbers utility")
root.geometry('{}x{}'.format(1400, 900))

# Create main frame containers
control_menu_left = tk.Frame(root)
control_menu_right = tk.Frame(root)
input_graph_builder = tk.Frame(root)
output_graph_visualiser = tk.Frame(root)
red_graph_frame = tk.Frame(input_graph_builder)
blue_graph_frame = tk.Frame(input_graph_builder)

# Layout these main containers inside the main window
control_menu_left.grid(row=0, column=0)
control_menu_right.grid(row=0, column=1)
input_graph_builder.grid(row=1, column=0)
output_graph_visualiser.grid(row=1, column=1)
red_graph_frame.grid(row=0, column=0)
blue_graph_frame.grid(row=1, column=0)

red_builder = GraphBuilder(red_graph_frame, G_DEFAULT_RED, 'r')
blue_builder = GraphBuilder(blue_graph_frame, G_DEFAULT_BLUE, 'b')

info_text_var = tk.StringVar(output_graph_visualiser)
info_text_var.set("Press a button to see something here")

# Draw empty figures to fill the space
graph_viz_figure = matplotlib.figure.Figure(figsize=(6, 3.7))
graph_viz_canvas = FigureCanvasTkAgg(graph_viz_figure, master=output_graph_visualiser)
graph_viz_canvas.draw()
graph_viz_canvas.get_tk_widget().grid(row=1, column=0)
matrix_viz_figure = matplotlib.figure.Figure(figsize=(6, 3.7))
matrix_viz_canvas = FigureCanvasTkAgg(matrix_viz_figure, master=output_graph_visualiser)
matrix_viz_canvas.get_tk_widget().grid(row=2, column=0)
matrix_viz_canvas.draw()

# computation_executor, holding either None or concurrent.futures.ThreadPoolExecutor object
side_executor_thread_interactive = None
side_executor_thread_all_solutions = None
# either None or concurrent.futures.Future object
future_avoiding_coloring = None
future_all_solutions = None


def periodic_thread_check():
    """
    Check every 200 ms the status of the side executor threads. If it finished running, displays the results and
    change the button appearance.
    """
    global side_executor_thread_interactive, side_executor_thread_all_solutions
    if side_executor_thread_interactive is not None:
        if future_avoiding_coloring is not None and future_avoiding_coloring.done():
            update_gui_with_found_coloring(future_avoiding_coloring.result())
            side_executor_thread_interactive = None
            next_solution_button['text'] = "Find next solution"
            next_solution_button.config(fg="black")
    if side_executor_thread_all_solutions is not None:
        if future_all_solutions is not None and future_all_solutions.done():
            side_executor_thread_all_solutions = None
            all_solutions_button['text'] = "Find all solutions in a separate thread"
            all_solutions_button.config(fg='black')
    root.after(3000, periodic_thread_check)


def get_special_conditions(maximum_vertex_num):
    """
    Extracts and parses data from the special_conditions_entry.
    :return: A possibly empty list of special conditions of the form [((1,4),'r'), ... ] or None, if the parsing failed.
    """
    special_conditions_text = special_conditions_entry.get()
    if special_conditions_text is "":
        return []
    special_conditions_list = []
    special_conditions_space_delimited_list = special_conditions_text.split(',')
    try:
        for s in special_conditions_space_delimited_list:
            i, j, color = s.split()
            i, j = int(i), int(j)
            if i < 1 or j < 1 or i > maximum_vertex_num or j > maximum_vertex_num or color not in ['r', 'b']:
                return None
            special_conditions_list.append(((i, j), color))
        return special_conditions_list
    except:
        return None



def check_create_new_solver_preconditions():
    """
    Helper function, which checks the preconditions for creating a new SAT formula, so that it is not misused
    :return True, if all the conditions are met, False otherwise
    """
    avoiding_graph_size = int(avoiding_graph_size_specifier.get())
    special_conditions_list = get_special_conditions(avoiding_graph_size)
    if special_conditions_list is None:
        tk.messagebox.showerror("Error", "Please write the special conditions in the specified format. Example:\n"
                                         "\"1 4 r, 3 5 b, 3 4 b\"\n"
                                         "The only permitted colors are 'r' and 'b', the vertices have to be integers in range "
                                         "from 1 to the currently specified 'Avoiding graph size'.")
        return False
    if avoiding_graph_size < red_builder.graph.size or avoiding_graph_size < blue_builder.graph.size:
        tk.messagebox.showerror("Error", "Please choose bigger Avoiding graph size.")
        return False
    if not red_builder.graph.get_edge_list() or not blue_builder.graph.get_edge_list():
        tk.messagebox.showerror("Error", "Both graphs need to have at least one edge.")
        return False
    return True


def create_new_solver():
    """
    Creates a new solver with a different sat problem. Uses the current graphs from GraphBuilders as well as
    specified conditions like avoiding graph size, enforce symmetry and special conditions.
    """
    if check_create_new_solver_preconditions():
        avoiding_graph_size = int(avoiding_graph_size_specifier.get())
        special_conditions_list = get_special_conditions(avoiding_graph_size)
        global ramsey_solver
        ramsey_solver = RamseySolver(avoiding_graph_size, red_builder.graph, blue_builder.graph,
                                     solver=solver_box.get(),
                                     enforce_symmetry=bool(enforce_symmetry_var.get()),
                                     special_conditions=special_conditions_list)
        info_text_var.set("↑↑↑ Created new SAT solver formula ↑↑↑")
        info_label.config(fg="black")


def update_gui_with_found_coloring(avoiding_drawing):
    """
    Updates the graphs to display the (newly found) avoiding drawing.
    :param avoiding_drawing: Either ColoredGraph structure or None
    """
    global current_graph_viz, current_matrix_viz, current_avoiding_graph
    if avoiding_drawing is None:
        info_text_var.set("Coloring (or next coloring) for " + str(ramsey_solver.n) + " vertices doesn't exist.")
        info_label.config(fg="red")
        return
    graph_fig, _ = avoiding_drawing.get_visualization()
    matrix_fig, _ = avoiding_drawing.get_matrix_visualization()
    current_avoiding_graph, current_graph_viz, current_matrix_viz = avoiding_drawing, graph_fig, matrix_fig
    canvas_graph = FigureCanvasTkAgg(graph_fig, master=output_graph_visualiser)
    canvas_graph.draw()
    canvas_graph.get_tk_widget().grid(row=1, column=0, sticky='N')
    canvas_graph = FigureCanvasTkAgg(matrix_fig, master=output_graph_visualiser)
    canvas_graph.draw()
    canvas_graph.get_tk_widget().grid(row=2, column=0, sticky='S')
    info_text_var.set("Avoiding coloring for " + str(ramsey_solver.n) + ":")
    info_label.config(fg="green")


def find_coloring():
    """
    Prompts the ramsey_solver for a next avoiding coloring in a separate thread.
    """
    # TODO this part is maybe useless
    global current_graph_viz, current_matrix_viz, current_avoiding_graph, side_executor_thread_interactive
    if current_avoiding_graph is not None:
        current_graph_viz.clf()
        current_matrix_viz.clf()

    if side_executor_thread_interactive is not None:
        side_executor_thread_interactive.shutdown()
        side_executor_thread_interactive = None
        next_solution_button['text'] = "Find next solution"
        next_solution_button.config(fg="black")
        info_text_var.set("Computation cancelled")
        info_label.config(fg="black")
        return

    info_text_var.set("Finding coloring for " + str(ramsey_solver.n) + " vertices...")
    info_label.config(fg="grey")
    side_executor_thread_interactive = concurrent.futures.ThreadPoolExecutor()
    next_solution_button['text'] = "Terminate computation"
    next_solution_button.config(fg="red")
    global future_avoiding_coloring
    future_avoiding_coloring = side_executor_thread_interactive.submit(ramsey_solver.find_next_avoiding_drawing)


def find_all_colorings():
    """
    If not already running, starts a side_executor_thread_all_solutions ThreadPool, which searches for all possible
    solutions to a given SAT problem and saves them in the specified folder
    If already running, the function terminates the current ThreadPool.
    """
    global side_executor_thread_all_solutions, future_all_solutions, all_colorings_exit_flag
    if side_executor_thread_all_solutions is not None:
        all_colorings_exit_flag = True
        side_executor_thread_all_solutions.shutdown()
        side_executor_thread_all_solutions = None
        all_solutions_button['text'] = "Find all solutions in a separate thread"
        all_solutions_button.config(fg='black')
        future_all_solutions = None
        return
    if not check_create_new_solver_preconditions():
        return
    # choose a dir to save the colorings in
    target_directory = filedialog.askdirectory()
    if not target_directory:
        return
    avoiding_graph_size = int(avoiding_graph_size_specifier.get())
    special_conditions_list = get_special_conditions(avoiding_graph_size)
    enforce_symmetry = bool(enforce_symmetry_var.get())
    r_graph = red_builder.graph
    b_graph = blue_builder.graph
    solver = solver_box.get()

    side_executor_thread_all_solutions = concurrent.futures.ThreadPoolExecutor()
    all_solutions_button['text'] = "Terminate computation"
    all_solutions_button.config(fg='red')

    all_colorings_exit_flag = False
    future_all_solutions = side_executor_thread_all_solutions.submit(get_and_save_all_colorings, target_directory, avoiding_graph_size, r_graph, b_graph, solver,
                                                    enforce_symmetry,
                                                    special_conditions_list)


def get_and_save_all_colorings(target_directory, avoiding_graph_size, r_graph, b_graph, solver, enforce_symmetry,
                               special_conditions_list):
    """
    Searches exhaustively for all solutions for a given Ramsey problem and saves them in the specified folder. As it is
    intended to be run in a separate ThreadPool, it contains an exit flag condition, which can be used to terminate this
    function from outside.
    """
    r_solver = RamseySolver(avoiding_graph_size, r_graph, b_graph,
                            solver=solver,
                            enforce_symmetry=enforce_symmetry,
                            special_conditions=special_conditions_list)
    i = 1
    while not all_colorings_exit_flag:
        avoiding_coloring = r_solver.find_next_avoiding_drawing()
        if avoiding_coloring is None:
            return
        # create figure

        fig = plt.figure(figsize=(15, 6))
        gs = fig.add_gridspec(1, 2)
        ax1 = fig.add_subplot(gs[0, 0])
        _, ax1 = avoiding_coloring.get_visualization(ax=ax1)
        ax2 = fig.add_subplot(gs[0, 1])
        _, ax2 = avoiding_coloring.get_matrix_visualization(ax=ax2)
        plt.tight_layout()
        # save figure
        file_name = os.path.join(target_directory, str(i) + ".png")
        plt.savefig(file_name)
        plt.close()
        i += 1


def copy_graph():
    """
    Places the currently displayed graph as a string of the form "1 2 r, 1 3 b,..." in the clipboard
    """
    if current_avoiding_graph:
        colored_edge_list = current_avoiding_graph.get_colored_edge_list()
        colored_edge_list.sort()
        str_tokens = [str(v1) + " " + str(v2) + " " + str(c) for (v1, v2), c in colored_edge_list]
        root.clipboard_clear()
        root.clipboard_append(','.join(str_tokens))


def save_figures():
    """
    Takes the red builder, blue builder, current graph and matrix outputs and saves them as a single Figure.
    """
    if current_avoiding_graph is None:
        return
    target_directory = filedialog.askdirectory()
    if not target_directory:
        return
    fig = plt.figure(figsize=(15, 6))
    gs = fig.add_gridspec(2, 5)
    ax1 = fig.add_subplot(gs[0, 0])
    _, ax1 = red_builder.graph.get_visualization(ax=ax1)
    ax2 = fig.add_subplot(gs[:, 1:3])
    _, ax2 = current_avoiding_graph.get_visualization(ax=ax2)
    ax3 = fig.add_subplot(gs[1, 0])
    _, ax3 = blue_builder.graph.get_visualization(ax=ax3)
    ax4 = fig.add_subplot(gs[:, 3:5])
    _, ax4 = current_avoiding_graph.get_matrix_visualization(ax=ax4)
    plt.tight_layout()
    # TODO custom name entry, directory entry?
    i = 1
    file_name = os.path.join(target_directory, str(i) + ".png")
    while os.path.exists(file_name):
        i += 1
        file_name = os.path.join(target_directory, str(i) + ".png")
    plt.savefig(file_name)
    return


help_button = tk.Button(master=control_menu_left, text="Help!", command=general_help_popup, fg="purple", width=8)
help_button.grid(row=1, column=0, columnspan=2)

solver_info_label = tk.Label(master=control_menu_left, text="SAT solver:")
solver_info_label.grid(row=0, column=0)

solver_box = ttk.Combobox(master=control_menu_left, values=["minisat", "glucose"], width=8)
solver_box.current(0)
solver_box.grid(row=0, column=1)

graph_size_info_label = tk.Label(master=control_menu_left, text="Avoiding graph size:")
graph_size_info_label.grid(row=0, column=2)

avoiding_graph_size_specifier = tk.Spinbox(control_menu_left, from_=5, to=22, width=4)
avoiding_graph_size_specifier.grid(row=0, column=3)

enforce_symmetry_var = tk.IntVar()
enforce_symmetry_checkbox = tk.Checkbutton(control_menu_left, text="Enforce symmetry", variable=enforce_symmetry_var)
enforce_symmetry_checkbox.grid(row=0, column=4)

special_conditions_label = tk.Label(master=control_menu_left, text="Special conditions:")
special_conditions_label.grid(row=0, column=5)

special_conditions_entry = tk.Entry(master=control_menu_left)
special_conditions_entry.grid(row=0, column=6)

all_solutions_button = tk.Button(master=control_menu_left, text="Find all solutions in a separate thread",
                                 command=find_all_colorings)
all_solutions_button.grid(row=1, column=2, columnspan=2)

new_problem_button = tk.Button(master=control_menu_left, text="Create new SAT formula", command=create_new_solver)
new_problem_button.grid(row=1, column=4, columnspan=3)

next_solution_button = tk.Button(master=control_menu_right, text="Find next solution", command=find_coloring)
next_solution_button.grid(row=0, column=0)


copy_solution_button = tk.Button(master=control_menu_right, text="Copy graph as text", command=copy_graph)
copy_solution_button.grid(row=0, column=2)

save_solution_button = tk.Button(master=control_menu_right, text="Save current figures", command=save_figures)
save_solution_button.grid(row=0, column=3)

info_label = tk.Label(master=output_graph_visualiser, textvariable=info_text_var)
info_label.grid(row=0, column=0, sticky='N')


def on_closing():
    global all_colorings_exit_flag
    all_colorings_exit_flag = True #terminates the all_solutions thread
    if side_executor_thread_interactive is not None:
        side_executor_thread_interactive.shutdown() #terminates the interactive solutions thread
    root.quit()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", on_closing)

periodic_thread_check()
tk.mainloop()