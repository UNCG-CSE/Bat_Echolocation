import pandas as pd
import plotly.graph_objs as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

app = dash.Dash()

markdown_text = '''

This project aims to identify and classify real bat calls according to the purpose of that call, ranging from echolocation to mating. The calls are stored in Zero Crossing format; the data will have to be cleaned up as it contains a significant amount of noise. Once the data is cleaned, the bat calls will be clustered according to their shapes, and then classified for future scientific research. If all goes well, we will also be able to predict the nature of the calls based on metadata such as the time, location, and season that the calls were recorded in. The project is written in Python.
'''
app.layout = html.Div(children=[
    html.H1(children='Bat Echolocation Data'),

    html.H4(children='Hadi Soufi, Yang Peng, Bety Rostandy, Thien Le, Kevin Keomalaythong'),
    html.Div([dcc.Markdown(children=markdown_text)]),
    # dcc.Input(id='input', value='', type='text'),
    html.Div(id='output-graph'),
    html.Label('Select the following years for the label data: '),
    dcc.Dropdown(
        id='input',
        options=[
            {'label': 'S8072135 Night Data Bat Calls', 'value': 'S8072135.07#.csv'},
            {'label': 'S8072159 Night Data Bat Calls', 'value': 'S8072159.22#.csv'},
            {'label': 'S8072143 Night Data Bat Calls', 'value': 'S8072143.12#.csv'},
        ],
        value=['S8072143.12#.csv'],
        multi=False
    ),
])


@app.callback(
    Output(component_id='output-graph', component_property='children'),
    [Input(component_id='input', component_property='value')]
)
def update_value(input_data):
    df = pd.DataFrame.from_csv(input_data, sep=',')
    df.reset_index(inplace=True)
    return dcc.Graph(
        id='BatData',
        figure={
            'data': [
                go.Scatter(
                    x=df['Time'],
                    y=df['Frequency'],
                    text=df['Filename'],
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


if __name__ == '__main__':
    app.run_server(debug=True)
