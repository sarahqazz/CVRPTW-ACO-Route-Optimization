import networkx as nx

def parse_cvrptw_data(filepath):
    data = {}
    with open(filepath, 'r') as f:
        section = None
        node_coords = {}
        demands = {}
        time_windows = {}
        service_times = {}
        distance_matrix = []
        time_matrix = []

        for line in f:
            line = line.strip()
            if not line:
                continue
            if line == "EOF":
                break

            if "DIMENSION" in line:
                data['DIMENSION'] = int(line.split(":")[1].strip())
            elif "VEHICLE_CAPACITY" in line:
                # KAMI ASUMSIKAN KAPASITAS KENDARAAN JUGA BISA DESIMAL JIKA DEMAND-NYA DESIMAL
                data['VEHICLE_CAPACITY'] = float(line.split(":")[1].strip()) 
            elif "NUM_VEHICLES" in line:
                data['NUM_VEHICLES'] = int(line.split(":")[1].strip())
            elif "INITIAL_PHEROMONE" in line:
                data['INITIAL_PHEROMONE'] = float(line.split(":")[1].strip())
            elif "NODE_COORD_SECTION" in line:
                section = "NODE_COORD_SECTION"
            elif "DEMAND_SECTION" in line:
                section = "DEMAND_SECTION"
            elif "TIME_WINDOW_SECTION" in line:
                section = "TIME_WINDOW_SECTION"
            elif "SERVICE_TIME_SECTION" in line:
                section = "SERVICE_TIME_SECTION"
            elif "EDGE_WEIGHT_SECTION" in line:
                section = "EDGE_WEIGHT_SECTION"
            elif "TRAVEL_TIME_SECTION" in line:
                section = "TRAVEL_TIME_SECTION"
            elif section:
                parts = line.split()
                if not parts:
                    continue
                try:
                    if section == "NODE_COORD_SECTION":
                        node_coords[int(parts[0])] = (float(parts[1]), float(parts[2]))
                    elif section == "DEMAND_SECTION":
                        # PERUBAHAN DI SINI: UBAH KE FLOAT UNTUK DEMAND DENGAN KOMA
                        demands[int(parts[0])] = float(parts[1]) 
                    elif section == "TIME_WINDOW_SECTION":
                        time_windows[int(parts[0])] = (float(parts[1]), float(parts[2]))
                    elif section == "SERVICE_TIME_SECTION":
                        service_times[int(parts[0])] = float(parts[1])
                    elif section == "EDGE_WEIGHT_SECTION":
                        distance_matrix.append([float(x) for x in parts])
                    elif section == "TRAVEL_TIME_SECTION":
                        time_matrix.append([float(x) for x in parts])
                except ValueError as e:
                    raise ValueError(f"Error parsing line '{line}' in section {section}: {e}. Check data type (int/float) or format.")

    data['node_coords'] = node_coords
    data['demands'] = demands
    data['time_windows'] = time_windows
    data['service_times'] = service_times

    dist_graph = nx.DiGraph()
    time_graph = nx.DiGraph()

    num_nodes = data['DIMENSION']
    for i in range(num_nodes):
        for j in range(num_nodes):
            dist_graph.add_edge(i + 1, j + 1, weight=distance_matrix[i][j])
            time_graph.add_edge(i + 1, j + 1, time=time_matrix[i][j])

    data['distance_graph'] = dist_graph
    data['time_graph'] = time_graph

    if len(node_coords) != num_nodes or len(demands) != num_nodes or \
       len(time_windows) != num_nodes or len(service_times) != num_nodes:
       raise ValueError("Data sections do not match DIMENSION.")
    if len(distance_matrix) != num_nodes or len(time_matrix) != num_nodes:
        raise ValueError("Matrix dimensions do not match DIMENSION.")
    
    return data