import collections

box = collections.deque(maxlen=1) # I <3 deque

box.append("a")
box.append("b")
box.append("c")

print(box.pop())