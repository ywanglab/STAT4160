# src/mathy.py
def moving_avg(xs, w):
    if w <= 0: raise ValueError("w>0")
    out = []
    for i in range(len(xs)):
        j = max(0, i-w+1)
        out.append(sum(xs[j:i+1])/(i-j+1))
    return out