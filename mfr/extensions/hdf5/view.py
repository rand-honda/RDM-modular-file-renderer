from flask import Flask

app = Flask(__name__)

@app.route('/render/HDF5Renderer/view', methods=['GET', 'POST'])
def handle_node_path():
    return 'Test on 20230908 by KWT'

if __name__ == '__main__':
    app.run()
