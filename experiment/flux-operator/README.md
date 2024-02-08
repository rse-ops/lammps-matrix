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

I don't know that I have preference for either, so I'll take the path of least resistence (Flux Operator).

### Gradient of Compatibility

I realized we could have a gradient in our compatibility (!!), with the "complete descriptive" case using compspec, and the others just taking marginal steps toward that:

 - **basic** (aka, a static platform) emulates a standard image selection from a static platform (e.g., ubuntu jammy) where we select only based on matching amd64, and the rest is "wild westy" - we can get ubuntu or rocky for any version, or gpu/cpu. The only filter is the base platform type.
 - **platform**: is more selective to, given choosing an ubuntu container, to match to another ubuntu. This can still have issues with glibc or similar.
 - **platform-version** is the same, but we also match based on ubuntu or rocky version.
 - **descriptive-basic**: takes core metadata into account, but not mpi (but maybe that's ok?)

With the above, we will be able to show a gradient of success. We aren't at the point (yet) of this selection being for optimizing based on performance, but this will come. For this gradient, we can easily turn it into a number by representing the set of features as a vector, and then taking a cosine distance. We will do this in the analysis section.

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
```

#### Questions for group

We didn't talk much about these but I think I have what I need to move forward.

1. We need to decide how much of the "basic" matching to control. E.g., "complete wild west" is to only match on platform. Technically this is what the image selection would do, but in most cases we do better matching manually with image tags corresponding to OS, minimally, sometimes version. I'm wondering if we should scope to OS (and then randomly select version, so we still see glibc errors) but not allow, for example, rocky + ubuntu combined. If we do too much controlled then we won't see much variance in the experiments - the variation we see will come down to the mpi variant used, which has nothing to do with image selection.
2. Do we want to match the os version? If we don't we will have a lot of errors because of glibc, but maybe that's what we want - the platform matching is the current way it would happen. We can compensate by doing more runs (and getting more successful runs) and then categorizing the failures into buckets of "why/"
3. What scale do we want to do this at, and with/without GPU (will add complexity - maybe do vanilla case first without GPU then add in?)
4. Do we want to do separate experiments for each of arm and amd? What about gpu?
4. General feedback - is this approach OK?

A more robust experiment would have a cluster with multiple node types (arm and amd) and some with GPU, and then we would do something like, based on nodes free, choose the best image. But that might be too complex for this first shot.

### Experiment 1: AMD64 cluster

This is almost the same as the above experiment, but we will do more runs (N=30).

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
```bash
kubectl apply -f https://raw.githubusercontent.com/flux-framework/flux-operator/test-refactor-modular/examples/dist/flux-operator-refactor.yaml
```

Here are the run commands (note that I ran basic mode first, saving to test, so we would pull the containers).

```bash
# basic "wild west"
python run_experiments.py --manifests ../../manifests.yaml --mode basic --outdir ./results/amd64 --iters 30

# account for platform
python run_experiments.py --manifests ../../manifests.yaml --mode platform --outdir ./results/amd64 --iters 30

# account for platform and version (12/25 successful)
python run_experiments.py --manifests ../../manifests.yaml --mode platform-version --outdir ./results/amd64 --iters 30

# use compspec (complete descriptive case)
export PATH=/home/vanessa/Desktop/Code/supercontainers/compspec-go/bin:$PATH
python run_experiments.py --manifests ../../manifests.yaml --mode descriptive-basic --outdir ./results/amd64 --iters 30

# mpi modes (to add a dimension of performance?)
python run_experiments.py --manifests ../../manifests.yaml --mode openmpi --outdir ./results/amd64 --iters 30
python run_experiments.py --manifests ../../manifests.yaml --mode mpich --outdir ./results/amd64 --iters 30
python run_experiments.py --manifests ../../manifests.yaml --mode intel-mpi --outdir ./results/amd64 --iters 30
```

When you are done:

```bash
gcloud container clusters delete test-cluster --region=us-central1-a
```

### Experiment 1: AARM64 cluster

Let's now run the same, but with arm! Note that arm do not support compact placement!

```bash
GOOGLE_PROJECT=myproject
gcloud container clusters create test-cluster \
    --threads-per-core=1 \
    --num-nodes=5 \
    --region=us-central1-a \
    --project=${GOOGLE_PROJECT} \
    --machine-type=t2a-standard-8
```

Note that Google labels will prevent this from being scheduled so we manually tweak the nodes:

```bash
for node in $(kubectl get nodes -o json | jq -r .items[].metadata.name); do
    kubectl taint nodes $node kubernetes.io/arch=arm64:NoSchedule-
done
```
```bash
kubectl apply -f https://raw.githubusercontent.com/flux-framework/flux-operator/test-refactor-modular/examples/dist/flux-operator-refactor-arm.yaml
```

Here are the run commands (note that I ran basic mode first, saving to test, so we would pull the containers).

```bash
# basic "wild west"
python run_experiments.py --manifests ../../manifests.yaml --mode basic --outdir ./results/arm64 --iters 30 --platform arm64

# account for platform
python run_experiments.py --manifests ../../manifests.yaml --mode platform --outdir ./results/arm64 --iters 30 --platform arm64

# account for platform and version
python run_experiments.py --manifests ../../manifests.yaml --mode platform-version --outdir ./results/arm64 --iters 30 --platform arm64 --force

# use compspec (complete descriptive case)
export PATH=/home/vanessa/Desktop/Code/supercontainers/compspec-go/bin:$PATH
python run_experiments.py --manifests ../../manifests.yaml --mode descriptive-basic --outdir ./results/arm64 --iters 30 --platform arm64  --force

# mpi modes (to add a dimension of performance?)
python run_experiments.py --manifests ../../manifests.yaml --mode openmpi --outdir ./results/arm64 --iters 30 --platform arm64


python run_experiments.py --manifests ../../manifests.yaml --mode mpich --outdir ./results/arm64 --iters 30 --platform arm64  --force
python run_experiments.py --manifests ../../manifests.yaml --mode intel-mpi --outdir ./results/arm64 --iters 30 --platform arm64  --force
```

When you are done:

```bash
gcloud container clusters delete test-cluster --region=us-central1-a
```


## Analysis

For our analysis, we are interested in:

 - parsing output files to derive a reason for failure
 - plots, we that show, for each compatibility mode, the breakdown of failures.

```bash
# amd64
python plot-results.py --results ./results/amd64 --out ./img/amd64

# arm64
python plot-results.py --results ./results/arm64 --out ./img/arm64
```

For next steps we will want to assume compatibility of platform / os / version and add in application specifics, and then instead of "it worked or not" we can say "it worked better" or not.

This is awesome!

TODO talk notes:

SLIDE on what we know / general needs/ what can go wrong
 - slide about what we know about enviornment general needs (flux added on fly, build needs to match our application, this is an example of app -> app compatibility) - potential errors are glibc
 - We don't need to bind MPI to the host (not HPC) BUT we need to know MPI variant for setup of the enviroment potential errors are MPI built with one app being used for otherbecause correct one not on path
 - some containers built for GPU
 
slide that reviews cases

walks through results, shows that even for tiny runs, detail that GKErun better with mpich is importnat.

### Clean Up

When you are done:

```bash
gcloud container clusters delete test-cluster --region=us-central1-a
```
