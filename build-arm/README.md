# Build Arm

To generate the arm images we will build on an AWS VM. Note that originally I was using one arm variant, but quickly learned that compatiility (on the level of the architecture) was not guaranteed and wanted to extend the matrix. So here is how to create a base arm image. 

## Setup

We will be doing this from the command line. The AMI we want is `ami-07ce5684ee3b5482c`. Here is how to ensure you have an hpc instance type (and then choose one):

```bash
aws ec2 describe-instance-type-offerings --location-type availability-zone --filters Name=instance-type,Values=hpc7g.* --region us-east-1 --query InstanceTypeOfferings[*].[InstanceType,Location]
```
```console
[
    [
        "hpc7g.16xlarge",
        "us-east-1a"
    ],
    [
        "hpc7g.8xlarge",
        "us-east-1a"
    ],
    [
        "hpc7g.4xlarge",
        "us-east-1a"
    ]
]
```

Then run it, and for your selected ami! You will need to replace the below with your security group, and subnet ids.

```bash
aws ec2 run-instances --image-id ami-07ce5684ee3b5482c --count 1 --region us-east-1 --instance-type hpc7g.4xlarge --key-name MyKeyPair --security-group-ids $SECURITY_GROUP --subnet-id $SUBNET
```

Note that the subnet ID will associate you with an availability zone. In this case we needed us-east-1a (where the instance is shown to be above).

## Virtual Machine Setup

Shell into the instance with your PEM:

```bash
ssh -o 'IdentitiesOnly yes' -i path-to-key.pem ec2-user@ec2-52-55-54-40.compute-1.amazonaws.com
```

And then install docker and update:

```bash
sudo yum update -y
sudo yum install -y docker
sudo systemctl start docker
sudo usermod -aG docker $USER
sudo setfacl --modify user:ec2-user:rw /var/run/docker.sock
```

At this point give it a test!

```bash
docker run hello-world
```

You should **not** (and should never) need sudo to use docker. If that works, we are good to build here. Let's run this in a screen because we can expect our credential to expire or otherwise get kicked off.

```bash
sudo yum install -y screen git make
screen
```

## Platforms

Let's see what platforms are available to us.

```bash
docker buildx ls
```
```console
  default default         running v0.11.6+0a15675913b7 linux/arm64, linux/arm/v7, linux/arm/v6
```

Let's try adding more builders.

```bash
docker buildx create --name builderbro --use --bootstrap
docker run --privileged --rm tonistiigi/binfmt --install all
```
```bash
docker buildx ls
```
```console
$ docker buildx ls
NAME/NODE     DRIVER/ENDPOINT             STATUS  BUILDKIT             PLATFORMS
builderbro *  docker-container                                         
  builderbro0 unix:///var/run/docker.sock running v0.12.5              linux/arm64, linux/arm/v7, linux/arm/v6, linux/amd64, linux/amd64/v2, linux/riscv64, linux/ppc64le, linux/s390x, linux/mips64le, linux/mips64
default       docker                                                   
  default     default                     running v0.11.6+0a15675913b7 linux/arm64, linux/arm/v7, linux/arm/v6, linux/amd64, linux/amd64/v2, linux/riscv64, linux/ppc64le, linux/s390x, linux/386, linux/mips64le, linux/mips64
```

Wow, that's great!

## Testing Extraction

We next are concerned about being able to run compspec and extract metadata that has the correct platform - the one in qemu and not the container. Let's do some tests. For my strategy I'm going to build LAMMPS and then do a second Dockerfile that installs compspec Go and runs it (and we will see the output). Let's choose a random ARM architecture and try it out. Clone this repository for the Dockerfile.

```bash
git clone https://github.com/rse-ops/lammps-matrix
cd lammps-matrix
```

Let's build two images, two different arm variants.

```bash
docker buildx build --load --platform linux/arm64 --build-arg tag=22.04 --tag ghcr.io/rse-ops/lammps-matrix:openmpi-ubuntu-gpu-22.04-arm64 openmpi-ubuntu-gpu/
```

Now let's test this Dockerfile, which will use the above as a base image and then install go, build compspec-go, run the extraction, and generate the result file.

```dockerfile
ARG BASE
FROM $BASE
RUN wget https://go.dev/dl/go1.21.6.linux-arm64.tar.gz && \
    tar -C /usr/local -xzf go1.21.6.linux-arm64.tar.gz
ENV PATH=/usr/local/go/bin:$PATH
RUN git clone -b tweaks-testing-arm https://github.com/supercontainers/compspec-go
RUN cd ./compspec-go && \
    make build-arm || GO111MODULE="on" GOARCH=arm/7 go build -o ./bin/compspec-arm cmd/compspec/compspec.go && \
    mv ./bin/compspec-arm /usr/local/bin/compspec
RUN compspec extract --name system[processor] /system-processor.json
ENTRYPOINT ["/bin/bash"]
CMD ["cat", "/system-processor.json"]
```

