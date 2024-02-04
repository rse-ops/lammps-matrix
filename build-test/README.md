# Test Builds

This was our original matrix of builds (separated into different images for easier building). I wound up splitting by architecture and building in the same environment (on AWS VM) for consistency. We should review this matrix (and what we want to use for our experiment, and determine if a combination is missing). Some are not done or hard, e.g., [intel-mpi](https://github.com/GoogleCloudPlatform/hpc-tools/issues/4) installed with hpc-tools does not have support for ARM). There are likely ways to build the missing entries in the matrix if we decide they are important.

| Image               | Architecture | OS    | OS Version | MPI     | MPI version | GPU |
|---------------------|--------------|-------|------------|---------|-------------|-----|
| [intel-mpi-rocky](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169779744?tag=intel-mpi-rocky-8-amd64)     | linux/amd64  | rocky | 8          |intel-mpi|             | no  |
| [intel-mpi-rocky](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169782781?tag=intel-mpi-rocky-9-amd64)     | linux/amd64  | rocky | 9          |intel-mpi|             | no  |
| [openmpi-ubuntu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169782423?tag=openmpi-ubuntu-20.04-amd64)      | linux/amd64  | ubuntu| 20.04      | openmpi |             | no  |
| [openmpi-ubuntu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169792857?tag=openmpi-ubuntu-20.04-arm64)      | linux/arm64  | ubuntu| 20.04      | openmpi |             | no  |
| [openmpi-ubuntu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169810547?tag=openmpi-ubuntu-20.04-ppc64le)      | linux/ppc64le| ubuntu| 20.04      | openmpi |             | no  |
| [openmpi-ubuntu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169782169?tag=openmpi-ubuntu-22.04-amd64)      | linux/amd64  | ubuntu| 22.04      | openmpi |             | no  |
| [openmpi-ubuntu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169809314?tag=openmpi-ubuntu-22.04-arm64)    | linux/arm64  | ubuntu| 22.04      | openmpi |             | no  |
| [openmpi-ubuntu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169809649?tag=openmpi-ubuntu-22.04-ppc64le)      | linux/ppc64le| ubuntu| 22.04      | openmpi |             | no  |
| [openmpi-ubuntu-gpu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169858346?tag=openmpi-ubuntu-gpu-20.04-amd64)  | linux/amd64  | ubuntu| 20.04      | openmpi |             | yes |
| [openmpi-ubuntu-gpu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169812970?tag=openmpi-ubuntu-gpu-22.04-amd64)  | linux/amd64  | ubuntu| 22.04      | openmpi |             | yes |
| [openmpi-ubuntu-gpu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169878136?tag=openmpi-ubuntu-gpu-20.04-arm64)  | linux/arm64  | ubuntu| 20.04      | openmpi |             | yes |
| [openmpi-ubuntu-gpu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169880385?tag=openmpi-ubuntu-gpu-22.04-arm64)  | linux/arm64  | ubuntu| 22.04      | openmpi |             | yes |
| [openmpi-rocky-gpu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169886720?tag=openmpi-rocky-gpu-9-arm64)  | linux/arm64  | rocky | 9      | openmpi |             | yes |
| [mpich-ubuntu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169781948?tag=mpich-ubuntu-20.04-amd64)        | linux/amd64  | ubuntu| 20.04      | mpich   |             | no  |
| [mpich-ubuntu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169810873?tag=mpich-ubuntu-20.04-arm64)        | linux/arm64  | ubuntu| 20.04      | mpich   |             | no  |
| [mpich-ubuntu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169810274?tag=mpich-ubuntu-20.04-ppc64le)        | linux/ppc64le| ubuntu| 20.04      | mpich   |             | no  |
| [mpich-ubuntu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169782384?tag=mpich-ubuntu-22.04-amd64)        | linux/amd64  | ubuntu| 22.04      | mpich   |             | no  |
| [mpich-ubuntu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169814135?tag=mpich-ubuntu-22.04-arm64)        | linux/arm64  | ubuntu| 22.04      | mpich   |             | no  |
| [mpich-ubuntu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169814902?tag=mpich-ubuntu-22.04-ppc64le)        | linux/ppc64le| ubuntu| 22.04      | mpich   |             | no  |

You can find these container builds [here](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix).
More are coming soon, I mostly just need to do the builds / write the Dockerfile (or think of the combination).

### Combined Builds

These are (when appropriate) combined into single manifests, meaning we have three architectures.

| Image               | Architecture | OS    | OS Version | MPI     | MPI version | GPU |
|---------------------|--------------|-------|------------|---------|-------------|-----|
| [mpich-ubuntu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169858124?tag=mpich-ubuntu-20.04)    | arm64,amd64,ppc64le | ubuntu | 20.04 | mpich | | no |    
| [mpich-ubuntu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169858137?tag=mpich-ubuntu-22.04)    | arm64,amd64,ppc64le | ubuntu | 22.04 | mpich | | no |    
| [openmpi-ubuntu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169857305?tag=openmpi-ubuntu-20.04)    | arm64,amd64,ppc64le | ubuntu | 20.04 | openmpi | | no |    
| [openmpi-ubuntu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169857680?tag=openmpi-ubuntu-22.04)    | arm64,amd64,ppc64le | ubuntu | 22.04 | openmpi | | no |    
| [openmpi-ubuntu-gpu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169881124?tag=openmpi-ubuntu-gpu-20.04)    | arm64,amd64 | ubuntu | 20.04 | openmpi | | yes |    
| [openmpi-ubuntu-gpu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169881107?tag=openmpi-ubuntu-gpu-22.04)    | arm64,amd64 | ubuntu | 22.04 | openmpi | | yes |    


