from collections import deque, namedtuple
import networkx as nx
import matplotlib.pyplot as plt
from collections.abc import Hashable

def is_primitive_type (obj):
    return type(obj) in [int, float, bool, str, None]

def general_getter(obj, key):
    if isinstance(obj, dict):
        return obj[key]
    if isinstance(obj, list):
        return str(key)
    return getattr(obj, key)

def zoom(nested_object):
    dtype = type(nested_object)
    if dtype is dict:
        return list(nested_object.keys())
    return [k for k in dir(nested_object) if not k.startswith('__') and not callable(getattr(nested_object, k))]

class ExamineNestedObject:   
    def __init__ (self, nested_object, max_iter=1000):
        self.Node = namedtuple('Node', ['idx',  'name', 'parent','data_type'])
        self.max_iter = max_iter
        self.child_parent_pair = [self.Node(i, str(pair[0]), str(pair[1]), type(pair[0])) for i, pair in enumerate(self.__flatten__(nested_object=nested_object, max_iter=self.max_iter))]
        self.__all_nodes__ = [child.name for child in self.child_parent_pair]

    def __flatten__(self, nested_object, max_iter):
        stack = [(nested_object, key, 'root') for key in zoom(nested_object)]
        result = set()
        i = 0 
        while stack:
            current_obj, key, parent_name = stack.pop()
            if not isinstance(key, Hashable):
                result.add((str(key), parent_name))
            else:
                result.add((key, parent_name))
            content = general_getter(current_obj, key)
            if not is_primitive_type(content):
                for child_key in zoom(content):
                    stack.append((content, child_key, key))
            else:
                if not isinstance(key, Hashable):
                    result.add((str(key), parent_name))
                else:
                    result.add((content, key))
            i = i + 1
            if i == max_iter:
                raise RuntimeError(f"Max iter. = {max_iter} exceeded")
        return result
    
    def get_parent (self, idx):
        return self.child_parent_pair[idx].parent
    
    def fuzzy_find(self, query):
        query = str(query)
        return [choice for choice in self.child_parent_pair if query.lower() in str(choice.name).lower()]


    
    def find(self, query):
        for i, node in enumerate(self.child_parent_pair):
            if node.name == 'root':
                return 'root'
            if node.name == query:
                return node
        raise ValueError(f"FATAL: {query} not found. Check the string or use fuzzy find")

    def build_parent_chain (self, start_at_child):
        parent_queue = deque()
        parent_queue.appendleft(start_at_child)
        index_of_parent = self.find(parent_queue[0]).idx
        max_depth = len(self.child_parent_pair)
        i=0
        while True:
            parent = self.get_parent(index_of_parent)
            parent_queue.appendleft(parent)
            if parent == 'root':
                break
            index_of_parent = self.find(parent).idx
            i = i + 1
            if i == max_depth:            
                raise ValueError(f"FATAL: Max depth reached. This should never happen.\n{parent_queue}")
        return parent_queue
            
    def get_to (self, query, exact_match=False):
        if not exact_match:
            candidates = self.fuzzy_find(query)
        else:
            candidates = [self.find(query)]
        for candidate in candidates:
            print(f"--- {candidate} ---")
            print(self.build_parent_chain(candidate.name))
            print("\n")

    def plot(self):
        G = nx.DiGraph()
        G.add_edges_from((node.name, node.parent) for node in self.child_parent_pair)
        pos = nx.nx_agraph.graphviz_layout(G, prog="dot")
        nx.draw(G, pos, with_labels=True, arrows=False, node_size=0,
            font_size=8, font_family='monospace', edge_color='gray', width=0.5)
        plt.show()