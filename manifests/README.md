# Manifest Lists

In order to emulate an actual pull -> choosing of a platform by a container runtime tool, we need to put the (currently separate tags for an image) in an image manifest list. We can do that with [manifest-tool](https://github.com/estesp/manifest-tool). After following the instructions to install it there, here is how to generate our manifests.

```bash
manifest-tool push from-spec ./openmpi-ubuntu-20.04.yaml
manifest-tool push from-spec ./openmpi-ubuntu-22.04.yaml
manifest-tool push from-spec ./mpich-ubuntu-20.04.yaml
manifest-tool push from-spec ./mpich-ubuntu-22.04.yaml
```

The first of those might make [this tag](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169857305?tag=openmpi-ubuntu)
