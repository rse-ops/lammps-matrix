# LAMMPS Matrix

Testing builds of lammps across a few:

 - MPI implementations
 - OS and versions
 - architectures

## Strategy
 
Note that we take the following approach:

1. Build the containers separately, one per arch, to fit into GitHub actions. This is done via the workflow [.github/workflows/docker-builds.yaml](.github/workflows/docker-builds.yaml)
2. Use a custom tool to emulate the image selection process that is normally done by a container runtime. The reason is because we want to inject randomness - a registry will typically deliver a manifest list, and then the runtime chooses the first match. This doesn't give very interesting experiment results, so instead we are going to select based on platform (what the registry does) and then randomly choose from that set. 

Note that if you are interested in the assembled manifest images, we have prepared them, and you can see those specs in [manifests](manifests).

## Vision

Note that for this initial prototype, we are largely doing everything manually. However, these manual steps will eventually be easily automated. Here are the ideal before and after scenarios.

### Prototype

Currently we build them separately, and then will use a custom tool that takes pairings of image and [ORAS artifact](https://oras.land/docs/how_to_guides/pushing_and_pulling) URIs, and assembles the two together into a graph. For the case that emulates a vanilla registry, choosing an image based on platform and nothing else, we will filter by platform and then randomly select. For the informed case using more descriptors, we will add more metadata to that choice. In both cases we will run the application and assess performance (wall time for now). In practice this means (the steps here) for this experiment:

1. Ask the plugin to choose a best image from a set
2. The plugin will take the pairings of images and metadata, and (based on mode of operation) choose basic or descriptive
3. In basic mode, images are filtered based on platform, and one randomly chosen from that set.
4. In descriptive mode, images are filtered based on all metadata provided (e.g., matching to MPI, platform, OS, etc)
5. In both cases, a final image URI is delivered to run for the application.

In the above, the builds are done in CI, but separate (so we can consider them more manual). The metadata is also prepared and pushed manually, and this would eventually be an automated process.

### Production

When we have a production compatibility specification, it will be defined and paired alongside an image in a registry. The container runtime tool will likely accept similar plugins that discover the compatibility artifacts, and then (also with a plugin-based approach) be able to more intelligently select the right image for an environment.

1. Images are built and pushed with automated metadata extraction and artifact generationm.
2. Ask the registry for an image URI via a container runtime
4. The registry links compatibility metadata with each image
5. The container runtime uses the compatibility metadata to select the best image.

## Matrices

### Builds

Here is our matrix of original builds (separated into different images for easier building). We should review this matrix (and what we want to use for our experiment, and determine if a combination is missing). Some are not done or hard, e.g., [intel-mpi](https://github.com/GoogleCloudPlatform/hpc-tools/issues/4) installed with hpc-tools does not have support for ARM). There are likely ways to build the missing entries in the matrix if we decide they are important.

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


## Next Steps

- **Extraction of metadata**: into a JSON blob that conforms to our [prototype spec](https://github.com/supercontainers/compspec),one associated per URI (undecided if I should automate this given the potential need to extract or shell, I'm hoping I can do something statically but might just make them manually for this first shot since we know most of the metadata).
- **Generation of artifacts**: and push to an OCI registry with ORAS.
- **Command Line Tool**: to assist with image selection based on paired images and their metadata, and in a basic or descriptive mode.


## License

HPCIC DevTools is distributed under the terms of the MIT license.
All new contributions must be made under this license.

See [LICENSE](https://github.com/converged-computing/cloud-select/blob/main/LICENSE),
[COPYRIGHT](https://github.com/converged-computing/cloud-select/blob/main/COPYRIGHT), and
[NOTICE](https://github.com/converged-computing/cloud-select/blob/main/NOTICE) for details.

SPDX-License-Identifier: (MIT)

LLNL-CODE- 842614
