from mission_generator import delivery_mission, reconnaissance_mission
import numpy as np
from uav import UAV
import time
import random
import psycopg2.extensions
import psycopg2
from mission_type import MissionType, mission_duration


# uncomment if real sim time is needed for monitoring
time_scale = 0.1
mission_prep_time = 15
# hover_bearing_mntnc = 15
# hover_coil_mntnc = 25
# pusher_bearing_mntnc = 20
# pusher_coil_mntnc = 30
battery_charging = 10

# uncomment if fast sim time is needed for plotting
# time_scale = 0
# mission_prep_time = 0
hover_bearing_mntnc = 0
hover_coil_mntnc = 0
pusher_bearing_mntnc = 0
pusher_coil_mntnc = 0
# battery_charging = 0


def mission_execution(uav: UAV, distance: int):
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

    start_time = time.time()
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

    print("UAV {} mission prep".format(uav.uav_id))
    # add mission initial status
    for _ in range(mission_prep_time):
        start_time = time.time()
        elapsed_time = time.time() - start_time
        if elapsed_time < time_scale:
            time.sleep(time_scale - elapsed_time)
        uav.store_to_database(con, cur)

    if uav.mission_type == 0:
        uav.mission_mode = 0  # set mission_mode to delivery mission
        print("UAV {} started on delivery mission".format(uav.uav_id))

    if uav.mission_type == 1:
        uav.mission_mode = 1  # set mission_mode to SAR mission
        print("UAV {} started on SAR mission".format(uav.uav_id))

    # start mission
    for i in range(len(mission)):
        start_time = time.time()

        uav.degradation(mission[i])  # new health values for single step
        uav.mission_progress = (i + 1) / len(mission) * 100  # 100 - (1 - (len(mission[:i + 1]) / len(mission))) * 100

        uav.store_to_database(con, cur)

        elapsed_time = time.time() - start_time
        if elapsed_time < time_scale:
            time.sleep(time_scale - elapsed_time)


        # print(uav.battery_level)
        if uav.battery_level < 0.3 and len(mission) - i > distance + UAV.LANDING_TIME:
            # print(len(mission)-len(mission[:i]), distance+2)
            # print('Battery capacity critical!')
            uav.mission_mode = 4  # set return to home
            uav.flight_mode = 2  # starting to cruise home
            ###########uav.log = 4  # return to home ÜBERPRÜFEN

            uav.store_to_database(con, cur)
            r2h_distance = distance + distance//10  # int(float(distance + int(distance * 0.1)))
            r2h_mission = np.zeros(distance + UAV.LANDING_TIME)
            r2h_mission[0:r2h_distance] = 0
            r2h_mission[-UAV.LANDING_TIME:] = 1
            print('UAV {} Safe R2H triggered with a length of '.format(uav.uav_id), len(r2h_mission), 'km')
            ###########uav.log = 3 ÜBERPRÜFEN

            for k in range(len(r2h_mission)):
                start_time = time.time()
                # print("UAV {} - {}/{} of R2H done".format(uav.uav_id, k+1, len(r2h_mission)))
                uav.degradation(r2h_mission[k])
                uav.mission_progress = 100 * (k + 1) / len(r2h_mission)

                uav.store_to_database(con, cur)

                elapsed_time = time.time() - start_time
                if elapsed_time < time_scale:
                    time.sleep(time_scale - elapsed_time)

            # """Leave R2H mission and continue with maintenance"""
            # print('UAV {}: Safely landed at base'.format(uav.uav_id))
            # uav.mission_progress = 100
            # ############uav.log = 4 ÜBERPRÜFEN
            #
            # # uav.store_to_database(con, cur)
            #
            # # print('Battery charging...')
            # ##############uav.log = 5 ÜBERPRÜFEN
            #
            # uav.flight_mode = 0  # set flight_mode to not-flying
            # uav.mission_mode = 5  # change status: maintenance
            #
            # elapsed_time = time.time() - start_time
            # if elapsed_time < time_scale:
            #     time.sleep(time_scale - elapsed_time)
            # uav.store_to_database(con, cur)
            #
            # # maintenance procedures
            # # hover bearing maintenance
            # if np.any(uav.hover_bearing_health < 0.05):
            #     time.sleep(hover_bearing_mntnc)
            #     affected_asset = np.where(uav.hover_bearing_health < 0.05)[0]
            #     uav.hover_bearing_health[affected_asset] = random.uniform(0.95, 1.0)
            #     uav.hover_bearing_factors[affected_asset] = 1.0
            #     uav.hover_bearing_failure_appearance[affected_asset] = round(random.uniform(0.4, 0.75), 3)
            #
            # # hover coil maintenance
            # if np.any(uav.hover_coil_health < 0.05):
            #     time.sleep(hover_coil_mntnc)
            #     affected_asset = np.where(uav.hover_coil_health < 0.05)[0]
            #     uav.hover_coil_health[affected_asset] = random.uniform(0.95, 1.0)
            #     uav.hover_coil_factors[affected_asset] = 1.0
            #     uav.hover_coil_failure_appearance[affected_asset] = round(random.uniform(0.75, 0.85), 3)
            #
            # # pusher bearing maintenance
            # if uav.pusher_bearing_health < 0.05:
            #     time.sleep(pusher_bearing_mntnc)
            #     uav.pusher_bearing_health = random.uniform(0.95, 1.0)
            #     uav.pusher_bearing_factor = 1.0
            #     uav.pusher_bearing_failure_appearance = round(random.uniform(0.4, 0.5), 3)
            #
            # # pusher coil maintenance
            # if uav.pusher_coil_health < 0.05:
            #     time.sleep(pusher_coil_mntnc)
            #     uav.pusher_coil_health = random.uniform(0.95, 1.0)
            #     uav.pusher_coil_factor = 1.0
            #     uav.pusher_coil_failure_appearance = round(random.uniform(0.8, 0.9), 3)
            #
            # ###################uav.log = 8 ÜBERPRÜFEN
            #
            # # uav.store_to_database(con, cur) da sich log nicht ändert, muss hier kein Eintrag in die DB getätigt werden
            #
            # ################uav.log = 5 ÜBERPRÜFEN
            # # print('Battery charging...', )
            # uav.mission_mode = 5  # change status: maintenance
            # uav.flight_mode = 0  # set to not-flying
            #
            # print("UAV {} in battery service".format(uav.uav_id))
            # for q in range(battery_charging):
            #     start_time = time.time()
            #     elapsed_time = time.time() - start_time
            #     if elapsed_time < time_scale:
            #         time.sleep(time_scale - elapsed_time)
            #     uav.store_to_database(con, cur)
            #
            # # load battery before mission while on ground, respect max cap degradation
            # uav.battery_level = 1 - uav.number_of_missions * 0.0003
            # uav.mission_progress = 0  # reset mission progression bar
            #
            # uav.mission_mode = 2  # change status: available
            # uav.flight_mode = 0  # not-flying
            # ###############uav.log = 6 ÜBERPRÜFEN
            #
            # uav.store_to_database(con, cur)
            #
            # print('UAV {}: Battery charged - UAV available'.format(uav.uav_id))
            # # uav.store_to_database(con, cur)
            #
            # # print("Time for mission: ", end-start)

            break

    """post mission procedures"""
    uav.mission_progress = 100  # remaining mission length
    # print('Mission completed')

    # maintenance procedures
    # hover bearing maintenance
    if np.any(uav.hover_bearing_health < 0.05):
        time.sleep(hover_bearing_mntnc)
        affected_asset = np.where(uav.hover_bearing_health < 0.05)[0]
        uav.hover_bearing_health[affected_asset] = random.uniform(0.95, 1.0)
        uav.hover_bearing_factors[affected_asset] = 1.0
        uav.hover_bearing_failure_appearance[affected_asset] = round(random.uniform(0.4, 0.75), 3)

    # hover coil maintenance
    if np.any(uav.hover_coil_health < 0.05):
        time.sleep(hover_coil_mntnc)
        affected_asset = np.where(uav.hover_coil_health < 0.05)[0]
        uav.hover_coil_health[affected_asset] = random.uniform(0.95, 1.0)
        uav.hover_coil_factors[affected_asset] = 1.0
        uav.hover_coil_failure_appearance[affected_asset] = round(random.uniform(0.75, 0.85), 3)

    # pusher bearing maintenance
    if uav.pusher_bearing_health < 0.05:
        time.sleep(pusher_bearing_mntnc)
        uav.pusher_bearing_health = random.uniform(0.95, 1.0)
        uav.pusher_bearing_factor = 1.0
        uav.pusher_bearing_failure_appearance = round(random.uniform(0.4, 0.5), 3)

    # pusher coil maintenance
    if uav.pusher_coil_health < 0.05:
        time.sleep(pusher_coil_mntnc)
        uav.pusher_coil_health = random.uniform(0.95, 1.0)
        uav.pusher_coil_factor = 1.0
        uav.pusher_coil_failure_appearance = round(random.uniform(0.8, 0.9), 3)

    ###################uav.log = 8 ÜBERPRÜFEN

    # uav.store_to_database(con, cur) da sich log nicht ändert, muss hier kein Eintrag in die DB getätigt werden

    ################uav.log = 5 ÜBERPRÜFEN
    # print('Battery charging...', )
    uav.mission_mode = 5  # change status: maintenance
    uav.flight_mode = 0  # set to not-flying

    print("UAV {} in battery service".format(uav.uav_id))
    for q in range(battery_charging):
        start_time = time.time()
        print("UAV {} - {}/{} of battery service done".format(uav.uav_id, q + 1, battery_charging))
        elapsed_time = time.time() - start_time
        if elapsed_time < time_scale:
            time.sleep(time_scale - elapsed_time)
        uav.store_to_database(con, cur)

    # load battery before mission while on ground, respect max cap degradation
    uav.battery_level = 1 - uav.number_of_missions * 0.0003
    uav.mission_progress = 0  # reset mission progression bar

    uav.mission_mode = 2  # change status: available
    uav.flight_mode = 0  # not-flying
    ###############uav.log = 6 ÜBERPRÜFEN

    uav.store_to_database(con, cur)

    print('UAV {} Battery charged - UAV available'.format(uav.uav_id))

    # uav.store_to_database(con, cur) doppelter Eintrag!?

    elapsed_time = time.time() - start_time
    if elapsed_time < time_scale:
        time.sleep(time_scale - elapsed_time)  # delay until time_scale is reached

    # close cursor
    cur.close()

uav = UAV(1)
mission_type = random.choice(list(MissionType))
uav.mission_type = mission_type.value
mission_length = random.randint(*mission_duration[mission_type])
mission_execution(uav, 1)
