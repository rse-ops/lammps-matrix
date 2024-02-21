# Spack Experiment

We are going to build variants of packages with spack.
  
## Setup

Let's clone spack and ensure we have compspec go.

```
git clone https://github.com/compspec/compspec-go
cd compspec-go
make
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

Starting from the above:

```
# Lassen
spack install lammps ^mpich

# Corona
spack install lammps ^intel-oneapi-mpi

# Quartz
spack install lammps
spack install openmpi@4.1.2%gcc@12.1.1 arch=linux-rhel8-broadwell
spack install lammps%gcc@12.1.1 ^openmpi@4.1.2
```

chmod -R g+rwx /p/vast1/fractale/descriptive-thrust

Note that most of these didn't work. Godspeed.
After we have builds we will use [extract-metadata.py](extract-metadata.py) to do that,
and run experiments on some nodes.
