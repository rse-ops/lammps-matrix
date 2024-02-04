# LAMMPS Matrix

Testing builds of lammps across a few:

 - MPI implementations (openmpi, mpich, intel-mpi)
 - OS and versions (ubuntu, rocky, and different versions)
 - architectures (arm64 and amd64)

This is a small set of builds in retrospect, but I'm hopeful will be enough for a proof of concept.

## Strategy
 
Note that we take the following approach:

1. Build the containers separately, one per arch, on AWS VMs. I originally was using GitHub actions but wanted consistency of build environment for each architecture. This was previously done via the workflow [.github/workflows/docker-builds.yaml](.github/workflows/docker-builds.yaml) and now is done in the build subdirectories.
2. Extract metadata with [compspec-go](https://github.com/supercontainers/compspec-go) and put into artifacts we can associate with the images. This gets pushed to the same registry with `-compsec` appended to the tag.
3. Use a custom tool to emulate the image selection process that is normally done by a container runtime. The reason is because we want to inject randomness - a registry will typically deliver a manifest list, and then the runtime chooses the first match. This doesn't give very interesting experiment results, so instead we are going to select based on platform (what the registry does) and then randomly choose from that set.  This will be done with the same tool (but not here).

Note that our tool is implemented at [supercontainers/compspec-go](https://github.com/supercontainers/compspec-go). We also have a directory of [manifests](manifests) that show how to use the manifest-tool to generate actually (multi-platform) manifests. We can't use this approach yet because the compatibility artifact working group has not finished work (and there is no representation of compatibility there).

## Preparing Images

 - See [build-arm](build-arm) for instructions.

## Matrices

See the subdirectories for testing builds. Our final set of images + artifacts are in [manifests.yaml](manifests.yaml)

 - [build-test](build-test): prototyping
 - [build-arm](build-arm): builds for arm
 - [build-amd](build-amd): builds for amd (x86_64)

The final images and matched artifacts are in [manifests.yaml](manifests.yaml). We will next prototype the experiment setup using compspec-go.

## Vision

Note that for this initial prototype, we are largely emulating the steps of image selection with our custom tool. However, these steps can hopefully and eventually be part of a more standard pipeline.

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

## License

HPCIC DevTools is distributed under the terms of the MIT license.
All new contributions must be made under this license.

See [LICENSE](https://github.com/converged-computing/cloud-select/blob/main/LICENSE),
[COPYRIGHT](https://github.com/converged-computing/cloud-select/blob/main/COPYRIGHT), and
[NOTICE](https://github.com/converged-computing/cloud-select/blob/main/NOTICE) for details.

SPDX-License-Identifier: (MIT)

LLNL-CODE- 842614
