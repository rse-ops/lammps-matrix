#!/bin/bash

# These need more room, and thus are done elsewhere

# I did these on the dinosaur burninator instance, with enough storage / memory (I didn't have locally)
# openmpi-ubuntu-gpu on amd64
docker buildx build --platform linux/amd64 --build-arg tag=20.04 --provenance false --tag ghcr.io/rse-ops/lammps-matrix:openmpi-ubuntu-gpu-20.04-amd64 openmpi-ubuntu-gpu/ --push
docker buildx build --platform linux/amd64 --build-arg tag=22.04 --provenance false --tag ghcr.io/rse-ops/lammps-matrix:openmpi-ubuntu-gpu-22.04-amd64 openmpi-ubuntu-gpu/ --push

# I did these on AWS with an hpc7G instance, an aws-node arm image (1.26) with docker installed.
# There isn't build kit, but we don't need it since our platform is already arm.
# Note that 20.04 didn't work - no right key
# openmpi-ubuntu-gpu on arm64
docker build --build-arg tag=20.04 --network host --tag ghcr.io/rse-ops/lammps-matrix:openmpi-ubuntu-gpu-20.04-arm64 openmpi-ubuntu-gpu/
docker build --build-arg tag=22.04 --network host --tag ghcr.io/rse-ops/lammps-matrix:openmpi-ubuntu-gpu-22.04-arm64 openmpi-ubuntu-gpu/

# intel-mpi-rocky on arm
# Note: the hpc-tools from Google does not have support for ARM
# https://github.com/GoogleCloudPlatform/hpc-tools/issues/4
# docker build --build-arg tag=8 --network host --tag ghcr.io/rse-ops/lammps-matrix:intel-mpi-rocky-8-arm64 ./intel-mpi-rocky
# docker build --build-arg tag=9 --network host --tag ghcr.io/rse-ops/lammps-matrix:intel-mpi-rocky-9-arm64 ./intel-mpi-rocky

# openmpi-rocky-gpu on arm (note that the 8 tag had a timeout for getting a library)
# docker build --build-arg tag=8 --network host --tag ghcr.io/rse-ops/lammps-matrix:openmpi-rocky-gpu-8-arm64 openmpi-rocky-gpu/
docker build --build-arg tag=9 --network host --tag ghcr.io/rse-ops/lammps-matrix:openmpi-rocky-gpu-9-arm64 openmpi-rocky-gpu/

# docker push ghcr.io/rse-ops/lammps-matrix --all-tags

# openmpi-ubuntu-gpu on ppc64le (not done yet)
docker buildx build --platform linux/arm64 --build-arg tag=20.04 --provenance false --tag ghcr.io/rse-ops/lammps-matrix:openmpi-ubuntu-gpu-20.04-ppc64le openmpi-ubuntu-gpu/ --push
docker buildx build --platform linux/arm64 --build-arg tag=22.04 --provenance false --tag ghcr.io/rse-ops/lammps-matrix:openmpi-ubuntu-gpu-22.04-ppc64le openmpi-ubuntu-gpu/ --push
