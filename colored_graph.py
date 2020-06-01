import networkx as nx
import numpy as np
import matplotlib

matplotlib.use('TkAgg')


class ColoredGraph:
    """
    A structure holding a graph, capable of quick conversions, re-colorings and graph/matrix visualizations.
    """

    def __init__(self, number_of_vertices, edge_list, edge_coloring):
        """
        :param number_of_vertices: An integer denoting the number of vertices
        :param edge_list: A list of integer pairs denoting the graph edges.
        :param edge_coloring: A dict containing pairs edge: color, where edge is a pair of integers and color is either
        'r' or 'b'.
        """
        self.size = number_of_vertices
        self.edge_list = edge_list
        self.edge_coloring = edge_coloring
        self._check_and_normalize_graph()

    def _check_and_normalize_graph(self):
        for i in range(len(self.edge_list)):
            v1, v2 = self.edge_list[i]
            # Checks the structures if they hold the correct data
            if not isinstance(v1, int) or not isinstance(v2, int) and not (0 < v1 < self.size and 0 < v2 < self.size):
                raise RuntimeError(
                    "The edge list vertices are not integers in the interval from 1 to " + str(self.size) + ".")
            if (v1, v2) not in self.edge_coloring:
                raise RuntimeError("The edge " + str(v1) + " " + str(v2) + " has no color.")
            # Normalize the underlying structures to satisfy v1 < v2 for all edges
            if v1 > v2:
                self.edge_list[i] = (v2, v1)
                prev_color = self.edge_coloring[(v1, v2)]
                del self.edge_coloring[(v1, v2)]
                self.edge_coloring[(v2, v1)] = prev_color

    def __len__(self):
        return self.size

    def get_edge_list(self):
        return self.edge_list

    def get_colored_edge_list(self):
        """
        Returns a representation interfacing with other parts of the program
        :return: A list of entries of the form (edge, color) = ((v1,v2), 'r'/'b' denoting the edge color)
        """
        edgelist_with_colors = []
        for edge in self.edge_list:
            edgelist_with_colors.append((edge, self.edge_coloring[edge]))
        return edgelist_with_colors

    def get_adjacency_list(self):
        """
        Returns the adjacency list form for the given graph without colors
        :return: A list of lists.
        """
        adj = [[] for _ in range(self.size)]
        for v1, v2 in self.edge_list:
            # TODO remove?
            if v1 > v2:
                v1, v2 = v2, v1
            adj[v1 - 1].append(v2)
        return adj

    def edge_exists(self, edge):
        """
        :param edge: A pair of positive integers denoting the edge.
        :return: A boolean whether the edge exists in the current structure
        """
        return edge in self.edge_list

    def add_edge(self, edge, color):
        """
        Insert one edge into the graph.
        :param edge: A pair of positive integers denoting the edge.
        :param color: The edge color, either 'r' or 'b'
        """
        if edge in self.edge_list:
            raise RuntimeError("The edge " + str(edge) + " already exists in the graph.")
        self.edge_list.append(edge)
        self.edge_coloring[edge] = color

    def remove_edge(self, edge):
        """
        Removes an edge from the data structure along with its color.
        :param edge: A pair of positive integers denoting the edge.
        """
        if edge not in self.edge_list:
            raise RuntimeError("The edge " + str(edge) + " doesn't exist in the graph.")
        self.edge_list.remove(edge)
        del self.edge_coloring[edge]

    def color_edges_monochromatic(self, color):
        """
        For convenience, overwrites the previous edge_coloring of this graph - make all edges the same color
        :param color: Either 'r' or 'b'
        """
        self.edge_coloring = {}
        for e in self.edge_list:
            self.edge_coloring[e] = color

    def get_visualization(self, ax=None):
        """
        Returns a Figure, Ax pair containing the graph visualization as an ordered graph. Red edges will appear on the
        top, blue ones on the bottom. Library networkx is used (with a slight change to support this behaviour).
        :param ax: If specified, it uses the ax to draw the visualization. If not, a new Figure object is created along
        with its ax.
        """
        if ax is None:
            fig = matplotlib.figure.Figure(figsize=(6, 3.5))
            ax = fig.add_subplot(111)
        ax.plot()

        G = nx.DiGraph()
        edge_colors = []
        for u, v in self.edge_list:
            G.add_edge(u, v)
        # Reusing the DiGraph self-made new edge ordering to supply the corresponding list of colors in correct order
        for u, v in G.edges:
            edge_colors.append(self.edge_coloring[(u, v)])
        G.add_nodes_from(range(1, self.size + 1))
        # Rad must be a minus value, elsewise the hack for inverting blue edges in nx_pylab.py won't work. The hack
        # the only change from the original networkx package.
        custom_connectionstyle = 'arc3, rad=-0.8'
        nx.draw_networkx(G, pos={vertex: (vertex - 1, 0) for vertex in range(1, self.size + 1)},
                         edge_color=edge_colors,
                         connectionstyle=custom_connectionstyle,
                         ax=ax)
        return ax.figure, ax

    def get_matrix_visualization(self, ax=None):
        """
        Returns a Figure, Ax pair containing the graph visualization as a red-blue matrix (non-existing edge is a white)
        :param ax: If specified, it uses the ax to draw the visualization. If not, a new Figure object is created along
        with its ax.
        """
        adj = np.zeros((self.size, self.size), dtype='uint8')
        for edge, color in self.get_colored_edge_list():
            i, j = edge
            adj[i - 1][j - 1] = 2 if color == 'r' else 1
        cmap = matplotlib.colors.ListedColormap(['white', 'blue', 'red'])
        bounds = [-1, 0.5, 1.5, 3]
        norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)

        if ax is None:
            fig = matplotlib.figure.Figure(figsize=(6, 3.7))
            ax = fig.add_subplot(111)
        ax.plot()

        ax.imshow(adj, interpolation='nearest', cmap=cmap, norm=norm)
        ax.set_xticks(np.arange(0, self.size, 1))
        ax.set_yticks(np.arange(0, self.size, 1))
        ax.set_xticklabels(np.arange(1, self.size + 1, 1))
        ax.set_yticklabels(np.arange(1, self.size + 1, 1))

        return ax.figure, ax

    @staticmethod
    def create_colored_graph_from_adj_list(adjacency_list, color):
        """
        For convenience - a method for creating monochromatic ColoredGraphs from adjacency lists.
        :param adjacency_list: A list of lists of integers.
        :param color: Either 'r' or 'b'
        :return: The ColoredGraph structure with the specified monochromatic graph.
        """
        edge_list = []
        for i in range(0, len(adjacency_list)):
            for j in range(0, len(adjacency_list[i])):
                edge_list.append((i + 1, adjacency_list[i][j]))
        colored_graph = ColoredGraph(len(adjacency_list), edge_list, {edge: color for edge in edge_list})
        return colored_graph
