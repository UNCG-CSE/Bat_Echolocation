from dash.dependencies import Output, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd

from .server import app
from . import router


markdown_text = '''

This project aims to identify and classify real bat calls according to the purpose of that call, ranging from echolocation to mating. The calls are stored in Zero Crossing format; the data will have to be cleaned up as it contains a significant amount of noise. Once the data is cleaned, the bat calls will be clustered according to their shapes, and then classified for future scientific research. If all goes well, we will also be able to predict the nature of the calls based on metadata such as the time, location, and season that the calls were recorded in. The project is written in Python.
'''
app.layout = html.Div(children=[
    html.H1(children='Bat Echolocation Data'),

    html.H4(children='Hadi Soufi, Yang Peng, Bety Rostandy, Thien Le, Kevin Keomalaythong'),
    dcc.Location(id='url', refresh=False),
    dcc.Link('Home Page', href=app.url_base_pathname),
    ', ',
    dcc.Link('Page 1', href=f'{app.url_base_pathname}fig1'),
    ', ',
    dcc.Link('Page 2', href=f'{app.url_base_pathname}fig2'),
    html.Br(),
    html.Br(),
    html.Div(id='content'),
    html.Div([dcc.Markdown(children=markdown_text)]),
    # dcc.Input(id='input', value='', type='text'),
    html.Div(id='output-graph'),
    html.Label('Select the following years for the label data: '),
    dcc.Dropdown(
        id='input',
        options=[
            {'label': '2018 Night Data Bat Calls', 'value': '2018_night.txt'},
            {'label': '2017 Night Data Bat Calls', 'value': '2017_night.txt'},
            {'label': '2016 Night Data Bat Calls', 'value': '2016_night.txt'},
            {'label': '2015 Night Data Bat Calls', 'value': '2015_night.txt'}
        ],
        value=['2018_night.txt'],
        multi=False
    ),
])


@app.callback(
    Output(component_id='output-graph', component_property='children'),
    [Input(component_id='input', component_property='value')]
)
def update_value(input_data):
    df = pd.DataFrame.from_csv(input_data, sep='\t')
    df.reset_index(inplace=True)
    return dcc.Graph(
        id='BatData',
        figure={
            'data': [
                go.Scatter(
                    x=df[df['Label'] == i]['Night'],
                    y=df[df['Label'] == i]['Number'],
                    text=df[df['Label'] == i]['Folder2'],
                    mode='markers',
                    opacity=0.7,
                    marker={
                        'size': 10,
                        'line': {'width': 0.5, 'color': 'white'}
                    },
                    name=i
                ) for i in df.Label.unique()
            ],
            'layout': go.Layout(
                title=('Bat Recording for all the Night in ' + input_data),
                xaxis=dict(
                    title='Date(Night)'
                ),
                yaxis=dict(
                    title='Number of Calls'
                )
            )
        }
    )


if __name__ == '__main__':
    app.run_server(debug=True)
