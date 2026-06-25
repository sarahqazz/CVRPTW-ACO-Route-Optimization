import tkinter as tk
from tkinter.constants import INSERT
from tkinter.filedialog import askopenfilename
import matplotlib.pyplot as plt
import networkx as nx
import tkinter.messagebox as messagebox
import matplotlib.backends.backend_tkagg as tkagg
import numpy as np
from problem import parse_cvrptw_data 
from colony import Colony
from solver import Solver
from solution import Solution 


problem_data = None

def load_file():
    global problem_data
    filepath = askopenfilename(
        filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
    )
    if not filepath:
        return
    
    try:
        problem_data = parse_cvrptw_data(filepath)
        fpath.delete(0, tk.END)
        fpath.insert(tk.END, filepath)
        window.title(f"Ant Colony Optimization for CVRPTW - Loaded {filepath}")

        if 'INITIAL_PHEROMONE' in problem_data:
            initial_pheromone_entry.delete(0, tk.END)
            initial_pheromone_entry.insert(tk.END, str(problem_data['INITIAL_PHEROMONE']))
        if 'ALPHA' in problem_data:
            nalpha.delete(0, tk.END)
            nalpha.insert(tk.END, str(problem_data['ALPHA']))
        if 'BETA' in problem_data:
            nbeta.delete(0, tk.END)
            nbeta.insert(tk.END, str(problem_data['BETA']))
        if 'RHO' in problem_data:
            nrho.delete(0, tk.END)
            nrho.insert(tk.END, str(problem_data['RHO']))

    except Exception as e:
        messagebox.showerror("Error", f"Gagal memuat atau memproses file: {e}")

def plot_solution(daily_solutions):
    fig, ax = plt.subplots()
    ax.set_title(f"Solusi Rute Harian (Total Hari: {len(daily_solutions)})")
    
    # Plot depot (Node 1)
    depot_coords = problem_data['node_coords'][1]
    ax.plot(depot_coords[0], depot_coords[1], 's', color='black', markersize=10, label='Gudang bahan baku (Node 1)')

    # Plot customer nodes
    for node_id, coords in problem_data['node_coords'].items():
        if node_id != 1:
            ax.plot(coords[0], coords[1], 'o', color='blue', markersize=5)
            ax.text(coords[0], coords[1], str(node_id), fontsize=8, ha='right')

    # Plot routes for each day
    colors = plt.cm.rainbow(np.linspace(0, 1, len(daily_solutions)))
    
    for day_idx, solution in enumerate(daily_solutions):
        if solution.cost == float('inf'):
            continue # Skip infeasible solutions

        route_nodes = list(solution.nodes)

        if route_nodes and route_nodes[-1] != 1:
            route_nodes.append(1)
        
        # Plot the path
        x_coords = [problem_data['node_coords'][node][0] for node in route_nodes]
        y_coords = [problem_data['node_coords'][node][1] for node in route_nodes]
        
        ax.plot(x_coords, y_coords, color=colors[day_idx], linestyle='-', marker='o', 
                label=f'Hari {day_idx + 1} (Jarak: {solution.cost:.2f} km)')

    ax.legend(loc='best')
    ax.grid(True)
    
    # Display the plot in the Tkinter window
    canvas = tkagg.FigureCanvasTkAgg(fig, master=fr_plot)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    # Add a toolbar
    toolbar = tkagg.NavigationToolbar2Tk(canvas, fr_plot)
    toolbar.update()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

def clear_plot():
    for widget in fr_plot.winfo_children():
        widget.destroy()

def display_results(daily_best_solutions):
    # Clear previous plot
    clear_plot()

    # Display results in the text area
    result_text.delete("1.0", tk.END)
    
    if not daily_best_solutions:
        result_text.insert(tk.END, "Tidak ada solusi yang ditemukan.\n")
        return

    result_text.insert(tk.END, f"--- Hasil Optimasi CVRPTW ---\n")
    result_text.insert(tk.END, f"Total Hari yang Dibutuhkan: {len(daily_best_solutions)}\n\n")
    
    total_cost = 0
    
    for idx, solution in enumerate(daily_best_solutions):
        if solution.cost != float('inf'):
            result_text.insert(tk.END, f"Hari {idx + 1}:\n")
            result_text.insert(tk.END, f"  Jarak Rute: {solution.cost:.2f} km\n")
            result_text.insert(tk.END, f"  Kapasitas Terpakai: {solution.current_capacity:.2f}\n")
            result_text.insert(tk.END, f"  Rute: {' -> '.join(map(str, solution.nodes))} -> 1\n")
            result_text.insert(tk.END, f"  Waktu Kedatangan: {solution.arrival_times}\n")
            result_text.insert(tk.END, f"  Waktu Mulai Layanan: {solution.service_start_times}\n")
            result_text.insert(tk.END, f"  Waktu Kembali ke Depot: {solution.current_time:.2f}\n\n")
            total_cost += solution.cost

        else:
            result_text.insert(tk.END, f"Hari {idx + 1}: Tidak ada solusi feasible ditemukan.\n\n")

    result_text.insert(tk.END, f"Total Jarak Keseluruhan: {total_cost:.2f} km\n")

    # Plot the solution
    plot_solution(daily_best_solutions)

