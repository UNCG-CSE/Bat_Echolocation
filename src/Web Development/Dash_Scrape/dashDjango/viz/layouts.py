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
        # html.Div([dcc.Markdown(children=markdown_text)]),
        html.Label('Select the following years for the label data: '),
        dcc.Dropdown(
            id='input1',
            options=[
                {'label': '2018 Night Data Bat Calls', 'value': '2018_night.txt'},
                {'label': '2017 Night Data Bat Calls', 'value': '2017_night.txt'},
                {'label': '2016 Night Data Bat Calls', 'value': '2016_night.txt'},
                {'label': '2015 Night Data Bat Calls', 'value': '2015_night.txt'}
            ],
            value=['2018_night.txt'],
            multi=False
        ),
        html.Div(id='output1')
    ])


def fig2():
    return html.Div(children=[
        # html.Div([dcc.Markdown(children=markdown_text)]),
        html.Label('Select the following years for the label data: '),
        dcc.Dropdown(
            id='input2',
            options=[
                {'label': 'S8072135 Night Data Bat Calls', 'value': 'S8072135.07#.csv'},
                {'label': 'S8072159 Night Data Bat Calls', 'value': 'S8072159.22#.csv'},
                {'label': 'S8072143 Night Data Bat Calls', 'value': 'S8072143.12#.csv'},
                {'label': 'P7132033_37.csv Night Data Bat Calls', 'value': 'P7132033_37.csv'},
                {'label': 'P7132035_14.csv Night Data Bat Calls', 'value': 'P7132035_14.csv'},
                {'label': 'P7132037_05.csv Night Data Bat Calls', 'value': 'P7132037_05.csv'},
                {'label': 'P7132038_32.csv Night Data Bat Calls', 'value': 'P7132038_32.csv'},
            ],
        ),
        html.Div(id='output2')
    ])
