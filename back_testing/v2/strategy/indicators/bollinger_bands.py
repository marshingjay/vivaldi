'''
FILE: bollinger_bands.py
AUTHORS:
    -> Jacob Marshall (marshingjay@gmail.com)
WHAT:
    -> This file contains the Bollinger Band Indicator
'''
from v2.strategy.indicators.indicator import Indicator
from v2.strategy.indicators.param import Param
from v2.utils import findParams
from v2.strategy.indicators.sma import SMA
from talib import BBANDS
import pandas

'''
CLASS: EMA
WHAT:
    -> Implements the Bollinger Bands Indicator and adds the approprite columns to the dataset
    -> What are Bollinger Bands? --> 
    -> Params Required:
        -> 'period'
'''

class BollingerBands(Indicator):
    '''
    ARGS:
        -> dataset (DataFrame): dataset to add the indicator values as a column to
        -> gen_new_values (Boolean) <optional>: weather or not we should generate new values for each param belonging
            to this Indicator
        -> value (String) <optional>: dataframe column name to use for calculations
    RETURN:
        -> None
    WHAT: 
        -> calculates and adds the Bollinger Bands of the specified value over the given period to the dataset
    '''
    def genData(self, dataset, gen_new_values=True):
        dev_down, dev_up, period = findParams(self.params, ['nbdevup', 'nbdevdn', 'period'])
        
        if gen_new_values:
            if dev_down and dev_up:
                dev_down.genValue()
                dev_up.genValue()
            period.genValue()
        if dev_down and dev_up:
            dataset['boll_upper' + self.appended_name], dataset['boll_middle' + self.appended_name], dataset['boll_lower' + self.appended_name] = BBANDS(dataset[self.value], timeperiod=getattr(period, self.value), nbdevup=getattr(dev_up, self.value), nbdevdown=getattr(dev_down, self.value))
        else:
            dataset['boll_upper' + self.appended_name], dataset['boll_middle' + self.appended_name], dataset['boll_lower' + self.appended_name] = BBANDS(dataset[self.value], timeperiod=getattr(period, self.value))

        return ['boll_upper' + self.appended_name, 'boll_upper' + self.appended_name]
    def setDefaultParams(self):
        self.params = [
            Param(0.1, 5.0, 1, 'nbdevup', 2.0),
            Param(0.1, 5.0, 1, 'nbdevdn', 2.0),
            Param(5, 10000, 1, 'period', 400)
        ]