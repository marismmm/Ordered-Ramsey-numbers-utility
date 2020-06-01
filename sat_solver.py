import sys
from subprocess import call
from tempfile import NamedTemporaryFile

from satispy.io import DimacsCnf
from satispy import CnfFromString


def write_dimacs_input_file(satispy_cnf_expression, file_name):
    """
    Writes the Satispy_cnf_expression as a DIMACS formatted file. This means a forces conversion from our variables
    to other ordering (from 1 to #number of variables). Therefore we return the mapping from the new variables to our.
    :return: A dictionary of the form {int: int} converting the SAT variables to our former variables
    """
    io = DimacsCnf()
    file_name.write(io.tostring(satispy_cnf_expression))
    file_name.flush()
    return {int(k): int(str(v)[1:]) for k, v in io.varobj_dict.items()}


def read_dimacs_output_file(file_name):
    """
    Reads the DIMACS formatted output file
    :return: A mapping from SAT variables to their values
    """
    lines = file_name.readlines()

    variable_mapping = {}

    for line in lines:
        if line in ["SAT", "UNSAT", "SATISFIABLE", "UNSATISFIABLE"]:
            continue
        variable_tokens = line.split(" ")[:-1]
        for v in variable_tokens:
            v = v.strip()
            value = v[0] != '-'
            v = v.lstrip('-')
            variable_mapping[int(v)] = value

    return variable_mapping


class SatFormulaSolver:
    """
    Abstract class enforcing an interface for SAT Solver tools
    """

    def __init__(self, sat_string):
        """
        :param sat_string: A SAT string of the form "(v1 | v2) & (-v3 | ...)"
        """
        self.sat_string = sat_string
        self.stopped_searching = False
        self.satispy_cnf_expression, _ = CnfFromString.create(sat_string)

    def find_next_solution(self):
        """
        Finds a solution for the given SAT string. If there is no new solution (or no solution), returns None
        :return: A mapping between variables and their values, or None if no new solution is found
        """
        pass
        """
        Could look like this:
        
        if self.stopped_searching:
            return None

        infile = NamedTemporaryFile(mode='w')
        outfile = NamedTemporaryFile(mode='r')

        var_map = write_dimacs_input_file(self.satispy_cnf_expression, infile)

        ret = call(SAT_SOLVER_COMMAND % (infile.name, outfile.name), shell=True)
        infile.close()

        if NO_SOLUTION_FOUND:
            self.stopped_searching = True
            return None

        resulting_sat_mapping = read_dimacs_output_file(outfile)
        # Convert the mapping to our graph values beforehand
        resulting_mapping = {}
        for k, v in resulting_sat_mapping.items():
            resulting_mapping[var_map[k]] = v
        # Close deletes the tmp files
        outfile.close()
        if NO_INNATE_SUPPORT_FOR_NEXT_SOLUTIONS_IN_THE_SAT_SOLVER:
            self.forbid_given_solution_sat_string(resulting_mapping)
        return resulting_mapping
        """


class MinisatSatFormulaSolver(SatFormulaSolver):
    def find_next_solution(self):
        """
        Finds a solution for the given SAT string. If there is no new solution (or no solution), returns None
        :return: A mapping between variables and their values, or None if no new solution is found
        """
        if self.stopped_searching:
            return None

        infile = NamedTemporaryFile(mode='w')
        outfile = NamedTemporaryFile(mode='r')

        var_map = write_dimacs_input_file(self.satispy_cnf_expression, infile)

        ret = call(('minisat %s %s > ' + ('NUL' if sys.platform == 'win32' else '/dev/null')) %
                   (infile.name, outfile.name), shell=True)
        infile.close()

        if ret != 10:
            self.stopped_searching = True
            return None

        resulting_sat_mapping = read_dimacs_output_file(outfile)
        # Convert the mapping to our graph values beforehand
        resulting_mapping = {}
        for k, v in resulting_sat_mapping.items():
            resulting_mapping[var_map[k]] = v
        # Close deletes the tmp files
        outfile.close()

        self.forbid_given_solution_sat_string(resulting_mapping)
        return resulting_mapping

    def forbid_given_solution_sat_string(self, mapping):
        """
        Appends a clause which forbids a given sat_string, so that new solutions are found. Unfortunately, Minisat
        solver probably doesn't just support this "find next solution" function by itself.
        :param mapping: A dict of int:bool denoting the values for every symbol.
        """
        literal_list = []
        for symbol_name, value in mapping.items():
            literal = ("v" if not value else "-v") + str(symbol_name)
            literal_list.append(literal)
        self.sat_string += ' & (' + ' | '.join(literal_list) + ')'
        self.satispy_cnf_expression, _ = CnfFromString.create(self.sat_string)


# TODO test this somehow more... basically the same as for Minisat
class GlucoseSatFormulaSolver(SatFormulaSolver):
    def find_next_solution(self):
        """
        Finds a solution for the given SAT string. If there is no new solution (or no solution), returns None
        :return: A mapping between variables and their values, or None if no new solution is found
        """
        if self.stopped_searching:
            return None

        infile = NamedTemporaryFile(mode='w')
        outfile = NamedTemporaryFile(mode='r')

        var_map = write_dimacs_input_file(self.satispy_cnf_expression, infile)

        ret = call(('glucose %s %s > ' + ('NUL' if sys.platform == 'win32' else '/dev/null')) %
                   (infile.name, outfile.name), shell=True)
        infile.close()

        if ret != 10:
            self.stopped_searching = True
            return None

        resulting_sat_mapping = read_dimacs_output_file(outfile)
        # Convert the mapping to our graph values beforehand
        resulting_mapping = {}
        for k, v in resulting_sat_mapping.items():
            resulting_mapping[var_map[k]] = v
        # Close deletes the tmp files
        outfile.close()

        self.forbid_given_solution_sat_string(resulting_mapping)
        return resulting_mapping

    def forbid_given_solution_sat_string(self, mapping):
        """
        Probably not needed here, but need to find out more about Glucose
        """
        literal_list = []
        for symbol_name, value in mapping.items():
            literal = ("v" if not value else "-v") + str(symbol_name)
            literal_list.append(literal)
        self.sat_string += ' & (' + ' | '.join(literal_list) + ')'
        self.satispy_cnf_expression, _ = CnfFromString.create(self.sat_string)
