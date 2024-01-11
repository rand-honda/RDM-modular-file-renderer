from flask import Flask, request
import h5py

app = Flask(__name__)

@app.route('/render/HDF5Renderer/view', methods=['GET', 'POST'])
def handle_node_path():
    # node_path = request.form.get('path')
    
    # try:
    #     with h5py.File('your_file.h5', 'r') as f:
    #         dataset = f[node_path]            
    # except Exception as e:
    #     return str(e)      
    return 'Test on 20230908 by KWT'  

if __name__ == '__main__':
    app.run()