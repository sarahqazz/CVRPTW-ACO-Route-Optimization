import networkx as nx
import math
import random
from solution import Solution
from colony import Colony # Import Colony if not already imported in the original file

class Solver:
    def __init__(self, rho=0.5, Q=100):
        """
        Initializes the ACO Solver with evaporation rate (rho) and pheromone constant (Q).
        """
        self.rho = rho
        self.Q = Q
        
        # Initialize attributes that will be set during the solve method
        self.colony = None
        self.distance_graph = None
        self.time_graph = None
        self.demands = None
        self.time_windows = None
        self.service_times = None
        self.vehicle_capacity = None
        self.start_node = None
        self.limit = None
        self.num_ants = None
        self.globally_unvisited_customer_nodes = set()

    # NOTE: We remove num_days from the parameters since the number of days is now determined dynamically.
    def solve(self, distance_graph, time_graph, demands, time_windows, service_times, colony, limit, num_ants, start, vehicle_capacity, all_customer_nodes, initial_pheromone_value):
        """
        Main solving method for CVRPTW using ACO. The solver runs until all customers
        are served.
        
        Args:
            distance_graph (networkx.Graph): The distance graph with pheromone levels.
            time_graph (networkx.Graph): The travel time graph.
            demands (dict): Customer demands.
            time_windows (dict): Customer time windows.
            service_times (dict): Customer service times.
            colony (Colony): The ACO Colony instance.
            limit (int): Number of iterations per day.
            num_ants (int): Number of ants to send per iteration.
            start (int): The depot node ID (usually 1).
            vehicle_capacity (float): Max vehicle capacity.
            all_customer_nodes (list): List of all customer nodes (excluding depot).
            initial_pheromone_value (float): Initial pheromone value for all edges.
        """
        
        self.colony = colony 
        self.distance_graph = distance_graph
        self.time_graph = time_graph
        self.demands = demands
        self.time_windows = time_windows
        self.service_times = service_times
        self.vehicle_capacity = vehicle_capacity
        self.start_node = start
        self.limit = limit
        self.num_ants = num_ants
        
        # Initialize pheromone levels for all edges
        for u, v in self.distance_graph.edges:
            self.distance_graph.edges[u, v]['pheromone'] = initial_pheromone_value

        # Keep track of customers visited across all days
        self.globally_unvisited_customer_nodes = set(all_customer_nodes)
        
        daily_best_solutions = []
        day_idx = 0 # Track the current day

        # Main loop: Continue optimization until all customers are visited
        while self.globally_unvisited_customer_nodes:
            print(f"--- Optimasi Hari {day_idx + 1} ---")
            
            # The available nodes for this day are those not yet visited globally.
            available_customer_nodes_today = list(self.globally_unvisited_customer_nodes)
            
            # --- ACO Optimization for the current day ---
            # Call the colony to run the ACO iterations and find the best route for this day's customers.
            # colony.send_ants() will now handle 'limit' iterations and 'num_ants' ants, 
            # returning the best solution found for this day.
            daily_best_solution = self.colony.send_ants(
                distance_graph=self.distance_graph, 
                time_graph=self.time_graph, 
                num_vehicles_for_ant=1, # We still build one route at a time (per ant) for CVRPTW
                start_node=self.start_node, 
                vehicle_capacity=self.vehicle_capacity, 
                demands=self.demands, 
                time_windows=self.time_windows, 
                service_times=self.service_times, 
                available_customer_nodes=available_customer_nodes_today,
                limit=self.limit,  # Total iterations for this day's optimization
                num_ants=self.num_ants # Total ants for this day's optimization
            )
            
            # --- Check and process the best solution found for the day ---
            if daily_best_solution and daily_best_solution.cost != float('inf'):
                # We found a feasible route for this day.
                print(f"Hari {day_idx + 1}: Solusi rute terbaik ditemukan. Jarak: {daily_best_solution.cost:.2f} km")
                
                # Apply pheromone update based on the best solution found for this day.
                self.global_update(self.distance_graph, daily_best_solution)

                # Store the solution for this day
                daily_best_solutions.append(daily_best_solution)

                # Update the set of globally unvisited customers.
                # Ensure we only remove customer nodes, not the depot (Node 1).
                nodes_in_solution = [node for node in daily_best_solution.nodes if node != self.start_node]
                self.globally_unvisited_customer_nodes -= set(nodes_in_solution)

                print(f"Pelanggan yang tersisa: {len(self.globally_unvisited_customer_nodes)}")
                
                # Move to the next day
                day_idx += 1
            else:
                # If no feasible solution is found for the remaining customers, stop.
                print(f"Hari {day_idx + 1}: Tidak ada solusi feasible ditemukan untuk pelanggan yang tersisa. Menghentikan optimasi.")
                # If there are remaining unserved customers but no feasible route was found for them, 
                # we can break the loop.
                break 

        # Return the solutions for all days until the problem was solved or stopped.
        return daily_best_solutions

    def global_update(self, distance_graph, best_solution):
        """
        Applies pheromone evaporation and deposition based on the best solution.
        """
        # Evaporation
        for u, v in distance_graph.edges:
            distance_graph.edges[u, v]['pheromone'] *= (1 - self.rho)
            
        # Deposition (only by the best solution)
        if best_solution is not None and best_solution.cost != 0 and best_solution.cost != float('inf'):
            # Ensure cost is not zero or infinite to avoid division by zero
            pheromone_deposit = self.Q / best_solution.cost
            for u, v in best_solution.path:
                if (u, v) in distance_graph.edges: # Check if edge exists
                    distance_graph.edges[u, v]['pheromone'] += pheromone_deposit