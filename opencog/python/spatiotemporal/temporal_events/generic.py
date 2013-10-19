from datetime import datetime
from scipy import integrate
from spatiotemporal.time_intervals import assert_is_time_interval, TimeInterval, TimeIntervalListBased
from fuzzy.membership_function import MembershipFunctionPiecewiseLinear
from spatiotemporal.unix_time import UnixTime
from utility.numeric.globals import EPSILON

__author__ = 'keyvan'


class BaseTemporalEvent(TimeInterval):
    def membership_function(self, time=None):
        if time is None:
            time = self

        result = []
        try:
            for point in time:
                result.append(self.membership_function_single_point(point))
        except:
            return self.membership_function_single_point(time)
        return result

    def membership_function_single_point(self, time_step):
        """
        to override, membership_function calls to it
        alternatively one can directly override membership_function
        """
        return 0

    def _interval_from_self_if_none(self, a, b, interval):
        if interval is None:
            if (a, b) == (None, None):
                interval = self
            else:
                interval = TimeInterval(a, b)
        else:
            assert_is_time_interval(interval)
        return interval

    def degree_in_interval(self, a=None, b=None, interval=None):
        """
        use either 'a' and 'b' or 'interval'
        """
        interval = self._interval_from_self_if_none(a, b, interval)
        return integrate.quad(self.membership_function, interval.a, interval.b) / interval.duration

    def to_dict(self):
        result = {}
        for time_step in self.to_list():
            result[time_step] = self.membership_function(time_step)
        return result

    def plot(self):
        import matplotlib.pyplot as plt
        from spatiotemporal.unix_time import UnixTime

        x_axis = [UnixTime(time).to_datetime() for time in self]
        plt.plot(x_axis, self.membership_function)
        return plt


class TemporalEventPiecewiseLinear(TimeIntervalListBased, BaseTemporalEvent):
    def __init__(self, input_list, output_list):
        TimeIntervalListBased.__init__(self, input_list)
        self.output_list = output_list
        self.membership_function = MembershipFunctionPiecewiseLinear(self, output_list)
        self.membership_function_single_point = self.membership_function

    def degree_in_interval(self, a=None, b=None, interval=None):
        interval = self._interval_from_self_if_none(a, b, interval)
        return self.membership_function_single_point.integrate(interval.a, interval.b) / (interval.b - interval.a)

    def to_list(self):
        result = []
        for i, time_step in enumerate(self):
            if i == len(self) - 1 and self.output_list[len(self) - 1] == 0:
                result.append(UnixTime(time_step - EPSILON))
            result.append(time_step)
            if i == 0 and self.output_list[0] == 0:
                result.append(UnixTime(time_step + EPSILON))
        return result

    @TimeIntervalListBased.a.setter
    def a(self, value):
        TimeIntervalListBased.a.fset(value)
        self.membership_function_single_point.invalidate()

    @TimeIntervalListBased.b.setter
    def b(self, value):
        TimeIntervalListBased.b.fset(value)
        self.membership_function_single_point.invalidate()

    # Every time that self as list changes, or output_list
    # changes, membership_function_single_point should be invalidated
    # Here, only the two main methods that change the list content have been overridden
    # One can add more later if needed...
    def append(self, x):
        TimeIntervalListBased.append(self, x)
        self.membership_function_single_point.invalidate()

    def __setitem__(self, index, value):
        TimeIntervalListBased.__setitem__(self, index, value)
        self.membership_function_single_point.invalidate()


class TemporalEventSimple(TemporalEventPiecewiseLinear):
    def __init__(self, a, b):
        TemporalEventPiecewiseLinear.__init__(self, [a, b], [1, 1])


class TemporalEventDistributional(BaseTemporalEvent):
    def __init__(self, a, b, pdf, iter_step=1):
        assert callable(pdf), "'pdf' should be callable"
        BaseTemporalEvent.__init__(self, a, b, iter_step=iter_step)
        self.membership_function = pdf
        self.membership_function_single_point = pdf


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    event = TemporalEventSimple(datetime(2010, 1, 1), datetime(2011, 2, 1))
    event.plot().show()

    event = TemporalEventPiecewiseLinear([1, 2, 3], [4, 5, 6])
    event.plot().show()
