FROM intel/oneapi-vtune:2024.1.0-devel-ubuntu22.04
ENV DEBIAN_FRONTEND=noninteractive

# docker build -t ghcr.io/converged-computing/rainbow-experiments:vtune-singularity .

RUN apt-get update && \
    apt-get install -y fftw3-dev fftw3 pdsh libfabric-dev libfabric1 \
        dnsutils telnet strace cmake git g++ \
        openmpi-bin openmpi-doc libopenmpi-dev \
        build-essential wget curl unzip libnss3-dev libgtk2.0-dev

WORKDIR /opt/
RUN git clone --depth 1 --branch stable_29Sep2021_update2 https://github.com/lammps/lammps.git /opt/lammps && \
    cd /opt/lammps && \
    mkdir build && \
    cd build && \
    . /etc/profile && \ 
    cmake ../cmake -DCMAKE_INSTALL_PREFIX:PATH=/usr -DPKG_REAXFF=yes -DBUILD_MPI=yes -DPKG_OPT=yes -DFFT=FFTW3 -DCMAKE_PREFIX_PATH=/usr/lib/mpich -DCMAKE_PREFIX_PATH=/usr/lib/x86_64-linux-gnu && \
    make && \
    make install
   
RUN apt-get update && apt-get install -y vim
RUN /bin/bash -c "curl -L https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh > mambaforge.sh && \
    bash mambaforge.sh -b -p /opt/conda && \
    rm mambaforge.sh"
ENV PATH=$PATH:/opt/conda/bin
RUN mamba install singularity

WORKDIR /opt/lammps/examples/reaxff/HNS

