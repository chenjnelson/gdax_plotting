import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import gdax
import pandas as pd
import datetime
import time
import talib
import numpy as np

pd.options.mode.chained_assignment = None  # default='warn'
np.seterr(invalid='ignore')
public_client = gdax.PublicClient()

#5 minute candles
def get_data(pair):
    df = pd.DataFrame(public_client.get_product_historic_rates(pair, start = (datetime.datetime.now()-datetime.timedelta(minutes=720)).isoformat(), end = datetime.datetime.now().isoformat(), granularity=300))
    df.columns = ['time', 'low', 'high', 'open_price', 'close_price', 'volume']
    df['time'] = pd.to_datetime(df['time'],unit='s').dt.strftime("%H:%M")
    return (df[['open_price','close_price','high','low','volume','time']].sort_values('time',ascending=True).reset_index(drop=True))

def plot_candles(pricing, title=None,
                 volume_bars=False,
                 color_function=None,
                 overlays=None,
                 rsi = None,
                 adx = None,
                 macd = None,
                 cycles2 = None,
                 ad = None,
                 stoch = None,
                 cycles_title = None,
                 cycles = None,
                 cycles2_title = None,
                 technicals=None,
                 technicals_titles=None):

    def default_color(index, open_price, close_price, low, high):
        return 'r' if open_price[index] > close_price[index] else 'g'

    color_function = color_function or default_color
    overlays = overlays or []
    technicals = technicals or []
    technicals_titles = technicals_titles or []
    open_price = pricing['open_price']
    close_price = pricing['close_price']
    low = pricing['low']
    high = pricing['high']
    oc_min = pd.concat([open_price, close_price], axis=1).min(axis=1)
    oc_max = pd.concat([open_price, close_price], axis=1).max(axis=1)
    
    subplot_count = 1
    if volume_bars:
        subplot_count += 1
    if cycles:
        subplot_count += 1
    if macd:
        subplot_count += 1
    if adx:
        subplot_count += 1
    if stoch:
        subplot_count += 1
    if rsi:
        subplot_count += 1
    if ad:
        subplot_count += 1
    if cycles2:
        subplot_count += 1
    if technicals:
        subplot_count += len(technicals)
    
    if subplot_count == 1:
        fig, ax = plt.subplots(1, 1)
    else:
        ratios = np.insert(np.full(subplot_count - 1, 1), 0, 3)
        fig, subplots = plt.subplots(subplot_count, 1, sharex=True, gridspec_kw={'height_ratios': ratios}, figsize = (12,5))
        ax = subplots[0]
        
    if title:
        ax.set_title(title)
    
    x = np.arange(len(pricing))

    candle_colors = [color_function(i, open_price, close_price, low, high) for i in x]
    candles = ax.bar(x, oc_max-oc_min, bottom=oc_min, color=candle_colors, linewidth=0)
    lines = ax.vlines(x , low, high, color=candle_colors, linewidth=1)
    ax.xaxis.grid(False)
    ax.xaxis.set_tick_params(which='major', length=2.0, direction='in', top='off')

    frequency = 'minute' 
    if frequency == 'minute':
        time_format = '%H:%M'

    #Hacky ass way to reduce time intervals lmao
    plot_time = pricing['time']
    for index, item in enumerate(pricing['time']):
        if (index % 15):
            plot_time.loc[index] = ' '

    plt.xticks(x, plot_time, rotation='vertical')
    
    for overlay in overlays:
        ax.plot(x, (overlay))
            
    # Plot volume bars if needed
    if volume_bars:
        ax2 = subplots[1]
        volume = pricing['volume']
        volume_scale = None
        scaled_volume = volume
        if volume.max() > 1000000:
            volume_scale = 'M'
            scaled_volume = volume / 1000000
        elif volume.max() > 1000:
            volume_scale = 'K'
            scaled_volume = volume / 1000
        ax2.bar(x, scaled_volume, color=candle_colors)
        volume_title = 'Volume'
        if volume_scale:
            volume_title = 'Volume (%s)' % volume_scale
        ax2.set_title(volume_title, loc = 'left', fontsize = 8)
        ax.xaxis.grid(False)

    if rsi:
        if volume_bars:
            ax = subplots[2] 
        else:
            ax =subplots[1]
        ax.plot(x,np.transpose(rsi))
        ax.set_title('RSI - **70+ is overbought, 30- is oversold', loc = 'left', fontsize = 8)
        ax.fill_between(x, 30,70,facecolor= 'yellow',alpha = .2)
    
    if stoch:
        if volume_bars:
            ax = subplots[4] 
        else:
            ax =subplots[3]   
        ax.plot(x,stoch[0],x,stoch[1])
        ax.set_title('Stochastic Oscillator - **80+ is overbought, 20- is oversold,  blue crossing orange signals a buy or sell', loc = 'left', fontsize = 8)
        ax.fill_between(x, 20,80,facecolor= 'yellow',alpha = .2)

    if ad:
        y = ad[0]
        if volume_bars:
            ax = subplots[3] 
        else:
            ax =subplots[2]   
        ax.plot(x,y)
        ax.fill_between(x, 0, y, where= y > 0, facecolor= '#2ca02c', alpha = .4)
        ax.fill_between(x, 0, y, where= y < 0, color= 'r', alpha = .4)
        ax.set_title('Chaikin Accumulation/Distribution Indicator - **measure of momentum of the A/D line using MACD formula', loc = 'left', fontsize = 8)
        
    if macd:
        y = macd[2]
        ax = subplots[1]
        ax.plot(x,np.transpose(macd))
        ax.fill_between(x, 0, y,facecolor= '#2ca02c')
        ax.set_title('MACD - **blue line (MACD) crossing orange (MACDSIGNAL) hints bullish trend', loc = 'left', fontsize = 8)

    if adx:
        ax = subplots[subplot_count-1]
        ax.plot(x,adx[0],x,adx[1],x,adx[2])
        ax.set_title('ADX (green) - ** blue (Plus_DI) above orange (Minus_DI) hints upwards movement', loc = 'left', fontsize = 8)
        ax.axhspan(25, 50, color='orange', alpha=0.05)
        ax.axhspan(50, 75, color='yellow', alpha=0.05)
        ax.axhspan(75, 100, color='green', alpha=0.05)
        ax.fill_between(x, adx[0], adx[1], where= adx[0] > adx[1],facecolor= '#1f77b4',alpha = .2)
        ax.fill_between(x, adx[0], adx[1], where= adx[1] > adx[0],facecolor= '#ff7f0e',alpha = .2)

    # Plot additional technical indicators
    for (i, technical) in enumerate(technicals):
        if volume_bars:
            ax = subplots[i - len(technicals)]
        else:
            ax = subplots[i - len(technicals)-2]
        ax.plot(x, technical)
        if i < len(technicals_titles):
            ax.set_title(technicals_titles[i], loc = 'left', fontsize = 8)
    
    if cycles:
        ax = subplots[subplot_count-2]
        ax.plot(x,np.transpose(cycles))
        ax.set_title(cycles_title, loc = 'left', fontsize = 8)

    if cycles2:
        ax = subplots[subplot_count-1]
        ax.plot(x,np.transpose(cycles2))
        ax.set_title(cycles2_title, loc = 'left', fontsize = 8)

    plt.subplots_adjust(bottom=0.15, right=0.9, top=0.94, hspace = .28)

    plt.show()

