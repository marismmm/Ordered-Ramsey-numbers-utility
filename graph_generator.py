from collections import deque
from itertools import permutations, chain, combinations


def powerset(iterable):
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))


class GraphGenerator:
    """
    Helper class for generating special classes of ordered graphs. The ordering is given by 1,2,....,n.
    They are generated as adjacency list (list of lists) and indexed from 1. NOT necessarily only i<j edges are present,
    but every edge can be present at most once.
    E.g.
    monotone path of length 3 is [[2],[3],[]]
    alternating path of length 4 is [[4],[3,4],[], []]
    alternating path of length 5 is [[5],[5,4],[4],[],[]]
    alternating path of length 6 is [[6],[6,5],[5,4],[], [],[]]
    monotone cycle of length 4 is [[2,4],[3],[4]]
    """

    @staticmethod
    def monotone_path(path_length):
        temp = [[x] for x in range(2, path_length + 1)]
        temp.append([])
        return temp

    @staticmethod
    def monotone_cycle(cycle_length):
        temp = GraphGenerator.monotone_path(cycle_length)
        temp[0].append(cycle_length)
        return temp

    @staticmethod
    def alternating_path(path_length):
        n = path_length - 1
        max = n + 1
        temp = []
        for i in range(0, (n - 1) // 2 + 1):
            temp.append([max - i])
        if n % 2 == 0:
            temp.append([])
        for i in range(1, n // 2 + 1):
            temp[i].append(max - i + 1)
        while len(temp) < path_length:
            temp.append([])

        return temp

    @staticmethod
    def rainbow(k):
        temp = []
        for i in range(0, k):
            temp.append([2 * k - i])
        while len(temp) < 2 * k:
            temp.append([])
        return temp

    @staticmethod
    def monotone_doublepath(path_length):
        temp = [[x, x + 1] for x in range(2, path_length)]
        temp.append([path_length])
        temp.append([])
        return temp

    @staticmethod
    def full(size):
        temp = []
        s = deque(range(2, size + 1))
        while len(s) > 0:
            temp.append(sorted(s))
            s.popleft()
        temp.append([])
        return temp

    @staticmethod
    def star(left, right):
        total = left + right - 1
        temp = [[] for _ in range(total)]
        for i in range(0, left - 1):
            temp[i].append(left)
        for i in range(left, total):
            temp[i].append(left)
        return temp

    @staticmethod
    def there_and_back_way(path_length):
        temp = [[x + 1] for x in range(2, path_length)]
        while len(temp) < path_length:
            temp.append([])
        temp[path_length - 2].append(path_length)
        return temp

    @staticmethod
    def all_paths(path_length):
        normalized_graphs = []
        for perm in permutations(range(1, path_length + 1)):
            temp = [[] for _ in range(path_length)]
            for i in range(path_length):
                for j in range(path_length):
                    if perm[j] == perm[i] + 1:
                        temp[i].append(j + 1)
            normalized_temp = normalize_graph(temp)
            if normalized_temp not in normalized_graphs:
                normalized_graphs.append(normalized_temp)
                yield temp

    @staticmethod
    def all_cycles(cycle_length):
        for perm in permutations(range(1, cycle_length + 1)):
            temp = [[] for _ in range(cycle_length)]
            for i in range(cycle_length):
                for j in range(cycle_length):
                    if perm[j] == perm[i] + 1:
                        temp[i].append(j + 1)
                    elif perm[i] == 1 and perm[j] == cycle_length:
                        temp[i].append(j + 1)
            yield temp

    @staticmethod
    def all_matchings(size):
        normalized_graphs = []
        for perm in permutations(range(1, size + 1)):
            temp = [[] for _ in range(size)]
            for i in range(0, len(perm) - 1, 2):
                temp[perm[i] - 1].append(perm[i + 1])
            normalized_temp = normalize_graph(temp)
            if normalized_temp not in normalized_graphs:
                normalized_graphs.append(normalized_temp)
                yield temp

    @staticmethod
    def all_graphs(size):
        possible_edges = [(i, j) for i in range(1, size + 1) for j in range(i + 1, size + 1)]
        all_possible_graphs = powerset(possible_edges)
        for edge_list in all_possible_graphs:
            temp = [[] for _ in range(size)]
            if len(edge_list) != 4:
                continue
            for edge in edge_list:
                i, j = edge
                if i > j:
                    i, j = j, i
                temp[i - 1].append(j)
            print(temp)
            yield temp


def normalize_graph(adj):
    new_graph = [[] for _ in range(len(adj))]
    for i in range(len(adj)):
        for n in adj[i]:
            new_graph[n - 1].append(i + 1)
            new_graph[i].append(n)
    for node in new_graph:
        node.sort()
    return new_graph
