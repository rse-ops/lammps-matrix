# Flux Operator LAMMPS Experiment

I've struggled a bit with deciding how to run these experiments - there are too many options. I really dislike terraform (it's hard and annoying often) and I am not a huge fan of the batch / cloud formation stuff either. So instead I'm going to try creating a minicluster and running Singularity there - kind of a combination between cloud and HPC. We will prototype this with:

 - [c2d-standard-8](https://cloud.google.com/compute/docs/compute-optimized-machines#c2d_machine_types)
  
## Setup

To start I'm leaving out the network optimization. We will follow [these best practices](https://cloud.google.com/architecture/best-practices-for-using-mpi-on-compute-engine).

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

### Flux Operator

When the cluster is ready, install the Flux Operator from the development branch.

```bash
kubectl apply -f https://raw.githubusercontent.com/flux-framework/flux-operator/test-refactor-modular/examples/dist/flux-operator-refactor.yaml
```

You can check logs to ensure it is also running, in the `operator-system` namespace.

## Experiments

Thinking through this - I think we have two options:

1. Create a MiniCluster with Singularity installed, and then pull the Singularity containers to it. If we install compspec-go there, we can then (on the fly) do an image selection task and submit a job. Pros - it mimics an HPC cluster. Cons - we have to possibly deal with MPI / binding with Singularity.
2. Create a MiniCluster (that runs one job) per random selection. Compspec would be run on the host to do selection, and (in advance) I'd prototype a minicluster for each expected container. Pros - is a more cloud native approach, and the MPI is isolated within the application container. Cons - does not mimic an HPC cluster as well (but still uses the Flux Operator, so maybe not terrible?).

I don't know that I have preference for either so I'll try both.

### Test Case: Separate MiniCluster

Note that this experiment is designed to run on an ARM or AMD cluster, not both. It also is not designed for GPU. This means if we select based on platform (and don't ask for gpu) we are going to fake it and still provide the `lmp_gpu` executable (and not lmp) and it would fail either way - either from missing the binary, or from having it but not having the GPU. I'm choosing the second since that failure state is closer to emulating running something that is not compatible.

```bash
# basic "wild west" (only 2/25 successful)
python run_experiments.py --manifests ../../manifests.yaml --mode basic --outdir ./results/test --iters 25

# account for platform (6/25 successful)
python run_experiments.py --manifests ../../manifests.yaml --mode platform --outdir ./results/test --iters 25

# account for platform and version (12/25 successful)
python run_experiments.py --manifests ../../manifests.yaml --mode platform-version --outdir ./results/test --iters 25

# use compspec (complete descriptive case) WITHOUT mpi consideration (but still worked great - 25/25 successful!)
export PATH=/home/vanessa/Desktop/Code/supercontainers/compspec-go/bin:$PATH
python run_experiments.py --manifests ../../manifests.yaml --mode descriptive-basic --outdir ./results/test --iters 25

# use compspec with MPI consideration (not done yet)
```

I realized we could have a gradient in our compatibility (!!), with the "complete descriptive" case using compspec, and the others just taking marginal steps toward that:

 - **basic** (aka, a static platform) emulates a standard image selection from a static platform (e.g., ubuntu jammy) where we select only based on matching amd64, and the rest is "wild westy" - we can get ubuntu or rocky for any version, or gpu/cpu. The only filter is the base platform type.
 - **platform**: is more selective to, given choosing an ubuntu container, to match to another ubuntu. This can still have issues with glibc or similar.
 - **platform-version** is the same, but we also match based on ubuntu or rocky version.
 - **descriptive-basic**: takes core metadata into account, but not mpi (but maybe that's ok?)

With the above, we will be able to show a gradient of success. We aren't at the point (yet) of this selection being for optimizing based on performance, but this will come. Also note for the actual experiments you will want to pull the containers to the nodes first! I guess it doesn't matter so much for the wall time, but would for the wrapper time (if we care about that).

#### Questions for group

1. We need to decide how much of the "basic" matching to control. E.g., "complete wild west" is to only match on platform. Technically this is what the image selection would do, but in most cases we do better matching manually with image tags corresponding to OS, minimally, sometimes version. I'm wondering if we should scope to OS (and then randomly select version, so we still see glibc errors) but not allow, for example, rocky + ubuntu combined. If we do too much controlled then we won't see much variance in the experiments - the variation we see will come down to the mpi variant used, which has nothing to do with image selection.
2. Do we want to match the os version? If we don't we will have a lot of errors because of glibc, but maybe that's what we want - the platform matching is the current way it would happen. We can compensate by doing more runs (and getting more successful runs) and then categorizing the failures into buckets of "why/"
3. What scale do we want to do this at, and with/without GPU (will add complexity - maybe do vanilla case first without GPU then add in?)
4. Do we want to do separate experiments for each of arm and amd? What about gpu?
4. General feedback - is this approach OK?

A more robust experiment would have a cluster with multiple node types (arm and amd) and some with GPU, and then we would do something like, based on nodes free, choose the best image. But that might be too complex for this first shot.

#### TODO

- we will want a simple job / minicluster to run, one per image, to pull containers first.
- we will want a script to parse output files and derive "reason for failure"
- for the plots, we will want to show, for each compatibility mode, the breakdown of failures.
- for next steps we will want to assume compatibility of platform / os / version and add in application specifics, and then instead of "it worked or not" we can say "it worked better" or not.

This is awesome!

### Clean Up

When you are done:

```bash
gcloud container clusters delete test-cluster --region=us-central1-a
```

## Suggested Next Steps

1. Discuss fluence issues / PodGroup issues, and test again.
2. Discuss output timings we need (right now I am not calculating and saving any timings)
3. Run experiments slightly larger scale as a test run
4. Discuss larger run / strategy!
