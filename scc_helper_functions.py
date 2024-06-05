import re
import math
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib as plt
from matplotlib import pyplot as plt
from scipy.optimize import curve_fit
from matplotlib.widgets import SpanSelector 
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px
import plotly



######################################## POST CSV ANALYSIS ######################################################################################################################

def load_dataframe_csv(file):
  '''Used for ephys data that has been added to a CSV. For the purposes of making this code, this is for ephys data that has already be processed
  and is more user friendly since it is used as a learning tool. The function just takes the SVA and converts it to a dataframe.

  Inputs:
  file: CSV file generated from the ascii file containing the electrophysiology recording data.

  Outputs:
  df: dataframe of the CSV file containing already processed ephys data'''

  df = pd.read_csv(file)
  return df

def summary_plots_csv(df):
  '''Loads all sweep and plots them. This function is specific to the data that is contained in dfs generated from the example CSV file.

  Inputs:
  df: processed dataframe containing voltage and current data.

  Outputs:
  fig: an interactive plotly figure that shows voltage sweep and subsequent ephys recording for each'''

  #make subplot with one column and enough rows for the pressure step and current for all sweeps
  subplot_titles = ['Voltage Steps']
  grouped = df.groupby('voltages')
  for name, group in grouped:
    voltage = group['voltages'].max()
    voltage_string = str(voltage) + ' mV'
    subplot_titles.append(voltage_string)

  fig = make_subplots(rows = int(df['sweep'].max() + 3), cols=1, subplot_titles=subplot_titles)

  #go through each sweep and plot the current
  for name, group in df.groupby('sweep'):
      fig.add_trace(go.Scatter(mode='lines', name=name, x = group['ti'], y = group['voltages'], marker=dict(color='maroon'), connectgaps=False), row = 1, col = 1)
      fig.update_yaxes(title_text= 'Voltage (mV)', row=1, col=1)
      fig.add_trace(go.Scatter(mode='lines', name=name, x = group['ti'], y=group['i'],  marker=dict(color='black')), row= name + 2, col=1)          
      fig.update_yaxes(title_text= 'Current (pA)', row=name + 2, col=1)

  fig.update_layout(
    autosize=True,
    width=1000,
    height=1000,
    margin=dict(
        l=50,
        r=50,
        b=50,
        t=50,
        pad=4),
        showlegend=False)
  
  return fig

def basic_current_histo(df_cut, bins):
  fig = plt.hist(df_cut['i'], bins = bins, align= 'mid', edgecolor = 'black', color = 'white')
  plt.xlabel('current (pA)', fontsize = 15)
  plt.ylabel('Count', fontsize = 15)

  return fig

def isolate_openings(df, voltage, start_t, end_t):
  isolated_data = df.loc[(df['voltages'] == voltage) & (df['ti'].between(start_t, end_t))]
  sns.lineplot(x = 'ti', y = 'i', data = isolated_data, color = 'black')
  plt.xlabel('Time (ms)', fontsize = 15)
  plt.ylabel('Current (pA)', fontsize = 15)

  return isolated_data

def _1gaussian(x, amp1,cen1,sigma1):
    return amp1*(1/(sigma1*(np.sqrt(2*np.pi))))*(np.exp((-1.0/2.0)*(((x-cen1)/sigma1)**2)))

def _2gaussian(x, amp1,cen1,sigma1, amp2,cen2,sigma2):
    return amp1*(1/(sigma1*(np.sqrt(2*np.pi))))*(np.exp((-1.0/2.0)*(((x-cen1)/sigma1)**2))) + \
            amp2*(1/(sigma2*(np.sqrt(2*np.pi))))*(np.exp((-1.0/2.0)*(((x-cen2)/sigma2)**2)))

def double_fit_plot(current_histogram, df_cut, fit_guesses, bins):
  xdata = current_histogram[1]
  xdata = xdata[1:]
  ydata = current_histogram[0]

  popt_2gauss, pcov_2gauss = curve_fit(_2gaussian, xdata, ydata, p0 = fit_guesses)
  pars_1 = popt_2gauss[0:3]
  pars_2 = popt_2gauss[3:6]
  
  fitline1 = np.linspace(min(xdata), max(xdata), 400)
  fitline2 = np.linspace(min(xdata), max(xdata), 400)



  fig = plt.figure()
  plt.hist(df_cut['i'], bins = bins, align= 'mid', edgecolor = 'black', color = 'white', zorder = 1)
  plt.fill_between(fitline1, _1gaussian(fitline1, *pars_1), color = 'yellow', alpha = 0.6,  zorder = 2)
  plt.fill_between(fitline2, _1gaussian(fitline2, *pars_2), color = 'pink', alpha = 0.6,  zorder = 3)
  plt.xlabel('current (pA)', fontsize = 15)
  plt.ylabel('Count', fontsize = 15)

  if  pars_1[1] > pars_2[1]:
    print('Unitary current =', pars_2[1] - pars_1[1])
  if  pars_1[1] < pars_2[1]:
    print('Unitary current =', pars_1[1] - pars_2[1])

  return fig, pars_1[1], pars_2[1]

def linear_fit(x, a, b):
    y = (a * x) + b
    return y

def reversal_potential_file(file):
  df = pd.read_csv(file)
  popt, pcov = curve_fit(linear_fit, df['voltage'], df['current'])

  fitline = np.linspace(df['voltage'].min(), df['voltage'].max(), 400)
  sns.lineplot(x = fitline, y = linear_fit(fitline, *popt), color = 'red')
  sns.scatterplot(x = df['voltage'], y = df['current'], color = 'midnightblue', )
  plt.axvline(x=0, color = 'black')
  plt.axhline(y=0, color = 'black')
  plt.plot((-popt[1] / popt[0]), 0,  marker="o", markersize=20, color = 'gold')
  plt.ylim()
  reveral_pot = -popt[1] / popt[0]
  print('Reversal potential =', round(reveral_pot, 4), 'mV')
  print('Sigle channel conductance =', round(popt[0]*10**3, 4), 'pS')

