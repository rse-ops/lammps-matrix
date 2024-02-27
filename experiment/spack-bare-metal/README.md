# Spack Experiment

We are going to build variants of packages with spack.
  
## Setup

Let's clone spack and ensure we have compspec go.

```
git clone https://github.com/compspec/compspec-go
cd compspec-go

# This builds for x86
make

# This builds for ppc (lassen)
make build-ppc
```

Note that you should do all builds on quartz, where there is a newer Go. Lassen has an old go (1.15).

```
GO111MODULE="on" GOARCH=ppc64le /p/vast1/fractale/descriptive-thrust/software/go/bin/go build -o $(LOCALBIN)/compspec-ppc cmd/compspec/compspec.go
```

Note that current versions of packages.yaml and compilers.yaml are provided in [config](config),

This will need to be on the path

```bash
export PATH=$PWD/bin:$PATH
```

Setup the spack environment.

```bash
python3 -m venv spack-env
```
I put this in a script to source.

```bash
#!/bin/bash
# python3 -m venv spack-env
echo "Hello, your python is at $(which python3)"
source spack-env/bin/activate
. spack/share/spack/setup-env.sh
echo "Oh no... spack... 😱️ $(spack --version)"
echo "Godspeed, cluster adventurer"
```

[Here are all the variants](https://packages.spack.io/package.html?name=lammps) of lammps we can build! 

Let's just build a bunch. We will start with one and then see if we can get metadata for it.

```bash
spack install lammps
```

You can find where it was installed:

```
spack find --path lammps
```

Load it to get the executable on the path:

```
spack load lammps
```

We are going to want to have compatibility metadata linked to specific hashes for spack, and then load them in a flux job to run the experiment. But we need to 1. write a script to extract the metadata first, and 2. generate all the spack builds! Note that we can get some host environment metadata here:

```console
(spack-env) [sochat1@corona171:spack-bare-metal]$ cat /p/vast1/fractale/descriptive-thrust/experiment/spack-bare-metal/spack/opt/spack/linux-rhel8-zen2/gcc-10.3.1/lammps-20230802.2-l75zzkprajipt5e5daomwfyxe3meus3q/.spack/install_environment.json  | jq
{
  "host_os": "rhel8",
  "platform": "linux",
  "host_target": "zen2",
  "hostname": "corona171",
  "spack_version": "0.22.0.dev0 (fae6d3780fbf034390048d1fc706545ab83421f5)",
  "kernel_version": "#1 SMP Fri Jan 12 16:54:14 PST 2024"
}
```

## Spack Builds

Starting from the above, we were able to built four variants of spack on Lassen, Corona, and Quartz:

```
$ spack find --deps lammps
-- linux-rhel7-power9le / xl@16.1 -------------------------------
lammps@20230802.2
    cmake@3.23.1
    fftw@3.3.10
    gmake@4.2.1
    spectrum-mpi@2023.03.13

lammps@20230802.2
    cmake@3.23.1
    cuda@11.8.0
    fftw@3.3.10
    gmake@4.2.1
    spectrum-mpi@2023.03.13


-- linux-rhel8-broadwell / gcc@12.1.1 ---------------------------
lammps@20230802.2
    cmake@3.26.5
    fftw@3.3.10
    gcc-runtime@12.1.1
    gmake@4.2.1
    openmpi@4.1.2


-- linux-rhel8-broadwell / intel@2021.6.0 -----------------------
lammps@20230802.2
    cmake@3.26.5
    fftw@3.3.10
    gmake@4.4.1
    mvapich2@2.3.7
```

Here are the specs for each:

```
# Quartz
spack install lammps%intel@2021.6.0 ^mvapich2@2.3.7%intel@2021.6.0 ^fftw@3.3.10

# Lassen (without and with CUDA)
spack install lammps%xl@16.1 ^fftw@3.3.10%xl@16.1 ^spectrum-mpi@2023.03.13%xl@16.1 ^cmake@3.23.1
spack install lammps%xl@16.1 +cuda cuda_arch=70 ^fftw@3.3.10%xl@16.1 ^spectrum-mpi@2023.03.13%xl@16.1 ^cmake@3.23.1 ^cuda@11.8.0 

# Corona
spack install lammps%gcc@gcc@12.1.1 ^cmake@3.26.5 ^fftw@3.3.10 ^gmake@4.4.1 ^mvapich2@2.3.7
```

## Host Environment

To add to the metadata extraction, we will generate a host `compspec-<host>.json` on each of lassen, quartz, and corona. Here is what that looks like (assuming you have built compspec as shown above):

```
mkdir -p ./hosts
# On quartz
compspec extract --out ./hosts/compspec-quartz.json

# On lassen (a subset since we get permission errors with things)
compspec-ppc extract --allow-fail --name nfd[cpu,memory,network,storage,system] --name system[processor,arch,memory] --out ./hosts/compspec-lassen.json
compspec-ppc extract --out ./hosts/compspec-quartz.json

# On corona
compspec extract --out ./hosts/compspec-corona.json
```

## Metadata Extraction

We can now generate artifacts for each! Here is how I did that. We are going to use [extract-metadata.py](extract-metadata.py) to do that:

```bash
# The only extra dependency you need.
pip install pyyaml

usage: extract-metadata.py [-h] [--spack-root SPACK_ROOT] [--package PACKAGE] [--compspec-json COMPSPEC] [--outdir OUTDIR]

Extract Spack Metadata

optional arguments:
  -h, --help            show this help message and exit
  --spack-root SPACK_ROOT
                        spack root
  --package PACKAGE     package name to seach for
  --compspec-json COMPSPEC
                        host compatibility information
  --outdir OUTDIR       output directory for results
```

Let's do the extraction. We are going to target specific binaries (that match to hosts) just by including a subset of the path.
Note that this takes a little long on the filesystem, oups. Here is what I see in our install:

```
$ find . -name *lammps.h

# This is lassen
./linux-rhel7-power9le/xl-16.1/lammps-20230802.2-nof5qz5k6lrafqdd6bnzpu3va5hj6qbu/include/lammps/lammps.h
./linux-rhel7-power9le/xl-16.1/lammps-20230802.2-thmw3hvmel7xuew7cipxtspzrsu7nxq3/include/lammps/lammps.h

# This is quartz
./linux-rhel8-broadwell/gcc-12.1.1/lammps-20230802.2-fuuonv3y4cddfswssbuse5jfp2cjmn7p/include/lammps/lammps.h
./linux-rhel8-broadwell/intel-2021.6.0/lammps-20230802.2-rqspxlxcrxzhov5rlojh2rrus3x6mvbh/include/lammps/lammps.h

# And corona?
./linux-rhel8-zen2/gcc-10.3.1/lammps-20230802.2-l75zzkprajipt5e5daomwfyxe3meus3q/include/lammps/lammps.h
```

```console
# This is just for future us to remember!
mkdir -p ./specs/lassen ./specs/quartz ./specs/corona

# Lassen
# Note that I added system->arch->name->ppc64le because I haven't written a ppc extractor
# I also added system->processor->0.target and 0.vendor because of same
# And /etc/redhat-release for rhel 7.9
# This is with/without cuda
python extract-metadata.py \
    --spack-root /p/vast1/fractale/descriptive-thrust/experiment/spack-bare-metal/spack  \
    --compspec-json ./hosts/compspec-lassen.json \
    --package lammps-20230802.2-nof5qz5k6lrafqdd6bnzpu3va5hj6qbu \
    --package lammps-20230802.2-thmw3hvmel7xuew7cipxtspzrsu7nxq3
    --outdir ./specs/lassen

# Quartz
python extract-metadata.py \
    --spack-root /p/vast1/fractale/descriptive-thrust/experiment/spack-bare-metal/spack  \
    --compspec-json ./hosts/compspec-quartz.json \
    --package lammps-20230802.2-fuuonv3y4cddfswssbuse5jfp2cjmn7p \
    --package lammps-20230802.2-rqspxlxcrxzhov5rlojh2rrus3x6mvbh \
    --outdir ./specs/quartz

# Corona
python extract-metadata.py \
    --spack-root /p/vast1/fractale/descriptive-thrust/experiment/spack-bare-metal/spack  \
    --compspec-json ./hosts/compspec-corona.json \
    --package lammps-20230802.2-l75zzkprajipt5e5daomwfyxe3meus3q \
    --outdir ./specs/corona
```

This gives us the following specs. I think we can just use them locally (no need to push to a registry).

```bash
tree ./specs
```
```console
tree specs/
specs/
├── corona
│   └── lammps-20230802.2-l75zzkprajipt5e5daomwfyxe3meus3q.json
├── lassen
│   ├── lammps-20230802.2-nof5qz5k6lrafqdd6bnzpu3va5hj6qbu.json
│   └── lammps-20230802.2-thmw3hvmel7xuew7cipxtspzrsu7nxq3.json
└── quartz
    ├── lammps-20230802.2-fuuonv3y4cddfswssbuse5jfp2cjmn7p.json
    └── lammps-20230802.2-rqspxlxcrxzhov5rlojh2rrus3x6mvbh.json
```

## Experiments

I think we likely want to:

1. Write a dummy script that knows how to load the correct MPI, environment, etc. based on metadata. If there isn't metadata, we need to mock a "vanilla" unprepared environment.
2. Test running N jobs of lammps with a `spack load <spec>` at varying levels of metadata.
3. Try to save runtimes and show change with adding compatibility metadata.

Going back to sleep for a bit.
