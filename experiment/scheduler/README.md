# Descriptive Expression + Scheduler Experiment

> To select clusters to run LAMMPS.

This simple setup will mirror the [image selection](../flux-operator) experiments using the Flux Operator, but instead of relying on submitting separate MiniCluster, we will:

1. Create two large clusters: arm and x86 cluster (each with different node types)
2. On each cluster, deploy several instances of interactive MiniCluster, which will vary in architecture, base operating system and version.  Conceptually, you can think of this as several different clusters. We will have 8:

  - **ubuntu-amd-focal**: ghcr.io/rse-ops/rainbow-flux-ubuntu:amd-focal
  - **ubuntu-amd-jammy**: ghcr.io/rse-ops/rainbow-flux-ubuntu:amd-jammy
  - **rocky-amd-8**: ghcr.io/rse-ops/rainbow-flux-rocky:amd-8
  - **rocky-amd-9**: ghcr.io/rse-ops/rainbow-flux-rocky:amd-9

**Currently building**

  - **rocky-arm-8**: ghcr.io/converged-computing/flux-view-rocky:arm-8
  - **rocky-arm-9**: ghcr.io/converged-computing/flux-view-rocky:arm-9
  - **ubuntu-arm-focal**: ghcr.io/converged-computing/flux-view-ubuntu:arm-focal
  - **ubuntu-arm-jammy**: ghcr.io/converged-computing/flux-view-ubuntu:arm-jammy

These containers were built in [docker](docker), and for ARM, were built on an equivalent Google Cloud VM.
I gave each of the above a cluster name we can refer to that reflects the architecture, os and version.
These containers have been rebuilt based on the same [flux-views](https://github.com/converged-computing/flux-views) containers,
but the multi-stage build is removed and spack is added, as we are going to use these to provide a full flux install (and use disable view).
The aspect of compatibility will come by pulling down a Singularity container to run.
We will use this instance type again:

 - [c2d-standard-8](https://cloud.google.com/compute/docs/compute-optimized-machines#c2d_machine_types)

## Experiment

We will do the following:

1. Generate jobspecs from the previous compatibility artifacts
2. Write a means to generate subsystem graphs based on a cluster graph (will be done when clusters are created)
3. Deploy two clusters, one for arm and one for x86. 
4. Install the flux operator
5. Rainbow will be deployed (with an exposed service endpoint) on the x86.
6. Each cluster will have nodes generated via compspec, and register to rainbow.

## 1. Generate Jobspecs

We previously used compatibility artifacts to determine compatibility, but now we are representing this same metadata as part of a job, so we are going to include the attributes within jobspecs. Specifically, we will define them each as subsystems with requirements on the level of a job. E.g., "task A to run lammps requires X" and then X will be part of a subsystem graph. This means that we can generate the same dimension of compatibility by (step-wise) registering our different subsystems. 

```bash
# pip install rainbow-scheduler
cd ./compspec
python generate_jobspecs.py
```

For the above, we use [this function](https://github.com/converged-computing/rainbow/blob/8a8db39196d64536983ca6aaa6defdf229ea8b6a/python/v1/rainbow/jobspec/converter.py#L4-L47) from rainbow-scheduler (the Python rainbow library) and the [schema attributes](https://github.com/compspec/schemas) for each of mpi, io.archspec, hardware, and os as different subsystems. The resulting data is in [jobspecs](jobspecs) where each yaml is a jobspec we will submit to rainbow, and a cluster will be selected. When we receive the work on the clusters we will want to record which ones are sent where, etc.

## 2. Subsystems

We will have subsystems for:

- archspec 
- operating system (name and version)
- MPI variants
- hardware

And we need a script that can generate these on the fly for some specification of a node graph. For these experiments we have all the metadata on the level of a node, and for all nodes in a cluster, so it should be simple to write a script to do that. While this will be generated on the fly for the cluster, for now I'll prototype something in [subsystems](subsystems) assuming a faux cluster nodes graph.


## 1. Deploy Clusters

Let's create the ARM and X86 clusters.

```bash
GOOGLE_PROJECT=myproject
gcloud container clusters create test-cluster \
    --threads-per-core=1 \
    --placement-type=COMPACT \
    --num-nodes=5 \
    --region=us-central1-a \
    --project=${GOOGLE_PROJECT} \
    --machine-type=c2d-standard-8
```

Note that I stopped here - the LAMMPS containers were not running, just about anywhere, and I chose not to handle the task of debugging 18 different lammps installs. If someone else wants to do it, please do! It would be nice to reproduce the image selection experiments in a different context.


