from dash.dependencies import Output, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
from django.apps import AppConfig

from .server import app
from . import router


class ImagesConfig(AppConfig):
    name = 'viz'


app.layout = html.Div(children=[
    dcc.Link('Home Page', href=app.url_base_pathname),
    ', ',
    dcc.Link('Bat Echolocation Labeled Data',
             href=f'{app.url_base_pathname}BatEcholocationLabeledData'),
    ', ',
    dcc.Link('Bat Echolocation Frequency', href=f'{app.url_base_pathname}BatEcholocationFrequency'),
    html.H1(children='Bat Echolocation Data'),

    html.H4(children='Hadi Soufi, Yang Peng, Bety Rostandy, Thien Le, Kevin Keomalaythong'),
    dcc.Location(id='url', refresh=False),
    html.Br(),
    html.Div(id='content'),
    html.Br()
])


@app.callback(
    Output(component_id='output1', component_property='children'),
    [Input(component_id='input1', component_property='value')]
)
def update_value(input_data):
    df = pd.DataFrame.from_csv(('data/'+input_data), sep='\t')
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
                        'size': 12,
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


@app.callback(
    Output(component_id='output2', component_property='children'),
    [Input(component_id='input2', component_property='value')]
)
def update_value(input_data):
    df = pd.DataFrame.from_csv(('data/'+input_data), sep=',')
    df.reset_index(inplace=True)
    return dcc.Graph(
        id='BatData',
        figure={
            'data': [
                go.Scatter(
                    x=df['Time'],
                    y=df['Frequency'],
                    text=input_data,
                    mode='lines',
                    opacity=0.7,
                    marker={
                        'size': 10,
                        'line': {'width': 0.5, 'color': 'white'}
                    },
                )
            ],
            'layout': go.Layout(
                title=('Bat Recording for all the Night in ' + input_data),
                xaxis=dict(
                    title='Time'
                ),
                yaxis=dict(
                    title='Frequency'
                )
            )
        }
    )
