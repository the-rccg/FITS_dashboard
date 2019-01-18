# -*- coding: utf-8 -*-
"""
FITS Dash App
Quickly sketch and explore data tables and relations sae in FITS format 

@author: RCCG
"""
import numpy as np
from datetime import datetime as dt
import json


# Load Settings
settings = json.load(open('settings.json'))

# File names
# TODO: Allow dictionary for renaming in display
from os import listdir
filename_list = [file for file in listdir(settings['folderpath']) if file[-5:].lower()==".fits"]

# Load Data
from astropy.io import fits
# TODO: Allow dictionary for renaming in display
data = {
            filename: fits.open(settings['folderpath'] + filename, memmap=True)[1] 
            for filename in filename_list
        }

# Defining columns
# TODO: Allow dictionary for renaming in dispaly
column_names_file = settings['columns_to_use']
column_names_data = data[filename_list[0]].columns.names
if column_names_file:
    column_names = [
        column_name for column_name in column_names_file 
            if column_name in column_names_data
    ]
else:
    column_names = data[filename_list[0]].columns.names

# Draw Params
display_count_max = settings['display_count_max']
display_count = settings['display_count_default']
display_count_step = settings['display_count_granularity']

# Default Parameters: No Default

# Subsample when data is too large
import numpy as np
data_counts = {filename: data[filename].header['NAXIS2'] for filename in data.keys()}  # Header is fastest way to get number of data points
def getSampleIndices(sample_size, total_size):
    """ returns data points for the subsample in the range

    Timed Tests:   data_count = 100,000,000;  sample_size = 100,000;
        926 us  np.random.randint(low=0, high=data_count+1, size=sample_size) 
        935 us  np.random.choice(data_count, size=sample_size, replace=True, p=None)
         85 ms  random.sample(range(data_count), sample_size)
          6 s   np.random.choice(data_count, size=sample_size, replace=False, p=None)
    """
    # note: allows multiple identical values, hence n<=num_points, but orders mag faster
    select_points = np.random.randint(
                        low=0, high=total_size, 
                        size=sample_size
                    )
    return select_points


# Reduce Columns to Useful
selected_columns = column_names #[name for name in column_names if name.split('_')[-1] not in ['p50', 'p84', 'p16', 'Exp']]
#print("Selected Columns: {}".format(selected_columns))

# Start App
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
app = dash.Dash('fits_dashboard')
app.title = 'FITS Dashboard: {}'.format(settings['name'])

