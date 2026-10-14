# # Stage 1: Build Panda3D
# FROM python:3.9 as panda3d-builder

# # Install build essentials and dependencies for Panda3D
# RUN apt-get update && apt-get install -y \
#     build-essential pkg-config fakeroot python3-dev libpng-dev libjpeg-dev \
#     libtiff-dev zlib1g-dev libssl-dev libx11-dev libgl1-mesa-dev libxrandr-dev \
#     libxxf86dga-dev libxcursor-dev bison flex libfreetype6-dev libvorbis-dev \
#     libeigen3-dev libopenal-dev libode-dev libbullet-dev \
#     libgtk-3-dev libassimp-dev libopenexr-dev

# # Clone the Panda3D repository and build it
# RUN git clone https://github.com/open-toontown/panda3d
# RUN cd panda3d && \
#     python3 makepanda/makepanda.py --everything --installer --no-egl --no-gles --no-gles2 --no-opencv --wheel

# Stage 2: Setup the final image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the application code into the container
COPY . /app

# Install dependencies for Astron
RUN apt-get update && apt-get install -y \
    git \
    libyaml-cpp-dev \
    libuv1-dev \
    libboost-all-dev \
    libssl-dev \
    cmake \
    make \
    g++

# Clone Toontown resources
RUN git clone https://github.com/open-toontown/resources.git

# Clone astron
RUN git clone https://github.com/Astron/Astron.git /app/astron/linux

# Compile Astron
WORKDIR /app/astron/linux
RUN cmake -DCMAKE_BUILD_TYPE=Release . && make

# Change back to the app directory
WORKDIR /app

# Install dependencies for starting the servers
RUN apt-get install -y \
    libharfbuzz0b \
    libvorbisfile3 \
    libopenexr-dev \
    libode-dev \
    libassimp-dev \
    libgl1-mesa-dev \
    libopenal1 \
    x11-apps \
    libgl1-mesa-glx \
    libgl1-mesa-dri \
    mesa-utils

# Copy the Panda3D wheel from the builder stage
# COPY --from=panda3d-builder /panda3d/*.whl /tmp/

# Install the Panda3D wheel
# RUN pip install /tmp/*.whl && rm -f /tmp/*.whl
RUN pip install panda3d-1.11.0-cp39-cp39-linux_aarch64.whl && rm -f panda3d-1.11.0-cp39-cp39-linux_aarch64.whl

# Install dependencies from requirements.txt
RUN pip install -r requirements.txt

# Make the scripts executable
RUN chmod +x /app/linux/start-ai-server.sh \
			 /app/linus/run.sh \
             /app/linux/start-astron-server.sh \
             /app/linux/start-game.sh \
             /app/linux/start-uberdog-server.sh\
			 /app/linux/Districts/

# Copy the custom start script into the container
COPY run.sh /app/

# Make the custom start script executable
RUN chmod +x /app/linux/run.sh

# Expose the necessary ports
EXPOSE 7199 7197

# Command to run the servers
CMD ["./run.sh"]