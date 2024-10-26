import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from scipy.interpolate import interp1d
import numpy as np

def extract_numeric_part(filename):
    """Extract the numeric part after the last dot in the filename."""
    return float(filename.split('.')[-1])

def process_csv_folders(folder_paths):
    """Process CSV files in the specified folders."""
    all_data = {}

    ##### CAMBIOS DE UNIDADES #####
    lbf_a_N = 4.44822  # Pounds to Newtons
    fts_a_ms = 0.3048  # Feet to meters
    
    raiz_sigma_1700ft = ((1 - 22.558 * 10**-6 * 1700) ** 4.2559) ** (1 / 2)
    raiz_sigma_13000ft = ((1 - 22.558 * 10**-6 * 13000) ** 4.2559) ** (1 / 2)
    Tas_Eas_1700ft = fts_a_ms * raiz_sigma_1700ft
    Tas_Eas_13000ft = fts_a_ms * raiz_sigma_13000ft

    for folder_path in folder_paths:
        # Dictionary to store last values for each folder
        data = {}

        # Iterate over all files in the folder
        for filename in os.listdir(folder_path):
            if filename.endswith(".csv"):
                file_path = os.path.join(folder_path, filename)
                try:
                    # Read the CSV file
                    df = pd.read_csv(file_path)
               
                    # Check if the second column exists
                    if df.shape[1] > 1:
                        # Extract the last value from the second column
                        last_value = df.iloc[-1, 1]  # Index 1 refers to the second column
                        file_base_name = os.path.splitext(filename)[0]
                        data[file_base_name] = last_value
                    else:
                        print(f"File {filename} does not have a second column.")
                except Exception as e:
                    print(f"Error reading {filename}: {e}")

        # Convert the dictionary to a DataFrame for the current folder
        result_df = pd.DataFrame(list(data.items()), columns=['FileName', 'LastValue'])

        # Check if DataFrame is empty
        if result_df.empty:
            print(f"No valid data found in folder {folder_path}.")
            continue
        
        # Extract numeric part from file names for sorting
        result_df['NumericPart'] = result_df['FileName'].apply(extract_numeric_part)

        # Convert values
        v_true = result_df['NumericPart'] * fts_a_ms  # True airspeed in m/s
        drag = result_df['LastValue'] * lbf_a_N       # Drag in Newtons
        Potencia_necesaria = v_true * drag / 1000           # Power in KWatts
        
        # Add columns to the DataFrame
        result_df['NumericPart'] *= fts_a_ms               # Convert to m/s EAS
        result_df['Drag_N'] = drag                         # Drag in Newtons
        result_df['Potencia_necesaria'] = Potencia_necesaria  # Power in KWatts

        print(result_df)

        # Store DataFrame with folder name as suffix
        all_data[folder_path] = result_df

    return all_data

def plot_data(folder_paths, output_file, graph_file):
    """Process datasets from multiple folders and plot them on the same graph."""
    # Process all folders
    all_dfs = process_csv_folders(folder_paths)

    # Merge DataFrames for plotting
    merged_df = None
    for folder, df in all_dfs.items():
        if merged_df is None:
            merged_df = df
        else:
            merged_df = pd.merge(merged_df, df, on='NumericPart', suffixes=('', f'_{os.path.basename(folder)}'))

    # Check if merged DataFrame is valid
    if merged_df is None or merged_df.empty:
        print("No valid merged data found. Exiting.")
        return

    # Sort the merged DataFrame based on 'NumericPart'
    merged_df.sort_values(by='NumericPart', inplace=True)

    # Save merged results to an Excel file
    merged_df.to_excel(output_file, index=False)
    print(f"Output file '{output_file}' generated successfully.")

    # Plot the data
    plt.figure(figsize=(10, 6))

    # Plot each dataset on the same graph
    for folder, df in all_dfs.items():
        # Sort each dataset before plotting
        df = df.sort_values(by='NumericPart')
        
        # Interpolate values for smoother plotting
        x = df['NumericPart']
        y = df['Potencia_necesaria']
        
        # Create an interpolating function
        interp_func = interp1d(x, y, kind='cubic', fill_value="extrapolate")
        
        # Generate more points for a smooth curve
        x_interp = np.linspace(x.min(), x.max(), 500)
        y_interp = interp_func(x_interp)

        label = f'Power ({os.path.basename(folder)})'
        plt.plot(x_interp, y_interp, label=label)  # Plot the interpolated line
        plt.scatter(x, y, marker='o', label=f'Data points {os.path.basename(folder)}', alpha=0.6)  # Plot original data points

    # Adding labels, title, and legend
    plt.xlabel('Speed TAS (m/s)')
    plt.ylabel('Power (KW)')
    plt.title('Power vs Speed Comparison')
    plt.legend(loc='best')

    # Set up the grid with specified intervals
    plt.grid(visible=True, which='both', color='gray', linestyle='--', linewidth=0.5)
    plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(10))
    plt.gca().yaxis.set_major_locator(ticker.MultipleLocator(50))

    # Save the graph as a PNG file
    plt.tight_layout()
    plt.savefig(graph_file)
    print(f"Graph saved as '{graph_file}'.")

    # Optionally, display the plot
    plt.show()

# Example usage:
folder_paths = ["/Users/martinalonsolalanda/jsbsim-master/Results/1700ft-6100lbm",
                "/Users/martinalonsolalanda/jsbsim-master/Results/13000ft-6100lbm"]
output_file = "merged_output.xlsx"               # Desired output Excel file name
graph_file = "merged_output_graph.png"           # Desired graph file name
plot_data(folder_paths, output_file, graph_file)

output_file = "merged_output.xlsx"               # Desired output Excel file name
graph_file = "merged_output_graph.png"           # Desired graph file name
plot_data(folder_paths, output_file, graph_file)