def plot_graph1(coin,name):
    def highlights(index, open_price, close_price, low, high):
        return 'm' if dojis[index] else 'r' if open_price[index] > close_price[index] else 'g'
    #Mesa Adaptive Moving Average; sort of sinusoidal but staircase lag prevents whipsaw trades, also based on how close fast and slow is
    #Fast (blue),then slow/following (orange)
    MAMA0,MAMA1 = talib.MAMA(np.array(coin['close_price']),fastlimit = .7, slowlimit =.35)
    
    #Hilbert Indicators; sine, leadsine
    HT_SINE0,HT_SINE1 = talib.HT_SINE(np.asarray(coin['close_price']))
    HT_DCPERIOD = talib.HT_DCPERIOD(np.array(coin['close_price']))
    HT_DCPHASE = talib.HT_DCPHASE(np.array(coin['close_price']))
    inphase,quadrature = talib.HT_PHASOR(np.array(coin['close_price']))
    HT_TRENDMODE = talib.HT_TRENDMODE(np.array(coin['close_price']))
    plot_candles(coin , title= name + ": {} to {}".format(coin['time'].iloc[0] , coin['time'].iloc[-1] ), 
                volume_bars = False, 
                overlays=[MAMA0,MAMA1],
                cycles = [HT_SINE0,HT_SINE1],
                cycles2 = [inphase,quadrature],
                cycles_title = 'Hilbert Transformation - Sine',
                cycles2_title = 'Hilbert Transformation - Phasor',
                technicals=[HT_TRENDMODE,HT_DCPERIOD,HT_DCPHASE],
                rsi = None,
                technicals_titles=['HT_TRENDMODE','HT_DCPERIOD','HT_DCPHASE'], 
                color_function=None)

