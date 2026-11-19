FROM ros:humble-ros-base
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-turtlebot4-navigation ros-humble-turtlebot4-msgs \
    ros-humble-irobot-create-msgs ros-humble-nav2-bringup \
    python3-yaml python3-pip && rm -rf /var/lib/apt/lists/*
ENV FASTDDS_BUILTIN_TRANSPORTS=UDPv4
SHELL ["/bin/bash", "-c"]
RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc
WORKDIR /work
