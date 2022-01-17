import psycopg2
import numpy as np
import matplotlib.pyplot as plt

fig, axs = plt.subplots(10, figsize=(20, 15), sharex=True)

for i in range(10):
    con = psycopg2.connect(
        host="localhost",
        database="rt_phm_simulation",
        user="postgres",
        password="R!3senfelge"
    )


    cur = con.cursor()
    cur.execute("select health_index from uav{}".format(i+1))
    uav_health_index = np.asarray(cur.fetchall())
    cur.execute("select hb1, hb2, hb3, hb4, hc1, hc2, hc3, hc4, psb, psc from uav{}".format(i+1))
    uav_components_health = np.asarray(cur.fetchall())
    cur.execute("select bat_h from uav{}".format(i+1))
    uav_bat_h = np.asarray(cur.fetchall())

    cur.close()
    con.close()

    # print(uav_components_health)

    axs[i].plot(uav_bat_h, alpha=0.2)
    axs[i].plot(uav_components_health, alpha=0.2)
    axs[i].plot(uav_health_index, 'k')
    axs[i].set_ylabel("UAV {}".format(i+1))
    axs[i].set_ylim([0, 1])
    # axs[i].title.set_text("UAV {}".format(i+1))
axs[9].set_xlabel("Time in min")
fig.subplots_adjust(hspace=0.5)
fig.suptitle("Individual UAV Health Progressions", fontsize=30)
plt.ylim((0, 1))
plt.show()

