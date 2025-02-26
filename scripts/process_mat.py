import scipy.io
import h5py
import numpy as np
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from mpl_toolkits.mplot3d import Axes3D
import scipy.sparse
from scipy.io.matlab.mio5_params import mat_struct   # <-- Import mat_struct
from flask import url_for

OUTPUT_FOLDER = 'static/images'
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Max dimension threshold for downsampling 2D arrays
MAX_DIM = 200

def save_plot(fig, filename):
    # filepath = os.path.join(OUTPUT_FOLDER, f"{filename}.png")
    # fig.savefig(filepath, dpi=300)
    # plt.close(fig)
    # return f"/{filepath}"

    folder = 'static/images'
    os.makedirs(folder, exist_ok=True)
    localPath = os.path.join(folder, f"{filename}.png")
    fig.savefig(localPath,dpi=300)
    plt.close(fig)

    # Return absolute URL, e.g. https://my-flask-app.onrender.com/static/images/filename.png
    urlFor = url_for('static', filename=f"images/{filename}.png", _external=True)
    return urlFor,localPath

def analyze_mat_struct(key, data):
    """
    Recursively extract fields from a mat_struct object
    """
    results = []
    # Show a placeholder for the parent struct
    results.append({
        'variable': key,
        'file': '',
        'value': f"{key} is a MATLAB mat_struct (see subfields)"
    })

    # Iterate over all fields
    for field_name in data._fieldnames:
        value = getattr(data, field_name)
        results.extend(analyze_and_plot(f"{key}.{field_name}", value))
    return results

def get_basic_stats(arr):
    """Compute mean, std, min, max for numeric arrays."""
    return {
        'mean': float(np.mean(arr)),
        'std': float(np.std(arr)),
        'min': float(np.min(arr)),
        'max': float(np.max(arr))
    }

