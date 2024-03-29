# Build Arm

To generate the arm images we will build on an AWS VM. Note that originally I was using one arm variant, but quickly learned that compatiility (on the level of the architecture) was not guaranteed and wanted to extend the matrix. So here is how to create a base arm image. An early experiment to see if QEMU would have distinct archtecture information is in [experiment.md](experiment.md). Note that it does not - it reflects the host architecture. Note that we will use some of the commands there for setup (and not repeat them here). You should start this small tutorial with a running VM that has docker installed.

## Build

Shell into the instance with your PEM:

```bash
ssh -o 'IdentitiesOnly yes' -i path-to-key.pem ec2-user@ec2-52-55-54-40.compute-1.amazonaws.com
```

Install oras (for arm)!:

```bash
VERSION="1.1.0"
curl -LO "https://github.com/oras-project/oras/releases/download/v${VERSION}/oras_${VERSION}_linux_arm64.tar.gz"
mkdir -p oras-install/
tar -zxf oras_${VERSION}_*.tar.gz -C oras-install/
sudo mv oras-install/oras /usr/local/bin/
rm -rf oras_${VERSION}_*.tar.gz oras-install/
```

Note that we aren't going to use bulidx here. Clone this repository for the Dockerfiles.

```bash
git clone https://github.com/rse-ops/lammps-matrix
cd lammps-matrix
```

Let's now build our images and artifacts. Since we get no benefit from building inside the container, let's run it post build.
We will use [generate.sh](generate.sh). You'll need to login to ghcr.io with a GitHub personal access token for password.

```bash
docker login ghcr.io
```

And then run the builds and extractions and pushes. Note that we are manually specifying the hasGpu command, and we are sticking with building arm on arm. We will do another instance for x86. Note that we load first so we have the layers.

```bash
# create directory for output specs
cd build-arm
mkdir -p ./specs

# These are gpu, openmpi and ubuntu
hasGpu=yes
for version in 20.04 22.04; do
    tag=openmpi-ubuntu-gpu-${version}-arm64
    image=ghcr.io/rse-ops/lammps-matrix:${tag}
    echo "Building $image"
    docker build --build-arg tag=${version} --network=host --tag $image ../openmpi-ubuntu-gpu/
    docker push ${image}
    cmd=". /etc/profile && /tmp/data/generate.sh $hasGpu /tmp/data/specs/compspec-${tag}.json"
    docker run --entrypoint bash -v $PWD:/tmp/data -it ${image} -c "$cmd"
    oras push ${image}-compspec --artifact-type application/org.supercontainers.compspec ./specs/compspec-${tag}.json:application/org.supercontainers.compspec
done


# gpu, openmpi rocky (hpc-tools for intel-mpi does not support arm)
for version in 8 9; do
    tag=openmpi-rocky-gpu-${version}-arm64
    image=ghcr.io/rse-ops/lammps-matrix:${tag}
    echo "Building $image"
    docker build --build-arg tag=${version} --network=host --tag $image ../openmpi-rocky-gpu/
    docker push ${image}
    cmd=". /etc/profile && /tmp/data/generate.sh $hasGpu /tmp/data/specs/compspec-${tag}.json"
    docker run --entrypoint bash -v $PWD:/tmp/data -it ${image} -c "$cmd"
    oras push ${image}-compspec --artifact-type application/org.supercontainers.compspec ./specs/compspec-${tag}.json:application/org.supercontainers.compspec
done

hasGpu=no
for version in 20.04 22.04; do
    for mpi in openmpi mpich; do
        tag=${mpi}-ubuntu-${version}-arm64
        image=ghcr.io/rse-ops/lammps-matrix:${tag}
        echo "Building $image"
        docker build --build-arg tag=${version} --network=host --tag $image ../${mpi}-ubuntu/
        docker push ${image}
        cmd=". /etc/profile && /tmp/data/generate.sh $hasGpu /tmp/data/specs/compspec-${tag}.json"
        docker run --entrypoint bash -v $PWD:/tmp/data -it ${image} -c "$cmd"
        oras push ${image}-compspec --artifact-type application/org.supercontainers.compspec ./specs/compspec-${tag}.json:application/org.supercontainers.compspec
    done
done
```

## Builds

Here are the final builds (with artifacts each) for the above.

| Image               | Architecture | OS    | OS Version | MPI     | MPI version | GPU |
|---------------------|--------------|-------|------------|---------|-------------|-----|
| [openmpi-ubuntu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169792857?tag=openmpi-ubuntu-20.04-arm64)          | linux/arm64  | ubuntu| 20.04      | openmpi |             | no  |
| [openmpi-ubuntu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169809314?tag=openmpi-ubuntu-22.04-arm64)          | linux/arm64  | ubuntu| 22.04      | openmpi |             | no  |
| [openmpi-ubuntu-gpu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169878136?tag=openmpi-ubuntu-gpu-20.04-arm64)  | linux/arm64  | ubuntu| 20.04      | openmpi |             | yes |
| [openmpi-ubuntu-gpu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169880385?tag=openmpi-ubuntu-gpu-22.04-arm64)  | linux/arm64  | ubuntu| 22.04      | openmpi |             | yes |
| [openmpi-rocky-gpu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169886720?tag=openmpi-rocky-gpu-9-arm64)        | linux/arm64  | rocky | 8          | openmpi |             | yes |
| [openmpi-rocky-gpu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169886720?tag=openmpi-rocky-gpu-9-arm64)        | linux/arm64  | rocky | 9          | openmpi |             | yes |
| [mpich-ubuntu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169810873?tag=mpich-ubuntu-20.04-arm64)              | linux/arm64  | ubuntu| 20.04      | mpich   |             | no  |
| [mpich-ubuntu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169814135?tag=mpich-ubuntu-22.04-arm64)              | linux/arm64  | ubuntu| 22.04      | mpich   |             | no  |

These will be represented in [manifests.yaml](../manifests.yaml)
