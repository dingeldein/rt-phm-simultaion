import numpy as np
import random
from db import row_insert_query
import psycopg2.extensions
import psycopg2
import math

pusher_bearing_factor = [1]
pusher_coil_factor = [1]

class UAV:
    """Die Klasse UAV modelliert eine hybride Drohne mit einem Pusher-Motor, 8 Hover-Motoren und einer Batterie."""
    CRUISE_SPEED = 60  # in kmh
    TAKEOFF_TIME = 2  # in minutes
    LANDING_TIME = 2  # in minutes

    def __init__(self, uav_id: int):
        self.uav_id = uav_id
        self.flight_mode = None
        self.hover_bearing_health = np.zeros(4)
        self.hover_bearing_factors = np.zeros(4)
        self.hover_coil_health = np.zeros(4)
        self.hover_coil_factors = np.zeros(4)
        self.pusher_bearing_health = None
        self.pusher_bearing_factor = 1
        self.pusher_coil_health = None
        self.pusher_coil_factor = 1
        self.battery_level = None
        self.hover_bearing_failure_appearance = np.empty(4)
        self.hover_coil_failure_appearance = np.empty(4)
        self.pusher_bearing_failure_appearance = None
        self.pusher_coil_failure_appearance = None
        self.number_of_missions = 0
        self.mission_mode = 0  # --> 0: on delivery mission, 1: on SAR mission, 2: available, 3: R2H, 4: in maintenance
        self.log = None
        self.mission_progress = None
        self.health_initialization()

    def health_initialization(self) -> None:
        """Initialsiert die Gesundheitswerte der Motoren, deren failure-Appearance und die Ladung der Batterie.

        Args: None

        Returns: None

        """
        self.flight_mode = 0  # set UAV not-flying
        self.mission_mode = 2  # set UAV available
        self.mission_progress = 0

        # initial hover health
        for i in range(len(self.hover_bearing_health)):
            self.hover_bearing_health[i] = random.uniform(0.5, 1.0)
        for i in range(len(self.hover_bearing_factors)):
            self.hover_bearing_factors[i] = 1.0
        for i in range(len(self.hover_bearing_failure_appearance)):
            self.hover_bearing_failure_appearance[i] = round(random.uniform(0.4, 0.75), 3)

        for i in range(len(self.hover_coil_health)):
            self.hover_coil_health[i] = random.uniform(0.8, 1.0)
        for i in range(len(self.hover_coil_factors)):
            self.hover_coil_factors[i] = 1.0
        for i in range(len(self.hover_coil_failure_appearance)):
            self.hover_coil_failure_appearance[i] = round(random.uniform(0.75, 0.85), 3)

        # initial pusher health
        self.pusher_bearing_health = random.uniform(0.5, 1.0)
        self.pusher_bearing_failure_appearance = round(random.uniform(0.4, 0.5), 3)

        self.pusher_coil_health = random.uniform(0.9, 1.0)
        self.pusher_coil_failure_appearance = round(random.uniform(0.8, 0.9), 3)

        # initial battery health
        self.battery_level = 1

    def health_index(self) -> int:  # 26
        """Berechnet das Minimum der Gesundheitswerte der Motoren.

        Args: None

        Returns: None

        """
        return min([*self.hover_bearing_health, *self.hover_coil_health,
                    self.pusher_bearing_health, self.pusher_coil_health])

    def store_to_database(self, con: psycopg2.extensions.connection, cur: psycopg2.extensions.cursor) -> None:
        """Schreibt die aktuellen Werte der Drohne in die entsprechend Datenbanktabelle

        Args:
            con(psycopg2.extensions.connection): Verbindung zur Datenbank
            cur(): Cursor der Datenbank

        Returns: None

        """
        cur.execute(row_insert_query.format(self.uav_id), self.get_array())
        con.commit()  # commit changes

    def get_array(self) -> np.ndarray:
        """Gibt alle Werte der Drohne in Form eines numpy.arrays zurück.

        Args: None

        Returns:
            np.array: Die Werte der Drohne
        """
        values = np.zeros(38)

        values[0] = self.uav_id
        values[1] = self.flight_mode
        values[2:6] = self.hover_bearing_health
        values[6:10] = self.hover_bearing_factors
        values[10:14] = self.hover_coil_health
        values[14:18] = self.hover_coil_factors
        values[18] = self.pusher_bearing_health
        values[19] = self.pusher_bearing_factor
        values[20] = self.pusher_coil_health
        values[21] = self.pusher_coil_factor
        values[22] = self.battery_level
        values[23:27] = self.hover_bearing_failure_appearance
        values[27:31] = self.hover_coil_failure_appearance
        values[31] = self.pusher_bearing_failure_appearance
        values[32] = self.pusher_coil_failure_appearance
        values[33] = self.number_of_missions
        values[34] = self.mission_mode
        values[35] = self.log
        values[36] = self.mission_progress
        values[37] = self.health_index()

        return values

    def degradation(self, mission_mode: int) -> None:
        """Simuliert den Verschleiß der Motoren und die Entladung der Batterie abhängig vom aktuellen Missions-Modus.

        Args:
            mission_mode(int): Der aktuelle Missionsmodus -> 0=no-flying, 1=hover, 2=cruise

        Returns: None

        """
        self.flight_mode = mission_mode

        if mission_mode == 1:

            """Hover bearing degradation:"""
            hover_bearing_deg_values = np.empty(len(self.hover_bearing_health))
            for j in range(len(self.hover_bearing_health)):
                if self.hover_bearing_health[j] > self.hover_bearing_failure_appearance[j]:
                    hover_bearing_deg_values[j] = round(random.uniform(1, 3) * 0.0001, 6)
                else:
                    hover_bearing_deg_values[j] = self.hover_bearing_factors[j]*round((random.uniform(1, 3) * 0.0001), 6)
                    self.hover_bearing_factors[j] = self.hover_bearing_factors[j] * 1.002

            self.hover_bearing_health -= hover_bearing_deg_values

            """Hover coil degradation:"""
            hover_coil_deg_values = np.empty(len(self.hover_coil_health))
            for j in range(len(self.hover_coil_health)):
                if self.hover_coil_health[j] > self.hover_coil_failure_appearance[j]:
                    hover_coil_deg_values[j] = round(random.uniform(0.00005, 0.0001), 5)
                else:
                    hover_coil_deg_values[j] = self.hover_coil_factors[j]*round(random.uniform(0.00005, 0.0001), 5)
                    self.hover_coil_factors[j] = self.hover_coil_factors[j]*1.004

            self.hover_coil_health -= hover_coil_deg_values

            """Battery discharge: way higher discharge rate more rapid changes in discharge due to hover mode"""
            hover_health_bat_fac = 1+(1-(min(min(self.hover_bearing_health), min(self.hover_coil_health))))*0.33
            discharge_rate = round((random.uniform(0.03, 0.07)*hover_health_bat_fac), 2)
            self.battery_level -= discharge_rate

        if mission_mode == 2:
            """Pusher bearing degradation:"""
            if self.pusher_bearing_health > self.pusher_bearing_failure_appearance:
                pusher_bearing_deg_rate = round(random.uniform(1, 3) * 0.000023, 6)
            else:
                pusher_bearing_deg_rate = self.pusher_bearing_factor*round((random.uniform(1, 3) * 0.000023), 6)
                self.pusher_bearing_factor = self.pusher_bearing_factor*1.0004

            self.pusher_bearing_health -= pusher_bearing_deg_rate

            """Pusher coil degradation:"""
            if self.pusher_coil_health > self.pusher_coil_failure_appearance:
                pusher_coil_deg_rate = round(random.uniform(1, 3) * 0.000005, 6)
            else:
                pusher_coil_deg_rate = self.pusher_coil_factor*round(random.uniform(1, 3) * 0.000005, 6)
                self.pusher_coil_factor = self.pusher_coil_factor*1.002

            self.pusher_coil_health -= pusher_coil_deg_rate

            """Battery discharge: lower discharge rate, more constant discharge due to cruise mode"""
            pusher_health_bat_fac = 1+((1-min(self.pusher_bearing_health, self.pusher_coil_health))*0.33)
            discharge_rate = round((random.uniform(0.005, 0.015)*pusher_health_bat_fac), 3)
            self.battery_level -= discharge_rate
