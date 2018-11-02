import pandas as pd
import plotly.graph_objs as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

app = dash.Dash()

app.layout = html.Div(children=[
    html.H1(children='Bat Echolocation Data'),

    html.H4(children='Hadi Soufi, Yang Peng, Bety Rostandy, Thien Le, Kevin Keomalaythong'),
    html.Div(children='''
        \n Please input the Year:
    '''),
    dcc.Input(id='input', value='', type='text'),
    html.Div(id='output-graph'),
])


@app.callback(
    Output(component_id='output-graph', component_property='children'),
    [Input(component_id='input', component_property='value')]
)
def update_value(input_data):
    df = pd.DataFrame.from_csv((input_data + '_night.txt'), sep='\t')
    df.reset_index(inplace=True)

    return dcc.Graph(
        id='example-graph',
        figure={
            'data': [
                go.Scatter(
                    x=df[df['Label'] == i]['Night'],
                    y=df[df['Label'] == i]['Number'],
                    text=df[df['Label'] == i]['Folder2'],
                    mode='markers',
                    opacity=0.7,
                    marker={
                        'size': 15,
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
