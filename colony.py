from ant import Ant
from solution import Solution # Ensure Solution is imported

class Colony:
    def __init__(self, alpha, beta):
        """
        Initializes an Ant Colony with common parameters for all ants.
        """
        self.alpha = alpha
        self.beta = beta
    
    # We add 'limit' (number of iterations for this day's optimization) and 'num_ants' (number of ants per iteration)
    def send_ants(self, distance_graph, time_graph, num_vehicles_for_ant, start_node,
                  vehicle_capacity, demands, time_windows, service_times, available_customer_nodes, limit, num_ants):
        """
        Sends multiple ants over a specified number of iterations to construct a single 
        best route for a specific day in the CVRPTW problem.
        
        Args:
            distance_graph (networkx.Graph): The distance graph with pheromones.
            time_graph (networkx.Graph): The travel time graph.
            num_vehicles_for_ant (int): Always 1 for this implementation (one route per ant).
            start_node (int): The starting node (depot).
            vehicle_capacity (float): Max capacity.
            demands (dict): Node demands.
            time_windows (dict): Node time windows.
            service_times (dict): Node service times.
            available_customer_nodes (list): Eligible customer nodes for this route.
            limit (int): Number of iterations for this daily optimization phase.
            num_ants (int): Number of ants to run in each iteration.

        Returns:
            Solution: The best single route found by any ant during all iterations for this day.
        """
        
        # We will track the single best solution found across all iterations for this day
        best_solution_today = None
        
        # We run the ACO process for 'limit' iterations for this specific day
        for iteration in range(limit):
            
            # List to store solutions found in this iteration
            current_iteration_solutions = []
            
            # Send 'num_ants' ants for this iteration
            for ant_id in range(num_ants):
                
                # 1. Create a new Ant instance
                ant = Ant(self.alpha, self.beta)
                
                # 2. Have the ant build a single route (tour)
                single_day_route = ant.tour(
                    distance_graph, 
                    time_graph, 
                    num_vehicles_for_ant, 
                    start_node, 
                    vehicle_capacity, 
                    demands, 
                    time_windows, 
                    service_times,
                    available_customer_nodes
                )
                
                # 3. Store feasible solutions from this ant
                # We check if cost is not float('inf') to ensure it's a valid solution
                if single_day_route.cost != float('inf'):
                    current_iteration_solutions.append(single_day_route)

            # 4. Find the best solution in this iteration (optional, useful for logging)
            # if current_iteration_solutions:
            #     best_solution_in_iteration = min(current_iteration_solutions, key=lambda x: x.cost)

            # 5. Update the overall best solution for the day
            if current_iteration_solutions:
                # Find the best solution among all ants in this iteration
                best_in_iteration = min(current_iteration_solutions, key=lambda x: x.cost)
                
                if best_solution_today is None or best_in_iteration.cost < best_solution_today.cost:
                    best_solution_today = best_in_iteration
            
            # NOTE: Pheromone update (evaporation and deposition) is handled by Solver.global_update() 
            # after this function returns the best solution for the day. 

        # Return the best solution found after all 'limit' iterations for this day.
        return best_solution_today