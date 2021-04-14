import matplotlib.pyplot as plt
import pandas as pd

data = pd.read_csv('motor_sim_2.csv')
data.plot(x='RPM_x', y='RPM_y', grid=True)
plt.legend(['RPM'])
plt.ylabel('Simulated Rounds per Minute')
plt.xlabel('time in seconds')
plt.show()