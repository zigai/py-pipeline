from filter import IntFilter

x = IntFilter.parse("1:2")
print(x.low)
print(x.high)
