from colored_graph import ColoredGraph
from sat_solver import MinisatSatFormulaSolver, GlucoseSatFormulaSolver
from sat_generator import generate_general_ordered_ramsey_sat, decode_edge


class RamseySolver:
    """
    Class providing an interface to get multiple avoiding colorings for a given graph,
    number of vertices and some special voluntarily enforces conditions.
    """

    def __init__(self, n, red_graph, blue_graph=None, solver="minisat", enforce_symmetry=False,
                 special_conditions=None):
        """

        :param n: The number of vertices for the avoiding graph
        :param red_graph: A ColoredGraph data structure
        :param blue_graph: A ColoredGraph data structure (if not specified, does the Ramsey diagonal case for red graph)
        :param solver: An underlying SAT solver - currently supported is Minisat #TODO glucose
        :param enforce_symmetry: If specified, the avoiding graph coloring will have to be symmetric.
        Note that this may decrease the Ramsey number
        :param special_conditions: A list of the form ((v1,v2),color) where (v1,v2) specifies an edge whose color is
        forced to be either 'r' or 'b'. Note that this may decrease the Ramsey number
        """
        self.n = n
        self.red_graph = red_graph
        self.blue_graph = red_graph if blue_graph == None else blue_graph
        sat_string = generate_general_ordered_ramsey_sat(n, red_graph, blue_graph, enforce_symmetry, special_conditions)
        if solver == "minisat":
            self.solver = MinisatSatFormulaSolver(sat_string)
        if solver == "glucose":
            self.solver = GlucoseSatFormulaSolver(sat_string)

    def find_next_avoiding_drawing(self):
        """
        :return: Returns the next ColoredGraph avoiding coloring, or None if it doesn't exist
        """
        variable_mapping = self.solver.find_next_solution()
        if variable_mapping is None:
            return None
        avoiding_graph = ColoredGraph(self.n, [], {})
        for key, value in variable_mapping.items():
            i, j = decode_edge(key, self.n)
            avoiding_graph.add_edge((i, j), color="r" if not value else "b")
        return avoiding_graph

#export obarvení jako text
