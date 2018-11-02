import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go

df = pd.DataFrame.from_csv('2018_night.txt', sep='\t')

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


def generate_table(dataframe, max_rows=1000):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )


app.layout = html.Div(children=[
    html.H1(children='Bat Echolocation Data'),

    html.Div(children='''
        Hadi Soufi, Yang Peng, Bety Rostandy, Thien Le, Kevin Keomalaythong
    '''),
    dcc.Graph(
        id='2018-night.txt',
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
                title='Bat Recording for all the Night in 2018',
                xaxis=dict(
                    title='Date(Night)'
                ),
                yaxis=dict(
                    title='Number of Calls'
                )
            )
        }
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
