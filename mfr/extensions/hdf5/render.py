import os

import chardet
from mfr.core import extension
from mako.lookup import TemplateLookup
import pandas as pd
import h5py
import json
import gc
from PIL import Image
import io
import base64
import pathlib
import numpy as np
import tempfile
import requests
import re
from PIL import Image
from io import BytesIO
from requests.auth import HTTPBasicAuth
from requests import PreparedRequest, Session
import csv
from urllib.parse import urlparse, parse_qs
import  requests
from requests.auth import HTTPBasicAuth
import uuid
from mfr.core import extension
from mfr.extensions.tabular import settings, exceptions
import re
import logging

logger = logging.getLogger(__name__)

class HDF5Renderer(extension.BaseRenderer):
           
    TEMPLATE = TemplateLookup(
        directories=[
            os.path.join(os.path.dirname(__file__), 'templates')
        ]).get_template('viewer.mako')

    TEMPLATE_TEXT = TemplateLookup(
        directories=[
            os.path.join(os.path.dirname(__file__), 'templates')
        ]).get_template('viewerText.mako')
    
    TABULAR_TEMPLATE = TemplateLookup(
        directories=[        
            os.path.join(('/code/mfr/extensions/tabular'), 'templates')
        ]).get_template('viewer.mako')
    
    IMAGE_TEMPLATE = TemplateLookup(
        directories=[        
            os.path.join(('/code/mfr/extensions/image'), 'templates')
        ]).get_template('viewer.mako')
    
    CODE_PYGMENTS_TEMPLATE = TemplateLookup(
        directories=[
            os.path.join(('/code/mfr/extensions/codepygments'), 'templates')
        ]).get_template('viewer.mako')    
      
    def render(self):               
        # HDF5のマジックナンバーを定義
        HDF5_MAGIC_NUMBER = b'\x89\x48\x44\x46\x0d\x0a\x1a\x0a'

        # HDF5ファイルのパスを指定
        hdf5_file_path = self.file_path ##これが元ファイル

        body = ""
        
        try:
            # HDF5ファイルをバイナリモードで読み込む
            with open(hdf5_file_path, 'rb') as f:
                # ファイルの先頭から8バイトを読み取る
                magic_number = f.read(8)
                # 読み取ったバイト列がマジックナンバーと一致するかどうかを比較する
                if magic_number == HDF5_MAGIC_NUMBER:
                    # 一致した場合はHDF5ファイルと判定する
                    # body = 'This is an HDF5 file.'
                    # parsed_url = urlparse(self.export_url)
                    # query_params = parse_qs(parsed_url.query)
                    # parent_title = query_params.get('parentTitle', [''][0])
                    # file_name = parent_title[0].split('|')[-1].strip()
                    
                    with h5py.File(self.file_path, 'r') as f:
                        # tree_data = 'Tree data......xxxxx 230907'   
                        # data = self.read_hdf5_data(f, data)
                        tree_data = self.convert_hdf5_to_tree_structure('', f) 
                        dataset_paths = self.get_dataset_paths('', f)     
                        
                        div = ''
                        file_attribute = ''            
                        # for dataset_path in dataset_paths:
                        #     file_name = os.path.basename(dataset_path)                
                        #     file_name_formatted = file_name.replace('.', '_')                
                        #     with h5py.File(self.file_path, 'r') as f:
                        with h5py.File(self.file_path, 'r') as f:
                            for dataset_path in dataset_paths:
                                # file_name = os.path.basename(dataset_path)                
                                # file_name_formatted = file_name.replace('.', '_')   
                                # file_name_formatted = file_name_formatted.replace(' ', '_')
                                path_components = dataset_path.lstrip('/').split('/')
                                file_name = self.replace_special_characters_with_underscore(path_components[-1])
                                if len(path_components) > 1:
                                    dir_names = [self.replace_special_characters_with_underscore(component) for component in path_components[:-1]]
                                    file_name_formatted = '_' + '_'.join(dir_names) + '_' + file_name 
                                else:
                                    file_name_formatted = '_' + file_name
                                
                            
                                dataset = f[dataset_path]                    
                                if dataset.name.endswith(('txt','text')) or (isinstance(dataset[0], str) and not dataset.name.endswith(('csv', 'tsv'))):
                                    div += '<div id="' + file_name_formatted + '" style="display:none;">'
                                    div += self.code_pygments_render(dataset[0])
                                    div += '</div>'  
                                    
                                    attribute_names =  list(dataset.attrs.keys())                                                                                      
                                    if attribute_names:
                                        text_attribute = dataset.attrs
                                        # text_attribute['encoding']='ASCII'                                    
                                        html_table = '<div id="' + file_name_formatted + '_attribute" style="display:none;">'
                                        html_table += '<table><tr><td colspan="2">File Attribute</td></tr>'
                                        html_table += '<tr style="background: #eee;"><td>Name</td><td>Value</td></tr>'
                                        # for k in text_attribute.keys():                                                                                                        
                                        #     html_table += '<tr><td>' + str(k) + '</td><td>'+ str(text_attribute[k]) +'</td></tr>'
                                        for k, v in text_attribute.items():
                                            if v:
                                                html_table += '<tr><td>' + str(k) + '</td><td>'+ str(v[0].decode('utf-8')) +'</td></tr>'
                                            else:
                                                html_table += '<tr><td>' + str(k) + '</td><td>-</td></tr>'                                                
                                        html_table += '</table></div>'                      
                                        file_attribute += html_table
                                elif dataset.name.endswith(('xlsx','xls')):
                                    div += '<div id="' + file_name_formatted + '" style="display:none;">'
                                    div += self.tabular_render(dataset[0], 'xlsx', '')
                                    div += '</div>'   
                                                                                                            
                                    attribute_names =  list(dataset.attrs.keys())                                                                                      
                                    if attribute_names:
                                        excel_attribute = dataset.attrs 
                                        html_table = '<div id="' + file_name_formatted + '_attribute" style="display:none;">'
                                        html_table += '<table><tr><td colspan="2">File Attribute</td></tr>'
                                        html_table += '<tr style="background: #eee;"><td>Name</td><td>Value</td></tr>'
                                        # for k in excel_attribute.keys():                          
                                        #     html_table += '<tr><td>' + str(k) + '</td><td>'+ str(excel_attribute[k]) +'</td></tr>'
                                        for k, v in excel_attribute.items():
                                            if v:
                                                html_table += '<tr><td>' + str(k) + '</td><td>'+ str(v[0]) +'</td></tr>'
                                            else:
                                                html_table += '<tr><td>' + str(k) + '</td><td>-</td></tr>'
                                        html_table += '</table></div>'                    
                                        file_attribute += html_table  
                                elif dataset.name.endswith('csv'):
                                    div += '<div id="' + file_name_formatted + '" style="display:none;">'
                                    div += self.tabular_render(dataset[0], 'csv', ',')
                                    # div += self.code_pygments_render(dataset[0])
                                    div += '</div>'   
                                elif dataset.name.endswith('tsv'):
                                    div += '<div id="' + file_name_formatted + '" style="display:none;">'
                                    div += self.tabular_render(dataset[0], 'tsv', '\t')
                                    # div += self.code_pygments_render(dataset[0])
                                    div += '</div>'     
                                elif dataset.name.endswith(('bmp', 'jpg', 'jpeg', 'gif', 'ico', 'png', 'psd', 'tif', 'tiff')):
                                    div += '<div id="' + file_name_formatted + '" style="display:none;">'
                                    div += self.image_render(dataset[0])
                                    div += '</div>'  
                                    
                                    attribute_names =  list(dataset.attrs.keys())                                                                                      
                                    if attribute_names:
                                        image_attribute = dataset.attrs
                                        # image_attribute['Resolution']='1000dpi'                    
                                        html_table = '<div id="' + file_name_formatted + '_attribute" style="display:none;">'
                                        html_table += '<table><tr><td colspan="2">File Attribute</td></tr>'
                                        html_table += '<tr style="background: #eee;"><td>Name</td><td>Value</td></tr>'
                                        for k, v in image_attribute.items():
                                            if v:
                                                html_table += '<tr><td>' + str(k) + '</td><td>'+ str(v[0]) +'</td></tr>'
                                            else:
                                                html_table += '<tr><td>' + str(k) + '</td><td>-</td></tr>'
                                        html_table += '</table></div>'      
                                else:
                                    div += '<div id="' + file_name_formatted + '" style="display:none;">'
                                    div += 'unsupported File.'
                                    div += '</div>'                                                                                                                                      
                        file_path = ''
                # file_name = ''
                # div = ''
                    return self.TEMPLATE.render(base=self.assets_url, tree_data=tree_data, file_path=self.file_path, div=div, file_attribute=file_attribute, button='戻る')                        
                
                else:
                    # 一致しなかった場合はHDF5ファイルではないと判定する   
                    jsonBase = ""                                     
                    output = ""
                    errorString = ""
                    uploadUrl = ""
                    filepath = self.file_path ##これが元ファイル
                    metadata_download_url = str(self.metadata.download_url)##最初のはてなでぶった切り->そのまま行けそう               
                    jsondictString = "" 
                    auth = HTTPBasicAuth("jyunji.honda@pmb.rand.co.jp", "B1oF5Cl3")
                    
                    ##jsonファイルの読み込み
                    try:                                            
                        # jsondictString = "".join(res)     
                        with open(filepath, 'r') as json_open:
                            #jsonとして読み込み
                            jsondict = json.load(json_open)
                            json_open.close()            

                            jsonBase = str(jsondict)
                            ##jsonをlistに変換                            
                            dirs = self.dir_list_of(jsondict, 'root')
                            ##jsondictString = "".join(dirs)     
                            for item in dirs:
                                output = output + '~' + item                                                 
                        output = output + '<br>' + "json_read_ok"                
                    except Exception as e:
                        errorString = errorString + '<br>' + 'jsonfileopenerror「' + str(e) + '」'
                                            
                    ##作成するhdf5ファイルのパス        
                    h5_path = os.path.join(os.path.dirname(__file__), 'temp/temp.h5')   

                    try :
                        with h5py.File(h5_path, "w") as group1:                         

                            #ディレクトリlistのループ
                            rootPath = ""
                            for item in dirs:                
                                arr = item.split(":", 1);
                                h5ItemPath = arr[0];
                                
                                if rootPath:
                                    h5ItemPath = h5ItemPath.replace(rootPath,'')
                                else:
                                    rootPath = h5ItemPath + '/'
                                                            
                                output = output + '<br>ItemPath:' + h5ItemPath
                                #urlが存在する場合
                                if (len(arr) >1):
                                    h5ItemUrl = arr[1];
                                    replacePath1 = 'http://localhost:7777/'
                                    replacePath2 = 'http://192.168.168.167:7777/'
                                    h5ItemUrl = h5ItemUrl.replace(replacePath1,replacePath2)
                                    output = output + '<br>ItemUrl:' + h5ItemUrl                        

                                    ##拡張子を取得する                        
                                    file_name, file_extension = os.path.splitext(h5ItemPath)
                                    output = output + '<br>file_extension:' + file_extension

                                    ##拡張子リスト定義                
                                    textExtensions = ['.txt']
                                    csvtsvExtensions = ['.csv','.tsv']
                                    xlsxExtensions = ['.xlsx', '.xls']
                                    imageExtensions = ['.jpg', '.jpeg', '.bmp', '.gif']
                                    
                                    if file_extension in textExtensions:
                                        output = output + '<br>textFile_extension:' + file_extension
                                        returnOutput = self._procTextFile(group1, h5ItemPath, auth, h5ItemUrl)
                                        output = output + '<br>' + returnOutput

                                    elif file_extension in csvtsvExtensions:
                                        output = output + '<br>csvtsvFile_extension:' + file_extension
                                        returnOutput = self._procCsvTsvFile(group1, h5ItemPath, auth, h5ItemUrl, file_extension)
                                        output = output + '<br>' + returnOutput
                                        
                                    elif file_extension in xlsxExtensions:
                                        output = output + '<br>xlsxFile_extension:' + file_extension
                                        returnOutput = self._procExcelFile(group1, h5ItemPath, auth, h5ItemUrl)
                                        output = output + '<br>' + returnOutput
                                        
                                    elif file_extension in imageExtensions:
                                        output = output + '<br>imageFile_extension:' + file_extension
                                        returnOutput = self._procImageFile(group1, h5ItemPath, auth, h5ItemUrl)
                                        output = output + '<br>' + returnOutput                
                                            
                            output = output + '<br>' + "hdf5_open"
                            
                            try:                    
                                output = output +"<br>create hdf5 ok "                    
                                uploadUrl = metadata_download_url                 
                            
                            except Exception as e:
                                errorString = errorString + '<br>errorpos1:' + str(e)       
                                
                    except Exception as e:
                        errorString = errorString + '<br>errorpos2:' + str(e) 
                        
                    with h5py.File(h5_path, 'r') as f:
                        # tree_data = 'Tree data......xxxxx 230907'   
                        # data = self.read_hdf5_data(f, data)
                        tree_data = self.convert_hdf5_to_tree_structure('', f) 
                        dataset_paths = self.get_dataset_paths('', f)     
                        
                        div = ''
                        file_attribute = ''            
                        # for dataset_path in dataset_paths:
                        #     file_name = os.path.basename(dataset_path)                
                        #     file_name_formatted = file_name.replace('.', '_')                
                        #     with h5py.File(self.file_path, 'r') as f:
                        with h5py.File(h5_path, 'r') as f:
                            for dataset_path in dataset_paths:
                                # file_name = os.path.basename(dataset_path)                
                                # file_name_formatted = file_name.replace('.', '_')   
                                # file_name_formatted = file_name_formatted.replace(' ', '_')
                                path_components = dataset_path.lstrip('/').split('/')
                                file_name = self.replace_special_characters_with_underscore(path_components[-1])
                                if len(path_components) > 1:
                                    dir_names = [self.replace_special_characters_with_underscore(component) for component in path_components[:-1]]
                                    file_name_formatted = '_' + '_'.join(dir_names) + '_' + file_name 
                                else:
                                    file_name_formatted = '_' + file_name
                            
                                dataset = f[dataset_path]                    
                                if dataset.name.endswith(('txt','text')) or (isinstance(dataset[0], str) and not dataset.name.endswith(('csv', 'tsv'))):
                                    div += '<div id="' + file_name_formatted + '" style="display:none;">'
                                    div += self.code_pygments_render(dataset[0])
                                    div += '</div>'  
                                    
                                    attribute_names =  list(dataset.attrs.keys())                                                                                      
                                    if attribute_names:
                                        text_attribute = dataset.attrs
                                        # text_attribute['encoding']='ASCII'                                    
                                        html_table = '<div id="' + file_name_formatted + '_attribute" style="display:none;">'
                                        html_table += '<table><tr><td colspan="2">File Attribute</td></tr>'
                                        html_table += '<tr style="background: #eee;"><td>Name</td><td>Value</td></tr>'
                                        # for k in text_attribute.keys():                                                                                                        
                                        #     html_table += '<tr><td>' + str(k) + '</td><td>'+ str(text_attribute[k]) +'</td></tr>'
                                        for k, v in text_attribute.items():
                                            if v:
                                                html_table += '<tr><td>' + str(k) + '</td><td>'+ str(v[0].decode('utf-8')) +'</td></tr>'
                                            else:
                                                html_table += '<tr><td>' + str(k) + '</td><td>-</td></tr>'                                                
                                        html_table += '</table></div>'                      
                                        file_attribute += html_table
                                elif dataset.name.endswith(('xlsx','xls')):
                                    div += '<div id="' + file_name_formatted + '" style="display:none;">'
                                    div += self.tabular_render(dataset[0], 'xlsx', '')
                                    div += '</div>'   
                                                                                                            
                                    attribute_names =  list(dataset.attrs.keys())                                                                                      
                                    if attribute_names:
                                        excel_attribute = dataset.attrs 
                                        html_table = '<div id="' + file_name_formatted + '_attribute" style="display:none;">'
                                        html_table += '<table><tr><td colspan="2">File Attribute</td></tr>'
                                        html_table += '<tr style="background: #eee;"><td>Name</td><td>Value</td></tr>'
                                        # for k in excel_attribute.keys():                          
                                        #     html_table += '<tr><td>' + str(k) + '</td><td>'+ str(excel_attribute[k]) +'</td></tr>'
                                        for k, v in excel_attribute.items():
                                            if v:
                                                html_table += '<tr><td>' + str(k) + '</td><td>'+ str(v[0]) +'</td></tr>'
                                            else:
                                                html_table += '<tr><td>' + str(k) + '</td><td>-</td></tr>'
                                        html_table += '</table></div>'                    
                                        file_attribute += html_table  
                                elif dataset.name.endswith('csv'):
                                    div += '<div id="' + file_name_formatted + '" style="display:none;">'
                                    div += self.tabular_render(dataset[0], 'csv', ',')
                                    # div += self.code_pygments_render(dataset[0])
                                    div += '</div>'   
                                elif dataset.name.endswith('tsv'):
                                    div += '<div id="' + file_name_formatted + '" style="display:none;">'
                                    div += self.tabular_render(dataset[0], 'tsv', '\t')
                                    # div += self.code_pygments_render(dataset[0])
                                    div += '</div>'     
                                elif dataset.name.endswith(('bmp', 'jpg', 'jpeg', 'gif', 'ico', 'png', 'psd', 'tif', 'tiff')):
                                    div += '<div id="' + file_name_formatted + '" style="display:none;">'
                                    div += self.image_render(dataset[0])
                                    div += '</div>'  
                                    
                                    attribute_names =  list(dataset.attrs.keys())                                                                                      
                                    if attribute_names:
                                        image_attribute = dataset.attrs
                                        # image_attribute['Resolution']='1000dpi'                    
                                        html_table = '<div id="' + file_name_formatted + '_attribute" style="display:none;">'
                                        html_table += '<table><tr><td colspan="2">File Attribute</td></tr>'
                                        html_table += '<tr style="background: #eee;"><td>Name</td><td>Value</td></tr>'
                                        for k, v in image_attribute.items():
                                            if v:
                                                html_table += '<tr><td>' + str(k) + '</td><td>'+ str(v[0]) +'</td></tr>'
                                            else:
                                                html_table += '<tr><td>' + str(k) + '</td><td>-</td></tr>'
                                        html_table += '</table></div>'      
                                else:
                                    div += '<div id="' + file_name_formatted + '" style="display:none;">'
                                    div += 'unsupported File.'
                                    div += '</div>' 
                         
            
                    file = open(h5_path,'rb')
                    headers = {'Content-type': 'application/octet-stream'}     
            
                    r = requests.put(uploadUrl, data=file, headers=headers, auth=auth)
                    output = output + "<br>put hdf5 ok " + "<br>" + str(r.request.headers) + "<br>"+metadata_download_url+"<bt>"+str(r.status_code)        

                    #一時ファイルを削除する
                    removePath = os.path.join(os.path.dirname(__file__), 'temp')     
                    check_dir = pathlib.Path(removePath)
                    for file in check_dir.iterdir():
                        if file.is_file():
                            file.unlink()        
                        
                    # output = output + '<br>' +'Successfully created HDF5, please return to the file function.'
                    # output = output + '<br>' + errorString
                    if len(errorString) > 0:
                        output = output + '<br>' + errorString
                    else:
                        output = '<br>' +'Successfully created HDF5, please return to the file function.' + jsonBase
                    
                    # body = self.createHDF5Main()
                    # div = body
                    # tree_data = ''
                    file_path = ''
                    # file_name = ''
                    # file_attribute = ''

                    return self.TEMPLATE_TEXT.render(base=self.assets_url, body=output)
                    
        except Exception as e:
            return str(e)

        ##return self.TEMPLATE_TEXT.render(base=self.assets_url, body=output)
        ##return self.TEMPLATE.render(base=self.assets_url, tree_data=tree_data, file_path=self.file_path, div=div, file_attribute=file_attribute, button='戻る')                        
        
    @property
    def file_required(self):
        return True

    @property
    def cache_result(self):
        return True
    
    def replace_special_characters_with_underscore(self, text):        
        pattern = r'[#$%&()~=~|*+!?<>,./\\ ]'
        return re.sub(pattern, '_', text)
    
    def convert_hdf5_to_tree_structure(self, path, item):
        tree_data = []  
        count = 1      
        for name, obj in item.items():
            if isinstance(obj, h5py.Group):
                group_info = {
                    'text': name,
                    'nodes': self.convert_hdf5_to_tree_structure(path+"/"+name, obj),
                    'extension': '',
                    'path': path+"/"+name
                }
                tree_data.append(group_info)
            elif isinstance(obj, h5py.Dataset):                
                # if extension == 'text' or extension == 'txt' or extension == 'csv' or extension == 'tsv' or extension == name:
                #     dataset_data = obj[0]
                # else:
                #     dataset_data = obj[0].tolist()
                    # dataset_data = '[98, 20, 1, .....]'  
                file_name = self.replace_special_characters_with_underscore(path+"/"+name)              
                dataset_info = {
                    'text': name,
                    'extension': name.split('.')[-1],  # Get the extension
                    'path': path+"/"+name,
                    'file_name': file_name
                }
                tree_data.append(dataset_info)
                count = count + 1                                                    
        return tree_data

    def get_dataset_paths(self, path, item):
        dataset_paths = []        
        for name, obj in item.items():
            if isinstance(obj, h5py.Group):
                dataset_paths.extend(self.get_dataset_paths(path+"/"+name, obj))
            elif isinstance(obj, h5py.Dataset):                
                dataset_paths.append(path+"/"+name)                
        return dataset_paths
     
    def code_pygments_render(self, dataset):  
        try: 
            return self.CODE_PYGMENTS_TEMPLATE.render(base="http://localhost:7778/assets/codepygments", body=dataset)
        except Exception as e:                    
            return  str(e)             
        
    def tabular_render(self, dataset, type, delimiter):   
        try:
            unique_id = str(uuid.uuid4())
            chunk_size = 1024
            if type == 'xlsx':
                sheets = {}  
                excel_io = io.BytesIO(dataset)            
                with pd.ExcelFile(excel_io) as excel_file:            
                    for sheet_name in excel_file.sheet_names:                                       
                        df = pd.read_excel(excel_file, sheet_name, header=None)
                        columns_info = [{"id": str(i), "field": str(i), "name": str(i), "sortable": True} for i in range(len(df.columns))]
                        # columns_info = [{"name": str(col), "id": str(col), "field": str(col),  "sortable": True} for col in df.iloc[0]]
                        data_info = df.iloc[1:].to_dict(orient="records")
                        
                        sheet_data = [columns_info, data_info]
                        sheets[sheet_name] = sheet_data                                                                                                                                 
            elif type == 'csv' or type == 'tsv':  
                sheet1_data = []
                columns_info = []
                data_rows = []        
                    
                # if isinstance(dataset, str):                   
                # data_lines = dataset
                # else:                    
                data_lines = dataset.splitlines()                    
                    
                csv_reader = csv.reader(data_lines, delimiter=delimiter)                                 
                header = next(csv_reader)
                            
                columns_info.append({"id": header[0], "field": header[0], "name": header[0], "sortable": True})
    
                for idx, col_name in enumerate(header[1:], start=1):
                    if not col_name.strip():
                        col_name = str(idx)
                    columns_info.append({"id": col_name, "field": col_name, "name": col_name, "sortable": True})
                    
                sheet1_data.append(columns_info)
                
                chunk = []
                for row in csv_reader:
                    data_row = {}
                    for idx, col_value in enumerate(row):   
                        col_name = header[idx]   
                        if not col_name.strip():
                            col_name = str(idx)           
                        data_row[col_name] = col_value.strip() if col_value.strip() else None                                   
                    # data_rows.append(data_row)
                    chunk.append(data_row)

                    if len(chunk) >= chunk_size:
                        data_rows.extend(chunk)
                        chunk = []
                # sheet1_data.append(data_rows)
                data_rows.extend(chunk)
                sheet1_data.append(data_rows)
                sheets = {type: sheet1_data}
            options = {
                'forceFitColumns': True,
                'enableColumnReorder': False,
                'enableCellNavigation': True,
                'enableColumnReorder': False,
                'multiColumnSort': True,
                'syncColumnCellResize': True
            }            
                        
            return self.TABULAR_TEMPLATE.render(
                base= "http://localhost:7778/assets/tabular",             
                height = '600',
                sheets = json.dumps(sheets, default=str),
                options = json.dumps(options),
                unique_id = unique_id       
            )  
        except Exception as e:                    
            return  str(e)  
        
    def image_render(self, dataset):        
        try:
            encoded_image = base64.b64encode(dataset).decode("utf-8")                    
            url = "data:image/jpeg;base64," + encoded_image    
            return self.IMAGE_TEMPLATE.render(base="http://localhost:7778/assets/image", url=url)
        except Exception as e:                    
            return  str(e)   
                    
    def createHDF5Main(self):
        output = ""
        errorString = ""
        uploadUrl = ""
        filepath = self.file_path ##これが元ファイル
        metadata_download_url = str(self.metadata.download_url)##最初のはてなでぶった切り->そのまま行けそう               
        jsondictString = "" 
        auth = HTTPBasicAuth("jyunji.honda@pmb.rand.co.jp", "B1oF5Cl3")
        
        ##jsonファイルの読み込み
        try:                                            
            # jsondictString = "".join(res)     
            with open(filepath, 'r') as json_open:
                #jsonとして読み込み
                jsondict = json.load(json_open)
                json_open.close()            

                ##jsonをlistに変換                            
                dirs = self.dir_list_of(jsondict, 'root')
                 ##jsondictString = "".join(dirs)     
            #      for item in dirs:
            #         output = output + '~' + item                                                 
            # output = output + '<br>' + "json_read_ok"                
        except Exception as e:
            errorString = errorString + '<br>' + 'jsonfileopenerror「' + str(e) + '」'
                                  
        ##作成するhdf5ファイルのパス        
        h5_path = os.path.join(os.path.dirname(__file__), 'temp/temp.h5')   

        try :
            with h5py.File(h5_path, "w") as group1:                         

                #ディレクトリlistのループ
                rootPath = ""
                for item in dirs:                
                    arr = item.split(":", 1);
                    h5ItemPath = arr[0];
                    
                    if rootPath:
                        h5ItemPath = h5ItemPath.replace(rootPath,'')
                    else:
                        rootPath = h5ItemPath + '/'
                                                
                    output = output + '<br>ItemPath:' + h5ItemPath
                    #urlが存在する場合
                    if (len(arr) >1):
                        h5ItemUrl = arr[1];
                        replacePath1 = 'http://localhost:7777/'
                        replacePath2 = 'http://192.168.168.167:7777/'
                        h5ItemUrl = h5ItemUrl.replace(replacePath1,replacePath2)
                        output = output + '<br>ItemUrl:' + h5ItemUrl                        

                        ##拡張子を取得する                        
                        file_name, file_extension = os.path.splitext(h5ItemPath)
                        output = output + '<br>file_extension:' + file_extension

                        ##拡張子リスト定義                
                        textExtensions = ['.txt']
                        csvtsvExtensions = ['.csv','.tsv']
                        xlsxExtensions = ['.xlsx', '.xls']
                        imageExtensions = ['.jpg', '.jpeg', '.bmp', '.gif']
                        
                        if file_extension in textExtensions:
                            output = output + '<br>textFile_extension:' + file_extension
                            returnOutput = self._procTextFile(group1, h5ItemPath, auth, h5ItemUrl)
                            output = output + '<br>' + returnOutput

                        elif file_extension in csvtsvExtensions:
                            output = output + '<br>csvtsvFile_extension:' + file_extension
                            returnOutput = self._procCsvTsvFile(group1, h5ItemPath, auth, h5ItemUrl, file_extension)
                            output = output + '<br>' + returnOutput
                            
                        elif file_extension in xlsxExtensions:
                            output = output + '<br>xlsxFile_extension:' + file_extension
                            returnOutput = self._procExcelFile(group1, h5ItemPath, auth, h5ItemUrl)
                            output = output + '<br>' + returnOutput
                            
                        elif file_extension in imageExtensions:
                            output = output + '<br>imageFile_extension:' + file_extension
                            returnOutput = self._procImageFile(group1, h5ItemPath, auth, h5ItemUrl)
                            output = output + '<br>' + returnOutput                
                                   
                output = output + '<br>' + "hdf5_open"
                
                try:                    
                    output = output +"<br>create hdf5 ok "                    
                    uploadUrl = metadata_download_url                 
                
                except Exception as e:
                    errorString = errorString + '<br>errorpos1:' + str(e)       
                    
        except Exception as e:
            errorString = errorString + '<br>errorpos2:' + str(e)  
  
        file = open(h5_path,'rb')
        headers = {'Content-type': 'application/octet-stream'}     
   
        r = requests.put(uploadUrl, data=file, headers=headers, auth=auth)
        output = output + "<br>put hdf5 ok " + "<br>" + str(r.request.headers) + "<br>"+metadata_download_url+"<bt>"+str(r.status_code)        

        #一時ファイルを削除する
        removePath = os.path.join(os.path.dirname(__file__), 'temp')     
        check_dir = pathlib.Path(removePath)
        for file in check_dir.iterdir():
            if file.is_file():
                file.unlink()        
             
        output = output + '<br>' +'Successfully created HDF5, please return to the file function.'
        output = output + '<br>' + errorString
            
        return output       
    
    ## textファイルをダウンロードしてHDF5を作成
    ##  2023-09-10　R＆D honda
    ##    
    def _procTextFile(self, _group, _fileName, _auth, _downloadUrl):
        
        returnText = ""
        try:            
            ##downloadUrl = "http://192.168.168.167:7777/v1/resources/hq5tn/providers/osfstorage/64f8570780aeeb02097a8dc9?kind=file"
            downloadFileName = os.path.join(os.path.dirname(__file__), 'temp/text.txt')     
            urlData = requests.get(_downloadUrl, auth=_auth)
            
            retChardet  = chardet.detect(urlData.content).get('encoding')

            returnText = returnText +'<br>'+ "text_get_ok"
            with open(downloadFileName, mode='wt', encoding="utf-8") as file1w: # wb でバイト型を書き込める
                file1w.write(urlData.text)
                
            returnText = returnText +'<br>'+ "text_write_ok"            
            returnText = returnText + '<br>' + retChardet

            retChardet = 'utf-8'
            with open(downloadFileName, encoding=retChardet, mode='r') as file1:            
            ##with open(downloadFileName, encoding='UTF-8', mode='r') as file1:
                returnText = returnText +"<br>text_file_open "
                self._createHDF5TextFile(_group, file1, _fileName)
                ##self._createHDF5TextFile(group1, file1, 'temp/test.txt')この表記でディレクトリもつくられるのでgroupいらんくね？
                returnText = returnText + "<br>text_Create_Success "

        except Exception as e:
            returnText = returnText + '<br>errorProcText:' + str(e)  

        return returnText
    
    ## tsv_csvファイルをダウンロードしてHDF5を作成
    ##  2023-09-10　R＆D honda
    ##        
    def _procCsvTsvFile(self, _group, _fileName, _auth, _downloadUrl, _extension):

        returnText = ""
        try:            
            downloadFileName = os.path.join(os.path.dirname(__file__), 'temp/TsvCsv.txt')                         
            urlData = requests.get(_downloadUrl, auth=_auth)

            retChardet  = chardet.detect(urlData.content).get('encoding')
            returnText = returnText + '<br>' + retChardet
            if (retChardet == 'windows-1252'):
                retChardet = 'utf-8'
                                
            returnText = returnText +'<br>'+ "csvtsv_get_ok"
            with open(downloadFileName, mode='wt', encoding=retChardet) as file1w: # wb でバイト型を書き込める
            ##with open(downloadFileName, mode='wt', encoding="utf-8") as file1w: # wb でバイト型を書き込める
                file1w.write(urlData.text)
            returnText = returnText +'<br>'+ "csvtsv_write_ok"
            
            #if (retChardet == 'windows-1252'):
            #retChardet = 'utf-8'
            
            if (_extension == '.tsv'):
                #df = pd.read_csv(downloadFileName, encoding=retChardet, sep='\t')            
                df = pd.read_csv(downloadFileName, sep='\t')            
            else:
                #df = pd.read_csv(downloadFileName, encoding=retChardet)
                df = pd.read_csv(downloadFileName)
    
            returnText = returnText +"<br>csvtsv_file_open"   
            # with open(downloadFileName, mode='r') as file:                         
            # excel_dataset = _group.create_dataset(
            #     name =_fileName, data=df.values, dtype=h5py.special_dtype(vlen=str))
                # excel_dataset[0] = file.read()
                
            with open(downloadFileName, mode='r') as file:  
                excel_dataset = _group.create_dataset(
                    name=_fileName, shape=(1,), dtype=h5py.special_dtype(vlen=str)
                )
                excel_dataset[0] = file.read()
                
            returnText = returnText + '<br>' +"csvtsv_Create_Success "

        except Exception as e:
            returnText = returnText + '<br>errorProcCsvTsv:' + str(e)  

        return returnText        
    
    def _procExcelFile(self, _group, _fileName, _auth, _downloadUrl):

        returnText = ""
        try:            
            downloadFileName = os.path.join(os.path.dirname(__file__), 'temp/Excel.xlsx')                         
            urlData = requests.get(_downloadUrl, auth=_auth).content
            returnText = returnText + "excel_get_ok"

            with open(downloadFileName ,mode='wb') as file3w: # wb でバイト型を書き込める
                file3w.write(urlData)
            returnText = returnText + "<br>excel_write_ok "
            
            # TYPE_OF_BINARY = h5py.special_dtype(vlen=np.dtype('uint8'))    
            # ##with pd.read_excel(downloadFileName) as df:                            
            # df = pd.read_excel(downloadFileName)
            # returnText = returnText +"<br>text_file_open"                            
            # excel_dataset = _group.create_dataset(
            #     name =_fileName, data=df.values)   
            
            with open(downloadFileName, "rb") as file:
                excel_binary = file.read()
                
                excel_data = np.frombuffer(excel_binary, dtype='uint8')           
                dataset = _group.create_dataset(
                    name=_fileName, shape=excel_data.shape, dtype=h5py.special_dtype(vlen=np.dtype('uint8')), compression='gzip'
                )
                dataset[0] = excel_data 
            
            # with open(downloadFileName, "rb") as excelf1:
            #     excel_binary = excelf1.read()
            #     returnText = returnText +"<br>text_file_open"  
            #     excel_data = np.frombuffer(excel_binary, dtype='uint8')
            #     dataset = _group.create_dataset(
            #         name =_fileName, shape=excel_data.shape, dtype=h5py.special_dtype(vlen=np.dtype('uint8')), compression='gzip'
            #     )
            #     dataset[0]=excel_data
            #     returnText = returnText +"<br>create_dataset"  
                
            returnText = returnText + '<br>' +"excel_Create_Success"

        except Exception as e:
            returnText = returnText + '<br>errorProcExcel:' + str(e)  

        return returnText
    
    ## imageファイルをダウンロードしてHDF5を作成
    ##  2023-09-10　R＆D honda
    ##        
    def _procImageFile(self, _group, _fileName, _auth, _downloadUrl):

        returnText = ""
        try:            
            ##downloadUrl = "http://192.168.168.167:7777/v1/resources/hq5tn/providers/osfstorage/64f0955877192d0009c0da1f?kind=file"
            downloadFileName = os.path.join(os.path.dirname(__file__), 'temp/Image.jpg')                         
            urlData = requests.get(_downloadUrl, auth=_auth).content
            returnText = returnText + "image_get_ok "

            with BytesIO(urlData) as buf:
                file2w = Image.open(buf)
                file2w.save(downloadFileName)
            returnText = returnText + "<br>image_write_ok "
                
            with open(downloadFileName, mode='rb') as file2:
                returnText = returnText +"<br>image_file_open "
                self._createHDF5ImageFile_nparray(_group, file2, _fileName)  
                # self._createHDF5ImageFile_frombuffer(_group, file2, _fileName)                      
            returnText = returnText + "<br>image_Create_Success "

        except Exception as e:
            returnText = returnText + '<br>errorProcImage:' + str(e)  
        
        return returnText
    
    ## HDF5のフォルダを作成
    ##  2023-08-31　R＆D honda
    ##
    def _createHDF5Folder(self, _h5, _folderName):
        
        ##folderName = "dir1"
        _group = _h5.create_group(_folderName)
        
        return _group

    ## HDF5の子フォルダを作成
    ##  2023-08-31　R＆D honda
    ##
    def _createHDF5ChildrenFolder(self, _group, _folderName):
        
        ##_folderName = "dir1_1"
        _groupChild = _group.create_group(_folderName)
        
        return _groupChild    
    
    ## textファイルをhdf5化
    ##  2023-08-31　R＆D honda
    ##
    def _createHDF5TextFile(self, _group, _file, _fileName):
        
        _file_dataset = _group.create_dataset(
            name =_fileName, shape=(1,), dtype=h5py.special_dtype(vlen=str), compression="gzip"
        )
        ##_file_dataset.attrs['testinfo'] = 'hogehoge'
        _file_dataset[0] = _file.read()

    ## excelファイルをhdf5化
    ##  2023-08-31　R＆D honda
    ##
    def _createHDF5ExcelFile(self, _group, _excelfile, _fileName):
        
        excel_binary = _excelfile.read()
        
        excel_data = np.frombuffer(excel_binary, dtype='uint8') 
        TYPE_OF_BINARY = h5py.special_dtype(vlen=np.dtype('uint8'))
        # excel_dataset = _group.create_dataset(_fileName,(7,3), dtype=TYPE_OF_BINARY)                        
        excel_dataset = _group.create_dataset(
            name =_fileName, shape=excel_data.shape, dtype=TYPE_OF_BINARY
        )
        # excel_dataset = _group.create_dataset(
        #     name =_fileName, shape=excel_data.shape, dtype=h5py.special_dtype(vlen=np.dtype('uint8')),
        # )
        excel_dataset[0] = excel_data         
    
    def _createHDF5ImageFile_nparray(self, _group, _imagefile, _fileName):
        
        image_binary = _imagefile.read()
        
        # image_data = np.frombuffer(image_binary, dtype='uint8')
        image_data = np.array(list(image_binary), dtype='uint8')
        TYPE_OF_BINARY = h5py.special_dtype(vlen=np.dtype('uint8'))
        ds_img = _group.create_dataset(
            _fileName, shape=image_data.shape, dtype=TYPE_OF_BINARY)     
        ds_img[0] = image_data    

    ## url（upload）からファイルをダウンロード
    ##  2023-08-31　R＆D honda
    ##     
    def urlFileDownload(self, _downloadUrl, _downloadFileName, _encoding, _mode):
    
        headers_dic = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36"}
        urlData = requests.get(_downloadUrl).content
        ##urlData = requests.get(_downloadUrl, headers=headers_dic).content

        with open(_downloadFileName, encoding=_encoding, mode=_mode) as f: # wb でバイト型を書き込める
            f.write(urlData)

            return f            
        
    ## jsonのディレクトリ構造をlist化
    ##  2023-08-31　R＆D honda
    ##
    def dir_list_of(self, jsondata, current_dir='')->list:
        dirs = []
        pattern = "https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
        ##pattern = "https?://[¥w/:%#¥$&¥?¥(¥)~.¥=¥+¥-]+"
        if isinstance(jsondata, int) or isinstance(jsondata, str):
            return dirs
        elif isinstance(jsondata, list):
            for i in range(len(jsondata)):
                cur_dir = current_dir + '/' + str(i)
                dirs.append(cur_dir)
                dirs += self.dir_list_of(jsondata[i], cur_dir)
        elif isinstance(jsondata, dict):
            for key, val in jsondata.items():
                tempVal = str(val)
                if re.match(pattern, tempVal):
                    cur_dir = current_dir + '/' + key + ':' + str(val)
                else:
                    cur_dir = current_dir + '/' + key
                                        
                dirs.append(cur_dir)
                dirs += self.dir_list_of(jsondata[key], cur_dir)                    
            # for key in jsondata:
            #     cur_dir = current_dir + '/' + key
            #     dirs.append(cur_dir)
            #     dirs += self.dir_list_of(jsondata[key], cur_dir)

        return dirs

          