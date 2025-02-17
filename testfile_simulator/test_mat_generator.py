import numpy as np
import scipy.io as sio

def create_test_mat(filename="test_complex.mat"):
    # 1. Scalar values
    scalar_int = 42
    scalar_float = 3.14159
    
    # 2. 1D array
    array_1d = np.arange(10)  # [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    
    # 3. 2D array (5x5 random)
    array_2d = np.random.rand(5, 5)
    
    # 4. 3D array (2x5x5 random)
    array_3d = np.random.rand(2, 5, 5)
    
    # 5. Complex array (1D)
    complex_1d = np.array([1+2j, 3+4j, 5+6j])
    
    # 6. MATLAB struct/dict with mixed fields
    #    In Python, store as a dict of dicts for MATLAB struct
    struct_data = {
        'x': np.linspace(0, 1, 10),
        'y': np.random.randn(10),
        'info': 'Hello from struct!',
        'nested': {
            'nested_array': np.array([[10, 20], [30, 40]])
        }
    }
    
    # 7. Cell array (list of different data types)
    #    In MATLAB, stored as object arrays
    cell_array = np.empty((1, 3), dtype=object)  # 1x3 cell
    cell_array[0, 0] = 'String inside cell'
    cell_array[0, 1] = np.array([100, 200, 300])  # 1D numeric array
    cell_array[0, 2] = np.random.rand(3, 3)       # 2D numeric array

    # Package everything into a dictionary
    mat_dict = {
        'scalar_int': scalar_int,
        'scalar_float': scalar_float,
        'array_1d': array_1d,
        'array_2d': array_2d,
        'array_3d': array_3d,
        'complex_1d': complex_1d,
        'struct_data': struct_data,
        'cell_array': cell_array
    }

    # Save to .mat file
    sio.savemat(filename, mat_dict)
    print(f"✅ '{filename}' created with complex datatypes!")

if __name__ == "__main__":
    create_test_mat()