# Visual layout
app.layout = html.Div([
    
    # Element 1: Data File Selector
    html.Div(
        [
            dcc.Dropdown(
                id='brick_selector',
                placeholder='Select FITS files...',
                options=[
                    {'label': '{}'.format(i), 'value': i} 
                        for i in filename_list
                ],
                value=None,
                multi=True
            )
        ]
    ),

    # Element 2: Data Amount Selector
    html.Div(
        [
            dcc.Slider(
                id='display_count_selection',
                #placeholder='',
                min=0,
                max=display_count_max,
                value=display_count,
                step=display_count_step,
                marks={
                    0: '0', 
                    display_count_max: "{:,}".format(display_count_max)
                }
            )
        ],
        style={'height':34, 'width':'97%', 'margin':'auto auto'}
        #html.Div(id="selection-container")
    ),

    # Element 3: New Subsample Generator
    # To Be Coded
        
    # Axis Selection
    html.Div(
        [
            # 4.1: Select X-Axis
            html.Div(
                [
                    #html.H4('x-axis ', style={'display':'inline-block', 'width':60, 'margin': '0 auto', 'float':'left'}),
                    #html.Div([
                        dcc.Dropdown(
                            id='xaxis-column',
                            placeholder='Select X-Axis...',
                            options=[
                                {'label': i, 'value': i} 
                                    for i in selected_columns
                            ],
                            value=settings['default_x_column']
                        ),
                        #],
                        #style={'display':'inline-block', 'margin':'auto auto', 'width':'100%'}),
                    dcc.RadioItems(
                        id='xaxis-type',
                        options=[
                            {'label': i, 'value': i} 
                                for i in ['Linear', 'Log']
                        ],
                        value='Linear',
                        labelStyle={'display': 'inline-block'}
                    ),
                    dcc.RadioItems(
                        id='xaxis-orientation',
                        options=[
                            {'label': i, 'value': i} 
                                for i in ['increasing', 'reversed']
                        ],
                        value='increasing',
                        labelStyle={'display': 'inline-block'}
                    )
                ],
                style={'width': '48%', 'display': 'inline-block'}
            ),
            # 4.2: Select Y-Axis
            html.Div(
                [
                    dcc.Dropdown(
                        id='yaxis-column',
                        placeholder='Select Y-Axis...',
                        options=[
                            {'label': i, 'value': i} 
                                for i in selected_columns
                        ],
                        value=settings['default_y_column']
                    ),
                    dcc.RadioItems(
                        id='yaxis-type',
                        options=[
                            {'label': i, 'value': i} 
                                for i in ['Linear', 'Log']
                        ],
                        value='Linear',
                        labelStyle={'display': 'inline-block'}
                    )
                ],
                style={'width': '48%', 'float': 'right', 'display': 'inline-block'}
            ),
        ]
    ),
    html.Div(
        [
            dcc.Dropdown(
                id='color-column',
                placeholder='Select Color-Axis...',
                options=[
                    {'label': i, 'value': i} 
                        for i in selected_columns
                ],
                value=None
            ),
        ]
    ),

    # Scatter Plot
    dcc.Graph(id='indicator-graphic'),

    # Download
    html.A(
        'Download *FULL* Data',
        id='download-full-link',
        download="rawdata.fits",
        href="",
        target="_blank"
    ),

    html.A(
        'custom data',
        id='custom-data-link',
        download='custom.fits',
        href='',
        target="_blank"
    )
])


@app.callback(dash.dependencies.Output('download-full-link', 'href'),
              [dash.dependencies.Input('brick_selector', 'value')])
def update_download_link(file_list):
    '''  '''
    if not file_list or file_list == "None":
        return 
    if type(file_list) is list:
        print(file_list)
        return '/dash/download?value={}'.format(",".join(file_list))
        #file_value = file_value[0]
    filepath = settings['folderpath'] + file_list
    from os.path import isfile
    if not isfile(filepath):
        return
    else:
        return '/dash/download?value={}'.format(file_list)

@app.server.route('/dash/download') 
def download_file():
    from flask import request, send_file
    filename = request.args.get('value')
    file_list = filename.split(',')
    print("download: ", file_list)
    filepath_list = [settings['folderpath'] + filename for filename in file_list]
    filepath = filepath_list[0]  # TODO: Allow downloading of multiple files
    return send_file(filepath,
                #mimetype='text/csv',
                attachment_filename=filename,
                as_attachment=True)



@app.callback(
    dash.dependencies.Output('indicator-graphic', 'figure'),
    [   
        dash.dependencies.Input('xaxis-column', 'value'),
        dash.dependencies.Input('yaxis-column', 'value'),
        dash.dependencies.Input('color-column', 'value'),
        dash.dependencies.Input('xaxis-type', 'value'),
        dash.dependencies.Input('yaxis-type', 'value'),
        dash.dependencies.Input('xaxis-orientation', 'value'),
        dash.dependencies.Input('display_count_selection', 'value'),
        dash.dependencies.Input('brick_selector', 'value')
    ])