def analyze_and_plot(key, data):
    results = []

    # 1. Handle MATLAB structs (mat_struct)
    if isinstance(data, mat_struct):
        results.extend(analyze_mat_struct(key, data))

    # 2. Handle dict/h5py.Group
    elif isinstance(data, dict) or isinstance(data, h5py.Group):
        results.append({'variable': key, 'file': '', 'value': f"{key} is a struct/dict, see subfields"})
        for subkey, value in data.items():
            results.extend(analyze_and_plot(f"{key}.{subkey}", value))

    # 3. NumPy arrays
    elif isinstance(data, np.ndarray):
        data = np.squeeze(data)
        if data.size > 1e6:
            # 4D check or skip if user wants
            # If > 1 million elements, skip or partial downsample
            results.append({'variable': key, 'file': '', 'value': f"{key} too large: {data.shape}. Skipping or partial."})
            return results

        # Check for complex
        if np.iscomplexobj(data):
            real_part = np.real(data)
            imag_part = np.imag(data)
            fig, ax = plt.subplots()
            ax.plot(real_part, label='Real Part')
            ax.plot(imag_part, label='Imag Part', linestyle='dashed')
            ax.set_title(f"{key} (Complex)")
            ax.legend()
            plot_path,local_path = save_plot(fig, f"{key}_complex")
            results.append({'variable': f"{key} (Complex)", 'file': plot_path,'file_pathLocal':local_path})
            return results

        # Handle scalar stored in ndarray
        if data.ndim == 0:
            results.append({'variable': key, 'file': '', 'value': str(data)})

        # 1D -> numeric? Maybe bar chart or line plot
        elif data.ndim == 1:
            if hasattr(data, 'dtype') and data.dtype.kind in ['f', 'i', 'u']:
                unique_vals = np.unique(data)
                # If few unique values => bar chart
                if len(unique_vals) < 20 and len(unique_vals) != len(data):
                    # Possibly categorical
                    fig, ax = plt.subplots()
                    counts = [(val, np.sum(data == val)) for val in unique_vals]
                    labels, vals = zip(*counts)
                    ax.bar(labels, vals, color='skyblue')
                    ax.set_title(f"{key} - Bar Chart (Categorical)")
                    plot_path,local_path = save_plot(fig, f"{key}_bar")
                    results.append({'variable': key, 'file': plot_path,'file_pathLocal':local_path})
                else:
                    # Default to line plot
                    fig, ax = plt.subplots()
                    ax.plot(data)
                    ax.set_title(f"{key} - 1D Plot")
                    stats = get_basic_stats(data)
                    stats_str = f"(mean={stats['mean']:.2f}, std={stats['std']:.2f}, min={stats['min']:.2f}, max={stats['max']:.2f})"
                    ax.set_xlabel(stats_str)
                    plot_path,local_path = save_plot(fig, key)
                    results.append({'variable': key, 'file': plot_path, 'stats': stats,'file_pathLocal':local_path})
            elif data.dtype == object:
                # Possibly a cell array or object array
                results.append({
                    'variable': key,
                    'file': '',
                    'value': f"{key} is an object/Cell array of length {data.size}"
                })
                # Example: iterate each element for numeric
                # for i, elem in enumerate(data):
                #     if isinstance(elem, np.ndarray):
                #         results.extend(analyze_and_plot(f"{key}[{i}]", elem))
                #     else:
                #         results.append({
                #             'variable': f"{key}[{i}]",
                #             'file': '',
                #             'value': str(elem)
                #         })
            else:
                # Non-numeric 1D array, skip
                results.append({
                    'variable': key,
                    'file': '',
                    'value': f"{key} is 1D but not numeric (dtype={data.dtype})"
                })

        # 2D -> Scatter vs Heatmap
        elif data.ndim == 2:
            if hasattr(data, 'dtype') and data.dtype.kind in ['f', 'i', 'u']:
                # Downsample if too large
                rows, cols = data.shape
                if rows > MAX_DIM or cols > MAX_DIM:
                    row_factor = max(1, rows // MAX_DIM)
                    col_factor = max(1, cols // MAX_DIM)
                    data = data[::row_factor, ::col_factor]

                # If shape is Nx2 or Nx3 => Scatter
                if (data.shape[1] == 2 or data.shape[1] == 3) and data.shape[0] > 1:
                    # Scatter logic
                    if data.shape[1] == 2:
                        fig, ax = plt.subplots()
                        ax.scatter(data[:, 0], data[:, 1], alpha=0.7)
                        ax.set_title(f"{key} - 2D Scatter")
                    else:
                        fig = plt.figure()
                        ax = fig.add_subplot(111, projection='3d')
                        ax.scatter(data[:, 0], data[:, 1], data[:, 2], alpha=0.7)
                        ax.set_title(f"{key} - 3D Scatter")
                    stats = get_basic_stats(data)
                    plot_path,local_path = save_plot(fig, key)
                    results.append({'variable': key, 'file': plot_path, 'stats': stats,'file_pathLocal':local_path})
                else:
                    # Default Heatmap
                    fig, ax = plt.subplots()
                    sns.heatmap(data, cmap='viridis', ax=ax)
                    ax.set_title(f"{key} - 2D Heatmap")
                    stats = get_basic_stats(data)
                    plot_path,local_path = save_plot(fig, key)
                    results.append({'variable': key, 'file': plot_path, 'stats': stats,'file_pathLocal':local_path})
            elif data.dtype == object:
                results.append({
                    'variable': key,
                    'file': '',
                    'value': f"{key} is a 2D object array (cell array?). Skipping."
                })
            else:
                results.append({
                    'variable': key,
                    'file': '',
                    'value': f"{key} is 2D but not numeric (dtype={data.dtype})"
                })

        # 3D -> Sliced Heatmaps (Only if numeric)
        elif data.ndim == 3:
            if hasattr(data, 'dtype') and data.dtype.kind in ['f', 'i', 'u']:
                # Example approach: interpret axis=0 as 'depth/time'
                # We'll do up to 5 slices
                depth = min(data.shape[0], 5)
                for i in range(depth):
                    slice_data = data[i]
                    # Optionally downsample if too large
                    srows, scols = slice_data.shape
                    if srows > MAX_DIM or scols > MAX_DIM:
                        rf = max(1, srows // MAX_DIM)
                        cf = max(1, scols // MAX_DIM)
                        slice_data = slice_data[::rf, ::cf]
                    fig, ax = plt.subplots()
                    sns.heatmap(slice_data, cmap='viridis', ax=ax)
                    plot_path,local_path = save_plot(fig, f"{key}_slice_{i}")
                    results.append({'variable': f"{key} (slice {i})", 'file': plot_path,'file_pathLocal':local_path})
            else:
                results.append({
                    'variable': key,
                    'file': '',
                    'value': f"{key} is 3D but not numeric (dtype={data.dtype})"
                })

        # 4D or higher
        elif data.ndim >= 4:
            # Option: slice or skip
            results.append({
                'variable': key,
                'file': '',
                'value': f"{key} has {data.ndim} dimensions (shape={data.shape}). Handling advanced 4D+ is custom."
            })

    # 4. Sparse data
    elif scipy.sparse.issparse(data):
        dense_data = data.toarray()
        fig, ax = plt.subplots()
        sns.heatmap(dense_data, cmap='viridis', ax=ax)
        plot_path,local_path = save_plot(fig, key)
        results.append({'variable': key, 'file': plot_path,'file_pathLocal':local_path})

    # 5. Scalars
    elif isinstance(data, (int, float, bool)):
        results.append({'variable': key, 'file': '', 'value': str(data)})

    return results

def process_mat_file(file_path):
    try:
        mat_data = scipy.io.loadmat(file_path, struct_as_record=False, squeeze_me=True)
    except NotImplementedError:
        mat_data = h5py.File(file_path, 'r')

    results = []
    for key in mat_data:
        if key.startswith('__'):
            continue
        results.extend(analyze_and_plot(key, mat_data[key]))

    if not results:
        results.append({'variable': 'No valid data found', 'file': ''})
    return results



# import scipy.io
# import h5py
# import numpy as np

# def downsample_large_array(arr, max_size=10000):
#     """Downsample large arrays to reduce size before sending to GPT"""
#     if arr.size <= max_size:
#         return arr.tolist()
    
#     sampled_indices = np.random.choice(arr.size, max_size, replace=False)
#     sampled_values = arr.flatten()[sampled_indices]
    
#     return {
#         "sampled_values": sampled_values.tolist(),
#         "shape": arr.shape,
#         "mean": float(np.mean(arr)),
#         "std": float(np.std(arr)),
#         "min": float(np.min(arr)),
#         "max": float(np.max(arr))
#     }

# def process_mat_file(file_path):
#     """ Extracts data from `.mat` file and prepares it for GPT analysis """
#     try:
#         mat_data = scipy.io.loadmat(file_path, struct_as_record=False, squeeze_me=True)
#     except NotImplementedError:
#         return {"error": "Unsupported .mat format"}

#     extracted_data = {}
#     for key in mat_data:
#         if key.startswith('__'):  # Skip metadata
#             continue
#         value = mat_data[key]

#         if isinstance(value, np.ndarray):
#             extracted_data[key] = downsample_large_array(value) if value.size > 100000 else value.tolist()
#         else:
#             extracted_data[key] = str(value)

#     return extracted_data

