# Build amd64

We are going to use the same strategy here as we did for [build-arm](../build-arm) but on a different instance.
Note that this is the same image, but the x86 variant. The AMI is `ami-0277155c3f0ab2930` and the instance type instead of hpc7g.4xlarge 
is m5.4xlarge (it's the Amazon Linux 2023 AMI, and I still did 200 GiB storage).

## Build

Shell into the instance with your PEM:

```bash
ssh -o 'IdentitiesOnly yes' -i path-to-key.pem ec2-user@ec2-52-55-54-40.compute-1.amazonaws.com
```

You'll again want docker installed, here are the instructions again:

```bash
sudo yum update -y
sudo yum install -y docker screen git make
sudo systemctl start docker
sudo usermod -aG docker $USER
sudo setfacl --modify user:ec2-user:rw /var/run/docker.sock
```

Install oras:

```bash
VERSION="1.1.0"
curl -LO "https://github.com/oras-project/oras/releases/download/v${VERSION}/oras_${VERSION}_linux_amd64.tar.gz"
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
cd build-amd
mkdir -p ./specs

# These are gpu, openmpi and ubuntu
hasGpu=yes
for version in 20.04 22.04; do
    tag=openmpi-ubuntu-gpu-${version}-amd64
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
    tag=openmpi-rocky-gpu-${version}-amd64
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
        tag=${mpi}-ubuntu-${version}-amd64
        image=ghcr.io/rse-ops/lammps-matrix:${tag}
        echo "Building $image"
        docker build --build-arg tag=${version} --network=host --tag $image ../${mpi}-ubuntu/
        docker push ${image}
        cmd=". /etc/profile && /tmp/data/generate.sh $hasGpu /tmp/data/specs/compspec-${tag}.json"
        docker run --entrypoint bash -v $PWD:/tmp/data -it ${image} -c "$cmd"
        oras push ${image}-compspec --artifact-type application/org.supercontainers.compspec ./specs/compspec-${tag}.json:application/org.supercontainers.compspec
    done
done

# and rocky
for version in 8 9; do
    tag=intel-mpi-rocky-${version}-amd64
    image=ghcr.io/rse-ops/lammps-matrix:${tag}
    echo "Building $image"
    docker build --build-arg tag=${version} --network=host --tag $image ../intel-mpi-rocky/
    docker push ${image}
    cmd=". /etc/profile && /tmp/data/generate.sh $hasGpu /tmp/data/specs/compspec-${tag}.json"
    docker run --entrypoint bash -v $PWD:/tmp/data -it ${image} -c "$cmd"
    oras push ${image}-compspec --artifact-type application/org.supercontainers.compspec ./specs/compspec-${tag}.json:application/org.supercontainers.compspec
done
```

## Builds

Here are the final builds (with artifacts each) for the above.

| Image               | Architecture | OS    | OS Version | MPI     | MPI version | GPU |
|---------------------|--------------|-------|------------|---------|-------------|-----|
| [intel-mpi-rocky](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169779744?tag=intel-mpi-rocky-8-amd64)            | linux/amd64  | rocky | 8          |intel-mpi|             | no  |
| [intel-mpi-rocky](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169782781?tag=intel-mpi-rocky-9-amd64)            | linux/amd64  | rocky | 9          |intel-mpi|             | no  |
| [openmpi-ubuntu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169782423?tag=openmpi-ubuntu-20.04-amd64)          | linux/amd64  | ubuntu| 20.04      | openmpi |             | no  |
| [openmpi-ubuntu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169782169?tag=openmpi-ubuntu-22.04-amd64)          | linux/amd64  | ubuntu| 22.04      | openmpi |             | no  |
| [openmpi-ubuntu-gpu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169858346?tag=openmpi-ubuntu-gpu-20.04-amd64)  | linux/amd64  | ubuntu| 20.04      | openmpi |             | yes |
| [openmpi-ubuntu-gpu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169812970?tag=openmpi-ubuntu-gpu-22.04-amd64)  | linux/amd64  | ubuntu| 22.04      | openmpi |             | yes |
| [mpich-ubuntu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169781948?tag=mpich-ubuntu-20.04-amd64)              | linux/amd64  | ubuntu| 20.04      | mpich   |             | no  |
| [mpich-ubuntu](https://github.com/rse-ops/lammps-matrix/pkgs/container/lammps-matrix/169782384?tag=mpich-ubuntu-22.04-amd64)              | linux/amd64  | ubuntu| 22.04      | mpich   |             | no  |


These will also be represented in [manifests.yaml](../manifests.yaml)
