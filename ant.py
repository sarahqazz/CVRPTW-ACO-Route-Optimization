from solution import Solution
import itertools
import bisect
import random

class Ant:
    def __init__(self, alpha, beta):
        """
        Initializes an Ant with its pheromone influence (alpha) and heuristic influence (beta).
        """
        self.alpha = alpha
        self.beta = beta
        self.graph = None  # Distance graph
        self.time_graph = None # Travel time graph
        self.n = None # Total number of nodes in the problem

    def tour(self, distance_graph, time_graph, num_vehicles_for_ant, start_node, 
             vehicle_capacity, demands, time_windows, service_times, available_customer_nodes):
        """
        Constructs a single route (solution) for a specific day in a CVRPTW problem.
        
        Args:
            distance_graph (networkx.Graph): The distance graph.
            time_graph (networkx.Graph): The travel time graph.
            num_vehicles_for_ant (int): This will always be 1, indicating one route to build.
            start_node (int): The starting node (depot).
            vehicle_capacity (float): Max capacity of the vehicle.
            demands (dict): Node demands.
            time_windows (dict): Node time windows.
            service_times (dict): Node service times.
            available_customer_nodes (list): A list of customer node IDs that this ant
                                            is allowed to visit for this specific route.

        Returns:
            Solution: A single Solution object, representing the constructed route.
                      Returns an infeasible solution (cost=inf) if no valid route can be formed.
        """
        self.graph = distance_graph
        self.time_graph = time_graph
        self.n = len(distance_graph.nodes) 

        # Create a single Solution object for the current route/day
        current_solution = Solution(distance_graph, time_graph, start_node, self,
                                    vehicle_capacity, demands, time_windows, service_times)

        # The ant only considers nodes from the 'available_customer_nodes' list
        # We need a mutable list to track nodes visited within *this* specific route.
        nodes_to_visit_in_this_route = list(available_customer_nodes)

        # Loop to build the single route until no more feasible nodes or list is empty
        while nodes_to_visit_in_this_route:
            current_node = current_solution.current_node

            # Get feasible next nodes for the current route
            # Filter nodes that are in 'nodes_to_visit_in_this_route' AND satisfy CVRPTW constraints for this route
            feasible_next_nodes = []
            for node in nodes_to_visit_in_this_route:
                is_feasible, _, _ = current_solution.can_add_node(node)
                if is_feasible:
                    feasible_next_nodes.append(node)

            if not feasible_next_nodes:
                # No more feasible nodes to add to this route
                break 

            # Choose the next destination based on pheromones and heuristics
            next_node = self.choose_destination(current_node, feasible_next_nodes)
            
            # Re-check feasibility and get times before adding the node
            # This check is technically redundant if choose_destination only selects from feasible_next_nodes,
            # but it adds robustness.
            is_feasible, arrival_time, service_start_time = current_solution.can_add_node(next_node)
            
            if not is_feasible: # Should not happen if feasible_next_nodes logic is correct
                # Fallback: remove it and try next iteration
                if next_node in nodes_to_visit_in_this_route:
                    nodes_to_visit_in_this_route.remove(next_node)
                continue 

            # Add the chosen node to the current solution/route
            current_solution.add_node(next_node, arrival_time, service_start_time)
            # Remove from the list for *this route*
            nodes_to_visit_in_this_route.remove(next_node) 
        
        # After building the route, ensure it returns to the depot
        # This will also calculate the final cost and update final_time/capacity
        current_solution.close()
        
        return current_solution

    def choose_destination(self, current, feasible_unvisited_nodes):
        """
        Chooses the next node based on pheromone and heuristic information.
        Only considers nodes that are feasible according to CVRPTW constraints.
        """
        if not feasible_unvisited_nodes:
            raise ValueError("No feasible unvisited nodes to choose from.")
        if len(feasible_unvisited_nodes) == 1:
            return feasible_unvisited_nodes[0]

        # Calculate scores only for feasible nodes
        scores = self.get_scores(current, feasible_unvisited_nodes)
        
        # If all scores are zero, pick a random feasible node as fallback
        if sum(scores) == 0:
            return random.choice(feasible_unvisited_nodes)

        return self.choose_node(feasible_unvisited_nodes, scores)
    
    def choose_node(self, candidates, scores):
        """
        Selects a node from candidates based on their scores using a roulette wheel selection.
        """
        total = sum(scores)
        if total == 0:
            return random.choice(candidates)
            
        cumdist = list(itertools.accumulate(scores))
        
        rand_val = random.random() * total
        index = bisect.bisect_left(cumdist, rand_val)
        
        return candidates[min(index, len(candidates) - 1)]
    
    def get_scores(self, current, candidates):
        """
        Calculates the score for each candidate node based on pheromone and heuristic.
        """
        scores = []
        for node in candidates:
            if (current, node) not in self.graph.edges:
                scores.append(0) 
                continue

            distance_edge_data = self.graph.edges[current, node]
            # time_edge_data = self.time_graph.edges[current, node] # Not directly used in heuristic currently

            weight = distance_edge_data.get('weight', 1)
            if weight == 0:
                heuristic_value = 1e9 #infinity
            else:
                heuristic_value = 1 / weight
            
            phe = distance_edge_data['pheromone'] 
            score = (phe ** self.alpha) * (heuristic_value ** self.beta)
            scores.append(score)
        return scores