def channel_properties(voltage_list, unitary_current_list):
    data = {'voltage': voltage_list, 'current':unitary_current_list}
    df = pd.DataFrame(data)
    popt, pcov = curve_fit(linear_fit, df['voltage'], df['current'])
    fitline = np.linspace(df['voltage'].min(), 0, 100)

    fig, ax=plt.subplots(figsize=(10,6))

    sns.lineplot(x = fitline, y = linear_fit(fitline, *popt), color = 'black', linestyle='--', ax=ax)
    sns.scatterplot(x = df['voltage'], y = df['current'], hue=df['voltage'], palette='cool', ax=ax, 
                    edgecolor='black', s=200)
    ax.axvline(x=0, color = 'black')
    ax.axhline(y=0, color = 'black')
    ax.plot((-popt[1] / popt[0]), 0,  marker="o", markersize=20, color = 'gold')

    ax.set_xlabel('Voltage (mV)', fontsize = 20)
    ax.set_ylabel('Current(pA)', fontsize = 20)
    ax.tick_params(axis='both', labelsize=20)
    ax.get_legend().remove()
    reveral_pot = -popt[1] / popt[0]
    print('Reversal potential =', round(reveral_pot, 4), 'mV')
    print('Sigle channel conductance =', round(popt[0]*10**3, 4), 'pS')

    return fig

######################################## ASC FILE PROCESSING ######################################################################################################################
def load_dataframe_asc(file):

    '''Loads and processes the raw ascii file and converts it into a useable dataframe. It removes the headers, empty lines scattered throughout, renames
    the headers, and adds a "sweep" clumn to determine what data belongs to what sweep and therefore what negative pressure.

    Inputs:
    file: ascii file generated by the electrophysiology recording software patchmaster.

    Outputs:
    df: organized and processed dataframe containing original file data along with a sweep number column'''

    with open(file, 'r') as fhand:
    #removes spaces and separates string at \n
        raw_file = fhand.read().strip().split('\n')

    line_index = []
    count = 0
    #finding the lines that are not headers/have text in them/are blank and indexing them
    for line in raw_file:
        if re.search(r'[a-z]+', line) == None:
          line_index.append(count)
        count += 1

    #picking out data lines and adding them to this new list of lists
    processed_file = [raw_file[i].strip().replace(" ", "").split(",") for i in line_index]

    #determining the number of sweeps
    #original file has title (1 line) and each sweep has a header (2 lines)
    nsweeps = int((len(raw_file) - len(processed_file)-1)/2)

    #determining column names based on the length of  processed_file[0]
    if len(processed_file[0]) == 5:
          colnames = ['index','ti','i','tv','v']
    else:
          colnames = ['index','ti','i','tp','p','tv','v']

    df = pd.DataFrame(columns = colnames, data = processed_file)
    df = df.apply(pd.to_numeric)
    df = df.dropna(axis=0)

    #adding in sweeps
    datapoint_per_sweep = len(df) / nsweeps
    df['sweep'] = np.repeat(np.arange(nsweeps), datapoint_per_sweep)

    #adding in voltage in terms of mV
    df['voltages'] = round(df['v'] * 1000)

    #converting values to more user friendly units
    df['ti'] *= 1000
    df['i'] *= 1e12

    #making a voltage_step_id
    voltage_id_list=[]
    grouped=df.groupby(['sweep'])
    for name,group in grouped:
        voltage_id=int(group['voltages'].min())
        voltage_id_list+=[voltage_id]*len(group)
    df['voltage_id']=voltage_id_list

    return(df)

def summary_plots_asc(df):
    
    '''Loads all sweep and plots them. The top plot will show the voltage sweeps and each subsequent sweep show the ephys recordings for each voltage sweep.

    Inputs:
    df: processed dataframe containing voltage and current data.

    Outputs:
    fig: an interactive plotly figure that shows voltage sweep and subsequent ephys recording for each'''

    #make subplot with one column and enough rows for the pressure step and current for all sweeps
    subplot_titles = ['Voltage Steps']
    grouped = df.groupby('sweep')

    #generating a list to label each of the plots that will be generated later
    for name, group in grouped:
        voltage = group['voltage_id'].mode().iloc[0]
        voltage_string = str(voltage) + ' mV'
        subplot_titles.append(voltage_string)

    #generate the plotly figure that data will be added to
    fig = make_subplots(rows = int(df['sweep'].max() + 3), cols=1, subplot_titles=subplot_titles)

  #go through each sweep and plot the current
    for name, group in df.groupby('sweep'):
        group=group.loc[group['ti'].between(100, 10000)]
        fig.add_trace(go.Scatter(mode='lines', name=name, x = group['ti'], y = group['voltages'], marker=dict(color='maroon'), connectgaps=False), row = 1, col = 1) #adds voltage to voltage plot
        fig.update_yaxes(title_text= 'Voltage (mV)', row=1, col=1)
        fig.add_trace(go.Scatter(mode='lines', name=name, x = group['ti'], y=group['i'],  marker=dict(color='black')), row= name + 2, col=1) #adds ephys data to a new plot
        fig.update_yaxes(title_text= 'Current (pA)', row=name + 2, col=1)
    
    #figure parameters
    fig.update_layout(
    autosize=True,
    width=1000,
    height=1000,
    margin=dict(
        l=50,
        r=50,
        b=50,
        t=50,
        pad=4),
        showlegend=False)

    return fig

