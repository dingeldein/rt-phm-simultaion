from mission_generator import delivery_mission, reconnaissance_mission
import numpy as np
from uav import UAV
import time
import random
import psycopg2

time_scale = 0.5  # time taken for one minute in simulation (in seconds)
mission_prep_time = 5
battery_charging = 10
hover_bearing_mntnc = 300
hover_coil_mntnc = 200
pusher_bearing_mntnc = 400
pusher_coil_mntnc = 300


def mission_execution(uav: UAV, distance: int) -> None:
    """Simuliert den Ablauf der Mission für die übergebene Drohne.

    Args:
        uav(UAV): Die Drohne auf Mission
        distance(int): Distanz der Mission in km
        con(psycopg2.extensions.connection): Verbindung zur Datenbank, in der die Daten der Drohne gespeichert werden

    Returns: None

    """

    con = psycopg2.connect(
        host="localhost",
        database="rt_phm_simulation",
        user="postgres",
        password="R!3senfelge"
    )

    # print("Mission execution started")

    # cursor
    cur = con.cursor()

    # increase number of missions (no_missions) by one
    uav.number_of_missions += 1
    uav.mission_mode = 3  # LORENZ: mission mode = 3 bedeutet in mission preparation
    uav.flight_mode = 0  # while in mission preparation UAV is not-flying
    uav.mission_progress = 0

    mission = delivery_mission(distance) if uav.mission_type == 0 else reconnaissance_mission(distance)
    # uav.log = uav.mission_type --> hier erkennt man die Dopplung der Attribute

    # print("UAV {} mission prep".format(uav.uav_id))
    # add mission initial status
    for r in range(mission_prep_time):
        start_time = time.time()
        elapsed_time = time.time() - start_time
        if elapsed_time < time_scale:
            time.sleep(time_scale - elapsed_time)
        uav.store_to_database(con, cur)
        # print("{}/{} Mission prep time".format(r + 1, mission_prep_time))

    # start mission
    if uav.mission_type == 0:
        uav.mission_mode = 0  # set mission_mode to delivery mission
        print("UAV {} started on delivery mission".format(uav.uav_id))

    if uav.mission_type == 1:
        uav.mission_mode = 1  # set mission_mode to SAR mission
        print("UAV {} started on SAR mission".format(uav.uav_id))

    for i in range(len(mission)):
        start_time = time.time()

        uav.degradation(mission[i])  # new health values for single step
        uav.mission_progress = (i + 1) / len(mission) * 100  # 100 - (1 - (len(mission[:i + 1]) / len(mission))) * 100

        uav.store_to_database(con, cur)
        # print("{}/{} mission done".format(i + 1, len(mission)))
        elapsed_time = time.time() - start_time
        if elapsed_time < time_scale:
            time.sleep(time_scale - elapsed_time)


        if 0.1 < uav.battery_level < 0.3 and len(mission) - i > distance + UAV.LANDING_TIME:
            # print("UAV {} safe R2H triggered".format(uav.uav_id))
            uav.mission_mode = 4

            r2h_distance = int(int(distance) + int(distance) // 10)  # int(float(distance + int(distance * 0.1)))
            r2h_mission = np.zeros(r2h_distance + int(UAV.LANDING_TIME))
            r2h_mission[0:r2h_distance] = 2
            r2h_mission[-UAV.LANDING_TIME:] = 1
            print('Safe R2H triggered with a duration of ', len(r2h_mission), 'mins')

            for j in range(len(r2h_mission)):
                start_time = time.time()

                uav.degradation(r2h_mission[j])  # new health values for single step
                uav.mission_progress = (j + 1) / len(r2h_mission) * 100

                uav.store_to_database(con, cur)
                # print("{}/{} R2H mission done".format(j + 1, len(r2h_mission)))
                elapsed_time = time.time() - start_time
                if elapsed_time < time_scale:
                    time.sleep(time_scale - elapsed_time)

            print('!!!NOTICE: UAV proceeds to EARLY mission ending')
            uav.mission_progress = 100  # remaining mission length
            uav.mission_mode = 5  # change status: maintenance
            uav.flight_mode = 0

            # maintenance procedures
            # hover bearing maintenance
            if np.any(uav.hover_bearing_health < 0.05):
                print("UAV {} in hover bearing maintenance")
                for _ in range(hover_bearing_mntnc):
                    start_time = time.time()
                    elapsed_time = time.time() - start_time
                    if elapsed_time < time_scale:
                        time.sleep(time_scale - elapsed_time)
                    uav.store_to_database(con, cur)
                affected_asset = np.where(uav.hover_bearing_health < 0.05)[0]
                uav.hover_bearing_health[affected_asset] = random.uniform(0.95, 1.0)
                uav.hover_bearing_factors[affected_asset] = 1.0
                uav.hover_bearing_failure_appearance[affected_asset] = round(random.uniform(0.4, 0.75), 3)
                uav.store_to_database(con, cur)

            # hover coil maintenance
            if np.any(uav.hover_coil_health < 0.05):
                print("UAV {} in hover coil maintenance")
                for _ in range(hover_coil_mntnc):
                    start_time = time.time()
                    elapsed_time = time.time() - start_time
                    if elapsed_time < time_scale:
                        time.sleep(time_scale - elapsed_time)
                    uav.store_to_database(con, cur)
                affected_asset = np.where(uav.hover_coil_health < 0.05)[0]
                uav.hover_coil_health[affected_asset] = random.uniform(0.95, 1.0)
                uav.hover_coil_factors[affected_asset] = 1.0
                uav.hover_coil_failure_appearance[affected_asset] = round(random.uniform(0.75, 0.85), 3)
                uav.store_to_database(con, cur)

            # pusher bearing maintenance
            if uav.pusher_bearing_health < 0.05:
                print("UAV {} in pusher bearing maintenance")
                for q in range(pusher_bearing_mntnc):
                    start_time = time.time()
                    elapsed_time = time.time() - start_time
                    if elapsed_time < time_scale:
                        time.sleep(time_scale - elapsed_time)
                    uav.store_to_database(con, cur)
                uav.pusher_bearing_health = random.uniform(0.95, 1.0)
                uav.pusher_bearing_factor = 1.0
                uav.pusher_bearing_failure_appearance = round(random.uniform(0.4, 0.5), 3)
                uav.store_to_database(con, cur)

            # pusher coil maintenance
            if uav.pusher_coil_health < 0.05:
                print("UAV {} in pusher coil maintenance")
                for q in range(pusher_coil_mntnc):
                    start_time = time.time()
                    elapsed_time = time.time() - start_time
                    if elapsed_time < time_scale:
                        time.sleep(time_scale - elapsed_time)
                    uav.store_to_database(con, cur)
                uav.pusher_coil_health = random.uniform(0.95, 1.0)
                uav.pusher_coil_factor = 1.0
                uav.pusher_coil_failure_appearance = round(random.uniform(0.8, 0.9), 3)
                uav.store_to_database(con, cur)

            print("UAV {} in battery service".format(uav.uav_id))
            for q in range(battery_charging):
                start_time = time.time()
                # print("UAV {} - {}/{} of battery service done".format(uav.uav_id, q + 1, battery_charging))
                elapsed_time = time.time() - start_time
                if elapsed_time < time_scale:
                    time.sleep(time_scale - elapsed_time)
                uav.store_to_database(con, cur)

            # load battery before mission while on ground, respect max cap degradation
            uav.battery_level = 1 - uav.number_of_missions * 0.0003
            uav.mission_progress = 0  # reset mission progression bar

            uav.mission_mode = 2  # change status: available
            uav.flight_mode = 0  # not-flying

            uav.store_to_database(con, cur)

            print('UAV {} Battery charged - UAV available'.format(uav.uav_id))

            # close cursor
            cur.close()
            break

    if i+1 == len(mission) and uav.mission_mode == 0 or uav.mission_mode == 1:
        print('!!!NOTICE: UAV proceeds to NORMAL mission ending')
        uav.mission_progress = 100  # remaining mission length
        uav.mission_mode = 5  # change status: maintenance
        uav.flight_mode = 0

        # maintenance procedures
        # hover bearing maintenance
        if np.any(uav.hover_bearing_health < 0.05):
            print("UAV {} in hover bearing maintenance")
            for _ in range(hover_bearing_mntnc):
                start_time = time.time()
                elapsed_time = time.time() - start_time
                if elapsed_time < time_scale:
                    time.sleep(time_scale - elapsed_time)
                uav.store_to_database(con, cur)
            affected_asset = np.where(uav.hover_bearing_health < 0.05)[0]
            uav.hover_bearing_health[affected_asset] = random.uniform(0.95, 1.0)
            uav.hover_bearing_factors[affected_asset] = 1.0
            uav.hover_bearing_failure_appearance[affected_asset] = round(random.uniform(0.4, 0.75), 3)
            uav.store_to_database(con, cur)

        # hover coil maintenance
        if np.any(uav.hover_coil_health < 0.05):
            print("UAV {} in hover coil maintenance")
            for _ in range(hover_coil_mntnc):
                start_time = time.time()
                elapsed_time = time.time() - start_time
                if elapsed_time < time_scale:
                    time.sleep(time_scale - elapsed_time)
                uav.store_to_database(con, cur)
            affected_asset = np.where(uav.hover_coil_health < 0.05)[0]
            uav.hover_coil_health[affected_asset] = random.uniform(0.95, 1.0)
            uav.hover_coil_factors[affected_asset] = 1.0
            uav.hover_coil_failure_appearance[affected_asset] = round(random.uniform(0.75, 0.85), 3)
            uav.store_to_database(con, cur)

        # pusher bearing maintenance
        if uav.pusher_bearing_health < 0.05:
            print("UAV {} in pusher bearing maintenance")
            for q in range(pusher_bearing_mntnc):
                start_time = time.time()
                elapsed_time = time.time() - start_time
                if elapsed_time < time_scale:
                    time.sleep(time_scale - elapsed_time)
                uav.store_to_database(con, cur)
            uav.pusher_bearing_health = random.uniform(0.95, 1.0)
            uav.pusher_bearing_factor = 1.0
            uav.pusher_bearing_failure_appearance = round(random.uniform(0.4, 0.5), 3)
            uav.store_to_database(con, cur)

        # pusher coil maintenance
        if uav.pusher_coil_health < 0.05:
            print("UAV {} in pusher coil maintenance")
            for q in range(pusher_coil_mntnc):
                start_time = time.time()
                elapsed_time = time.time() - start_time
                if elapsed_time < time_scale:
                    time.sleep(time_scale - elapsed_time)
                uav.store_to_database(con, cur)
            uav.pusher_coil_health = random.uniform(0.95, 1.0)
            uav.pusher_coil_factor = 1.0
            uav.pusher_coil_failure_appearance = round(random.uniform(0.8, 0.9), 3)
            uav.store_to_database(con, cur)

        print("UAV {} in battery service".format(uav.uav_id))
        for q in range(battery_charging):
            start_time = time.time()
            # print("UAV {} - {}/{} of battery service done".format(uav.uav_id, q + 1, battery_charging))
            elapsed_time = time.time() - start_time
            if elapsed_time < time_scale:
                time.sleep(time_scale - elapsed_time)
            uav.store_to_database(con, cur)

        # load battery before mission while on ground, respect max cap degradation
        uav.battery_level = 1 - uav.number_of_missions * 0.0003
        uav.mission_progress = 0  # reset mission progression bar

        uav.mission_mode = 2  # change status: available
        uav.flight_mode = 0  # not-flying

        uav.store_to_database(con, cur)

        print('UAV {} Battery charged - UAV available'.format(uav.uav_id))

        # close cursor
        cur.close()

# uav = UAV(1)
# mission_type = random.choice(list(MissionType))
# uav.mission_type = mission_type.value
# mission_length = random.randint(*mission_duration[mission_type])
# mission_execution(uav, 10)