Assuming a Dockerfile in the present working directory, we will then build and run this, targeting the extraction step of just the architecture stuffs:

```bash
docker build -t test-arm-extract .
docker run -it test-arm-extract -c "compspec extract"
```

or for an interactive terminal (good for debugging):

```bash
docker build --build-arg BASE=ghcr.io/rse-ops/lammps-matrix:openmpi-ubuntu-gpu-22.04-arm64 -t test-arm-extract .
docker run -it test-arm-extract
```

We are also going to install this on the host for comparison

```bash
wget https://go.dev/dl/go1.21.6.linux-arm64.tar.gz && \
    sudo tar -C /usr/local -xzf go1.21.6.linux-arm64.tar.gz
export PATH=/usr/local/go/bin:$PATH
git clone -b tweaks-testing-arm https://github.com/supercontainers/compspec-go
cd ./compspec-go
```

Here is what a glimpse looks like. We would want to know if the QEMU builds are the same or different.

```bash
make build-arm && ./bin/compspec-arm extract --name system[processor]
```
```console
...
          "9.botomips": "2100.00",
          "9.family": "8",
          "9.features": "fp asimd evtstrm aes pmull sha1 sha2 crc32 atomics fphp asimdhp cpuid asimdrdm jscvt fcma lrcpc dcpop sha3 sm3 sm4 asimddp sha512 sve asimdfhm dit uscat ilrcpc flagm ssbs paca pacg dcpodp svei8mm svebf16 i8mm bf16 dgh rng",
          "9.model": "0x1",
          "9.vendor": "ARM"
        }
      }
    }
  }
}
```

### Matrix Test

We have two questions now:

1. Can we run the arm/7 (or othe) on this host?
2. Does the compspec extractor see the QEMU metadata or the host?

#### Can we run other arm variants on this host?

> yes, at least v7. v7 is like > 10 years old

We are going to use a dumb base image since the nvidia base doesn't have arm variants. Use this base:

```
# Dockerfile.ubuntu
FROM ubuntu
RUN apt-get update && apt-get install -y wget curl git build-essential mpich
```

And build

```bash
docker buildx build -f Dockerfile.ubuntu --load --platform linux/arm64 --tag ubuntu-arm64 .
docker buildx build -f Dockerfile.ubuntu --load --platform linux/arm/7 --tag ubuntu-arm7 .
```

OK - arm7 runs here.

```bash
[ec2-user@ip-172-31-35-252 lammps-matrix]$ docker run -it ubuntu-arm7 bash
root@913f7a8cbd82:/# echo "hello"
hello
```

That doesn't give us insight to the exec format error from the Flux Operator spack view. Unless
spack somehow built AMG-2023 with the wrong arch? And that works?

#### Does the compspec extractor see the QEMU metadata or the host?

Now let's build images with compspec and dump out the json during the build.
New Dockerfile for arm:

```dockerfile
FROM alpine as base
COPY --from=golang:1.21-alpine /usr/local/go/ /usr/local/go/
RUN apk update && apk add git 
ENV PATH=/usr/local/go/bin:$PATH
RUN git clone -b tweaks-testing-arm https://github.com/supercontainers/compspec-go
RUN cd ./compspec-go && \
    GO111MODULE="on" go build -o ./bin/compspec cmd/compspec/compspec.go && \
    mv ./bin/compspec /usr/local/bin/compspec
RUN compspec extract --name system[processor] -o /system-processor.json
```

And amd64:

```dockerfile
FROM alpine as base
COPY --from=golang:1.21-alpine /usr/local/go/ /usr/local/go/
RUN apk update && apk add git 
ENV PATH=/usr/local/go/bin:$PATH
RUN git clone -b tweaks-testing-arm https://github.com/supercontainers/compspec-go
RUN cd ./compspec-go && \
    GOOS=linux GOARCH=amd64 go build -o ./bin/compspec cmd/compspec/compspec.go
    mv ./bin/compspec /usr/local/bin/compspec
RUN compspec extract --name system[processor] -o /system-processor.json
```

We can compare these two.

```bash
docker buildx build --load -f Dockerfile.alpine --platform linux/arm64 --tag dump-arm . 
docker buildx build --load -f Dockerfile.alpine-amd --platform linux/amd64 --tag dump-amd64 .

docker save dump-arm -o dump-arm.tar
docker save dump-amd64 -o dump-amd.tar
```

It's important to use `--no-cache` if you see the same layer appear twice (it should not) across image dumps.
Export. You'll need to look in the manifest.json to see the last layer.

