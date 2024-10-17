# NCCL-Benchmark

This a little project that helps set up the
[nccl-tests](https://github.com/NVIDIA/nccl-tests) on Alps using a custom
**uenv**.

## Build Instructions

### Creating the uenv

The recipe for the **uenv** is located in `uenv-recipe`. You will need
[stackinator](https://github.com/eth-cscs/stackinator), see the
[docs](https://eth-cscs.github.io/stackinator/configuring/) for information on
how to configure and build the stack. The recipe needs to be specialized for
the intended vCluster, so you'll also need
[alps-cluster-config](https://github.com/eth-cscs/alps-cluster-config).

The process should look roughly like this:

1. Allocate a compute node for building

        salloc -N 1 --time=05:00:00 --account <my-account>

2. Run interactively once the allocation has been granted

        srun --nodes=1 --pty bash -i

3. Go to the recipe folder and configure the stack

        cd uenv-recipe
        /path/to/stackinator/bin/stack-config \
            -c /path/to/cache-config.yaml \
            -b /dev/shm/$USER/stack-build \
            -s /path/to/alps-cluster-config/todi \
            -m /user-environment \
            -r . \
            --develop
        cd /dev/shm/$USER/stack-build
        env --ignore-environment http_proxy="$http_proxy" https_proxy="$https_proxy" no_proxy="$no_proxy" PATH=/usr/bin:/bin:`pwd`/spack/bin HOME=$HOME make store.squashfs -j200

4. Copy the resulting store.squashfs into the top level directory

5. Quit the interactive session


### Building the Benchmarks

The binaries can be created using the `cmake` meta build system.

1. In order for all dependencies to be visible to `cmake` we need to first activate the uenv

        uenv start store.squashfs
        uenv view default

2. Build the code

        mkdir build; cd build
        cmake ..
        make -j16
        cd ..


## Run Instructions

The `run.sh` script launches a job. It takes for arguments:

    ./run.sh num-nodes [tasks-per-node] [time-limit] [path-to-binary]

- Only the first argument is necessary, the others are optional
- `tasks-per-node` can be either `1`or `4`
- `time-limit` should be in the format `HH:MM:SS`

Have a look at the script to potentially change the slurm parameters, such as
account and reservation. Be sure to create the output directory `logs` before
you run the first time.
