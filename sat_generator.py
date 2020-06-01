import math


def encode_edge(i, j, n):
    """
    For a given edge i,j and graph size n returns a one integer encoding of this edge (used inside SAT solver).
    """
    if i > j:
        i, j = j, i
    return (i - 1) * n + (j - 1)


def decode_edge(num, n):
    """
    For a given edge encoding and graph size returns the edge it corresponded to.
    """
    mod = num % n
    return math.ceil(num / n), mod + 1


def next_number_with_same_num_of_bits(num):
    c = num & -num
    r = num + c
    return (((r ^ num) >> 2) // c) | r


def generate_all_k_subsets(n, k):
    mask = int((n - k) * '0' + k * '1', 2)
    last_mask = int(k * '1' + (n - k) * '0', 2)
    while True:
        yield mask
        if mask == last_mask:
            return
        mask = next_number_with_same_num_of_bits(mask)


def generate_general_ordered_sat_clause(mask, ordered_graph, original_graph_size, invert=False):
    """
    For ordered graphs, the clause is uniquely determined by the graph ordering and chosen vertices. We just need to
    relabel the subgraph and generate the desired clause for this one subset of vertices given by mask.
    :param mask: An integer mask specifying the set of vertices to be taken into account for the clause
    :param ordered_graph: Adjacency list specifying the graph
    """
    # relabeling the graph indices chosen by mask to fit the ordered graph indices
    i = 1
    label = 1
    label_mapping = {}
    while i <= mask:
        if i & mask:
            label_mapping[label] = i.bit_length()
            label += 1
        i <<= 1

    ordered_graph_size = len(ordered_graph)  # label should be actually equal to this
    clause = []
    for i in range(1, ordered_graph_size + 1):
        i_neighbours = ordered_graph[i - 1]
        for neighbour in i_neighbours:
            if i == neighbour:
                raise RuntimeError("Faulty graph, self-loop")
            x = i
            y = neighbour
            if x > y:
                x, y = y, x
            edge_encoding = encode_edge(label_mapping[x], label_mapping[y], original_graph_size)
            clause.append(edge_encoding if not invert else -edge_encoding)
    return clause


def generate_general_ordered_ramsey_sat(n, red_graph, blue_graph=None, enforce_symmetry=False, special_conditions=None):
    """
    Creates a SAT string expressing the given ordered ramsey problem for this diagonal case and 2 colours.

    :param red_graph, blue_graph: ColoredGraph structures. If blue_graph
    is None, we clone the red one and it is the diagonal case
    :param n: The size of the complete graph we wish to find the ordered subgraph in
    :param enforce_symmetry: If set to True, the variables are force to take symmetric values
    :param special_conditions: Other custom conditions can be set, the format is a list of "conditions", where every
    condition is of the form ((v1,v2), color), where v1 and v2 are vertices and color is either 'r' or 'b'
    :return: Corresponding SAT string, which can be fed into the SAT solver interface
    """
    cnf_clauses = []
    if blue_graph is None:
        blue_graph = red_graph
    red_size = len(red_graph)
    blue_size = len(blue_graph)
    if red_size > n or blue_size > n:
        raise ValueError("One of the graphs is bigger than K_n, this doesn't make sense.")
    if not red_graph.get_edge_list() or not blue_graph.get_edge_list():
        raise ValueError("One of the graphs has no edges, this doesn't make sense.")
    subset_masks = generate_all_k_subsets(n, k=red_size)
    for mask in subset_masks:
        cnf_clauses.append(generate_general_ordered_sat_clause(mask, red_graph.get_adjacency_list(),n))
    subset_masks = generate_all_k_subsets(n, k=blue_size)
    for mask in subset_masks:
        cnf_clauses.append(generate_general_ordered_sat_clause(mask, blue_graph.get_adjacency_list(),n, invert=True))
    if special_conditions is not None:
        for edge, color in special_conditions:
            i, j = edge
            cnf_clauses.append(enforce_special_condition_clause(n, i, j, color))
    if enforce_symmetry:
        cnf_clauses.extend(enforce_symmetry_clauses(n))
    return clause_list_to_sat_string(cnf_clauses)


# effective remove space?
def clause_to_sat_string(clause):
    """
    :param clause: An iterable expressing the SAT clause in the following format: []
    :return: string representation of this clause for the minisat interface
    """
    sat_strs = []
    for literal in clause:
        sat_strs.append('v' + str(literal) if literal > 0 else '-v' + str(-literal))
    return '(' + ' | '.join(sat_strs) + ')'


def clause_list_to_sat_string(cnf_clauses):
    sat_clauses_list = []
    for clause in cnf_clauses:
        sat_clauses_list.append(clause_to_sat_string(clause))
    return ' & '.join(sat_clauses_list)


def enforce_symmetry_edge_clauses(n, i, j):
    edge = encode_edge(i, j, n)
    symmetric_edge = encode_edge(n + 1 - j, n + 1 - i, n)
    return [edge, -symmetric_edge], [-edge, symmetric_edge]


def enforce_special_condition_clause(n, i, j, color):
    edge = encode_edge(i, j, n)
    return [edge if color == 'b' else -edge]


def enforce_symmetry_clauses(n):
    sat_clauses_list = []
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            if i + j == n + 1:
                continue
            cl1, cl2 = enforce_symmetry_edge_clauses(n, i, j)
            sat_clauses_list.append(cl1)
            sat_clauses_list.append(cl2)
    return sat_clauses_list