#ADOSC, RSI, Candlestick patterns
def plot_graph2(coin,name):
    #Magenta
        #doji, represents indecision
    #Cyan
        #engulfing possible reversal
        #hammer, bullish reversal (end of downtrend)
        #hangingman, bearish reversal
        #harami, possible reversal which the engulfing pattern precedes
    #Black
        #dark cloud candle, highest candlestick is compared to first three but is red so sellers take profits early, bearish
        #shooting star, bearish reversal (end of uptrend), includes 3 green candles preceeding
    #Red/Green otherwise

    engulfing = talib.CDLENGULFING(coin['open_price'].as_matrix(),coin['high'].as_matrix(),coin['low'].as_matrix(),coin['close_price'].as_matrix())
    dojis = talib.CDLDOJI(coin['open_price'].as_matrix(),coin['high'].as_matrix(),coin['low'].as_matrix(),coin['close_price'].as_matrix())
    hammer = talib.CDLHAMMER(coin['open_price'].as_matrix(),coin['high'].as_matrix(),coin['low'].as_matrix(),coin['close_price'].as_matrix())
    shooting = talib.CDLSHOOTINGSTAR(coin['open_price'].as_matrix(),coin['high'].as_matrix(),coin['low'].as_matrix(),coin['close_price'].as_matrix())
    hangingman = talib.CDLHANGINGMAN(coin['open_price'].as_matrix(),coin['high'].as_matrix(),coin['low'].as_matrix(),coin['close_price'].as_matrix())
    harami = talib.CDLHARAMI(coin['open_price'].as_matrix(),coin['high'].as_matrix(),coin['low'].as_matrix(),coin['close_price'].as_matrix())
    dark = talib.CDLDARKCLOUDCOVER(coin['open_price'].as_matrix(),coin['high'].as_matrix(),coin['low'].as_matrix(),coin['close_price'].as_matrix())

    def highlights(index, open_price, close_price, low, high):
        return 'm' if dojis[index] else 'c' if engulfing[index] or hammer[index] or hangingman[index] or harami[index] else 'k' if shooting[index] or dark[index] else 'r' if open_price[index] > close_price[index] else 'g'

    fastk, fastd = talib.STOCH(coin['high'].as_matrix(),coin['low'].as_matrix(),coin['close_price'].as_matrix())
    ADOSC = talib.ADOSC(coin['high'].as_matrix(),coin['low'].as_matrix(),coin['close_price'].as_matrix(),np.array(coin['volume']))
    RSI = talib.RSI(coin['close_price'].as_matrix())

    #HT Trendline (like moving average but less lag) - long if price is above this line and short if price is below
    HT_TRENDLINE = talib.HT_TRENDLINE(coin['close_price'].as_matrix())

    plot_candles(coin , title=name + ": {} to {}".format(coin['time'].iloc[0] , coin['time'].iloc[-1] ), 
                volume_bars = True, 
                overlays= [HT_TRENDLINE],
                cycles = None,
                cycles_title = None,
                technicals=None,
                ad = [ADOSC],
                rsi = [RSI],
                stoch = [fastk, fastd],
                technicals_titles=None, 
                color_function=highlights)

#MACD and ADX
def plot_graph3(coin,name):
    #For MACD: if blue line (MACD) falls below orange (signal), it is bearish. Histogram shows the diff between the two
    #ADX: strength of the trend, 25+ indicates strong trend aka momentum of the movement (can be falling quickly)
    ADX = talib.ADX(coin['high'].as_matrix(),coin['low'].as_matrix(),coin['close_price'].as_matrix())
    PLUS_DI = talib.PLUS_DI(coin['high'].as_matrix(),coin['low'].as_matrix(),coin['close_price'].as_matrix())
    MINUS_DI = talib.MINUS_DI(coin['high'].as_matrix(),coin['low'].as_matrix(),coin['close_price'].as_matrix())
    macd,macdsignal,macdhist = talib.MACD(coin['close_price'].as_matrix())

    plot_candles(coin , title=name + ": {} to {}".format(coin['time'].iloc[0] , coin['time'].iloc[-1] ), 
                volume_bars = False, 
                overlays= None,
                cycles = None,
                cycles_title = None,
                technicals=None,
                rsi = None,
                adx = [PLUS_DI,MINUS_DI,ADX],
                macd = [macd,macdsignal,macdhist],
                color_function=None)

btc = get_data('BTC-USD')
plot_graph1(btc,'BTC-USD')
plot_graph2(btc,'BTC-USD')
plot_graph3(btc,'BTC-USD')

#help(talib.HT_TRENDLINE)
#print (plt.rcParams['axes.color_cycle']) #blue is first, orange is second, green is last


