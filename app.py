########################################################

# DASH WEB APP FOR VISUALIZING RANCHER NUMBERS PROJECT
# Run this app with `python app.py` and
# visit http://0.0.0.0:8050/ in your web browser.

########################################################

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc
from dash import html
from dictionaries import titles_Dict, legends_Dict

## Read in cleaned, (State, Year) - level data
data = pd.read_excel('data/family_farmer_estimates_state_year_level.xlsx')
data = data[data['State'] != "United States"] # only analyze every state
data['Year'] = data['Year'].astype(str)
# Join state codes
state_codes = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/2011_us_ag_exports.csv').loc[:, ['code', 'state']]
state_codes = state_codes.rename(columns = {'state': 'State'})
data = data.merge(state_codes, on='State')

###### COMPUTE NORMALIZATION METRICS #####
## farmers per person, no feed
data['farmers_no_feed_per_person'] = data['Farmers_in_animal_ag_no_feed'] / data['Total_Population']
## farmers per person, feed
data['farmers_feed_per_person'] = data['Farmers_in_animal_ag_feed'] / data['Total_Population']
## farmers per registered voter, no feed
data['farmers_no_feed_per_voter'] = data['Farmers_in_animal_ag_no_feed'] / data['Total_Registered']
## farmers per registered voter, feed
data['farmers_feed_per_voter'] = data['Farmers_in_animal_ag_feed'] / data['Total_Registered']
###### END NORMALIZATION METRICS ######

###### CREATE DASH APPLICATION ######
app = dash.Dash(__name__)
server = app.server

app.layout = html.Div( 
    children=[
        # Header
        html.H1(
            children='Rancher Numbers Dashboard',
            style={
                'textAlign': 'center',
                'color': 'white',
                'backgroundColor': 'darkcyan'
            }
        ),
        # Map Description
        html.Div(
            children='Select a metric to visualize in the maps and tables below:', 
            style={
                'textAlign': 'left',
                'color': 'black',
                'backgroundColor': 'white'
            }
        ),
        # Map Dropdown
        dcc.Dropdown(
            id='map_dropdown',
            options=[{'label': v, 'value': k} for (k, v) in titles_Dict.items()],
            value="Farmers_in_animal_ag_no_feed"
        ),
        # Map Header
        html.H2(
            children='Geographic Distribution',
            style={
                'textAlign': 'center',
                'color': 'white',
                'backgroundColor': 'darkcyan'
            }
        ),
        # Map
        html.Hr(),
        dcc.Graph(
            id='map_figure'
        ),
        # 2012 Table Description Description
        html.H2(
            children='Data Table for the selected metric in 2012', 
            style={
                'textAlign': 'center',
                'color': 'white',
                'backgroundColor': 'darkcyan'
            }
        ),
        html.Div(
            children='This table displays the same data used to create the 2012 map above, and the metric of interest is sorted in decreasing order.', 
            style={
                'textAlign': 'left',
                'color': 'black',
                'backgroundColor': 'white'
            }
        ),
        # 2012 Table
        dcc.Graph(
            id='table_figure_2012'
        ),
        # 2017 Table Description Description
        html.H2(
            children='Data Table for the selected metric in 2017', 
            style={
                'textAlign': 'center',
                'color': 'white',
                'backgroundColor': 'darkcyan'
            }
        ),
        html.Div(
            children='This table displays the same data  used to create the 2017 map above, and the metric of interest is sorted in decreasing order.', 
            style={
                'textAlign': 'left',
                'color': 'black',
                'backgroundColor': 'white'
            }
        ),
        # 2017 Table
        dcc.Graph(
            id='table_figure_2017'
        ),
        # Bottom Text
        html.Div(
            children=[
                html.Label(
                    children='The data used to generate these maps is public available through the U.S. Department of Agriculture and the U.S. Census Bureau.', 
                    style={
                        'textAlign': 'left',
                        'color': 'black',
                        'backgroundColor': 'white'
                    }
                ),
                html.Label(
                    children = ['  For an overview of the project, and for details on how some of these metrics were calculated, refer to this ', 
                        dcc.Link('repository', href='https://github.com/Kendall-Kikkawa/GFI_rancher_project'),
                        "."
                    ],
                    style={
                        'color': 'black',
                        'backgroundColor': 'white'
                    }
                )
            ]
        )
    ]
)

@app.callback(
    dash.dependencies.Output('map_figure', 'figure'),
    [dash.dependencies.Input('map_dropdown', 'value')])
def update_map(value):
    """
    Updates the Map based upon the desired quantity to plot - the figure plots the value in each state of
    the U.S. in the years 2017 and 2012

    Args:
        value (string): String describing the metric to be plotted

    Returns:
        figure (px.Figure): figure to be displayed on the Dash app
    """
    fig = px.choropleth(data,
        locations = 'code', # State Code for spatial coordinates
        color = value, # Data to be color-coded
        facet_col='Year',
        locationmode = 'USA-states', # set of locations match entries in `locations`
        scope='usa',
        title=titles_Dict[value],
        labels={
            value: legends_Dict[value]
        },
        color_continuous_scale="speed"
    )
    return fig


@app.callback(
    [dash.dependencies.Output('table_figure_2012', 'figure'), 
    dash.dependencies.Output('table_figure_2017', 'figure')],
    dash.dependencies.Input('map_dropdown', 'value'))
def update_table(value):
    """
    Updates the Table based upon the desired quantity to sort on, drops all other columns
    - rearranges table so that sorted table goes 3rd (after State, code)

    Args:
        value (string): String describing the metric to be plotted

    Returns:
        figure (px.Figure): table to be displayed on the Dash app
    """
    ### Create Data Frame for 2012
    data_2012 = data[data['Year'] == '2012']
    data_2012 = data_2012.reset_index()
    data_2012 = data_2012.drop(columns=['Year'])
    # Shift code and value columns
    code_col = data_2012.pop('code')
    data_2012.insert(1, 'code', code_col)
    value_col = data_2012.pop(value)
    data_2012.insert(2, value, value_col)
    # Drop all other columns
    data_2012 = data_2012.loc[:, ['State', 'code', value]]
    data_2012 = data_2012.sort_values(by=[value], ascending=False)
    data_2012[value] = data_2012[value].round(4)

    ### Create 2012 Table
    fig_2012 = go.Figure()
    fig_2012.add_table(cells=dict(
                        values=[data_2012[col].tolist() for col in ['State', 'code', value]]
                        ), 
                  header=dict(values=['State', 'State Code', titles_Dict[value] + ' in 2012'])
                 )

    ### Create Data Frame for 2017
    data_2017 = data[data['Year'] == '2017']
    data_2017 = data_2017.reset_index()
    data_2017 = data_2017.drop(columns=['Year'])
    # Shift code and value columns
    code_col = data_2017.pop('code')
    data_2017.insert(1, 'code', code_col)
    value_col = data_2017.pop(value)
    data_2017.insert(2, value, value_col)
    # Drop all other columns
    data_2017 = data_2017.loc[:, ['State', 'code', value]]
    data_2017 = data_2017.sort_values(by=[value], ascending=False)
    data_2017[value] = data_2017[value].round(4)

    ### Create 2017 Table
    fig_2017 = go.Figure()
    fig_2017.add_table(cells=dict(
                    values=[data_2017[col].tolist() for col in ['State', 'code', value]]
                    ), 
                header=dict(values=['State', 'State Code', titles_Dict[value] + ' in 2017'])
                )

    return fig_2012, fig_2017

###### END DASH APPLICATION ######


if __name__ == '__main__':
    app.run_server(host='0.0.0.0')
