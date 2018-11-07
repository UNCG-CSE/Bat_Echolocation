from random import randint
from dash.dependencies import Output, Input
import dash_core_components as dcc
import dash_html_components as html
from .server import app
import plotly.graph_objs as go
import pandas as pd

markdown_text = '''
This project aims to identify and classify real bat calls according to the purpose of that call, ranging from echolocation to mating. The calls are stored in Zero Crossing format; the data will have to be cleaned up as it contains a significant amount of noise. Once the data is cleaned, the bat calls will be clustered according to their shapes, and then classified for future scientific research. If all goes well, we will also be able to predict the nature of the calls based on metadata such as the time, location, and season that the calls were recorded in. The project is written in Python.
'''


def index():
    return (markdown_text,
            html.Br(),
            html.Br(),
            html.A([
                html.Img(
                    src='https://i.imgur.com/OSQWp0v.jpg',
                    alt='Bat Echolocation Image',
                    style={
                        'height': '50%',
                        'width': '50%',
                        'float': 'center',
                        'position': 'relative',
                        'padding-top': 0,
                        'padding-right': 0
                    })
            ], href='https://github.com/UNCG-CSE/Bat_Echolocation'),
            html.H4('Target Goal'),
            dcc.Markdown('''
            1. Extraction: Extract meaningful signal from noise.

            2. Clustering: Categorize the extracted calls into different types using clustering techniques.

            3. Classification: Classify if a Bat Echolocation(zero-crossing files) contains abnormal calls(i.e. social calls, foraging calls).
            ''')
            )


def fig1():
    return html.Div(children=[
        html.Div(id='output-graph'),
        # html.Div([dcc.Markdown(children=markdown_text)]),
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


def fig2():
    return dcc.Graph(
        id='main-graph',
        figure={
            'data': [{
                'name': 'Some name',
                'mode': 'line',
                'line': {
                    'color': 'rgb(0, 0, 0)',
                    'opacity': 1
                },
                'type': 'scatter',
                'x': [randint(1, 100) for x in range(20)],
                'y': [randint(1, 100) for x in range(20)]
            }],
            'layout': {
                'autosize': True,
                'scene': {
                    'bgcolor': 'rgb(255, 255, 255)',
                    'xaxis': {
                        'titlefont': {'color': 'rgb(0, 0, 0)'},
                        'title': 'X-AXIS',
                        'color': 'rgb(0, 0, 0)'
                    },
                    'yaxis': {
                        'titlefont': {'color': 'rgb(0, 0, 0)'},
                        'title': 'Y-AXIS',
                        'color': 'rgb(0, 0, 0)'
                    }
                }
            }
        }
    )
