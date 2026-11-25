#!/usr/bin/env python3
"""patrol_corredor.py - patrol sala + corredor do lab, com retorno a dock por bateria baixa.

Base: patrol_robo.py. Diferencas:
- rota so com (x, y): o angulo de cada ponto e calculado para olhar o proximo
- goal que falha e tentado de novo; se falhar de novo, o ponto e PULADO
- 3 falhas seguidas: vai para a dock e para
- bateria baixa: vai para a dock e para (com --resume: carrega e retoma)
- --first N : usa so os N primeiros pontos (teste por etapas)
- --no-dock : sem dock/undock | --loops N : voltas (0 = infinito)
"""
import argparse
import math
import sys
from threading import Lock, Thread
from time import sleep, time

import rclpy
from nav2_simple_commander.robot_navigator import TaskResult
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.signals import SignalHandlerOptions
from rclpy.utilities import remove_ros_args
from sensor_msgs.msg import BatteryState
from turtlebot4_navigation.turtlebot4_navigator import TurtleBot4Navigator

BATTERY_HIGH = 0.95
BATTERY_LOW = 0.25       # volta para a dock
BATTERY_CRITICAL = 0.12  # para tudo
MAX_FAILS_IN_A_ROW = 3

# Rota (x, y) em metros no frame map: sala -> corredor ate o fundo.
ROUTE = [
    (-3.31, -0.64),
    (-3.94, 0.62),
    (-4.03, 3.72),
    (-1.24, 4.36),
    (-0.90, 7.09),
    (0.55, 7.79),
    (3.24, 8.65),
    (5.67, 9.26),
    (10.17, 10.64),
    (14.57, 12.48),
    (20.80, 14.90),
]
# 0.6 m "atras" da dock (dock em 0,0 com o robo olhando 0 grau), olhando para ela
DOCK_APPROACH = ([-0.6, 0.0], 0)


def build_waypoints(route):
    wps = []
    for i, (x, y) in enumerate(route):
        if i + 1 < len(route):
            nx, ny = route[i + 1]
            yaw = math.degrees(math.atan2(ny - y, nx - x))
        else:
            px, py = route[i - 1]
            yaw = math.degrees(math.atan2(y - py, x - px)) + 180.0
        wps.append(([x, y], yaw % 360.0))
    return wps


class BatteryMonitor(Node):

    def __init__(self, lock):
        super().__init__('battery_monitor')
        self.lock = lock
        self.battery_percent = None
        self.create_subscription(
            BatteryState, 'battery_state', self.battery_state_callback,
            qos_profile_sensor_data)

    def battery_state_callback(self, msg: BatteryState):
        with self.lock:
            self.battery_percent = msg.percentage

    def thread_function(self):
        executor = SingleThreadedExecutor()
        executor.add_node(self)
        executor.spin()


def parse_args(argv):
    p = argparse.ArgumentParser()
    p.add_argument('--no-dock', action='store_true', help='sem dock/undock')
    p.add_argument('--resume', action='store_true', help='bateria baixa: carrega e retoma')
    p.add_argument('--first', type=int, default=0, help='usa so os N primeiros pontos')
    p.add_argument('--loops', type=int, default=0, help='voltas (0 = infinito)')
    return p.parse_args(argv)


def go_to(navigator, xy, yaw, tries=2):
    for k in range(1, tries + 1):
        navigator.startToPose(navigator.getPoseStamped(xy, yaw))
        result = navigator.getResult()
        if result == TaskResult.SUCCEEDED:
            return True
        navigator.warn(f'Goal {xy} nao concluido: {result} (tentativa {k}/{tries})')
        sleep(2)
    return False


def dock_now(navigator):
    for attempt in range(1, 4):
        if go_to(navigator, *DOCK_APPROACH):
            break
        navigator.warn(f'DOCK_APPROACH falhou (tentativa {attempt}/3)')
        sleep(3)
    navigator.dock()
    if not navigator.getDockedStatus():
        navigator.error('Falha ao dockar')
        return False
    return True


def charge(navigator, battery_monitor, lock):
    if not dock_now(navigator):
        return False
    navigator.info('Charging...')
    while True:
        sleep(15)
        with lock:
            batt = battery_monitor.battery_percent
        if batt is not None:
            navigator.info(f'Battery is at {batt * 100:.2f}% charge')
            if batt >= BATTERY_HIGH:
                break
    navigator.undock()
    return True


def patrol(navigator, battery_monitor, lock, args):
    route = ROUTE[:args.first] if args.first else ROUTE
    waypoints = build_waypoints(route)

    navigator._waitForNodeToActivate('amcl')
    navigator._waitForNodeToActivate('bt_navigator')

    if not args.no_dock:
        if not navigator.getDockedStatus():
            navigator.error('Robo nao esta na dock. Coloque na dock ou use --no-dock')
            return 1
        navigator.undock()

    idx, laps, fails = 0, 0, 0
    t0, warned = time(), False
    while True:
        with lock:
            batt = battery_monitor.battery_percent

        if batt is None:
            if time() - t0 < 10:
                sleep(1)
                continue
            if not warned:
                navigator.warn('Sem battery_state; seguindo sem checar a bateria')
                warned = True
        else:
            navigator.info(f'Battery is at {batt * 100:.2f}% charge')
            if batt < BATTERY_CRITICAL:
                navigator.error('Battery critically low. Charge or power down')
                return 1
            if batt < BATTERY_LOW:
                if args.no_dock:
                    navigator.error('Bateria baixa e sem dock (--no-dock): parando')
                    return 1
                navigator.warn('Bateria baixa: voltando para a dock')
                if args.resume:
                    if not charge(navigator, battery_monitor, lock):
                        return 1
                    idx, fails = 0, 0
                    continue
                return 0 if dock_now(navigator) else 1

        navigator.info(f'Ponto {idx + 1}/{len(waypoints)}')
        if go_to(navigator, *waypoints[idx]):
            fails = 0
        else:
            fails += 1
            navigator.warn(f'Pulando ponto {idx + 1} (falhas seguidas: {fails})')
            if fails >= MAX_FAILS_IN_A_ROW:
                navigator.error('Falhas demais; voltando para a dock')
                if not args.no_dock:
                    dock_now(navigator)
                return 1
        idx += 1
        if idx >= len(waypoints):
            idx = 0
            laps += 1
            navigator.info(f'Volta {laps} concluida')
            if args.loops and laps >= args.loops:
                break

    if not args.no_dock:
        return 0 if dock_now(navigator) else 1
    return 0


def main():
    args = parse_args(remove_ros_args(sys.argv)[1:])
    if not ROUTE:
        print('ERRO: preencha ROUTE no topo do arquivo.')
        return 1

    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    lock = Lock()
    battery_monitor = BatteryMonitor(lock)
    navigator = TurtleBot4Navigator()
    Thread(target=battery_monitor.thread_function, daemon=True).start()
    sleep(5)  # deixa a descoberta DDS fechar antes da 1a chamada de servico

    code = 1
    try:
        code = patrol(navigator, battery_monitor, lock, args)
    except KeyboardInterrupt:
        navigator.warn('Ctrl+C: cancelando goal')
        navigator.cancelTask()
    finally:
        battery_monitor.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return code


if __name__ == '__main__':
    sys.exit(main())
