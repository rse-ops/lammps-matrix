#!/bin/bash

# These need more room, and thus are done locally

# openmpi-ubuntu-gpu on amd64
docker buildx build --platform linux/amd64 --build-arg tag=20.04 --provenance false --tag ghcr.io/rse-ops/lammps-matrix:openmpi-ubuntu-gpu-20.04-amd64 openmpi-ubuntu-gpu/ --push
docker buildx build --platform linux/amd64 --build-arg tag=22.04 --provenance false --tag ghcr.io/rse-ops/lammps-matrix:openmpi-ubuntu-gpu-22.04-amd64 openmpi-ubuntu-gpu/ --push

# openmpi-ubuntu-gpu on arm64
docker buildx build --platform linux/arm64 --build-arg tag=20.04 --provenance false --tag ghcr.io/rse-ops/lammps-matrix:openmpi-ubuntu-gpu-20.04-arm64 openmpi-ubuntu-gpu/ --push
docker buildx build --platform linux/arm64 --build-arg tag=22.04 --provenance false --tag ghcr.io/rse-ops/lammps-matrix:openmpi-ubuntu-gpu-22.04-arm64 openmpi-ubuntu-gpu/ --push

# openmpi-ubuntu-gpu on ppc64le
docker buildx build --platform linux/arm64 --build-arg tag=20.04 --provenance false --tag ghcr.io/rse-ops/lammps-matrix:openmpi-ubuntu-gpu-20.04-ppc64le openmpi-ubuntu-gpu/ --push
docker buildx build --platform linux/arm64 --build-arg tag=22.04 --provenance false --tag ghcr.io/rse-ops/lammps-matrix:openmpi-ubuntu-gpu-22.04-ppc64le openmpi-ubuntu-gpu/ --push
