import psycopg2
import numpy as np
from uav import UAV
from db import row_insert_query
import time


def continuous_uav():
    time_scale = 0.5

    while True:
        start_time = time.time()

        con = psycopg2.connect(
                host="localhost",
                database="rt_phm_simulation",
                user="postgres",
                password="R!3senfelge"
            )

        cur = con.cursor()
        uav_status = np.empty((10))
        for i in range(10):
            uav = UAV(i+1)
            cur.execute('select mission_mode from uav{} order by index desc limit 1'.format(i + 1))
            uav_status[i] = np.array(cur.fetchall())
            print("{}/{} UAV idle".format(np.count_nonzero(uav_status == 2), 10))
            if uav_status[i] == 2:
                cur.execute('select * from uav{} order by index desc limit 1'.format(i+1))
                uav_values = np.asarray(cur.fetchall())[0]
                cur.execute(row_insert_query.format(i+1), uav_values[1:])
                con.commit()
                # print("UAV {} stationary".format(i+1))

        elapsed_time = time.time() - start_time
        if elapsed_time < time_scale:
            time.sleep(time_scale - elapsed_time)

        cur.close()
        con.close()


continuous_uav()