def evalf():
    global problem_data
    
    try:
        # Mengambil parameter dari input GUI
        alpha = float(nalpha.get())
        beta = float(nbeta.get())
        rho = float(nrho.get())
        limit = int(niter.get()) # Jumlah Iterasi
        
        # Mengambil Jumlah Semut dari input GUI (nsemut)
        num_ants = int(nants.get()) 

        # Mengambil Feromon Awal
        initial_pheromone_value = float(initial_pheromone_entry.get())
        
        # Cek apakah data sudah dimuat
        if problem_data is None:
            messagebox.showerror("Error", "Data masalah belum dimuat. Silakan gunakan tombol 'Masukkan Data' terlebih dahulu.")
            return

        # Ambil data dari problem_data
        distance_graph = problem_data['distance_graph']
        time_graph = problem_data['time_graph']
        demands = problem_data['demands']
        time_windows = problem_data['time_windows']
        service_times = problem_data['service_times']
        vehicle_capacity = problem_data['VEHICLE_CAPACITY']
        start_node = 1  # Depot
        
        # Dapatkan daftar semua node pelanggan kecuali depot (Node 1)
        all_customer_nodes = [node for node in distance_graph.nodes if node != start_node]

        # Inisialisasi Solver dan Colony
        # Kita menggunakan Q=1 sesuai data_cvrptw_gemini.txt
        solver = Solver(rho=rho, Q=1) 
        colony = Colony(alpha=alpha, beta=beta)

        # Panggil solver.solve() dengan parameter baru
        # Jumlah Hari (num_days) tidak lagi diteruskan. Solver akan berjalan sampai semua pelanggan terlayani.
        daily_best_solutions = solver.solve(
            distance_graph=distance_graph,
            time_graph=time_graph,
            demands=demands,
            time_windows=time_windows,
            service_times=service_times,
            colony=colony,
            limit=limit,
            num_ants=num_ants, # Parameter baru: Jumlah Semut
            start=start_node,
            vehicle_capacity=vehicle_capacity,
            all_customer_nodes=all_customer_nodes,
            initial_pheromone_value=initial_pheromone_value
        )
        
        # Tampilkan hasil solusi
        display_results(daily_best_solutions)
        
    except ValueError as e:
        messagebox.showerror("Error", f"Pastikan input numerik benar (Alpha, Beta, Rho, Iterasi, Jumlah Semut): {e}")
    except Exception as e:
        messagebox.showerror("Error", f"Terjadi kesalahan saat menjalankan ACO: {e}")

# --- Setup GUI ---
window = tk.Tk()
window.title("Ant Colony Optimization for CVRPTW")

# Main frame untuk input dan tombol
fr_buttons = tk.Frame(window, relief=tk.RAISED, bd=2)
fr_buttons.grid(row=0, column=0, sticky="ns")

# Frame untuk plot hasil
fr_plot = tk.Frame(window)
fr_plot.grid(row=0, column=1, sticky="nsew")

# Frame untuk hasil teks
fr_results = tk.Frame(window)
fr_results.grid(row=1, column=0, columnspan=2, sticky="ew")

# Konfigurasi grid untuk frame plot agar bisa diresize
window.grid_columnconfigure(1, weight=1)
window.grid_rowconfigure(0, weight=1)

# Labels and Inputs
lb_alpha = tk.Label(fr_buttons, text="Alpha")
lb_beta = tk.Label(fr_buttons, text="Beta")
lb_rho = tk.Label(fr_buttons, text="Rho")
lb_ants = tk.Label(fr_buttons, text="Jumlah Semut") # Label baru untuk Jumlah Semut
lb_iter = tk.Label(fr_buttons, text="Iterasi")
bt_load = tk.Button(fr_buttons, text="Masukkan Data", command=load_file)
bt_solve = tk.Button(fr_buttons, text="Cari Solusi", command=evalf)
lb_initial_pheromone = tk.Label(fr_buttons, text="Feromon Awal") 
lb_filepath = tk.Label(fr_buttons, text="File Path:")

nalpha = tk.Entry(fr_buttons)
nbeta = tk.Entry(fr_buttons) 
nrho = tk.Entry(fr_buttons)
nants = tk.Entry(fr_buttons) 
niter = tk.Entry(fr_buttons)
fpath = tk.Entry(fr_buttons)
initial_pheromone_entry = tk.Entry(fr_buttons)

# Default values
nalpha.insert(0,"")
nbeta.insert(0,"") 
nrho.insert(0,"")
nants.insert(0,"")  
niter.insert(0,"") 
fpath.insert(0,"")
initial_pheromone_entry.insert(0,"") 

# Positioning elements in the grid
lb_filepath.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
fpath.grid(row=0, column=1, padx=5, columnspan=3, sticky="ew")
bt_load.grid(row=0, column=4, padx=5, pady=5)

lb_alpha.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
nalpha.grid(row=1, column=1, padx=5)

lb_beta.grid(row=1, column=2, sticky="ew", padx=5, pady=5)
nbeta.grid(row=1, column=3, padx=5)

lb_rho.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
nrho.grid(row=2, column=1, padx=5)

lb_iter.grid(row=2, column=2, sticky="ew", padx=5, pady=5)
niter.grid(row=2, column=3, padx=5)

lb_ants.grid(row=3, column=0, sticky="ew", padx=5, pady=5)
nants.grid(row=3, column=1, padx=5)

lb_initial_pheromone.grid(row=3, column=2, sticky="ew", padx=5, pady=5)
initial_pheromone_entry.grid(row=3, column=3, padx=5)

bt_solve.grid(row=4, column=0, columnspan=4, sticky="ew", padx=5, pady=10)

# Text area for results
result_text = tk.Text(fr_results, height=15, width=80)
result_text.pack(expand=True, fill=tk.BOTH)

# Start the Tkinter event loop
if __name__ == "__main__":
    window.mainloop()