```bash
tar -xvf dump-arm.tar 
3c1e2f908b4bcdc67af437b3408e3e3253a4a834604923c6b6254bd970b2c371/
3c1e2f908b4bcdc67af437b3408e3e3253a4a834604923c6b6254bd970b2c371/VERSION
3c1e2f908b4bcdc67af437b3408e3e3253a4a834604923c6b6254bd970b2c371/json
3c1e2f908b4bcdc67af437b3408e3e3253a4a834604923c6b6254bd970b2c371/layer.tar
5687db405796cd706882630eab3706c75383a4c4f84b0cf7867bb4d023d0492e.json
6b253cccc690ee789bfa53b37a057c3aecc5cfda1a514e0c13fb08a4afc94adb/
6b253cccc690ee789bfa53b37a057c3aecc5cfda1a514e0c13fb08a4afc94adb/VERSION
6b253cccc690ee789bfa53b37a057c3aecc5cfda1a514e0c13fb08a4afc94adb/json
6b253cccc690ee789bfa53b37a057c3aecc5cfda1a514e0c13fb08a4afc94adb/layer.tar
865aba25526efd1374f8139ebcd604817484a7f159307a028dd522fca1a520ad/
865aba25526efd1374f8139ebcd604817484a7f159307a028dd522fca1a520ad/VERSION
865aba25526efd1374f8139ebcd604817484a7f159307a028dd522fca1a520ad/json
865aba25526efd1374f8139ebcd604817484a7f159307a028dd522fca1a520ad/layer.tar
9a6e5a8be5847534c8f0cfa2afd2bcfa544ada55a0f5dc2e7bd208fd94314349/
9a6e5a8be5847534c8f0cfa2afd2bcfa544ada55a0f5dc2e7bd208fd94314349/VERSION
9a6e5a8be5847534c8f0cfa2afd2bcfa544ada55a0f5dc2e7bd208fd94314349/json
9a6e5a8be5847534c8f0cfa2afd2bcfa544ada55a0f5dc2e7bd208fd94314349/layer.tar
a195f48bacf358da49ca6598a1b6a8244442fb873378f5a8b9c6a5d7b5073356/
a195f48bacf358da49ca6598a1b6a8244442fb873378f5a8b9c6a5d7b5073356/VERSION
a195f48bacf358da49ca6598a1b6a8244442fb873378f5a8b9c6a5d7b5073356/json
a195f48bacf358da49ca6598a1b6a8244442fb873378f5a8b9c6a5d7b5073356/layer.tar
e0e0188576ac2dc737a32a6f3e085869a45e4b927c044ea176943cb05ea3141a/
e0e0188576ac2dc737a32a6f3e085869a45e4b927c044ea176943cb05ea3141a/VERSION
e0e0188576ac2dc737a32a6f3e085869a45e4b927c044ea176943cb05ea3141a/json
e0e0188576ac2dc737a32a6f3e085869a45e4b927c044ea176943cb05ea3141a/layer.tar
manifest.json
repositories
```

```bash
$ cd a195f48bacf358da49ca6598a1b6a8244442fb873378f5a8b9c6a5d7b5073356/
$ ls
VERSION  json  layer.tar
$ tar -xvf layer.tar 
system-processor.json
```

Moment of truth... I did this for both ARM and x86.

```console
# This is for arm
          "9.botomips": "2100.00",
          "9.family": "8",
          "9.features": "fp asimd evtstrm aes pmull sha1 sha2 crc32 atomics fphp asimdhp cpuid asimdrdm jscvt fcma lrcpc dcpop sha3 sm3 sm4 asimddp sha512 sve asimdfhm dit uscat ilrcpc flagm ssbs paca pacg dcpodp svei8mm svebf16 i8mm bf16 dgh rng",
          "9.model": "0x1",
          "9.vendor": "ARM"

# This is amd64
          "9.botomips": "2100.00",
          "9.family": "8",
          "9.features": "fp asimd evtstrm aes pmull sha1 sha2 crc32 atomics fphp asimdhp cpuid asimdrdm jscvt fcma lrcpc dcpop sha3 sm3 sm4 asimddp sha512 sve asimdfhm dit uscat ilrcpc flagm ssbs paca pacg dcpodp svei8mm svebf16 i8mm bf16 dgh rng",
          "9.model": "0x1",
          "9.vendor": "ARM"
```

OH NOOOO it's the same! We don't see the buildx innards, we see our host. Oh no no no. This build strategy won't work. To step back, I've identified two issues here:

- Most base images are the basic, vanilla arches (amd64, arm64) and we won't get a lot of variation beyond that.
- Even when we use buildx, we still are getting the host it was built on.

I think we probably need to have an on-the-fly build for the node we are deploying to, which we've talked about, OR we can try manually setting flags to match faux architectures (or node architectures that we haven't been able to build for, but now I'm seriously doubting the niche ones we want even exist). Need to think more on this.
