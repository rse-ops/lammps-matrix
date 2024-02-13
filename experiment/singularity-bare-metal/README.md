# Singularity LAMMPS Experiment

This will pull our experiment containers down to "bare metal" to run with Singularity on an HPC cluster. 
  
## Setup

Get a nice location, ensure you have Singularity, and pull your containers.
The example script is provided as [pull-containers.sh](pull-containers.sh). And **important**!
Ensure that you set `SINGULARITY_CACHEDIR` to somewhere with a lot of space (that is not your home...)

```bash
mkdir -p ./containers
cd ./containers
# get an allocation
flux alloc -N 1 --queue pdebug --time 3600s
# run pull-containers.sh
```

We already have go on the cluster, and just need to clone and build compspec go.

```
git clone https://github.com/supercontainers/compspec-go
cd compspec-go
make
```

This will need to be on the path

```bash
export PATH=$PWD/bin:$PATH
```

## Test Run

Let's grab a debug node and do some test runs with a container. I'm not great using HPC so I need to sanity check what I'm doing.

```
# Note there are 96 tasks on the node
flux alloc -N 1 --queue pdebug --time 3600s
container=/p/vast1/fractale/descriptive-thrust/singularity-bare-metal/containers/lammps-matrix_openmpi-ubuntu-20.04-amd64.sif

module load openmpi
flux run -N 1 --ntasks 48 -c 1 -o cpu-affinity=per-task singularity exec $container /usr/bin/lmp -v x 16 -v y 8 -v z 16 -in /opt/lammps/examples/reaxff/HNS/in.reaxc.hns -nocite
```

I think we are going to need to do loads and binds associated with each mpi variant. This would be the next step here!
Perhaps that is part of metadata?

```
mpiA=/usr/tce/packages/openmpi/openmpi-4.1.2-intel-classic-2021.6.0-magic/lib/libmpi.so
mpiB=/usr/lib/x86_64-linux-gnu/libmpi.so
flux run -N 1 --ntasks 48 -c 1 -o cpu-affinity=per-task singularity exec --bind $mpiA:$mpiB $container /usr/bin/lmp -v x 16 -v y 8 -v z 16 -in /opt/lammps/examples/reaxff/HNS/in.reaxc.hns -nocite
```

