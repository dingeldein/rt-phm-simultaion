import psycopg2
import numpy as np
import matplotlib.pyplot as plt

labels = ['UAV 1', 'UAV 2', 'UAV 3', 'UAV 4', 'UAV 5', 'UAV 6', 'UAV 7', 'UAV 8', 'UAV 9', 'UAV 10']
X = np.arange(len(labels))
fig, ax = plt.subplots()
fig.set_figwidth(10)
fig.set_figheight(6)
ax.set_ylabel('Duration in hours')
ax.set_xticks(X+0.2)
ax.set_xticklabels(labels, rotation=45)

delivery_times = []
sar_times = []
idle_times = []
prep_times = []
mtnc_times = []

for i in range(10):
    con = psycopg2.connect(
        host="localhost",
        database="rt_phm_simulation",
        user="postgres",
        password="R!3senfelge"
    )

    cur = con.cursor()
    data = cur.execute("select mission_mode from uav{}".format(i+1))
    mission_mode = np.asarray(cur.fetchall())

    overall_time = len(mission_mode)
    delivery_time = np.round(np.count_nonzero(mission_mode == 0)/60, 2)
    delivery_times.append(delivery_time)

    sar_time = np.round((np.count_nonzero(mission_mode == 1)+np.count_nonzero(mission_mode == 4))/60, 2)
    sar_times.append(sar_time)

    idle_time = np.round(np.count_nonzero(mission_mode == 2)/60, 2)
    idle_times.append(idle_time)

    prep_time = np.round(np.count_nonzero(mission_mode == 3)/60, 2)
    prep_times.append(prep_time)

    mtnc_time = np.round(np.count_nonzero(mission_mode == 5)/60, 2)
    mtnc_times.append(mtnc_time)

    # print("UAV 1 total time: {} h".format(np.round(overall_time/60, 2)))
    # print("UAV 1 on delivery mission: {} h".format(np.round(delivery_time/60, 2)))
    # print("UAV 1 on sar mission: {} h".format(np.round(((sar_time+r2h_time)/60), 2)))
    # print("UAV 1 idle: {} h".format(np.round(idle_time/60, 2)))
    # print("UAV 1 in mission preparation: {} h".format(np.round(prep_time/60, 2)))
    # print("UAV 1 in maintenance: {} h".format(np.round(mtnc_time/60, 2)))
    # print(overall_time == sum([delivery_time, sar_time, idle_time, prep_time, r2h_time, mtnc_time]))

    cur.close()
    con.close()

oa_deployment_time = sum(delivery_times)+sum(sar_times)
oa_idle_time = sum(idle_times)
oa_mtnc_time = sum(mtnc_times)

dply_ratio = np.round((oa_deployment_time/oa_idle_time), 2)
mtnc_ratio = np.round((oa_deployment_time/oa_mtnc_time), 2)

ax.set_title('UAV utilization \nDeployment Time / Idle Time: {} \nDeployment Time / Maintenance Time: {}'.format(dply_ratio, mtnc_ratio))
ax.bar(X+0.0, delivery_times, width=0.1, color="#005AA9", label="Delivery Mission Time")
ax.bar(X+0.1, sar_times, width=0.1, color="#009D81", label="SAR Mission Time")
ax.bar(X+0.2, idle_times, width=0.1, color="#F5A300", label="Idle Time")
ax.bar(X+0.3, prep_times, width=0.1, color="#E6001A", label="Preparation Time")
ax.bar(X+0.4, mtnc_times, width=0.1, color="#721085", label="Maintenance Time")

ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
fig.subplots_adjust(right=0.7)
fig.show()