def update_graph(xaxis_column_name, yaxis_column_name, color_column_name,
                 xaxis_type, yaxis_type, 
                 xaxis_orientation,
                 display_count, bricks_selected
                 ):
    """ update graph based on new selected variables """
    # Brick selection
    print("Brick {} selected".format(bricks_selected))
    # Define Marker properties
    marker_properties = {
        'size': settings['marker_size'],
        'opacity': settings['marker_opacity'],
        'line': {'width': 0.5, 'color': 'white'}
    }
    x_axis_properties = {
        'title': xaxis_column_name,
        'type': 'linear' if xaxis_type == 'Linear' else 'log'
    }
    if xaxis_orientation == 'reversed':
        x_axis_properties['autorange'] = 'reversed'
    # Special Functions on columns
    # 1. Herzsprung Russel columns
    # absolut magnitude / luminosity
    # stellar classification / effective temperatures
    custom_functions =  {}
    # Fill new data
    t0 = dt.now()
    # Check for valid axis
    has_xaxis = (xaxis_column_name in selected_columns)
    has_yaxis = (yaxis_column_name in selected_columns)
    has_caxis = (color_column_name in selected_columns)
    # Require X and Y to plot
    if has_xaxis and has_yaxis:
        get_data(bricks_selected, display_count)
    else:
        x_data = np.array([])
        y_data = np.array([])
        c_data = np.array([])
        text = np.array([''])
        

    # Format for sending  
    data_dic = {
        'x': x_data,
        'y': y_data
    }
    # Add color scale
    if has_caxis:
        marker_properties['color'] = c_data  
        marker_properties['colorscale'] = settings['color_scale']  # 'Greys', 'YlGnBu', 'Greens', 'YlOrRd', 'Bluered', 'RdBu', 'Reds', 'Blues', 'Picnic', 'Rainbow', 'Portland', 'Jet', 'Hot', 'Blackbody', 'Earth', 'Electric', 'Viridis', 'Cividis'
        marker_properties['showscale'] = True
        marker_properties['colorbar'] = {'title':color_column_name}

    
    return {'data': [
        go.Scatter(
            **data_dic,
            text = text,
            mode = 'markers',
            marker = marker_properties
        )],
        'layout': go.Layout(
            xaxis=x_axis_properties,
            yaxis={
                'title': yaxis_column_name,
                'type': 'linear' if yaxis_type == 'Linear' else 'log'
            },
            margin={'l': 40, 'b': 40, 't': 10, 'r': 0},
            hovermode='closest'
        )
    }
    
def get_data(bricks_selected, display_count):
        # Number of bricks
        brick_count = len(bricks_selected)
        # Allocate Memory for Data
        x_data = np.empty(display_count)  # X-Axis
        y_data = np.empty(display_count)  # Y-Axis
        if has_caxis:
            c_data = np.empty(display_count)  # Color
        else:
            c_data = np.array([])
        text = np.empty(display_count, dtype=str)  # Description
        t1 = dt.now()
        print("empty:      {}".format(t1-t0))
        # Create new random sample
        print("resampling with {} points".format(display_count))
        # Add Data to Array
        current_length = 0
        for brick_i in bricks_selected:
            sample_size = int(display_count/brick_count)
            select_points = getSampleIndices(sample_size, data_counts[brick_i])
            print("random:     {}".format(dt.now()-t1))
            x_data[current_length:current_length+sample_size] = data[brick_i].data[xaxis_column_name][select_points]
            y_data[current_length:current_length+sample_size] = data[brick_i].data[yaxis_column_name][select_points]
            if has_caxis:  
                c_data[current_length:current_length+sample_size] = data[brick_i].data[color_column_name][select_points]
            text[current_length:current_length+sample_size] = data[brick_i].data['Name'][select_points]
            print("assign {}:  {}".format(brick_i, dt.now()-t1))
            current_length += sample_size
            t1 = dt.now()
    return x_data, y_data, c_data


def update_data_link(data):
    # Create temp file
    import StringIO
    strIO = StringIO.StringIO()
    strIO.write('You have selected {}'.format(value)) 
    strIO.seek(0)    
    from flask import send_file
    send_file(strIO,
                     mimetype='text/csv',
                     attachment_filename='downloadFile.csv',
                     as_attachment=True)
    


if __name__ == '__main__':
    app.run_server(debug=True, port='5001')# host='129.206.102.157')