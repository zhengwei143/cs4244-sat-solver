import matplotlib.pyplot as plt
import numpy as np

filepath = 'data/4/data_points.txt'

x, y = np.loadtxt(filepath, delimiter=',', unpack=True)
plt.plot(x,y, label='Probability of satisfiability of Fk(n,rn)')

plt.xlabel('r')
plt.ylabel('Fk(n,rn)')
plt.title('K = 4')
plt.legend()
plt.savefig('data/4/k4_n150.png')
plt.show()
