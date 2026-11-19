#!/usr/bin/env python3
"""patrol_robo.py - patrol no TurtleBot 4 fisico (rodar no container Humble).

Base: patrol_loop (Clearpath). Diferencas:
- namespace pela linha de comando: --ros-args -r __ns:=/robot1
- NAO publica initial pose: defina no RViz (2D Pose Estimate) ANTES de rodar
- waypoints e ponto da dock nas constantes abaixo
- --no-dock : sem dock/undock | --loops N : para apos N voltas (0 = infinito)
- se um goal falhar, para (nao segue as cegas); Ctrl+C cancela o goal
"""
import argparse
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
from turtlebot4_navigation.turtlebot4_navigator import TurtleBot4Directions, TurtleBot4Navigator

BATTERY_HIGH = 0.95
BATTERY_LOW = 0.2       # vai carregar
BATTERY_CRITICAL = 0.1  # para tudo

# PREENCHER com pontos livres do mapa_sala_teste: ([x, y], direcao), em metros no frame map
WAYPOINTS = [
    ([0.37, 1.52], TurtleBot4Directions.WEST),
    ([-0.14, 4.76], TurtleBot4Directions.SOUTH),
    ([-2.24, 4.32], TurtleBot4Directions.EAST),
    ([-2.52, 0.23], TurtleBot4Directions.NORTH),
]
# Ponto logo em frente a dock (pose do robo logo apos o undock). None = sem docking
DOCK_APPROACH = ([0.0, 0.6], 270)  # provisorio: 0.6 m a frente da dock, olhando para ela


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
    p.add_argument('--loops', type=int, default=0, help='voltas (0 = infinito)')
    return p.parse_args(argv)


def go_to(navigator, xy, direction):
    navigator.startToPose(navigator.getPoseStamped(xy, direction))
    result = navigator.getResult()
    if result != TaskResult.SUCCEEDED:
        navigator.error(f'Goal nao concluido: {result}')
        return False
    return True


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
    # Espera os nodes do Nav2 sem publicar initial pose (waitUntilNav2Active publicaria)
    navigator._waitForNodeToActivate('amcl')
    navigator._waitForNodeToActivate('bt_navigator')

    if not args.no_dock:
        if not navigator.getDockedStatus():
            navigator.error('Robo nao esta na dock. Coloque na dock ou use --no-dock')
            return 1
        navigator.undock()

    idx, laps = 0, 0
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
                if not charge(navigator, battery_monitor, lock):
                    return 1
                idx = 0
                continue

        if not go_to(navigator, *WAYPOINTS[idx]):
            return 1
        idx += 1
        if idx >= len(WAYPOINTS):
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
    if not WAYPOINTS:
        print('ERRO: preencha WAYPOINTS no topo do arquivo.')
        return 1
    if not args.no_dock and DOCK_APPROACH is None:
        print('ERRO: defina DOCK_APPROACH ou rode com --no-dock.')
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
