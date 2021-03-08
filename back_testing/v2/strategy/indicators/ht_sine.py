'''
FILE: ht_trendline.py
AUTHORS:
    -> Jacob Marshall (marshingjay@gmail.com)
WHAT:
    -> This file contains the ADX Indicator
'''

import pandas
import numpy as np


from v2.strategy.indicators.param import Param
from v2.strategy.indicators.indicator import Indicator
from v2.utils import findParams

from talib import HT_SINE as talib_HT

'''
CLASS: ADX
WHAT:
    -> What is beta? --> https://www.investopedia.com/terms/a/adx.asp
    -> Params Required:
        -> 'period'
'''
class HT_SINE(Indicator):

    '''
    ARGS:
        -> dataset (DataFrame): dataset to add the indicator values as a column to
        -> gen_new_values (Boolean) <optional>: weather or not we should generate new values for each param belonging
            to this Indicator
        -> value (String) <optional>: dataframe column name to use for calculations
    RETURN:
        -> None
    WHAT: 
        -> calculates Hilbert Transform trendline for the given period
    '''
    def genData(self, dataset, gen_new_values=True):

        dataset[self.name + '_sine'], dataset[self.name + '_leadsine'] = talib_HT(dataset[self.value])
        return [self.name + '_sine', self.name + '_leadsine']

    def setDefaultParams(self):
        return []