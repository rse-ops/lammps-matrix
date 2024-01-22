ARG tag="22.04"
FROM nvidia/cuda:12.2.0-devel-ubuntu${tag}

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH=/usr/local/bin:$PATH

WORKDIR /opt
RUN apt-get -y update && apt-get -y install -y \
    wget git cmake build-essential \
    openmpi-bin openmpi-common openssh-client openssh-server libopenmpi-dev \
    libpng-dev zlib1g-dev gfortran ffmpeg
RUN git clone  https://github.com/lammps/lammps.git && \
    cd lammps && \
    mkdir build && \
    cd build && \
    cmake -D CMAKE_INSTALL_PREFIX=/usr/local -DCMAKE_LIBRARY_PATH=/usr/local/cuda/lib64/stubs -DBIN2C=/usr/local/cuda/bin/bin2c -D LAMMPS_MACHINE=gpu -D PKG_MOLECULE=on -D PKG_ASPHERE=on -D PKG_BODY=on -D PKG_CLASS2=on -D PKG_COLLOID=on -D PKG_COMPRESS=on -D PKG_CORESHELL=on -D PKG_DIPOLE=on -D PKG_GRANULAR=on -D PKG_KSPACE=on -D PKG_MANYBODY=on -D PKG_MC=on -D PKG_MISC=on -D PKG_PERI=on -D PKG_QEQ=on -D PKG_RIGID=on -D PKG_SHOCK=on -D PKG_SNAP=on -D PKG_SRD=on -D PKG_USER-REAXC=on -D PKG_USER-TALLY=on -D PKG_GPU=on -D GPU_API=cuda -D  GPU_ARCH=sm_70 ../cmake && \
    make -j && \
    make install       

ENTRYPOINT ["lmp_gpu"]
