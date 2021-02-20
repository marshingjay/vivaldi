from indicators.indicator import Indicator
from talib import CMO as talib_CMO
from data.data_queue import DataQueue


class CMO(Indicator):
    def __init__(self, params, name, scalingWindowSize, value):
        super().__init__(params, name, scalingWindowSize, value)
        period = self.params['period']
        self.values = DataQueue(maxlen=period)
        self.results = DataQueue()
    
    
    def compute(self, data):
        self.values.queue.append(data[self.value])
        
        
        if len(self.values.queue) == self.params['period']:
            result = talib_CMO(self.high_values.queue, self.low_values.queue, self.close_values.queue, timeperiod=self.params['period'])[-1]
            results.addData(result)
            scaled_result = 0.5
            if results.curMax != results.curMin:
                scaled_result = (result - results.curMin) / (results.curMax - results.curMin)
            return {self.name: scaled_result}
        else:
            return {}