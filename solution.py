import functools

@functools.total_ordering
class Solution:
    def __init__(self, graph, time_graph, start_node, ant=None, 
                 vehicle_capacity=None, demands=None, time_windows=None, service_times=None):
        """
        Initializes a Solution object representing a single route.

        Args:
            graph (networkx.Graph): The distance graph of the problem.
            time_graph (networkx.Graph): The travel time graph of the problem.
            start_node (int): The starting node (depot) for this route.
            ant (Ant, optional): The ant that constructed this solution. Defaults to None.
            vehicle_capacity (float, optional): The maximum capacity of the vehicle. Defaults to None.
            demands (dict, optional): Dictionary of node demands {node_id: demand_value}. Defaults to None.
            time_windows (dict, optional): Dictionary of time windows {node_id: (earliest_time, latest_time)}. Defaults to None.
            service_times (dict, optional): Dictionary of service times {node_id: service_time_value}. Defaults to None.
        """
        self.graph = graph  # Distance graph
        self.time_graph = time_graph # Travel time graph
        self.start_node = start_node
        self.ant = ant
        self.current_node = start_node # Current node the vehicle is at

        self.cost = 0  # Total distance of the route
        self.path = [] # List of edges (u, v) in the route

        self.nodes = [start_node] # List of nodes visited in order
        self.visited = {start_node} # Set of nodes visited for quick lookup

        # CVRPTW specific attributes
        self.vehicle_capacity = vehicle_capacity
        self.demands = demands
        self.time_windows = time_windows
        self.service_times = service_times
        
        # Initialize capacity and time for the current route
        self.current_capacity = 0 
        self.current_time = 0 

        # Record arrival and service start times for each node
        # For depot, arrival time is 0, service starts at its earliest time window
        self.arrival_times = {start_node: 0.0}
        self.service_start_times = {start_node: float(self.time_windows.get(start_node, (0, float('inf')))[0])}
        self.current_time = self.service_start_times[start_node] + self.service_times.get(start_node, 0)


    def __iter__(self):
        """Allows iteration over the edges in the path."""
        return iter(self.path)
    
    def __eq__(self, other):
        """Compares two Solution objects based on their total cost."""
        if not isinstance(other, Solution):
            return NotImplemented
        return self.cost == other.cost
    
    def __lt__(self, other):
        """Compares two Solution objects to determine if self has a lower cost. (Fixed typo from __it__)"""
        if not isinstance(other, Solution):
            return NotImplemented
        return self.cost < other.cost 
    
    def __contains__(self, item):
        """Checks if a node has been visited in this solution (route)."""
        return item in self.visited or item == self.current_node
    
    def __repr__(self):
        """Provides a string representation of the solution for debugging/display."""
        easy_id = self.get_easy_id(sep=' =>', monospace=False)
        return 'Route:\n{}km\t\t\t{}\nCapacity: {}/{}\tTime: {} (Arrival: {} Service: {})\n'.format(
            round(self.cost, 2), easy_id,
            self.current_capacity, self.vehicle_capacity,
            round(self.current_time, 2),
            ', '.join([f"{n}: {round(self.arrival_times.get(n, 0), 2)}" for n in self.nodes]),
            ', '.join([f"{n}: {round(self.service_start_times.get(n, 0), 2)}" for n in self.nodes])
        )
    
    def get_easy_id(self, sep=' ', monospace=True):
        """Formats the route path for easier reading."""
        nodes = [str(n) for n in self.get_id()]
        if monospace:
            size = max([len(n) for n in nodes]) if nodes else 0
            nodes = [n.rjust(size) for n in nodes]
        return sep.join(nodes)
    
    def get_id(self):
        """Returns a canonical representation of the route (e.g., for comparison)."""
        # Finds the smallest node ID in the route and rotates the path to start from it
        # Useful for comparing routes that are the same but started at different points.
        if not self.nodes:
            return tuple()
        first = min(self.nodes)
        index = self.nodes.index(first)
        return tuple(self.nodes[index:] + self.nodes[:index])
    
    def can_add_node(self, node):
        """
        Checks if a node can be added to the current route without violating CVRPTW constraints.
        Returns (True, arrival_time, service_start_time) if feasible, else (False, None, None).
        """
        if node in self.visited:
            return False, None, None # Node already visited in this route

        # 1. Capacity Constraint
        node_demand = self.demands.get(node, 0)
        if self.current_capacity + node_demand > self.vehicle_capacity:
            return False, None, None # Capacity exceeded

        # 2. Time Window Constraint
        travel_time = self.time_graph.edges[self.current_node, node]['time']
        service_time = self.service_times.get(node, 0)
        earliest_tw, latest_tw = self.time_windows.get(node, (0, float('inf')))

        arrival_time = self.current_time + travel_time
        
        # If arrives before earliest_tw, wait until earliest_tw
        service_start_time = max(arrival_time, earliest_tw)

        # If service starts after latest_tw, this path is infeasible
        if service_start_time > latest_tw:
            return False, None, None

        return True, arrival_time, service_start_time


    def add_node(self, node, arrival_time=None, service_start_time=None):
        """
        Adds a node to the current route and updates cost, capacity, and time.
        It's assumed that can_add_node was called first to validate.
        """
        if node in self.visited:
            raise ValueError(f"Node {node} already visited in this route.")

        # If arrival_time and service_start_time are not provided, calculate them (less efficient)
        # It's better to get them from can_add_node beforehand for efficiency
        if arrival_time is None or service_start_time is None:
            is_feasible, arrival_time, service_start_time = self.can_add_node(node)
            if not is_feasible:
                raise ValueError(f"Attempted to add an infeasible node {node}. Call can_add_node first.")

        edge = (self.current_node, node)
        
        # Update path and cost (distance)
        distance_data = self.graph.edges[edge]
        self.path.append(edge)
        self.cost += distance_data['weight']
        
        # Update CVRPTW specific attributes
        self.nodes.append(node)
        self.visited.add(node)
        self.current_capacity += self.demands.get(node, 0)
        
        # Update time
        self.arrival_times[node] = arrival_time
        self.service_start_times[node] = service_start_time
        self.current_time = service_start_time + self.service_times.get(node, 0)
        
        self.current_node = node # Move to the new current node

    def close(self):
        """
        Closes the route by returning to the start_node (depot).
        This method will also perform final checks for feasibility.
        """
        if self.current_node != self.start_node:
            # Check if returning to depot is feasible
            travel_time_to_depot = self.time_graph.edges[self.current_node, self.start_node]['time']
            depot_est, depot_lst = self.time_windows.get(self.start_node, (0, float('inf')))
            depot_service_time = self.service_times.get(self.start_node, 0)

            arrival_at_depot = self.current_time + travel_time_to_depot
            service_start_at_depot = max(arrival_at_depot, depot_est)

            # If arriving at depot too late, the route is infeasible
            if service_start_at_depot > depot_lst:
                # This route is not feasible. You might want to assign a very high cost
                # or handle it as an invalid route in the Ant/Solver.
                # For now, let's just make it very expensive.
                self.cost = float('inf') 
                self.current_time = float('inf') # Mark time as infinite for infeasible route
                print(f"Warning: Route {self.get_id()} infeasible due to late return to depot.")
                return

            # Add the edge back to depot
            edge_to_depot = (self.current_node, self.start_node)
            self.path.append(edge_to_depot)
            self.cost += self.graph.edges[edge_to_depot]['weight']
            
            # Update time
            self.arrival_times[self.start_node] = arrival_at_depot
            self.service_start_times[self.start_node] = service_start_at_depot
            self.current_time = service_start_at_depot + depot_service_time # Final time for the route

            self.current_node = self.start_node # Vehicle is back at depot